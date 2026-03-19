from app.modules.university_core.service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


def list_enrollments(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("enrollments", tenant_id)


def create_enrollment(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("enrollments", payload, tenant_id)


def update_enrollment(enrollment_id: int, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return update_entity_for_tenant("enrollments", enrollment_id, payload, tenant_id)


def delete_enrollment(enrollment_id: int, tenant_id: int) -> dict[str, object]:
    return delete_entity_for_tenant("enrollments", enrollment_id, tenant_id)
