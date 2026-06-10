"""Service layer for NOBD Reporting runtime endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.regulatory_reporting_integration.service import (
    get_regulatory_reporting_provider_l4_visibility_summary,
)
from app.modules.reporting_runtime.runtime_nobd_schemas import (
    NobdCompletenessResponse,
    NobdCompletenessSummary,
    NobdDatasetResponse,
    NobdDatasetSummary,
    NobdQualityResponse,
    NobdQualitySummary,
    NobdReportingResponse,
    NobdReportingSummary,
    NobdRiskResponse,
    NobdRiskSummary,
    NobdSyncStatusResponse,
    NobdSyncStatusSummary,
)
from app.modules.reporting_runtime.runtime_registry_service import ReportingRegistryRuntimeService


class NobdReportingRuntimeService:
    """Read-only aggregation service for NOBD runtime visibility."""

    _NOBD_DATASETS = [
        ("NOBD-STUDENT", "Student Data", "student_lifecycle"),
        ("NOBD-STAFF", "Staff Data", "hr"),
        ("NOBD-ACADEMIC", "Academic Data", "academic_operations"),
        ("NOBD-PROGRAM", "Educational Programs", "admissions"),
        ("NOBD-RESEARCH", "Research Data", "research_science"),
        ("NOBD-GRADUATE", "Graduate Data", "analytics"),
        ("NOBD-INFRA", "Infrastructure Data", "finance"),
    ]

    _SIGNALS = [
        "nobd_completeness_low",
        "nobd_quality_risk",
        "nobd_sync_delay",
        "missing_required_dataset",
        "nobd_readiness_low",
    ]

    def __init__(self) -> None:
        self._registry = ReportingRegistryRuntimeService()

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _sync_status(self, completeness_percentage: int, warnings: int, blockers: int) -> str:
        if blockers > 1 or completeness_percentage < 70:
            return "ON_HOLD"
        if warnings > 0 or completeness_percentage < 85:
            return "DELAYED"
        return "SCHEDULED"

    def _risk_level(self, completeness_percentage: int, quality_score: int, sync_status: str) -> str:
        if sync_status == "ON_HOLD" or completeness_percentage < 70 or quality_score < 65:
            return "HIGH"
        if sync_status == "DELAYED" or completeness_percentage < 85 or quality_score < 78:
            return "MEDIUM"
        return "LOW"

    def _build_entries(self, tenant_id: int) -> tuple[int, datetime, list[dict[str, object]]]:
        tenant = validate_tenant_id_provided(tenant_id)
        registry = self._registry.get_registry(tenant)
        provider_visibility = get_regulatory_reporting_provider_l4_visibility_summary(tenant)

        blockers = int(provider_visibility.get("blocker_count", 0))
        warnings = int(provider_visibility.get("warning_count", 0))
        tenant_factor = (tenant % 9) + 1
        registry_shift = len(registry.entries) % 5

        entries: list[dict[str, object]] = []
        for index, (dataset_code, dataset_name, owner_module) in enumerate(self._NOBD_DATASETS):
            records_total = 1600 + (index * 240) + (tenant_factor * 60)
            incomplete_penalty = (warnings * 18) + (blockers * 36) + (index % 4) * 12 + registry_shift * 7
            records_complete = max(0, records_total - incomplete_penalty)
            completeness_percentage = max(0, min(100, int((records_complete * 100) / records_total)))
            quality_score = max(45, min(98, completeness_percentage - (index % 3) * 3 + 4 - blockers))
            sync_status = self._sync_status(completeness_percentage, warnings, blockers)
            risk_level = self._risk_level(completeness_percentage, quality_score, sync_status)

            entries.append(
                {
                    "id": f"nobd-{tenant}-{index + 1}",
                    "dataset_code": dataset_code,
                    "dataset_name": dataset_name,
                    "records_total": records_total,
                    "records_complete": records_complete,
                    "completeness_percentage": completeness_percentage,
                    "quality_score": quality_score,
                    "sync_status": sync_status,
                    "risk_level": risk_level,
                    "owner_module": owner_module,
                    "generated_at": registry.generated_at,
                    "_completeness_gap": max(0, records_total - records_complete),
                    "_dataset_priority": "HIGH" if index < 3 else "MEDIUM",
                    "_sync_lag_hours": (warnings * 6) + (blockers * 9) + (index % 3) * 2,
                    "_quality_band": "HIGH" if quality_score >= 85 else "MEDIUM" if quality_score >= 70 else "LOW",
                }
            )

        return tenant, registry.generated_at, entries

    def get_nobd(self, tenant_id: int) -> NobdReportingResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        reports = [
            NobdReportingSummary(**{k: v for k, v in entry.items() if not k.startswith("_")}) for entry in entries
        ]
        return NobdReportingResponse(
            tenant_id=tenant,
            generated_at=generated_at,
            reports=reports,
            signal_inventory=list(self._SIGNALS),
        )

    def get_datasets(self, tenant_id: int) -> NobdDatasetResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        datasets = [
            NobdDatasetSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                dataset_priority=str(entry["_dataset_priority"]),
            )
            for entry in entries
        ]
        return NobdDatasetResponse(tenant_id=tenant, generated_at=generated_at, datasets=datasets)

    def get_completeness(self, tenant_id: int) -> NobdCompletenessResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        completeness = [
            NobdCompletenessSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                completeness_gap=int(entry["_completeness_gap"]),
            )
            for entry in entries
        ]
        return NobdCompletenessResponse(tenant_id=tenant, generated_at=generated_at, completeness=completeness)

    def get_quality(self, tenant_id: int) -> NobdQualityResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        quality = [
            NobdQualitySummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                quality_band=str(entry["_quality_band"]),
            )
            for entry in entries
        ]
        return NobdQualityResponse(tenant_id=tenant, generated_at=generated_at, quality=quality)

    def get_sync_status(self, tenant_id: int) -> NobdSyncStatusResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        sync_status = [
            NobdSyncStatusSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                sync_lag_hours=int(entry["_sync_lag_hours"]),
            )
            for entry in entries
        ]
        return NobdSyncStatusResponse(tenant_id=tenant, generated_at=generated_at, sync_status=sync_status)

    def get_risks(self, tenant_id: int) -> NobdRiskResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        risks = [
            NobdRiskSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                signal_name=self._SIGNALS[index % len(self._SIGNALS)],
            )
            for index, entry in enumerate(entries)
        ]
        return NobdRiskResponse(tenant_id=tenant, generated_at=generated_at, risks=risks)