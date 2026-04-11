from __future__ import annotations

from datetime import UTC, datetime, timedelta

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
    def __init__(self, db_session: Session):
        self.db = db_session

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
