from app.modules.university_core.service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


def list_students(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("students", tenant_id)


def create_student(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("students", payload, tenant_id)


def update_student(student_id: int, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return update_entity_for_tenant("students", student_id, payload, tenant_id)


def delete_student(student_id: int, tenant_id: int) -> dict[str, object]:
    return delete_entity_for_tenant("students", student_id, tenant_id)
