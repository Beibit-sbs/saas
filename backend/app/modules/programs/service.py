from app.modules.university_core.tenant_entity_service import (
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


def get_program_consistency_report(tenant_id: int) -> dict[str, object]:
    programs = list_entities_for_tenant("programs", tenant_id)

    allowed_degree_types = {"bachelor", "master", "doctorate", "associate", "certificate", "diploma"}
    allowed_statuses = {"active", "inactive", "archived", "draft"}

    issues: list[dict[str, object]] = []
    code_counts: dict[str, int] = {}

    for program in programs:
        code_raw = program.get("program_code")
        code = str(code_raw).strip() if code_raw is not None else ""
        if code:
            code_counts[code] = code_counts.get(code, 0) + 1

    duplicate_codes = {
        code for code, count in code_counts.items() if count > 1
    }

    for program in programs:
        program_id_raw = program.get("id")
        code_raw = program.get("program_code")
        title_raw = program.get("title")
        degree_type_raw = program.get("degree_type")
        status_raw = program.get("status")

        try:
            program_id = int(program_id_raw)
        except (TypeError, ValueError):
            program_id = None

        code = str(code_raw).strip() if code_raw is not None else ""
        if not code:
            issues.append(
                {
                    "issue_type": "program_missing_code",
                    "program_id": program_id,
                }
            )
        elif code in duplicate_codes:
            issues.append(
                {
                    "issue_type": "duplicate_program_code",
                    "program_id": program_id,
                    "program_code": code,
                }
            )

        title = str(title_raw).strip() if title_raw is not None else ""
        if not title:
            issues.append({"issue_type": "program_missing_name", "program_id": program_id})

        degree_type = str(degree_type_raw).strip().lower() if degree_type_raw is not None else ""
        if degree_type not in allowed_degree_types:
            issues.append(
                {
                    "issue_type": "program_invalid_degree_type",
                    "program_id": program_id,
                    "degree_type": degree_type_raw,
                }
            )

        status = str(status_raw).strip().lower() if status_raw is not None else ""
        if status not in allowed_statuses:
            issues.append(
                {
                    "issue_type": "program_invalid_status",
                    "program_id": program_id,
                    "status": status_raw,
                }
            )

    return {
        "program_count": len(programs),
        "issue_count": len(issues),
        "issues": issues,
    }
