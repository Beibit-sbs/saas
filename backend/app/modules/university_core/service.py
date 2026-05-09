from __future__ import annotations

from typing import Any

UNIVERSITY_CORE_TABLE_CLASSIFICATIONS = frozenset(
    {
        "active_migrated",
        "planned_not_active",
        "test_only_or_stub",
        "fallback_classified",
        "unknown",
    }
)

UNIVERSITY_CORE_READINESS_STATUSES = frozenset(
    {"ready", "ready_with_known_conditions", "partial", "blocked", "unknown"}
)

UNIVERSITY_CORE_READINESS_RISK_LEVELS = ("low", "medium", "high", "critical")


def validate_university_core_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _risk_rank(level: str) -> int:
    return UNIVERSITY_CORE_READINESS_RISK_LEVELS.index(level)


def _max_risk(current: str, candidate: str) -> str:
    return candidate if _risk_rank(candidate) > _risk_rank(current) else current


def build_university_core_evidence_item(
    *,
    classification: str,
    table_name: str,
    source_entity_type: str,
    source_entity_id: str,
    source_report: str | None = None,
) -> dict[str, str | None]:
    normalized = str(classification or "").strip().lower() or "unknown"
    if normalized not in UNIVERSITY_CORE_TABLE_CLASSIFICATIONS:
        normalized = "unknown"

    return {
        "classification": normalized,
        "table_name": str(table_name or "").strip(),
        "source_entity_type": source_entity_type,
        "source_entity_id": source_entity_id,
        "source_report": source_report,
    }


def classify_university_core_readiness(
    *,
    active_migrated_count: int,
    planned_not_active_count: int,
    test_only_or_stub_count: int,
    fallback_classified_count: int,
    unknown_count: int,
    known_condition_count: int,
) -> tuple[str, str, bool]:
    if active_migrated_count == 0 and unknown_count == 0 and known_condition_count == 0:
        return "unknown", "high", True

    risk = "low"
    status = "ready"
    review_required = False

    if unknown_count > 0:
        risk = _max_risk(risk, "critical")
        status = "blocked"
        review_required = True

    if planned_not_active_count > 0 or test_only_or_stub_count > 0:
        risk = _max_risk(risk, "medium")
        if status == "ready":
            status = "ready_with_known_conditions"

    if fallback_classified_count > 0:
        risk = _max_risk(risk, "medium")
        if status == "ready":
            status = "ready_with_known_conditions"

    if known_condition_count > 0:
        risk = _max_risk(risk, "high")
        if status == "ready":
            status = "ready_with_known_conditions"

    if active_migrated_count == 0 and status != "blocked":
        status = "partial"
        risk = _max_risk(risk, "high")
        review_required = True

    if status in {"blocked", "partial"}:
        review_required = True

    return status, risk, review_required


def build_university_core_readiness_summary(
    *,
    tenant_id: int,
    active_migrated_tables: list[str],
    planned_not_active_tables: list[str],
    test_only_or_stub_tables: list[str],
    fallback_classified_tables: list[str],
    unknown_tables: list[str],
    known_conditions: list[str],
    source_entity_type: str,
    source_entity_id: str,
    source_report: str | None = None,
) -> dict[str, Any]:
    validate_university_core_tenant(tenant_id)

    if not source_entity_type:
        raise ValueError("source_entity_type is required")
    if not source_entity_id:
        raise ValueError("source_entity_id is required")

    def _normalize(values: list[str]) -> list[str]:
        return sorted({str(v).strip() for v in values if str(v).strip()})

    active_migrated = _normalize(active_migrated_tables)
    planned_not_active = _normalize(planned_not_active_tables)
    test_only_or_stub = _normalize(test_only_or_stub_tables)
    fallback_classified = _normalize(fallback_classified_tables)
    unknown = _normalize(unknown_tables)
    known_conditions_normalized = _normalize(known_conditions)

    total_classified_count = (
        len(active_migrated)
        + len(planned_not_active)
        + len(test_only_or_stub)
        + len(fallback_classified)
        + len(unknown)
    )

    readiness_status, risk_level, review_required = classify_university_core_readiness(
        active_migrated_count=len(active_migrated),
        planned_not_active_count=len(planned_not_active),
        test_only_or_stub_count=len(test_only_or_stub),
        fallback_classified_count=len(fallback_classified),
        unknown_count=len(unknown),
        known_condition_count=len(known_conditions_normalized),
    )

    evidence_items: list[dict[str, str | None]] = []
    for table in active_migrated:
        evidence_items.append(
            build_university_core_evidence_item(
                classification="active_migrated",
                table_name=table,
                source_entity_type=source_entity_type,
                source_entity_id=source_entity_id,
                source_report=source_report,
            )
        )
    for table in planned_not_active:
        evidence_items.append(
            build_university_core_evidence_item(
                classification="planned_not_active",
                table_name=table,
                source_entity_type=source_entity_type,
                source_entity_id=source_entity_id,
                source_report=source_report,
            )
        )
    for table in test_only_or_stub:
        evidence_items.append(
            build_university_core_evidence_item(
                classification="test_only_or_stub",
                table_name=table,
                source_entity_type=source_entity_type,
                source_entity_id=source_entity_id,
                source_report=source_report,
            )
        )
    for table in fallback_classified:
        evidence_items.append(
            build_university_core_evidence_item(
                classification="fallback_classified",
                table_name=table,
                source_entity_type=source_entity_type,
                source_entity_id=source_entity_id,
                source_report=source_report,
            )
        )
    for table in unknown:
        evidence_items.append(
            build_university_core_evidence_item(
                classification="unknown",
                table_name=table,
                source_entity_type=source_entity_type,
                source_entity_id=source_entity_id,
                source_report=source_report,
            )
        )

    evidence_items = sorted(
        evidence_items,
        key=lambda item: (
            str(item["classification"]),
            str(item["table_name"]),
        ),
    )

    data_quality_note: str | None = None
    if total_classified_count == 0:
        data_quality_note = "no table classification evidence available"
    elif len(unknown) > 0:
        data_quality_note = "unknown table classification requires review"

    return {
        "tenant_id": tenant_id,
        "readiness_status": readiness_status,
        "risk_level": risk_level,
        "active_migrated_count": len(active_migrated),
        "planned_not_active_count": len(planned_not_active),
        "test_only_or_stub_count": len(test_only_or_stub),
        "fallback_classified_count": len(fallback_classified),
        "unknown_count": len(unknown),
        "total_classified_count": total_classified_count,
        "review_required": review_required,
        "known_conditions": known_conditions_normalized,
        "evidence_items": evidence_items,
        "data_quality_note": data_quality_note,
        "source_entity_type": source_entity_type,
        "source_entity_id": source_entity_id,
        "source_report": source_report,
        "no_fake_table_creation": True,
        "no_fake_migration": True,
        "no_fake_smoke_pass": True,
    }


__all__ = [
    "UNIVERSITY_CORE_TABLE_CLASSIFICATIONS",
    "UNIVERSITY_CORE_READINESS_STATUSES",
    "UNIVERSITY_CORE_READINESS_RISK_LEVELS",
    "validate_university_core_tenant",
    "build_university_core_evidence_item",
    "classify_university_core_readiness",
    "build_university_core_readiness_summary",
]
