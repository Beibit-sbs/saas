from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantResourceNotFoundError,
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
    validate_version_match,
)
from app.modules.audit.service import log_admin_action
from app.modules.interventions.playbook_models import (
    PlaybookExecutionModel,
    PlaybookExecutionStatus,
    PlaybookModel,
    PlaybookStepExecutionModel,
    PlaybookStepExecutionStatus,
    PlaybookStepModel,
)
from app.modules.interventions.playbook_schemas import (
    PlaybookCreateSchema,
    PlaybookExecutionStartSchema,
    PlaybookStepCompleteSchema,
    PlaybookStepSkipSchema,
    PlaybookUpdateSchema,
)
from app.modules.observability.metrics import (
    observe_playbook_execution_finished,
    observe_playbook_execution_started,
    observe_playbook_step_action,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


MAX_PLAYBOOK_STEPS = 50
MAX_CONCURRENT_EXECUTIONS_PER_STUDENT = 3
MAX_CONCURRENT_EXECUTIONS_PER_CASE = 2


def _audit(*, actor: str, action: str, entity: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path="playbook_service",
        client_ip="service",
        entity=entity,
        metadata=metadata,
        tenant_id=tenant_id,
    )


class PlaybookService:
    """CRUD + execution engine for F2 intervention playbooks."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Playbook templates
    # ------------------------------------------------------------------

    def create_playbook(
        self,
        *,
        tenant_id: int,
        actor: str,
        payload: PlaybookCreateSchema,
    ) -> PlaybookModel:
        validate_tenant_id_provided(tenant_id)
        db = self._db

        # Prevent duplicate name within tenant
        existing = db.scalar(
            select(PlaybookModel).where(
                and_(
                    PlaybookModel.tenant_id == tenant_id,
                    PlaybookModel.name == payload.name,
                )
            )
        )
        if existing is not None:
            raise DomainValidationError(
                f"Playbook with name '{payload.name}' already exists for this tenant."
            )
        if len(payload.steps) > MAX_PLAYBOOK_STEPS:
            raise DomainValidationError(
                f"Playbook exceeds max steps limit ({MAX_PLAYBOOK_STEPS})."
            )
        step_orders = [s.step_order for s in payload.steps]
        if len(step_orders) != len(set(step_orders)):
            raise DomainValidationError("Playbook contains duplicate step_order values.")

        playbook = PlaybookModel(
            tenant_id=tenant_id,
            name=payload.name,
            description=payload.description,
            trigger_threshold_id=payload.trigger_threshold_id,
            enabled=payload.enabled,
            metadata_json=payload.metadata_json,
            created_by=actor,
            updated_by=actor,
        )
        db.add(playbook)
        db.flush()

        for step_data in sorted(payload.steps, key=lambda s: s.step_order):
            step = PlaybookStepModel(
                playbook_id=playbook.id,
                step_order=step_data.step_order,
                title=step_data.title,
                action_type=step_data.action_type,
                rationale=step_data.rationale,
                is_mandatory=step_data.is_mandatory,
                due_days_offset=step_data.due_days_offset,
                assignee_role=step_data.assignee_role,
                metadata_json=step_data.metadata_json,
            )
            db.add(step)

        db.flush()
        _audit(
            actor=actor,
            action="playbook.create",
            entity=f"playbook:{playbook.id}",
            metadata={"name": payload.name, "steps": len(payload.steps)},
            tenant_id=tenant_id,
        )
        return playbook

    def get_playbook(self, *, tenant_id: int, playbook_id: int) -> PlaybookModel:
        validate_tenant_id_provided(tenant_id)
        playbook = self._db.scalar(
            select(PlaybookModel)
            .options(selectinload(PlaybookModel.steps))
            .where(PlaybookModel.id == playbook_id)
        )
        if playbook is None:
            raise TenantResourceNotFoundError(f"Playbook {playbook_id} not found.")
        assert_resource_belongs_to_tenant(playbook, tenant_id)
        return playbook

    def list_playbooks(
        self,
        *,
        tenant_id: int,
        enabled_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PlaybookModel], int]:
        validate_tenant_id_provided(tenant_id)
        q = select(PlaybookModel).options(selectinload(PlaybookModel.steps)).where(
            PlaybookModel.tenant_id == tenant_id
        )
        if enabled_only:
            q = q.where(PlaybookModel.enabled.is_(True))

        total: int = self._db.scalar(
            select(func.count()).select_from(q.subquery())
        ) or 0
        items = list(
            self._db.scalars(q.order_by(PlaybookModel.name).offset(offset).limit(limit))
        )
        return items, total

    def update_playbook(
        self,
        *,
        tenant_id: int,
        playbook_id: int,
        actor: str,
        payload: PlaybookUpdateSchema,
    ) -> PlaybookModel:
        validate_tenant_id_provided(tenant_id)
        playbook = self._db.get(PlaybookModel, playbook_id)
        if playbook is None:
            raise TenantResourceNotFoundError(f"Playbook {playbook_id} not found.")
        assert_resource_belongs_to_tenant(playbook, tenant_id)
        validate_version_match(playbook, payload.expected_version)

        if payload.name is not None:
            playbook.name = payload.name
        if payload.description is not None:
            playbook.description = payload.description
        if payload.trigger_threshold_id is not None:
            playbook.trigger_threshold_id = payload.trigger_threshold_id
        if payload.enabled is not None:
            playbook.enabled = payload.enabled
        if payload.metadata_json is not None:
            playbook.metadata_json = payload.metadata_json

        playbook.version += 1
        playbook.updated_by = actor
        playbook.updated_at = _utc_now()
        self._db.flush()

        _audit(
            actor=actor,
            action="playbook.update",
            entity=f"playbook:{playbook_id}",
            metadata={"new_version": playbook.version},
            tenant_id=tenant_id,
        )
        return playbook

    def delete_playbook(
        self, *, tenant_id: int, playbook_id: int, actor: str
    ) -> None:
        validate_tenant_id_provided(tenant_id)
        playbook = self._db.get(PlaybookModel, playbook_id)
        if playbook is None:
            raise TenantResourceNotFoundError(f"Playbook {playbook_id} not found.")
        assert_resource_belongs_to_tenant(playbook, tenant_id)

        # Guard: cannot delete if active executions exist
        active_count = self._db.scalar(
            select(func.count()).where(
                and_(
                    PlaybookExecutionModel.playbook_id == playbook_id,
                    PlaybookExecutionModel.status.in_(
                        [PlaybookExecutionStatus.PENDING, PlaybookExecutionStatus.IN_PROGRESS]
                    ),
                )
            )
        ) or 0
        if active_count > 0:
            raise DomainValidationError(
                f"Cannot delete playbook with {active_count} active execution(s)."
            )

        self._db.delete(playbook)
        self._db.flush()
        _audit(
            actor=actor,
            action="playbook.delete",
            entity=f"playbook:{playbook_id}",
            metadata={},
            tenant_id=tenant_id,
        )

    # ------------------------------------------------------------------
    # Playbook execution engine
    # ------------------------------------------------------------------

    def start_execution(
        self,
        *,
        tenant_id: int,
        actor: str,
        payload: PlaybookExecutionStartSchema,
    ) -> PlaybookExecutionModel:
        validate_tenant_id_provided(tenant_id)
        db = self._db

        # Load playbook (must be enabled + belong to tenant)
        playbook = db.scalar(
            select(PlaybookModel)
            .options(selectinload(PlaybookModel.steps))
            .where(PlaybookModel.id == payload.playbook_id)
        )
        if playbook is None:
            raise TenantResourceNotFoundError(
                f"Playbook {payload.playbook_id} not found."
            )
        assert_resource_belongs_to_tenant(playbook, tenant_id)
        if not playbook.enabled:
            raise DomainValidationError(
                f"Playbook {payload.playbook_id} is disabled."
            )

        if payload.student_profile_id is not None:
            active_for_student = db.scalar(
                select(func.count()).where(
                    and_(
                        PlaybookExecutionModel.tenant_id == tenant_id,
                        PlaybookExecutionModel.student_profile_id == payload.student_profile_id,
                        PlaybookExecutionModel.status.in_(
                            [
                                PlaybookExecutionStatus.PENDING,
                                PlaybookExecutionStatus.IN_PROGRESS,
                            ]
                        ),
                    )
                )
            ) or 0
            if active_for_student >= MAX_CONCURRENT_EXECUTIONS_PER_STUDENT:
                raise DomainValidationError(
                    "Too many active playbook executions for this student profile."
                )

        if payload.case_id is not None:
            active_for_case = db.scalar(
                select(func.count()).where(
                    and_(
                        PlaybookExecutionModel.tenant_id == tenant_id,
                        PlaybookExecutionModel.case_id == payload.case_id,
                        PlaybookExecutionModel.status.in_(
                            [
                                PlaybookExecutionStatus.PENDING,
                                PlaybookExecutionStatus.IN_PROGRESS,
                            ]
                        ),
                    )
                )
            ) or 0
            if active_for_case >= MAX_CONCURRENT_EXECUTIONS_PER_CASE:
                raise DomainValidationError(
                    "Too many active playbook executions for this intervention case."
                )

        execution = PlaybookExecutionModel(
            tenant_id=tenant_id,
            playbook_id=playbook.id,
            case_id=payload.case_id,
            student_profile_id=payload.student_profile_id,
            triggered_by=payload.triggered_by,
            status=PlaybookExecutionStatus.IN_PROGRESS,
            started_at=_utc_now(),
            metadata_json=payload.metadata_json,
            created_by=actor,
        )
        db.add(execution)
        db.flush()

        # Create step execution stubs in order
        for step in sorted(playbook.steps, key=lambda s: s.step_order):
            step_exec = PlaybookStepExecutionModel(
                execution_id=execution.id,
                step_id=step.id,
                status=PlaybookStepExecutionStatus.PENDING,
                metadata_json={},
            )
            db.add(step_exec)

        db.flush()
        observe_playbook_execution_started(
            tenant_id=tenant_id,
            triggered_by=payload.triggered_by.value,
        )
        _audit(
            actor=actor,
            action="playbook_execution.start",
            entity=f"execution:{execution.id}",
            metadata={
                "playbook_id": playbook.id,
                "triggered_by": payload.triggered_by.value,
                "case_id": payload.case_id,
                "student_profile_id": payload.student_profile_id,
            },
            tenant_id=tenant_id,
        )
        return execution

    def get_execution(
        self, *, tenant_id: int, execution_id: int
    ) -> PlaybookExecutionModel:
        validate_tenant_id_provided(tenant_id)
        execution = self._db.scalar(
            select(PlaybookExecutionModel)
            .options(selectinload(PlaybookExecutionModel.step_executions))
            .where(PlaybookExecutionModel.id == execution_id)
        )
        if execution is None:
            raise TenantResourceNotFoundError(f"Execution {execution_id} not found.")
        assert_resource_belongs_to_tenant(execution, tenant_id)
        return execution

    def list_executions(
        self,
        *,
        tenant_id: int,
        playbook_id: int | None = None,
        case_id: int | None = None,
        status: PlaybookExecutionStatus | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PlaybookExecutionModel], int]:
        validate_tenant_id_provided(tenant_id)
        q = (
            select(PlaybookExecutionModel)
            .options(selectinload(PlaybookExecutionModel.step_executions))
            .where(PlaybookExecutionModel.tenant_id == tenant_id)
        )
        if playbook_id is not None:
            q = q.where(PlaybookExecutionModel.playbook_id == playbook_id)
        if case_id is not None:
            q = q.where(PlaybookExecutionModel.case_id == case_id)
        if status is not None:
            q = q.where(PlaybookExecutionModel.status == status)

        total: int = self._db.scalar(
            select(func.count()).select_from(q.subquery())
        ) or 0
        items = list(
            self._db.scalars(
                q.order_by(desc(PlaybookExecutionModel.started_at))
                .offset(offset)
                .limit(limit)
            )
        )
        return items, total

    def complete_step(
        self,
        *,
        tenant_id: int,
        execution_id: int,
        step_execution_id: int,
        actor: str,
        payload: PlaybookStepCompleteSchema,
    ) -> PlaybookStepExecutionModel:
        validate_tenant_id_provided(tenant_id)
        db = self._db

        step_exec = db.get(PlaybookStepExecutionModel, step_execution_id)
        if step_exec is None:
            raise TenantResourceNotFoundError(
                f"Step execution {step_execution_id} not found."
            )
        if step_exec.execution_id != execution_id:
            raise DomainValidationError("Step execution does not belong to this execution.")

        # Verify parent execution belongs to tenant
        execution = db.get(PlaybookExecutionModel, execution_id)
        if execution is None:
            raise TenantResourceNotFoundError(f"Execution {execution_id} not found.")
        assert_resource_belongs_to_tenant(execution, tenant_id)

        if execution.status not in (
            PlaybookExecutionStatus.PENDING,
            PlaybookExecutionStatus.IN_PROGRESS,
        ):
            raise DomainValidationError(
                f"Cannot complete step on execution with status '{execution.status.value}'."
            )
        if step_exec.status == PlaybookStepExecutionStatus.COMPLETED:
            raise DomainValidationError("Step already completed.")

        step_exec.status = PlaybookStepExecutionStatus.COMPLETED
        step_exec.performed_by = actor
        step_exec.performed_at = _utc_now()
        step_exec.outcome_note = payload.outcome_note
        if payload.metadata_json:
            step_exec.metadata_json = payload.metadata_json
        db.flush()
        observe_playbook_step_action(tenant_id=tenant_id, action="completed")

        # Auto-advance execution if all mandatory steps done
        self._maybe_complete_execution(execution)
        db.flush()
        return step_exec

    def skip_step(
        self,
        *,
        tenant_id: int,
        execution_id: int,
        step_execution_id: int,
        actor: str,
        payload: PlaybookStepSkipSchema,
    ) -> PlaybookStepExecutionModel:
        validate_tenant_id_provided(tenant_id)
        db = self._db

        step_exec = db.get(PlaybookStepExecutionModel, step_execution_id)
        if step_exec is None:
            raise TenantResourceNotFoundError(
                f"Step execution {step_execution_id} not found."
            )
        if step_exec.execution_id != execution_id:
            raise DomainValidationError("Step execution does not belong to this execution.")

        execution = db.get(PlaybookExecutionModel, execution_id)
        if execution is None:
            raise TenantResourceNotFoundError(f"Execution {execution_id} not found.")
        assert_resource_belongs_to_tenant(execution, tenant_id)

        if execution.status not in (
            PlaybookExecutionStatus.PENDING,
            PlaybookExecutionStatus.IN_PROGRESS,
        ):
            raise DomainValidationError(
                f"Cannot skip step on execution with status '{execution.status.value}'."
            )

        # Check if mandatory
        step = db.get(PlaybookStepModel, step_exec.step_id)
        if step and step.is_mandatory:
            raise DomainValidationError("Cannot skip a mandatory step.")

        step_exec.status = PlaybookStepExecutionStatus.SKIPPED
        step_exec.performed_by = actor
        step_exec.performed_at = _utc_now()
        step_exec.outcome_note = payload.outcome_note
        db.flush()
        observe_playbook_step_action(tenant_id=tenant_id, action="skipped")

        self._maybe_complete_execution(execution)
        db.flush()
        return step_exec

    def abandon_execution(
        self,
        *,
        tenant_id: int,
        execution_id: int,
        actor: str,
        reason: str,
    ) -> PlaybookExecutionModel:
        validate_tenant_id_provided(tenant_id)
        db = self._db

        execution = db.get(PlaybookExecutionModel, execution_id)
        if execution is None:
            raise TenantResourceNotFoundError(f"Execution {execution_id} not found.")
        assert_resource_belongs_to_tenant(execution, tenant_id)

        if execution.status in (
            PlaybookExecutionStatus.COMPLETED,
            PlaybookExecutionStatus.ABANDONED,
        ):
            raise DomainValidationError(
                f"Execution already '{execution.status.value}'."
            )

        execution.status = PlaybookExecutionStatus.ABANDONED
        execution.abandoned_at = _utc_now()
        execution.abandon_reason = reason
        execution.updated_at = _utc_now()
        db.flush()
        duration_seconds = max(
            0.0,
            ((execution.abandoned_at or _utc_now()) - execution.started_at).total_seconds(),
        )
        observe_playbook_execution_finished(
            tenant_id=tenant_id,
            status=PlaybookExecutionStatus.ABANDONED.value,
            duration_seconds=duration_seconds,
        )

        _audit(
            actor=actor,
            action="playbook_execution.abandon",
            entity=f"execution:{execution_id}",
            metadata={"reason": reason},
            tenant_id=tenant_id,
        )
        return execution

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _maybe_complete_execution(self, execution: PlaybookExecutionModel) -> None:
        """Auto-complete execution when all non-skipped steps are done."""
        db = self._db
        step_execs = list(
            db.scalars(
                select(PlaybookStepExecutionModel).where(
                    PlaybookStepExecutionModel.execution_id == execution.id
                )
            )
        )
        all_done = all(
            se.status in (
                PlaybookStepExecutionStatus.COMPLETED,
                PlaybookStepExecutionStatus.SKIPPED,
            )
            for se in step_execs
        )
        if all_done and step_execs:
            execution.status = PlaybookExecutionStatus.COMPLETED
            execution.completed_at = _utc_now()
            execution.updated_at = _utc_now()
            duration_seconds = max(
                0.0,
                ((execution.completed_at or _utc_now()) - execution.started_at).total_seconds(),
            )
            observe_playbook_execution_finished(
                tenant_id=execution.tenant_id,
                status=PlaybookExecutionStatus.COMPLETED.value,
                duration_seconds=duration_seconds,
            )
