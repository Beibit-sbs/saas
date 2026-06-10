"""Read-only accreditation registry runtime service for Quality / Accreditation."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.modules.quality_accreditation import models, repository
from app.modules.quality_accreditation.dependencies import validate_tenant_id
from app.modules.quality_accreditation.quality_accreditation_registry_schemas import (
    AccreditationProviderSummary,
    AccreditationReadinessSummary,
    AccreditationRegistryItem,
    AccreditationRegistryRuntimeResponse,
    AccreditationRiskSummary,
    AccreditationStatusSummary,
)


_EXPIRING_THRESHOLD_DAYS = 180


def _now() -> datetime:
    return datetime.now(UTC)


def _coerce_datetime(value: object | None, fallback: datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return fallback


def _accreditation_type(title: str, framework_ref: str | None) -> str:
    title_lower = title.lower()
    if "institution" in title_lower:
        return "INSTITUTIONAL"
    if "program" in title_lower:
        return "PROGRAM"
    if framework_ref:
        return framework_ref.upper()
    return "STANDARD"


def _provider_name(framework_ref: str | None, source_capability_id: str | None, source_family_id: str | None) -> str:
    for value in (framework_ref, source_family_id, source_capability_id):
        if value:
            return str(value)
    return "quality_accreditation"


def _scope_name(framework_ref: str | None, program_ref: str | None, source_capability_id: str | None) -> str:
    for value in (program_ref, framework_ref, source_capability_id):
        if value:
            return str(value)
    return "quality_accreditation"


def _readiness_band(score: int) -> str:
    if score >= 85:
        return "READY"
    if score >= 70:
        return "NEAR_READY"
    if score >= 50:
        return "IN_PROGRESS"
    return "NEEDS_ATTENTION"


def _risk_level(score: int, status: str) -> str:
    status_upper = status.upper()
    if status_upper in {"ARCHIVED"}:
        return "LOW"
    if score >= 85:
        return "LOW"
    if score >= 70:
        return "MEDIUM"
    return "HIGH"


def _expiry_date(issued_at: datetime, status: str) -> datetime:
    status_upper = status.upper()
    if status_upper in {"ARCHIVED"}:
        return issued_at + timedelta(days=30)
    if status_upper in {"REVIEW_REQUIRED", "IN_PROGRESS", "EVIDENCE_INCOMPLETE"}:
        return issued_at + timedelta(days=120)
    if status_upper in {"DRAFT", "NOT_STARTED"}:
        return issued_at + timedelta(days=180)
    return issued_at + timedelta(days=365)


def _readiness_score(standard: Any, readiness_by_key: dict[str, int], readiness_by_scope: dict[str, int]) -> int:
    for key in (
        getattr(standard, "standard_ref", None),
        getattr(standard, "framework_ref", None),
        getattr(standard, "program_ref", None),
    ):
        if key and key in readiness_by_key:
            return readiness_by_key[key]
        if key and key in readiness_by_scope:
            return readiness_by_scope[key]
    return 60 if getattr(standard, "status", "") in {models.AccreditationStandardStatus.ACTIVE_METADATA_ONLY, models.AccreditationStandardStatus.UNDER_REVIEW} else 45


def _readiness_key(record: Any) -> str | None:
    for field_name in ("framework_ref", "program_ref", "readiness_ref"):
        value = getattr(record, field_name, None)
        if value:
            return str(value)
    return None


def _risk_key(record: Any) -> str | None:
    for field_name in ("standard_ref", "program_ref", "risk_ref"):
        value = getattr(record, field_name, None)
        if value:
            return str(value)
    return None


def _build_item(
    standard: Any,
    *,
    readiness_by_key: dict[str, int],
    readiness_by_scope: dict[str, int],
    risk_by_key: dict[str, str],
    generated_at: datetime,
) -> AccreditationRegistryItem:
    issued_at = _coerce_datetime(getattr(standard, "created_at", None), generated_at)
    status = str(getattr(standard, "status", "UNKNOWN"))
    readiness_score = max(0, min(100, _readiness_score(standard, readiness_by_key, readiness_by_scope)))
    risk_level = risk_by_key.get(str(getattr(standard, "standard_ref", ""))) or _risk_level(readiness_score, status)
    framework_ref = getattr(standard, "framework_ref", None)
    provider = _provider_name(framework_ref, getattr(standard, "source_capability_id", None), getattr(standard, "source_family_id", None))
    scope = _scope_name(framework_ref, getattr(standard, "program_ref", None), getattr(standard, "source_capability_id", None))

    return AccreditationRegistryItem(
        accreditation_id=str(getattr(standard, "standard_ref", getattr(standard, "id", "accreditation-unknown"))),
        accreditation_name=str(getattr(standard, "title", "Untitled Accreditation")),
        accreditation_type=_accreditation_type(str(getattr(standard, "title", "")), framework_ref),
        accreditation_scope=scope,
        provider=provider,
        status=status,
        issued_date=issued_at,
        expiry_date=_expiry_date(issued_at, status),
        readiness_score=readiness_score,
        risk_level=risk_level,
    )


def _summarize_provider(items: list[AccreditationRegistryItem]) -> list[AccreditationProviderSummary]:
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "active": 0, "expiring": 0})
    for item in items:
        bucket = grouped[item.provider]
        bucket["total"] += 1
        if item.status.upper() not in {"ARCHIVED"}:
            bucket["active"] += 1
        if item.expiry_date <= item.issued_date + timedelta(days=_EXPIRING_THRESHOLD_DAYS):
            bucket["expiring"] += 1
    return [
        AccreditationProviderSummary(provider=provider, accreditation_count=values["total"], active_count=values["active"], expiring_count=values["expiring"])
        for provider, values in sorted(grouped.items())
    ]


def _summarize_status(items: list[AccreditationRegistryItem]) -> list[AccreditationStatusSummary]:
    grouped: dict[str, int] = defaultdict(int)
    for item in items:
        grouped[item.status] += 1
    return [AccreditationStatusSummary(status=status, accreditation_count=count) for status, count in sorted(grouped.items())]


def _summarize_readiness(items: list[AccreditationRegistryItem]) -> list[AccreditationReadinessSummary]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for item in items:
        grouped[_readiness_band(item.readiness_score)].append(item.readiness_score)
    return [
        AccreditationReadinessSummary(
            readiness_band=band,
            accreditation_count=len(scores),
            average_readiness_score=sum(scores) / len(scores),
        )
        for band, scores in sorted(grouped.items())
    ]


def _summarize_risk(items: list[AccreditationRegistryItem]) -> list[AccreditationRiskSummary]:
    grouped: dict[str, int] = defaultdict(int)
    for item in items:
        grouped[item.risk_level] += 1
    return [AccreditationRiskSummary(risk_level=risk_level, accreditation_count=count) for risk_level, count in sorted(grouped.items())]


class AccreditationRegistryRuntimeService:
    """Read-only aggregation service for the accreditation registry runtime."""

    def get_accreditation_registry(self, db: Session, tenant_id: int) -> AccreditationRegistryRuntimeResponse:
        tenant = validate_tenant_id(tenant_id)
        generated_at = _now()

        standards = repository.list_resources(db, models.AccreditationStandard, tenant)
        program_readiness = repository.list_resources(db, models.ProgramAccreditationReadiness, tenant)
        institutional_readiness = repository.list_resources(db, models.InstitutionalAccreditationReadiness, tenant)
        risks = repository.list_resources(db, models.QualityRiskRegister, tenant)

        readiness_by_key: dict[str, int] = {}
        readiness_by_scope: dict[str, int] = {}
        for record in [*program_readiness, *institutional_readiness]:
            key = _readiness_key(record)
            if key:
                readiness_score = max(0, min(100, int(getattr(record, "completion_percent", 0))))
                readiness_by_key[key] = max(readiness_by_key.get(key, 0), readiness_score)
                readiness_by_scope[key] = max(readiness_by_scope.get(key, 0), readiness_score)

        risk_by_key: dict[str, str] = {}
        for record in risks:
            key = _risk_key(record)
            if key:
                risk_by_key[key] = str(getattr(record, "risk_band", "UNKNOWN"))

        items = [
            _build_item(
                standard,
                readiness_by_key=readiness_by_key,
                readiness_by_scope=readiness_by_scope,
                risk_by_key=risk_by_key,
                generated_at=generated_at,
            )
            for standard in standards
        ]

        active_items = [item for item in items if item.status.upper() not in {"ARCHIVED"}]
        expiring_items = [item for item in active_items if item.expiry_date <= generated_at + timedelta(days=_EXPIRING_THRESHOLD_DAYS)]

        return AccreditationRegistryRuntimeResponse(
            tenant_id=tenant,
            generated_at=generated_at,
            active_accreditations=active_items,
            expiring_accreditations=expiring_items,
            accreditation_provider=_summarize_provider(items),
            accreditation_status=_summarize_status(items),
            accreditation_readiness=_summarize_readiness(items),
            accreditation_risk=_summarize_risk(items),
        )


accreditation_registry_runtime_service = AccreditationRegistryRuntimeService()