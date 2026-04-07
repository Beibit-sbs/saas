from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


def list_records(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("academic_records", tenant_id)


def create_record(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("academic_records", payload, tenant_id)


def update_record(record_id: int, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return update_entity_for_tenant("academic_records", record_id, payload, tenant_id)


def delete_record(record_id: int, tenant_id: int) -> dict[str, object]:
    return delete_entity_for_tenant("academic_records", record_id, tenant_id)
