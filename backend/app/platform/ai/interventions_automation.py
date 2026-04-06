from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import logging
from typing import Any


logger = logging.getLogger(__name__)


def maybe_create_academic_risk_intervention_case(
    *,
    conn: Any,
    tenant_id: int,
    question: str,
    retrieved_context: dict[str, Any],
) -> dict[str, Any] | None:
    """Create one auto intervention case per day for severe academic risk.

    Fail-safe behavior: if DB is unavailable or tables are not ready, returns None
    and never breaks the copilot answer flow.
    """
    severe_at_risk_count = int(retrieved_context.get("severe_at_risk_count") or 0)
    at_risk_count = int(retrieved_context.get("at_risk_count") or 0)
    severe_at_risk_student_ids = [
        str(item).strip()
        for item in list(retrieved_context.get("severe_at_risk_student_ids") or [])
        if str(item).strip()
    ]
    if conn is None or severe_at_risk_count <= 0:
        return None

    now = datetime.now(UTC)
    auto_key = f"ai_academic_risk:{now.date().isoformat()}"

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM app_intervention_cases
                WHERE tenant_id = %s
                  AND case_type = 'academic_risk'
                  AND status IN ('open', 'in_progress')
                  AND COALESCE(metadata_json ->> 'auto_source', '') = 'ai_academic_risk'
                  AND COALESCE(metadata_json ->> 'auto_key', '') = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                (int(tenant_id), auto_key),
            )
            existing = cur.fetchone()
            if existing:
                return {
                    "created": False,
                    "case_id": int(existing[0]),
                }

            due_at = now + timedelta(days=3)
            title = f"High expulsion risk escalation ({severe_at_risk_count} student(s))"
            description = (
                "Automatically created from AI academic risk detection. "
                f"At-risk students: {at_risk_count}; severe risk students: {severe_at_risk_count}."
            )

            student_profile_id: int | None = None
            selected_student_identifier: str | None = severe_at_risk_student_ids[0] if severe_at_risk_student_ids else None
            if selected_student_identifier:
                cur.execute(
                    """
                    SELECT id
                    FROM app_students_profiles
                    WHERE tenant_id = %s
                      AND student_number = %s
                    ORDER BY id ASC
                    LIMIT 1
                    """,
                    (int(tenant_id), selected_student_identifier),
                )
                row = cur.fetchone()
                if row is not None:
                    student_profile_id = int(row[0])

            metadata_json = {
                "auto_source": "ai_academic_risk",
                "auto_key": auto_key,
                "at_risk_count": at_risk_count,
                "severe_at_risk_count": severe_at_risk_count,
                "severe_at_risk_student_ids": severe_at_risk_student_ids,
                "selected_student_identifier": selected_student_identifier,
                "linked_student_profile_id": student_profile_id,
                "question": question,
                "created_at": now.isoformat(),
            }

            risk_snapshot_json = {
                "at_risk_count": at_risk_count,
                "severe_at_risk_count": severe_at_risk_count,
                "severe_at_risk_student_ids": severe_at_risk_student_ids,
            }

            cur.execute(
                """
                INSERT INTO app_intervention_cases (
                    tenant_id,
                    case_type,
                    student_profile_id,
                    severity,
                    status,
                    title,
                    description,
                    risk_snapshot_json,
                    assignee_type,
                    assignee_ref,
                    due_at,
                    metadata_json,
                    created_by,
                    updated_by
                )
                VALUES (
                    %s,
                    'academic_risk',
                    %s,
                    'high',
                    'open',
                    %s,
                    %s,
                    %s::jsonb,
                    'group',
                    'dean_office',
                    %s,
                    %s::jsonb,
                    'ai.copilot',
                    'ai.copilot'
                )
                RETURNING id
                """,
                (
                    int(tenant_id),
                    student_profile_id,
                    title,
                    description,
                    json.dumps(risk_snapshot_json),
                    due_at,
                    json.dumps(metadata_json),
                ),
            )
            case_id = int(cur.fetchone()[0])

            cur.execute(
                """
                INSERT INTO app_intervention_actions (
                    tenant_id,
                    case_id,
                    action_type,
                    description,
                    performed_by,
                    metadata_json
                )
                VALUES (
                    %s,
                    %s,
                    'note',
                    %s,
                    'ai.copilot',
                    %s::jsonb
                )
                """,
                (
                    int(tenant_id),
                    case_id,
                    "Case auto-created by AI academic risk policy.",
                    json.dumps({"auto_source": "ai_academic_risk", "auto_key": auto_key}),
                ),
            )

            return {
                "created": True,
                "case_id": case_id,
            }
    except Exception as exc:  # noqa: BLE001
        logger.warning("academic risk auto-case creation skipped: %s", exc)
        return None
