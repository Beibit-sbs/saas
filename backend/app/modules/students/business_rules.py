from __future__ import annotations

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.students.models import StudentProgramBindingState, StudentStatus


class StudentLifecycleRules:
    """Domain rules for canonical Students lifecycle operations."""

    _ALLOWED_STATUS_TRANSITIONS: dict[StudentStatus, set[StudentStatus]] = {
        StudentStatus.ADMITTED: {
            StudentStatus.ACTIVE,
            StudentStatus.INACTIVE,
            StudentStatus.WITHDRAWN,
        },
        StudentStatus.ACTIVE: {
            StudentStatus.INACTIVE,
            StudentStatus.LEAVE_OF_ABSENCE,
            StudentStatus.SUSPENDED,
            StudentStatus.GRADUATED,
            StudentStatus.WITHDRAWN,
        },
        StudentStatus.INACTIVE: {
            StudentStatus.ACTIVE,
            StudentStatus.WITHDRAWN,
        },
        StudentStatus.LEAVE_OF_ABSENCE: {
            StudentStatus.ACTIVE,
            StudentStatus.WITHDRAWN,
        },
        StudentStatus.SUSPENDED: {
            StudentStatus.ACTIVE,
            StudentStatus.WITHDRAWN,
        },
        StudentStatus.GRADUATED: set(),
        StudentStatus.WITHDRAWN: set(),
    }

    @classmethod
    def validate_status_transition(cls, from_status: StudentStatus, to_status: StudentStatus) -> None:
        if from_status == to_status:
            raise DomainValidationError("status transition must change current status")

        allowed_targets = cls._ALLOWED_STATUS_TRANSITIONS.get(from_status, set())
        if to_status not in allowed_targets:
            raise DomainValidationError(
                f"status transition '{from_status.value}' -> '{to_status.value}' is not allowed"
            )

    @staticmethod
    def validate_person_eligible(person: object | None, tenant_id: int) -> None:
        if person is None:
            raise DomainValidationError(
                f"Person not found or does not belong to tenant {tenant_id}"
            )
        person_status = str(getattr(person, "status", "")).strip().lower()
        if person_status and person_status != "active":
            raise DomainValidationError("Person is not active and cannot be used for student profile")

    @staticmethod
    def validate_program_eligible(program: object | None, tenant_id: int) -> None:
        if program is None:
            raise DomainValidationError(
                f"Program not found or does not belong to tenant {tenant_id}"
            )
        program_status = str(getattr(program, "status", "")).strip().lower()
        if program_status and program_status != "active":
            raise DomainValidationError("Program is not active and cannot be bound to student")

    @staticmethod
    def validate_binding_is_active(binding_state: StudentProgramBindingState) -> None:
        if binding_state != StudentProgramBindingState.ACTIVE:
            raise DomainValidationError("Only active bindings are supported for this operation")
