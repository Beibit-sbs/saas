from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


def list_courses(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("courses", tenant_id)


def create_course(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("courses", payload, tenant_id)


def update_course(course_id: int, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return update_entity_for_tenant("courses", course_id, payload, tenant_id)


def delete_course(course_id: int, tenant_id: int) -> dict[str, object]:
    return delete_entity_for_tenant("courses", course_id, tenant_id)
