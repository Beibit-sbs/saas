from app.modules.university_core.service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


def list_programs(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("programs", tenant_id)


def create_program(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return create_entity_for_tenant("programs", payload, tenant_id)


def update_program(program_id: int, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    return update_entity_for_tenant("programs", program_id, payload, tenant_id)


def delete_program(program_id: int, tenant_id: int) -> dict[str, object]:
    return delete_entity_for_tenant("programs", program_id, tenant_id)
