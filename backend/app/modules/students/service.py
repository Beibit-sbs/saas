from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, case, desc, func, select
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
from app.modules.profiles.models import PersonModel, ProgramModel
from app.modules.students.business_rules import StudentLifecycleRules
from app.modules.students.models import (
    StudentAdmissionSource,
    StudentProfileModel,
    StudentProgramBindingModel,
    StudentProgramBindingState,
    StudentStatus,
    StudentStatusHistoryModel,
)
from app.modules.students.schemas import (
    AdmissionsProvisionStudentRequestSchema,
    AdmissionsProvisionStudentResultSchema,
    StudentProfileCreateSchema,
    StudentProfileListResponseSchema,
    StudentProfileReadSchema,
    StudentProgramBindingConsistencyIssueSchema,
    StudentProgramBindingCreateSchema,
    StudentProgramBindingReadSchema,
    StudentStatusChangeSchema,
)
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _audit(
    *,
    actor: str,
    action: str,
    path: str,
    entity: str,
    metadata: dict,
    tenant_id: int,
) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity=entity,
        metadata=metadata,
        tenant_id=tenant_id,
    )


class StudentLifecycleService:
    """Canonical lifecycle service for Students module Phase 2."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_student_profile(
        self,
        tenant_id: int,
        request: StudentProfileCreateSchema,
        created_by: str,
    ) -> StudentProfileReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        person = self.db.execute(
            select(PersonModel).where(
                and_(
                    PersonModel.id == request.person_id,
                    PersonModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        StudentLifecycleRules.validate_person_eligible(person, tenant_id)

        existing_profile = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.tenant_id == tenant_id,
                    StudentProfileModel.person_id == request.person_id,
                )
            )
        ).scalar_one_or_none()
        if existing_profile is not None:
            raise DomainValidationError(
                f"Student profile already exists for person {request.person_id} in tenant {tenant_id}"
            )

        profile = StudentProfileModel(
            tenant_id=tenant_id,
            person_id=request.person_id,
            student_number=request.student_number,
            cohort_year=request.cohort_year,
            academic_level=request.academic_level,
            current_status=StudentStatus.ADMITTED,
            admission_source=request.admission_source,
            metadata_json=request.metadata_json,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(profile)
        self.db.flush()

        self.db.add(
            StudentStatusHistoryModel(
                tenant_id=tenant_id,
                student_profile_id=profile.id,
                from_status=None,
                to_status=StudentStatus.ADMITTED,
                reason="initial_student_profile_creation",
                actor_id=created_by,
                changed_at=_utc_now(),
                metadata_json={"source": request.admission_source.value},
            )
        )

        self.db.flush()
        self.db.refresh(profile)

        EventPublisher(db_session=self.db).publish_event(
            tenant_id=tenant_id,
            event_type="student.created",
            aggregate_type="student_profile",
            aggregate_id=profile.id,
            payload_json={
                "student_profile_id": profile.id,
                "person_id": profile.person_id,
                "student_number": profile.student_number,
                "current_status": profile.current_status.value,
                "created_by": created_by,
            },
        )

        _audit(
            actor=created_by,
            action=build_audit_action("students", "profile", "created"),
            path=f"/internal/students/profiles/{profile.id}",
            entity="students_profile",
            metadata={
                "resource_id": str(profile.id),
                "person_id": profile.person_id,
                "student_number": profile.student_number,
            },
            tenant_id=tenant_id,
        )

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to create student profile due to constraint violation") from exc

        return StudentProfileReadSchema.model_validate(profile)

    async def get_student_profile(
        self,
        tenant_id: int,
        student_profile_id: int,
    ) -> StudentProfileReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        profile = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.id == student_profile_id,
                    StudentProfileModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            profile,
            tenant_id,
            resource_name="Student profile",
            resource_id=student_profile_id,
        )
        return StudentProfileReadSchema.model_validate(profile)

    async def list_student_profiles(
        self,
        tenant_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
        status: StudentStatus | None = None,
        person_id: int | None = None,
    ) -> StudentProfileListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        filters = [StudentProfileModel.tenant_id == tenant_id]
        if status is not None:
            filters.append(StudentProfileModel.current_status == status)
        if person_id is not None:
            filters.append(StudentProfileModel.person_id == person_id)

        total = self.db.execute(
            select(func.count()).select_from(StudentProfileModel).where(and_(*filters))
        ).scalar_one()

        items = self.db.execute(
            select(StudentProfileModel)
            .where(and_(*filters))
            .order_by(desc(StudentProfileModel.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        return StudentProfileListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=[StudentProfileReadSchema.model_validate(item) for item in items],
        )

    async def change_student_status(
        self,
        tenant_id: int,
        student_profile_id: int,
        request: StudentStatusChangeSchema,
        actor_id: str,
    ) -> StudentProfileReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        profile = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.id == student_profile_id,
                    StudentProfileModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            profile,
            tenant_id,
            resource_name="Student profile",
            resource_id=student_profile_id,
        )

        validate_version_match(profile.version, request.expected_version)
        previous_status = StudentStatus(profile.current_status)
        StudentLifecycleRules.validate_status_transition(previous_status, request.to_status)

        self.db.add(
            StudentStatusHistoryModel(
                tenant_id=tenant_id,
                student_profile_id=profile.id,
                from_status=previous_status,
                to_status=request.to_status,
                reason=request.reason,
                actor_id=actor_id,
                changed_at=_utc_now(),
                metadata_json=request.metadata_json,
            )
        )

        profile.current_status = request.to_status
        profile.version += 1
        profile.updated_by = actor_id
        self.db.flush()
        self.db.refresh(profile)

        _audit(
            actor=actor_id,
            action=build_audit_action("students", "profile", "status_changed"),
            path=f"/internal/students/profiles/{profile.id}/status",
            entity="students_profile",
            metadata={
                "resource_id": str(profile.id),
                "from_status": previous_status.value,
                "to_status": request.to_status.value,
                "version": profile.version,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return StudentProfileReadSchema.model_validate(profile)

    async def bind_student_to_program(
        self,
        tenant_id: int,
        request: StudentProgramBindingCreateSchema,
        actor_id: str,
    ) -> StudentProgramBindingReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        StudentLifecycleRules.validate_binding_is_active(request.binding_state)

        profile = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.id == request.student_profile_id,
                    StudentProfileModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            profile,
            tenant_id,
            resource_name="Student profile",
            resource_id=request.student_profile_id,
        )

        program = self.db.execute(
            select(ProgramModel).where(
                and_(
                    ProgramModel.id == request.program_id,
                    ProgramModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        StudentLifecycleRules.validate_program_eligible(program, tenant_id)

        existing_active_same_program = self.db.execute(
            select(StudentProgramBindingModel).where(
                and_(
                    StudentProgramBindingModel.tenant_id == tenant_id,
                    StudentProgramBindingModel.student_profile_id == request.student_profile_id,
                    StudentProgramBindingModel.program_id == request.program_id,
                    StudentProgramBindingModel.binding_state == StudentProgramBindingState.ACTIVE,
                )
            )
        ).scalar_one_or_none()
        if existing_active_same_program is not None:
            raise DomainValidationError(
                f"Active binding for program {request.program_id} already exists"
            )

        if request.is_primary:
            existing_primary = self.db.execute(
                select(StudentProgramBindingModel).where(
                    and_(
                        StudentProgramBindingModel.tenant_id == tenant_id,
                        StudentProgramBindingModel.student_profile_id == request.student_profile_id,
                        StudentProgramBindingModel.binding_state == StudentProgramBindingState.ACTIVE,
                        StudentProgramBindingModel.is_primary.is_(True),
                    )
                )
            ).scalar_one_or_none()
            if existing_primary is not None:
                raise DomainValidationError(
                    f"Student profile {request.student_profile_id} already has an active primary program"
                )

        binding = StudentProgramBindingModel(
            tenant_id=tenant_id,
            student_profile_id=request.student_profile_id,
            program_id=request.program_id,
            is_primary=request.is_primary,
            binding_state=request.binding_state,
            started_at=request.started_at or _utc_now(),
            metadata_json=request.metadata_json,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(binding)
        self.db.flush()
        self.db.refresh(binding)

        _audit(
            actor=actor_id,
            action=build_audit_action("students", "program_binding", "created"),
            path=f"/internal/students/program-bindings/{binding.id}",
            entity="students_program_binding",
            metadata={
                "resource_id": str(binding.id),
                "student_profile_id": binding.student_profile_id,
                "program_id": binding.program_id,
                "is_primary": binding.is_primary,
            },
            tenant_id=tenant_id,
        )

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to bind student to program due to constraint violation") from exc

        return StudentProgramBindingReadSchema.model_validate(binding)

    async def get_active_primary_program(
        self,
        tenant_id: int,
        student_profile_id: int,
    ) -> StudentProgramBindingReadSchema | None:
        tenant_id = validate_tenant_id_provided(tenant_id)

        binding = self.db.execute(
            select(StudentProgramBindingModel)
            .where(
                and_(
                    StudentProgramBindingModel.tenant_id == tenant_id,
                    StudentProgramBindingModel.student_profile_id == student_profile_id,
                    StudentProgramBindingModel.binding_state == StudentProgramBindingState.ACTIVE,
                    StudentProgramBindingModel.is_primary.is_(True),
                )
            )
            .order_by(desc(StudentProgramBindingModel.started_at), desc(StudentProgramBindingModel.id))
        ).scalars().first()

        if binding is None:
            return None
        return StudentProgramBindingReadSchema.model_validate(binding)

    async def list_program_binding_consistency_issues(
        self,
        tenant_id: int,
    ) -> list[StudentProgramBindingConsistencyIssueSchema]:
        tenant_id = validate_tenant_id_provided(tenant_id)

        duplicate_primary_student_ids = self.db.execute(
            select(StudentProgramBindingModel.student_profile_id)
            .where(
                and_(
                    StudentProgramBindingModel.tenant_id == tenant_id,
                    StudentProgramBindingModel.binding_state == StudentProgramBindingState.ACTIVE,
                    StudentProgramBindingModel.is_primary.is_(True),
                )
            )
            .group_by(StudentProgramBindingModel.student_profile_id)
            .having(func.count(StudentProgramBindingModel.id) > 1)
        ).scalars().all()

        missing_primary_student_ids = self.db.execute(
            select(StudentProgramBindingModel.student_profile_id)
            .where(
                and_(
                    StudentProgramBindingModel.tenant_id == tenant_id,
                    StudentProgramBindingModel.binding_state == StudentProgramBindingState.ACTIVE,
                )
            )
            .group_by(StudentProgramBindingModel.student_profile_id)
            .having(
                func.sum(
                    case(
                        (StudentProgramBindingModel.is_primary.is_(True), 1),
                        else_=0,
                    )
                )
                == 0
            )
        ).scalars().all()

        issues: list[StudentProgramBindingConsistencyIssueSchema] = []

        if duplicate_primary_student_ids:
            duplicate_bindings = self.db.execute(
                select(StudentProgramBindingModel)
                .where(
                    and_(
                        StudentProgramBindingModel.tenant_id == tenant_id,
                        StudentProgramBindingModel.student_profile_id.in_(duplicate_primary_student_ids),
                        StudentProgramBindingModel.binding_state == StudentProgramBindingState.ACTIVE,
                        StudentProgramBindingModel.is_primary.is_(True),
                    )
                )
                .order_by(
                    StudentProgramBindingModel.student_profile_id,
                    desc(StudentProgramBindingModel.started_at),
                    desc(StudentProgramBindingModel.id),
                )
            ).scalars().all()

            duplicate_map: dict[int, list[StudentProgramBindingModel]] = {}
            for binding in duplicate_bindings:
                duplicate_map.setdefault(int(binding.student_profile_id), []).append(binding)

            for student_profile_id in sorted(duplicate_map):
                bindings = duplicate_map[student_profile_id]
                issues.append(
                    StudentProgramBindingConsistencyIssueSchema(
                        student_profile_id=student_profile_id,
                        issue_type="duplicate_active_primary_bindings",
                        active_binding_count=len(bindings),
                        active_primary_count=len(bindings),
                        program_ids=[int(binding.program_id) for binding in bindings],
                    )
                )

        if missing_primary_student_ids:
            active_bindings = self.db.execute(
                select(StudentProgramBindingModel)
                .where(
                    and_(
                        StudentProgramBindingModel.tenant_id == tenant_id,
                        StudentProgramBindingModel.student_profile_id.in_(missing_primary_student_ids),
                        StudentProgramBindingModel.binding_state == StudentProgramBindingState.ACTIVE,
                    )
                )
                .order_by(
                    StudentProgramBindingModel.student_profile_id,
                    desc(StudentProgramBindingModel.started_at),
                    desc(StudentProgramBindingModel.id),
                )
            ).scalars().all()

            missing_map: dict[int, list[StudentProgramBindingModel]] = {}
            for binding in active_bindings:
                missing_map.setdefault(int(binding.student_profile_id), []).append(binding)

            for student_profile_id in sorted(missing_map):
                bindings = missing_map[student_profile_id]
                issues.append(
                    StudentProgramBindingConsistencyIssueSchema(
                        student_profile_id=student_profile_id,
                        issue_type="active_bindings_without_primary",
                        active_binding_count=len(bindings),
                        active_primary_count=0,
                        program_ids=[int(binding.program_id) for binding in bindings],
                    )
                )

        return sorted(issues, key=lambda item: (item.student_profile_id, item.issue_type))

    async def provision_student_for_admissions_compat(
        self,
        tenant_id: int,
        request: AdmissionsProvisionStudentRequestSchema,
        actor_id: str,
    ) -> AdmissionsProvisionStudentResultSchema:
        """
        Compatibility helper for phased admissions migration.

        Current behavior:
        - create student profile if absent
        - ensure active primary program binding exists for admitted program
        """
        tenant_id = validate_tenant_id_provided(tenant_id)

        profile = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.tenant_id == tenant_id,
                    StudentProfileModel.person_id == request.person_id,
                )
            )
        ).scalar_one_or_none()

        if profile is None:
            profile = (
                await self.create_student_profile(
                    tenant_id=tenant_id,
                    request=StudentProfileCreateSchema(
                        person_id=request.person_id,
                        student_number=request.student_number,
                        cohort_year=request.cohort_year,
                        admission_source=StudentAdmissionSource.ADMISSIONS_WORKFLOW,
                        metadata_json=request.metadata_json,
                    ),
                    created_by=actor_id,
                )
            )
            profile_id = profile.id
            profile_schema = profile
        else:
            profile_id = profile.id
            profile_schema = StudentProfileReadSchema.model_validate(profile)

        primary_binding = await self.get_active_primary_program(
            tenant_id=tenant_id,
            student_profile_id=profile_id,
        )

        if primary_binding is None:
            primary_binding = await self.bind_student_to_program(
                tenant_id=tenant_id,
                request=StudentProgramBindingCreateSchema(
                    student_profile_id=profile_id,
                    program_id=request.program_id,
                    is_primary=True,
                    binding_state=StudentProgramBindingState.ACTIVE,
                    metadata_json={"source": "admissions_compat", **request.metadata_json},
                ),
                actor_id=actor_id,
            )
        elif primary_binding.program_id != request.program_id:
            raise DomainValidationError(
                "Active primary program differs from admissions result; manual reconciliation required"
            )

        return AdmissionsProvisionStudentResultSchema(
            student_profile=profile_schema,
            active_primary_program=primary_binding,
        )


# ---------------------------------------------------------------------------
# Legacy compatibility for current router (to be removed in future phase).
# ---------------------------------------------------------------------------


def list_students(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("students", tenant_id)


def create_student(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("students", payload, tenant_id)


def update_student(student_id: int, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return update_entity_for_tenant("students", student_id, payload, tenant_id)


def delete_student(student_id: int, tenant_id: int) -> dict[str, object]:
    return delete_entity_for_tenant("students", student_id, tenant_id)
