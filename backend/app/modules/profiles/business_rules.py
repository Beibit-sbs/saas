from __future__ import annotations

from typing import Any

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import (
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
    validate_version_match,
)


class TenantIsolationRules:
    @classmethod
    def validate_tenant_id_provided(cls, tenant_id: int | None) -> None:
        validate_tenant_id_provided(tenant_id)

    @classmethod
    def assert_resource_belongs_to_tenant(
        cls,
        resource: Any,
        tenant_id: int,
        *,
        resource_name: str,
        resource_id: int | None = None,
    ) -> None:
        assert_resource_belongs_to_tenant(
            resource,
            tenant_id,
            resource_name=resource_name,
            resource_id=resource_id,
        )


class PersonRules:
    @classmethod
    def validate_unique_lookup_keys(cls, *, email: str, external_person_key: str | None) -> None:
        if not email.strip():
            raise ValueError("email is required")
        if external_person_key is not None and not external_person_key.strip():
            raise ValueError("external_person_key cannot be blank")


class DepartmentRules:
    @classmethod
    def validate_parent_not_self(cls, parent_department_id: int | None, department_id: int | None = None) -> None:
        if department_id is not None and parent_department_id == department_id:
            raise ValueError("department cannot be its own parent")

    @classmethod
    def validate_head_belongs_to_tenant(cls, person: Any, tenant_id: int) -> None:
        TenantIsolationRules.assert_resource_belongs_to_tenant(
            person,
            tenant_id,
            resource_name="Person",
            resource_id=getattr(person, "id", None),
        )


class ProgramRules:
    @classmethod
    def validate_department_belongs_to_tenant(cls, department: Any, tenant_id: int) -> None:
        TenantIsolationRules.assert_resource_belongs_to_tenant(
            department,
            tenant_id,
            resource_name="Department",
            resource_id=getattr(department, "id", None),
        )


class StudentRules:
    @classmethod
    def validate_person_eligible(cls, person: Any, tenant_id: int) -> None:
        TenantIsolationRules.assert_resource_belongs_to_tenant(
            person,
            tenant_id,
            resource_name="Person",
            resource_id=getattr(person, "id", None),
        )

    @classmethod
    def validate_program_eligible(cls, program: Any, tenant_id: int) -> None:
        TenantIsolationRules.assert_resource_belongs_to_tenant(
            program,
            tenant_id,
            resource_name="Program",
            resource_id=getattr(program, "id", None),
        )

    @classmethod
    def validate_no_existing_student_role(cls, existing_role: Any, person_id: int, tenant_id: int) -> None:
        if existing_role is not None:
            raise ValueError(f"Student role already exists for person {person_id} in tenant {tenant_id}")


class FacultyRules:
    @classmethod
    def validate_person_eligible(cls, person: Any, tenant_id: int) -> None:
        TenantIsolationRules.assert_resource_belongs_to_tenant(
            person,
            tenant_id,
            resource_name="Person",
            resource_id=getattr(person, "id", None),
        )

    @classmethod
    def validate_department_eligible(cls, department: Any, tenant_id: int) -> None:
        TenantIsolationRules.assert_resource_belongs_to_tenant(
            department,
            tenant_id,
            resource_name="Department",
            resource_id=getattr(department, "id", None),
        )

    @classmethod
    def validate_no_existing_faculty_role(cls, existing_role: Any, person_id: int, tenant_id: int) -> None:
        if existing_role is not None:
            raise ValueError(f"Faculty role already exists for person {person_id} in tenant {tenant_id}")


class OptimisticLockingRules:
    @classmethod
    def validate_version_match(cls, current_version: int, request_version: int) -> None:
        validate_version_match(current_version, request_version)


class AuditEventRules:
    EVENT_TO_ACTION = {
        "person.created": build_audit_action("profiles", "person", "created"),
        "person.updated": build_audit_action("profiles", "person", "updated"),
        "department.created": build_audit_action("profiles", "department", "created"),
        "program.created": build_audit_action("profiles", "program", "created"),
        "student.created": build_audit_action("profiles", "student", "created"),
        "faculty.created": build_audit_action("profiles", "faculty", "created"),
    }

    @classmethod
    def get_log_action_for_event(cls, event_name: str) -> str:
        return cls.EVENT_TO_ACTION.get(event_name, event_name)