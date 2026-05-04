from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from collections.abc import Callable

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import (
    DomainValidationError,
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
    validate_version_match,
)
from app.modules.audit.service import log_admin_action
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.modules.interventions.models import (
    InterventionActionModel,
    InterventionActionType,
    InterventionAssigneeType,
    InterventionCaseModel,
    InterventionCaseSeverity,
    InterventionCaseStatus,
)
from app.modules.interventions.schemas import (
    InterventionActionCreateSchema,
    InterventionCaseAssignSchema,
    InterventionCaseCreateSchema,
    InterventionCaseStatusUpdateSchema,
    InterventionCaseTakeSchema,
)
from app.modules.interventions.schemas import (
    InterventionConsistencyIssueSchema,
    InterventionConsistencyReportSchema,
)
from app.modules.students.models import StudentProfileModel
from app.modules.usage.service import record_usage_event
from app.platform.events.publisher import EventPublisher


logger = logging.getLogger(__name__)


_ALLOWED_STATUS_TRANSITIONS: dict[InterventionCaseStatus, set[InterventionCaseStatus]] = {
    InterventionCaseStatus.OPEN: {
        InterventionCaseStatus.IN_PROGRESS,
        InterventionCaseStatus.RESOLVED,
        InterventionCaseStatus.CLOSED,
    },
    InterventionCaseStatus.IN_PROGRESS: {
        InterventionCaseStatus.OPEN,
        InterventionCaseStatus.RESOLVED,
        InterventionCaseStatus.CLOSED,
    },
    InterventionCaseStatus.RESOLVED: {
        InterventionCaseStatus.CLOSED,
        InterventionCaseStatus.OPEN,
    },
    InterventionCaseStatus.CLOSED: set(),
}


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _audit(*, actor: str, action: str, path: str, entity: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity=entity,
        metadata=metadata,
        tenant_id=tenant_id,
    )


def _default_assignment_for_severity(
    severity: InterventionCaseSeverity,
) -> tuple[InterventionAssigneeType, str]:
    if severity == InterventionCaseSeverity.HIGH:
        return InterventionAssigneeType.GROUP, "dean_office"
    if severity == InterventionCaseSeverity.MEDIUM:
        return InterventionAssigneeType.GROUP, "faculty_advisor"
    return InterventionAssigneeType.GROUP, "student_support"


def _default_due_at(severity: InterventionCaseSeverity) -> datetime:
    days = {
        InterventionCaseSeverity.HIGH: 3,
        InterventionCaseSeverity.MEDIUM: 5,
        InterventionCaseSeverity.LOW: 7,
    }[severity]
    return _utc_now() + timedelta(days=days)


class InterventionService:
    def __init__(self, db_session: Session, on_case_outcome: Callable[..., object] | None = None):
        self.db = db_session
        self._on_case_outcome = on_case_outcome

    @staticmethod
    def _normalized_tenant_id(tenant_id: int) -> int:
        return int(tenant_id)

    @staticmethod
    def _emit_case_event(
        *,
        tenant_id: int,
        event_type: str,
        case: InterventionCaseModel,
        payload: dict,
        publish: bool = True,
    ) -> None:
        if not publish:
            return
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type=event_type,
            aggregate_type="intervention_case",
            aggregate_id=str(case.id),
            payload_json=payload,
        )

    async def create_case(
        self,
        *,
        tenant_id: int,
        request: InterventionCaseCreateSchema,
        actor: str,
    ) -> InterventionCaseModel:
        tenant_id = validate_tenant_id_provided(tenant_id)

        if request.student_profile_id is not None:
            student = self.db.execute(
                select(StudentProfileModel).where(
                    and_(
                        StudentProfileModel.id == request.student_profile_id,
                        StudentProfileModel.tenant_id == tenant_id,
                    )
                )
            ).scalar_one_or_none()
            assert_resource_belongs_to_tenant(
                student,
                tenant_id,
                resource_name="Student profile",
                resource_id=request.student_profile_id,
            )

            # Enforce: one open case per student (OPEN or IN_PROGRESS)
            existing_open = self.db.execute(
                select(InterventionCaseModel).where(
                    and_(
                        InterventionCaseModel.tenant_id == tenant_id,
                        InterventionCaseModel.student_profile_id == request.student_profile_id,
                        InterventionCaseModel.status.in_(
                            (InterventionCaseStatus.OPEN, InterventionCaseStatus.IN_PROGRESS)
                        ),
                    )
                )
            ).scalar_one_or_none()
            if existing_open is not None:
                raise DomainValidationError(
                    f"Student {request.student_profile_id} already has an open intervention case "
                    f"(case_id={existing_open.id}, status={existing_open.status.value}). "
                    "Close or resolve it before opening a new case."
                )
        assignee_type = request.assignee_type
        assignee_ref = request.assignee_ref
        if assignee_type is None or assignee_ref is None:
            assignee_type, assignee_ref = _default_assignment_for_severity(request.severity)

        due_at = request.due_at or _default_due_at(request.severity)

        case = InterventionCaseModel(
            tenant_id=tenant_id,
            case_type=request.case_type,
            student_profile_id=request.student_profile_id,
            severity=request.severity,
            status=InterventionCaseStatus.OPEN,
            title=request.title,
            description=request.description,
            risk_snapshot_json=request.risk_snapshot_json,
            assignee_type=assignee_type,
            assignee_ref=assignee_ref,
            due_at=due_at,
            metadata_json=request.metadata_json,
            created_by=actor,
            updated_by=actor,
        )
        self.db.add(case)
        self.db.flush()

        self.db.add(
            InterventionActionModel(
                tenant_id=tenant_id,
                case_id=case.id,
                action_type=InterventionActionType.ASSIGNMENT,
                description=f"Auto-assigned to {assignee_type.value}:{assignee_ref}",
                outcome_note=None,
                performed_by=actor,
                metadata_json={"auto_assignment": True},
            )
        )

        self.db.flush()
        self.db.refresh(case)

        _audit(
            actor=actor,
            action=build_audit_action("interventions", "case", "create"),
            path=f"/internal/interventions/cases/{case.id}",
            entity="intervention_case",
            metadata={
                "resource_id": str(case.id),
                "severity": case.severity.value,
                "status": case.status.value,
            },
            tenant_id=tenant_id,
        )

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to create intervention case due to constraint violation") from exc

        # Event emission strictly after successful persistence.
        self._emit_case_event(
            tenant_id=tenant_id,
            event_type="interventions.case.created",
            case=case,
            payload={
                "case_id": str(case.id),
                "case_type": case.case_type.value,
                "status": case.status.value,
                "severity": case.severity.value,
                "student_profile_id": str(case.student_profile_id) if case.student_profile_id else None,
                "source_entity_type": "intervention_case",
                "source_entity_id": str(case.id),
                "source_module": "interventions",
            },
        )
        record_usage_event(
            tenant_id=self._normalized_tenant_id(tenant_id),
            metric="interventions_cases_created",
            value=1,
        )

        return case

    async def list_cases(
        self,
        *,
        tenant_id: int,
        page: int,
        page_size: int,
        status: InterventionCaseStatus | None = None,
        severity: InterventionCaseSeverity | None = None,
        assignee_ref: str | None = None,
        overdue_only: bool = False,
    ) -> tuple[int, list[InterventionCaseModel]]:
        tenant_id = validate_tenant_id_provided(tenant_id)

        filters = [InterventionCaseModel.tenant_id == tenant_id]
        if status is not None:
            filters.append(InterventionCaseModel.status == status)
        if severity is not None:
            filters.append(InterventionCaseModel.severity == severity)
        if assignee_ref is not None:
            filters.append(InterventionCaseModel.assignee_ref == assignee_ref)
        if overdue_only:
            filters.append(InterventionCaseModel.due_at < _utc_now())
            filters.append(InterventionCaseModel.status.in_((InterventionCaseStatus.OPEN, InterventionCaseStatus.IN_PROGRESS)))

        total = self.db.execute(
            select(func.count()).select_from(InterventionCaseModel).where(and_(*filters))
        ).scalar_one()

        items = self.db.execute(
            select(InterventionCaseModel)
            .where(and_(*filters))
            .order_by(asc(InterventionCaseModel.status), desc(InterventionCaseModel.severity), asc(InterventionCaseModel.due_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        return total, items

    async def get_case(self, *, tenant_id: int, case_id: int) -> InterventionCaseModel:
        tenant_id = validate_tenant_id_provided(tenant_id)

        case = self.db.execute(
            select(InterventionCaseModel).where(
                and_(InterventionCaseModel.id == case_id, InterventionCaseModel.tenant_id == tenant_id)
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            case,
            tenant_id,
            resource_name="Intervention case",
            resource_id=case_id,
        )
        return case

    async def assign_case(
        self,
        *,
        tenant_id: int,
        case_id: int,
        request: InterventionCaseAssignSchema,
        actor: str,
    ) -> InterventionCaseModel:
        case = await self.get_case(tenant_id=tenant_id, case_id=case_id)
        validate_version_match(case.version, request.expected_version)

        case.assignee_type = request.assignee_type
        case.assignee_ref = request.assignee_ref
        if request.due_at is not None:
            case.due_at = request.due_at
        case.updated_by = actor
        case.version += 1

        self.db.add(
            InterventionActionModel(
                tenant_id=tenant_id,
                case_id=case.id,
                action_type=InterventionActionType.ASSIGNMENT,
                description=f"Assigned to {request.assignee_type.value}:{request.assignee_ref}",
                outcome_note=None,
                performed_by=actor,
                metadata_json={"case_version": case.version},
            )
        )

        self.db.flush()
        self.db.refresh(case)
        self.db.commit()
        return case

    async def take_case(
        self,
        *,
        tenant_id: int,
        case_id: int,
        request: InterventionCaseTakeSchema,
        actor: str,
    ) -> InterventionCaseModel:
        case = await self.get_case(tenant_id=tenant_id, case_id=case_id)
        validate_version_match(case.version, request.expected_version)

        case.assignee_type = InterventionAssigneeType.USER
        case.assignee_ref = actor
        if case.status == InterventionCaseStatus.OPEN:
            case.status = InterventionCaseStatus.IN_PROGRESS
        case.updated_by = actor
        case.version += 1

        self.db.add(
            InterventionActionModel(
                tenant_id=tenant_id,
                case_id=case.id,
                action_type=InterventionActionType.ASSIGNMENT,
                description=f"Taken into work by {actor}",
                outcome_note=None,
                performed_by=actor,
                metadata_json={"case_version": case.version},
            )
        )

        self.db.flush()
        self.db.refresh(case)
        self.db.commit()
        return case

    async def update_case_status(
        self,
        *,
        tenant_id: int,
        case_id: int,
        request: InterventionCaseStatusUpdateSchema,
        actor: str,
    ) -> InterventionCaseModel:
        case = await self.get_case(tenant_id=tenant_id, case_id=case_id)
        validate_version_match(case.version, request.expected_version)

        old_status = case.status
        allowed_statuses = _ALLOWED_STATUS_TRANSITIONS.get(old_status, set())
        if request.status != old_status and request.status not in allowed_statuses:
            raise DomainValidationError(
                f"Intervention status transition not allowed: {old_status.value} -> {request.status.value}"
            )

        case.status = request.status
        if request.status in (InterventionCaseStatus.RESOLVED, InterventionCaseStatus.CLOSED):
            case.resolved_at = _utc_now()
        elif request.status in (InterventionCaseStatus.OPEN, InterventionCaseStatus.IN_PROGRESS):
            case.resolved_at = None

        case.updated_by = actor
        case.version += 1

        self.db.add(
            InterventionActionModel(
                tenant_id=tenant_id,
                case_id=case.id,
                action_type=InterventionActionType.STATUS_CHANGE,
                description=(
                    f"Status changed {old_status.value} -> {request.status.value}"
                    if request.reason is None
                    else f"Status changed {old_status.value} -> {request.status.value}: {request.reason}"
                ),
                outcome_note=request.reason,
                performed_by=actor,
                metadata_json={"case_version": case.version},
            )
        )

        self.db.flush()
        self.db.refresh(case)
        self.db.commit()

        # Emit status_changed for all transitions (including terminal).
        _terminal_statuses = (InterventionCaseStatus.RESOLVED, InterventionCaseStatus.CLOSED)
        self._emit_case_event(
            tenant_id=tenant_id,
            event_type="interventions.case.status_changed",
            case=case,
            payload={
                "case_id": str(case.id),
                "case_type": case.case_type.value,
                "old_status": old_status.value,
                "new_status": request.status.value,
                "severity": case.severity.value,
                "student_profile_id": str(case.student_profile_id) if case.student_profile_id else None,
                "source_entity_type": "intervention_case",
                "source_entity_id": str(case.id),
                "source_module": "interventions",
            },
            publish=request.status not in _terminal_statuses,
        )
        record_usage_event(
            tenant_id=self._normalized_tenant_id(tenant_id),
            metric="interventions_case_status_updates",
            value=1,
        )

        # Emit outcome event to Brain Core learning loop when case is completed
        if request.status in (InterventionCaseStatus.RESOLVED, InterventionCaseStatus.CLOSED):
            effectiveness = "positive" if request.status == InterventionCaseStatus.RESOLVED else "neutral"
            self._emit_case_event(
                tenant_id=tenant_id,
                event_type="interventions.case_outcome.recorded",
                case=case,
                payload={
                    "case_id": str(case.id),
                    "case_type": case.case_type.value,
                    "status": request.status.value,
                    "severity": case.severity.value,
                    "outcome_type": request.status.value,
                    "effectiveness": effectiveness,
                    "reason": request.reason or "",
                    "student_profile_id": str(case.student_profile_id) if case.student_profile_id else None,
                    "source_entity_type": "intervention_case",
                    "source_entity_id": str(case.id),
                },
            )
            record_usage_event(
                tenant_id=self._normalized_tenant_id(tenant_id),
                metric="interventions_case_outcomes_recorded",
                value=1,
            )
            
            # Immediately ingest outcome into Brain Core if callback is registered
            if self._on_case_outcome is not None:
                try:
                    self._on_case_outcome(
                        tenant_id,
                        case_id=str(case.id),
                        payload={
                            "case_id": str(case.id),
                            "outcome_type": request.status.value,
                            "effectiveness": effectiveness,
                            "notes": request.reason or "",
                            "source_entity_type": "intervention_case",
                        },
                        actor="system",
                    )
                except Exception as exc:
                    logger.warning(
                        "brain_core_outcome_ingestion_failed",
                        extra={
                            "case_id": str(case.id),
                            "error": str(exc),
                        },
                    )

        return case

    async def add_case_action(
        self,
        *,
        tenant_id: int,
        case_id: int,
        request: InterventionActionCreateSchema,
        actor: str,
    ) -> tuple[InterventionCaseModel, InterventionActionModel]:
        case = await self.get_case(tenant_id=tenant_id, case_id=case_id)
        validate_version_match(case.version, request.expected_version)

        action = InterventionActionModel(
            tenant_id=tenant_id,
            case_id=case.id,
            action_type=request.action_type,
            description=request.description,
            outcome_note=request.outcome_note,
            performed_by=actor,
            metadata_json=request.metadata_json,
        )
        self.db.add(action)

        if request.mark_case_in_progress and case.status == InterventionCaseStatus.OPEN:
            case.status = InterventionCaseStatus.IN_PROGRESS
        if request.mark_case_resolved:
            case.status = InterventionCaseStatus.RESOLVED
            case.resolved_at = _utc_now()

        case.updated_by = actor
        case.version += 1

        self.db.flush()
        self.db.refresh(case)
        self.db.refresh(action)

        _audit(
            actor=actor,
            action=build_audit_action("interventions", "action", "create"),
            path=f"/internal/interventions/cases/{case.id}/actions/{action.id}",
            entity="intervention_action",
            metadata={
                "resource_id": str(action.id),
                "case_id": str(case.id),
                "action_type": action.action_type.value,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return case, action

    async def list_case_actions(
        self,
        *,
        tenant_id: int,
        case_id: int,
        limit: int = 100,
    ) -> list[InterventionActionModel]:
        await self.get_case(tenant_id=tenant_id, case_id=case_id)
        return self.db.execute(
            select(InterventionActionModel)
            .where(
                and_(
                    InterventionActionModel.tenant_id == tenant_id,
                    InterventionActionModel.case_id == case_id,
                )
            )
            .order_by(desc(InterventionActionModel.performed_at))
            .limit(limit)
        ).scalars().all()

    async def list_tenant_intervention_consistency_report(
        self, tenant_id: int
    ) -> InterventionConsistencyReportSchema:
        validate_tenant_id_provided(tenant_id)
        issues: list[InterventionConsistencyIssueSchema] = []

        cases = self.db.execute(
            select(InterventionCaseModel).where(
                InterventionCaseModel.tenant_id == tenant_id
            )
        ).scalars().all()
        case_ids = {c.id for c in cases}

        # Cases pointing to non-existent student profiles
        student_ids = set(
            self.db.execute(
                select(StudentProfileModel.id).where(
                    StudentProfileModel.tenant_id == tenant_id
                )
            ).scalars().all()
        )
        for case in cases:
            if case.student_profile_id not in student_ids:
                issues.append(
                    InterventionConsistencyIssueSchema(
                        issue_type="case_missing_student_profile",
                        case_id=case.id,
                        student_profile_id=case.student_profile_id,
                    )
                )

        # Actions pointing to non-existent cases
        actions = self.db.execute(
            select(InterventionActionModel).where(
                InterventionActionModel.tenant_id == tenant_id
            )
        ).scalars().all()
        for action in actions:
            if action.case_id not in case_ids:
                issues.append(
                    InterventionConsistencyIssueSchema(
                        issue_type="action_orphaned_case",
                        action_id=action.id,
                        case_id=action.case_id,
                    )
                )

        return InterventionConsistencyReportSchema(
            case_count=len(cases),
            action_count=len(actions),
            issue_count=len(issues),
            issues=issues,
        )


# ─── XXXV.2: Cohort-based risk analytics ──────────────────────────────────────

_DEFAULT_RISK_THRESHOLD: float = 0.7


def _segment_students_by_risk(
    students: list[dict[str, object]],
    threshold: float,
) -> dict[str, list[dict[str, object]]]:
    """Segment students into high / medium / low risk groups."""
    high, medium, low = [], [], []
    for s in students:
        try:
            score = float(s.get("risk_score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        if score >= threshold:
            high.append(s)
        elif score >= threshold * 0.5:
            medium.append(s)
        else:
            low.append(s)
    return {"high": high, "medium": medium, "low": low}


def analyze_cohort_risk(
    tenant_id: int,
    cohort_id: str | None = None,
    threshold: float = _DEFAULT_RISK_THRESHOLD,
) -> dict[str, object]:
    """Analyse risk distribution across a student cohort.

    Reads students from the entity store, segments them by risk_score, and
    persists a snapshot in `cohort_risk_snapshots`.  For high-risk students
    an auto-triggered intervention is also persisted.

    Returns the analysis result dict.
    """
    if tenant_id is None or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer.")

    students = list_entities_for_tenant("students", tenant_id)
    if cohort_id:
        students = [s for s in students if str(s.get("cohort_id") or "") == str(cohort_id)]

    segments = _segment_students_by_risk(students, threshold)
    high_risk = segments["high"]

    # Persist snapshot
    snapshot = create_entity_for_tenant(
        "cohort_risk_snapshots",
        {
            "tenant_id": tenant_id,
            "cohort_id": cohort_id or "all",
            "total_students": len(students),
            "high_risk_count": len(high_risk),
            "medium_risk_count": len(segments["medium"]),
            "low_risk_count": len(segments["low"]),
            "threshold": str(threshold),
        },
        tenant_id,
    )

    # Publish cohort.analyzed event (fire-and-forget)
    try:
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="interventions.cohort.analyzed",
            aggregate_type="cohort_risk_snapshots",
            aggregate_id=str(snapshot.get("id", "")),
            payload_json={
                "cohort_id": cohort_id or "all",
                "high_risk_count": len(high_risk),
                "threshold": threshold,
            },
        )
    except Exception:  # noqa: BLE001
        pass

    # Auto-trigger interventions for high-risk students
    auto_triggered: list[dict[str, object]] = []
    for student in high_risk:
        student_id = str(student.get("id") or student.get("student_id") or "")
        if not student_id:
            continue
        try:
            record = create_entity_for_tenant(
                "auto_triggered_interventions",
                {
                    "tenant_id": tenant_id,
                    "student_id": student_id,
                    "cohort_id": cohort_id or "all",
                    "trigger_score": str(student.get("risk_score") or 0.0),
                    "status": "pending",
                },
                tenant_id,
            )
            auto_triggered.append(record)

            # fire auto-trigger event (fire-and-forget)
            try:
                EventPublisher().publish_event(
                    tenant_id=tenant_id,
                    event_type="interventions.auto_triggered",
                    aggregate_type="auto_triggered_interventions",
                    aggregate_id=str(record.get("id", "")),
                    payload_json={"student_id": student_id, "trigger_score": float(student.get("risk_score") or 0.0)},
                )
            except Exception:  # noqa: BLE001
                pass
        except Exception:  # noqa: BLE001
            pass  # non-blocking per-student failure

    return {
        "snapshot_id": snapshot.get("id"),
        "cohort_id": cohort_id or "all",
        "total_students": len(students),
        "segments": {k: len(v) for k, v in segments.items()},
        "auto_triggered_count": len(auto_triggered),
    }


def get_cohort_risk_snapshots(
    tenant_id: int,
    cohort_id: str | None = None,
) -> list[dict[str, object]]:
    """Return persisted cohort risk snapshots for a tenant."""
    rows = list_entities_for_tenant("cohort_risk_snapshots", tenant_id)
    if cohort_id:
        rows = [r for r in rows if str(r.get("cohort_id") or "") == str(cohort_id)]
    return rows
