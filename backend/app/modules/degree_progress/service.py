from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantResourceNotFoundError,
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
)
from app.modules.audit.service import log_admin_action
from app.modules.degree_progress.business_rules import DegreeProgressRules
from app.modules.degree_progress.models import ProgramRequirementItemModel, ProgramRequirementModel
from app.modules.degree_progress.schemas import (
    DegreeProgressConsistencyIssueSchema,
    DegreeProgressConsistencyReportSchema,
    DegreeProgressSchema,
    GraduationEligibilitySchema,
    RequirementStatusSchema,
)
from app.modules.students.models import StudentProgramBindingModel, StudentProgramBindingState, StudentProfileModel
from app.modules.transcripts.service import TranscriptService


def _emit_graduation_risk_signal(
    *,
    tenant_id: int,
    student_profile_id: int,
    program_id: int,
    credits_earned: int,
    minimum_credits: int,
    gpa: Decimal | None,
    minimum_gpa: Decimal,
    remaining_required_items: int,
) -> None:
    """Fire-and-forget: publish graduation_risk to Brain Core."""
    try:
        from app.platform.events.publisher import EventPublisher

        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="degree_progress.graduation_risk.detected",
            aggregate_type="student_graduation_progress",
            aggregate_id=student_profile_id,
            payload_json={
                "student_profile_id": student_profile_id,
                "program_id": program_id,
                "credits_earned": credits_earned,
                "minimum_credits": minimum_credits,
                "gpa": str(gpa) if gpa else "0.00",
                "minimum_gpa": str(minimum_gpa),
                "remaining_required_items": remaining_required_items,
                "source_module": "degree_progress",
            },
        )
    except Exception:  # noqa: BLE001
        logger = logging.getLogger("app.modules.degree_progress")
        logger.exception(
            "graduation_risk signal failed silently for tenant_id=%s student_profile_id=%s",
            tenant_id,
            student_profile_id,
        )


def _audit(actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="degree_progress",
        metadata=metadata,
        tenant_id=tenant_id,
    )


class DegreeProgressService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def _check_course_exists_in_tenant(self, tenant_id: int, course_id: int) -> None:
        """Cross-entity guard: course_id must exist in the tenant's course catalog.

        A requirement item referencing a phantom course creates a permanently-unsatisfiable
        requirement — every student in the program will have remaining_required_items >= 1
        forever and can never graduate without admin intervention.
        
        HARDENING RULE: NO SILENT FALLBACK — if validation cannot complete, block the action.
        """
        try:
            from app.modules.courses.models import CourseModel  # lazy — avoid circular import risk
        except ImportError as e:
            raise DomainValidationError(
                f"Cannot verify course_id={course_id} exists: courses module unavailable. "
                "Cannot enforce requirement invariant without access to course catalog."
            ) from e

        try:
            course = self.db.execute(
                select(CourseModel).where(
                    and_(
                        CourseModel.id == course_id,
                        CourseModel.tenant_id == str(tenant_id),
                    )
                )
            ).scalar_one_or_none()
        except Exception as e:
            raise DomainValidationError(
                f"Cannot verify course_id={course_id} exists in tenant_id={tenant_id}: "
                "database query failed. Cannot enforce requirement invariant."
            ) from e

        if course is None:
            raise DomainValidationError(
                f"Cannot add requirement item: course_id={course_id} does not exist "
                f"in the course catalog for tenant_id={tenant_id}. "
                "A phantom course reference creates a permanently unsatisfiable graduation requirement."
            )

    def create_program_requirement_item(
        self,
        tenant_id: int,
        *,
        requirement_id: int,
        course_id: int,
        credits: int,
        required: bool = True,
    ) -> ProgramRequirementItemModel:
        """Create a requirement item, enforcing course catalog existence guard."""
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._check_course_exists_in_tenant(tenant_id, course_id)

        item = ProgramRequirementItemModel(
            tenant_id=tenant_id,
            requirement_id=requirement_id,
            course_id=course_id,
            credits=credits,
            required=required,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def _load_student(self, tenant_id: int, student_profile_id: int) -> StudentProfileModel:
        student = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.id == student_profile_id,
                    StudentProfileModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            student,
            tenant_id,
            resource_name="Student profile",
            resource_id=student_profile_id,
        )
        return student

    def _load_active_primary_program_binding(self, tenant_id: int, student_profile_id: int) -> StudentProgramBindingModel:
        binding = self.db.execute(
            select(StudentProgramBindingModel).where(
                and_(
                    StudentProgramBindingModel.tenant_id == tenant_id,
                    StudentProgramBindingModel.student_profile_id == student_profile_id,
                    StudentProgramBindingModel.binding_state == StudentProgramBindingState.ACTIVE,
                    StudentProgramBindingModel.is_primary.is_(True),
                )
            )
        ).scalar_one_or_none()
        if binding is None:
            raise TenantResourceNotFoundError(
                f"Active primary program binding not found for student {student_profile_id} in tenant {tenant_id}"
            )
        return binding

    def _load_active_requirement(self, tenant_id: int, program_id: int) -> ProgramRequirementModel:
        requirement = self.db.execute(
            select(ProgramRequirementModel).where(
                and_(
                    ProgramRequirementModel.tenant_id == tenant_id,
                    ProgramRequirementModel.program_id == program_id,
                    ProgramRequirementModel.is_active.is_(True),
                )
            )
        ).scalars().first()
        DegreeProgressRules.validate_program_requirement(requirement)
        return requirement

    def _resolve_course_names(self, tenant_id: int, course_ids: list[int]) -> dict[int, str]:
        """Return {course_id: title} for the given ids within the tenant."""
        if not course_ids:
            return {}
        try:
            from app.modules.courses.models import CourseModel  # lazy import
        except ImportError:
            return {}
        try:
            rows = self.db.execute(
                select(CourseModel).where(
                    and_(
                        CourseModel.id.in_(course_ids),
                        CourseModel.tenant_id == str(tenant_id),
                    )
                )
            ).scalars().all()
        except Exception:
            # Keep degree-progress APIs resilient when catalog lookup is mocked/incomplete.
            return {}
        return {int(row.id): row.title for row in rows}

    def _resolve_program_name(self, tenant_id: int, program_id: int) -> str | None:
        """Return program title or None if not found."""
        try:
            from app.modules.programs.models import ProgramModel  # lazy import
        except ImportError:
            return None
        try:
            row = self.db.execute(
                select(ProgramModel.title).where(
                    and_(
                        ProgramModel.id == program_id,
                        ProgramModel.tenant_id == str(tenant_id),
                    )
                )
            ).scalar_one_or_none()
            return row if isinstance(row, str) else None
        except Exception:
            return None

    def _load_requirement_items(self, tenant_id: int, requirement_id: int) -> list[ProgramRequirementItemModel]:
        return self.db.execute(
            select(ProgramRequirementItemModel)
            .where(
                and_(
                    ProgramRequirementItemModel.tenant_id == tenant_id,
                    ProgramRequirementItemModel.requirement_id == requirement_id,
                )
            )
            .order_by(ProgramRequirementItemModel.required.desc(), ProgramRequirementItemModel.id)
        ).scalars().all()

    async def evaluate_degree_progress(
        self,
        tenant_id: int,
        *,
        student_profile_id: int,
        actor_id: str,
    ) -> DegreeProgressSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_student(tenant_id, student_profile_id)

        binding = self._load_active_primary_program_binding(tenant_id, student_profile_id)
        requirement = self._load_active_requirement(tenant_id, binding.program_id)
        req_items = self._load_requirement_items(tenant_id, requirement.id)

        transcript = await TranscriptService(self.db).get_student_transcript(
            tenant_id,
            student_profile_id=student_profile_id,
        )

        completed_course_ids = {
            int(item.course_id)
            for item in transcript.items
            if item.grade_code is not None and item.grade_points is not None and Decimal(str(item.grade_points)) > Decimal("0")
        }
        earned_credits = int(transcript.total_credits)

        all_course_ids = [item.course_id for item in req_items]
        course_names = self._resolve_course_names(tenant_id, all_course_ids)
        program_name = self._resolve_program_name(tenant_id, binding.program_id)

        completed: list[RequirementStatusSchema] = []
        remaining: list[RequirementStatusSchema] = []
        for item in req_items:
            status = RequirementStatusSchema(
                requirement_item_id=item.id,
                course_id=item.course_id,
                course_name=course_names.get(item.course_id),
                required=bool(item.required),
                credits=int(item.credits),
                completed=item.course_id in completed_course_ids,
            )
            if status.completed:
                completed.append(status)
            elif status.required:
                remaining.append(status)

        gpa_passed = DegreeProgressRules.validate_gpa_threshold(transcript.gpa, requirement.minimum_gpa)
        eligible = DegreeProgressRules.validate_degree_completion(
            earned_credits=earned_credits,
            minimum_credits=int(requirement.minimum_credits),
            remaining_required_items=len(remaining),
            gpa_passed=gpa_passed,
        )

        progress = DegreeProgressSchema(
            student_profile_id=student_profile_id,
            program_id=binding.program_id,
            program_name=program_name,
            requirement_id=requirement.id,
            requirement_name=requirement.name,
            credits_earned=earned_credits,
            minimum_credits=int(requirement.minimum_credits),
            gpa=transcript.gpa,
            minimum_gpa=Decimal(str(requirement.minimum_gpa)),
            completed_requirements=completed,
            remaining_requirements=remaining,
            graduation_eligible=eligible,
        )

        _audit(
            actor_id,
            build_audit_action("degree_progress", "evaluation", "generated"),
            f"/internal/degree-progress/students/{student_profile_id}/evaluate",
            {
                "student_profile_id": student_profile_id,
                "program_id": binding.program_id,
                "requirement_id": requirement.id,
                "graduation_eligible": eligible,
            },
            tenant_id,
        )

        return progress

    async def get_completed_requirements(
        self,
        tenant_id: int,
        *,
        student_profile_id: int,
        actor_id: str,
    ) -> list[RequirementStatusSchema]:
        progress = await self.evaluate_degree_progress(
            tenant_id,
            student_profile_id=student_profile_id,
            actor_id=actor_id,
        )
        return progress.completed_requirements

    async def get_remaining_requirements(
        self,
        tenant_id: int,
        *,
        student_profile_id: int,
        actor_id: str,
    ) -> list[RequirementStatusSchema]:
        progress = await self.evaluate_degree_progress(
            tenant_id,
            student_profile_id=student_profile_id,
            actor_id=actor_id,
        )
        return progress.remaining_requirements

    async def is_student_eligible_for_graduation(
        self,
        tenant_id: int,
        *,
        student_profile_id: int,
        actor_id: str,
    ) -> GraduationEligibilitySchema:
        progress = await self.evaluate_degree_progress(
            tenant_id,
            student_profile_id=student_profile_id,
            actor_id=actor_id,
        )

        # Emit graduation risk signal if student not eligible (at-risk condition)
        if not progress.graduation_eligible:
            _emit_graduation_risk_signal(
                tenant_id=tenant_id,
                student_profile_id=student_profile_id,
                program_id=progress.program_id,
                credits_earned=progress.credits_earned,
                minimum_credits=progress.minimum_credits,
                gpa=progress.gpa,
                minimum_gpa=progress.minimum_gpa,
                remaining_required_items=len(progress.remaining_requirements),
            )

        return GraduationEligibilitySchema(
            student_profile_id=student_profile_id,
            eligible=progress.graduation_eligible,
            credits_earned=progress.credits_earned,
            minimum_credits=progress.minimum_credits,
            gpa=progress.gpa,
            minimum_gpa=progress.minimum_gpa,
            remaining_required_items=len(progress.remaining_requirements),
        )

    async def list_tenant_degree_progress_consistency_report(
        self,
        tenant_id: int,
    ) -> DegreeProgressConsistencyReportSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        active_primary_bindings = self.db.execute(
            select(StudentProgramBindingModel)
            .where(
                and_(
                    StudentProgramBindingModel.tenant_id == tenant_id,
                    StudentProgramBindingModel.binding_state == StudentProgramBindingState.ACTIVE,
                    StudentProgramBindingModel.is_primary.is_(True),
                )
            )
            .order_by(StudentProgramBindingModel.student_profile_id, StudentProgramBindingModel.id)
        ).scalars().all()

        active_requirements = self.db.execute(
            select(ProgramRequirementModel)
            .where(
                and_(
                    ProgramRequirementModel.tenant_id == tenant_id,
                    ProgramRequirementModel.is_active.is_(True),
                )
            )
            .order_by(ProgramRequirementModel.program_id, ProgramRequirementModel.id)
        ).scalars().all()

        requirement_items = self.db.execute(
            select(ProgramRequirementItemModel)
            .where(ProgramRequirementItemModel.tenant_id == tenant_id)
            .order_by(ProgramRequirementItemModel.requirement_id, ProgramRequirementItemModel.id)
        ).scalars().all()

        requirements_by_program: dict[int, list[ProgramRequirementModel]] = {}
        for requirement in active_requirements:
            requirements_by_program.setdefault(int(requirement.program_id), []).append(requirement)

        requirement_item_counts: dict[int, int] = {}
        for item in requirement_items:
            requirement_id = int(item.requirement_id)
            requirement_item_counts[requirement_id] = requirement_item_counts.get(requirement_id, 0) + 1

        issues: list[DegreeProgressConsistencyIssueSchema] = []

        for binding in active_primary_bindings:
            program_requirements = requirements_by_program.get(int(binding.program_id), [])
            if not program_requirements:
                issues.append(
                    DegreeProgressConsistencyIssueSchema(
                        issue_type="active_primary_binding_missing_requirement",
                        student_profile_id=int(binding.student_profile_id),
                        program_id=int(binding.program_id),
                    )
                )

        for program_id, program_requirements in requirements_by_program.items():
            if len(program_requirements) > 1:
                issues.append(
                    DegreeProgressConsistencyIssueSchema(
                        issue_type="program_multiple_active_requirements",
                        program_id=program_id,
                        requirement_id=int(program_requirements[0].id),
                        active_requirement_count=len(program_requirements),
                    )
                )

            for requirement in program_requirements:
                if requirement_item_counts.get(int(requirement.id), 0) == 0:
                    issues.append(
                        DegreeProgressConsistencyIssueSchema(
                            issue_type="active_requirement_without_items",
                            program_id=int(requirement.program_id),
                            requirement_id=int(requirement.id),
                        )
                    )

        return DegreeProgressConsistencyReportSchema(
            active_primary_binding_count=len(active_primary_bindings),
            active_requirement_count=len(active_requirements),
            requirement_item_count=len(requirement_items),
            issue_count=len(issues),
            issues=issues,
        )
