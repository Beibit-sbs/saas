from app.modules.university_core.tenant_entity_service import (
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


def get_faculty_consistency_report(tenant_id: int) -> dict[str, object]:
    faculty_rows = list_entities_for_tenant("faculty", tenant_id)

    issues: list[dict[str, object]] = []
    faculty_id_counts: dict[str, int] = {}
    email_counts: dict[str, int] = {}
    allowed_statuses = {"active", "inactive", "on_leave", "sabbatical"}

    for row in faculty_rows:
        row_id_raw = row.get("id")
        faculty_id_raw = row.get("faculty_id")
        email_raw = row.get("email")

        try:
            row_id = int(row_id_raw)
        except (TypeError, ValueError):
            row_id = None

        faculty_id = str(faculty_id_raw).strip() if faculty_id_raw is not None else ""
        email = str(email_raw).strip() if email_raw is not None else ""
        normalized_email = email.lower()
        status = str(row.get("status") or "").strip().lower()

        if not faculty_id:
            issues.append(
                {
                    "issue_type": "faculty_missing_identifier",
                    "faculty_row_id": row_id,
                    "email": email or None,
                }
            )
        else:
            faculty_id_counts[faculty_id] = faculty_id_counts.get(faculty_id, 0) + 1

        if not email:
            issues.append(
                {
                    "issue_type": "faculty_missing_email",
                    "faculty_row_id": row_id,
                    "faculty_id": faculty_id or None,
                }
            )
        else:
            email_counts[normalized_email] = email_counts.get(normalized_email, 0) + 1
            if "@" not in normalized_email or normalized_email.startswith("@") or normalized_email.endswith("@"):
                issues.append(
                    {
                        "issue_type": "faculty_invalid_email_format",
                        "faculty_row_id": row_id,
                        "faculty_id": faculty_id or None,
                        "email": email,
                    }
                )

        if not status or status not in allowed_statuses:
            issues.append(
                {
                    "issue_type": "faculty_invalid_status",
                    "faculty_row_id": row_id,
                    "faculty_id": faculty_id or None,
                    "email": email or None,
                }
            )

    duplicate_faculty_ids = {
        faculty_id for faculty_id, count in faculty_id_counts.items() if count > 1
    }
    duplicate_emails = {
        email for email, count in email_counts.items() if count > 1
    }

    for row in faculty_rows:
        row_id_raw = row.get("id")
        faculty_id_raw = row.get("faculty_id")
        email_raw = row.get("email")
        try:
            row_id = int(row_id_raw)
        except (TypeError, ValueError):
            row_id = None

        faculty_id = str(faculty_id_raw).strip() if faculty_id_raw is not None else ""
        email = str(email_raw).strip() if email_raw is not None else ""
        normalized_email = email.lower()

        if faculty_id and faculty_id in duplicate_faculty_ids:
            issues.append(
                {
                    "issue_type": "duplicate_faculty_identifier",
                    "faculty_row_id": row_id,
                    "faculty_id": faculty_id,
                    "email": email or None,
                }
            )

        if email and normalized_email in duplicate_emails:
            issues.append(
                {
                    "issue_type": "duplicate_faculty_email",
                    "faculty_row_id": row_id,
                    "faculty_id": faculty_id or None,
                    "email": email,
                }
            )

    return {
        "faculty_count": len(faculty_rows),
        "issue_count": len(issues),
        "issues": issues,
    }
