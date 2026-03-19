from app.modules.university_core.service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


def list_faculty(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("faculty", tenant_id)


def create_faculty_member(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("faculty", payload, tenant_id)


def update_faculty_member(faculty_row_id: int, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return update_entity_for_tenant("faculty", faculty_row_id, payload, tenant_id)


def delete_faculty_member(faculty_row_id: int, tenant_id: int) -> dict[str, object]:
    return delete_entity_for_tenant("faculty", faculty_row_id, tenant_id)
