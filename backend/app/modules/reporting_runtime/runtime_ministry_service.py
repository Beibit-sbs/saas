"""Service layer for Ministry Reporting runtime endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.regulatory_reporting_integration.service import (
    get_regulatory_reporting_provider_l4_visibility_summary,
)
from app.modules.reporting_runtime.runtime_ministry_schemas import (
    MinistryReportingCompleteness,
    MinistryReportingCompletenessResponse,
    MinistryReportingCycle,
    MinistryReportingCycleResponse,
    MinistryReportingDeadline,
    MinistryReportingDeadlineResponse,
    MinistryReportingReadiness,
    MinistryReportingReadinessResponse,
    MinistryReportingRisk,
    MinistryReportingRiskResponse,
    MinistryReportingSummary,
    MinistryReportingSummaryResponse,
)
from app.modules.reporting_runtime.runtime_registry_service import ReportingRegistryRuntimeService


class MinistryReportingRuntimeService:
    """Read-only aggregation service for Ministry Reporting runtime."""

    _MINISTRY_REPORT_CATALOG = [
        ("MIN-STAT-01", "Statistical reporting", "analytics"),
        ("MIN-ACAD-01", "Academic reporting", "ministry_reporting_dashboard"),
        ("MIN-SCI-01", "Scientific reporting", "research_science"),
        ("MIN-FIN-01", "Financial reporting", "finance_procurement_asset"),
        ("MIN-INFRA-01", "Infrastructure reporting", "campus_facilities_housing_transport"),
        ("MIN-HR-01", "Human resource reporting", "hr_staff_governance"),
        ("MIN-DIGI-01", "Digitalization reporting", "platform"),
    ]

    _SIGNALS = [
        "ministry_deadline_risk",
        "report_overdue",
        "missing_required_data",
        "reporting_incomplete",
        "reporting_readiness_low",
    ]

    def __init__(self) -> None:
        self._registry = ReportingRegistryRuntimeService()

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _readiness_status(self, completion_percentage: int, days_remaining: int) -> str:
        if completion_percentage >= 90 and days_remaining >= 10:
            return "READY"
        if completion_percentage >= 70 and days_remaining >= 5:
            return "PARTIAL"
        return "LOW"

    def _submission_status(self, completion_percentage: int, days_remaining: int) -> str:
        if completion_percentage >= 95:
            return "READY"
        if days_remaining <= 0:
            return "OVERDUE"
        if completion_percentage >= 70:
            return "IN_REVIEW"
        return "DRAFT"

    def _risk_level(self, completion_percentage: int, days_remaining: int, blockers: int) -> str:
        if days_remaining < 0 or completion_percentage < 55:
            return "CRITICAL"
        if days_remaining <= 5 or blockers >= 3 or completion_percentage < 70:
            return "HIGH"
        if days_remaining <= 10 or completion_percentage < 85:
            return "MEDIUM"
        return "LOW"

    def _build_entries(self, tenant_id: int) -> tuple[int, datetime, list[dict[str, object]]]:
        tenant = validate_tenant_id_provided(tenant_id)
        now = self._now()

        provider_visibility = get_regulatory_reporting_provider_l4_visibility_summary(tenant)
        blockers = int(provider_visibility.get("blocker_count", 0))
        warnings = int(provider_visibility.get("warning_count", 0))

        registry = self._registry.get_registry(tenant)
        registry_generated_at = registry.generated_at

        tenant_factor = (tenant % 6) + 1
        baseline_shift = len(registry.entries) % 4

        entries: list[dict[str, object]] = []
        for index, (report_code, report_name, owner_module) in enumerate(self._MINISTRY_REPORT_CATALOG):
            deadline = now + timedelta(days=3 + tenant_factor + index - blockers)
            days_remaining = (deadline.date() - now.date()).days
            completion_percentage = max(35, min(100, 62 + (tenant_factor * 4) + (index * 5) - (blockers * 6) - warnings - baseline_shift))
            readiness_status = self._readiness_status(completion_percentage, days_remaining)
            submission_status = self._submission_status(completion_percentage, days_remaining)
            risk_level = self._risk_level(completion_percentage, days_remaining, blockers)

            entries.append(
                {
                    "id": f"ministry-{tenant}-{index + 1}",
                    "report_code": report_code,
                    "report_name": report_name,
                    "reporting_period": f"{now.year}-Q{((now.month - 1) // 3) + 1}",
                    "deadline": deadline,
                    "completion_percentage": completion_percentage,
                    "readiness_status": readiness_status,
                    "submission_status": submission_status,
                    "risk_level": risk_level,
                    "days_remaining": days_remaining,
                    "owner_module": owner_module,
                    "generated_at": registry_generated_at,
                }
            )

        return tenant, registry_generated_at, entries

    def get_ministry(self, tenant_id: int) -> MinistryReportingSummaryResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        reports = [MinistryReportingSummary(**entry) for entry in entries]
        return MinistryReportingSummaryResponse(
            tenant_id=tenant,
            generated_at=generated_at,
            reports=reports,
            signal_inventory=list(self._SIGNALS),
        )

    def get_cycles(self, tenant_id: int) -> MinistryReportingCycleResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        cycles = [
            MinistryReportingCycle(
                **entry,
                cycle_status="ACTIVE" if entry["days_remaining"] >= 0 else "OVERDUE",
            )
            for entry in entries
        ]
        return MinistryReportingCycleResponse(tenant_id=tenant, generated_at=generated_at, cycles=cycles)

    def get_deadlines(self, tenant_id: int) -> MinistryReportingDeadlineResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        deadlines = [
            MinistryReportingDeadline(
                **entry,
                deadline_status="OVERDUE" if entry["days_remaining"] < 0 else "UPCOMING",
                overdue=entry["days_remaining"] < 0,
            )
            for entry in entries
        ]
        return MinistryReportingDeadlineResponse(tenant_id=tenant, generated_at=generated_at, deadlines=deadlines)

    def get_readiness(self, tenant_id: int) -> MinistryReportingReadinessResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        readiness = [
            MinistryReportingReadiness(
                **entry,
                readiness_score=max(0, min(100, int(entry["completion_percentage"]))),
            )
            for entry in entries
        ]
        return MinistryReportingReadinessResponse(tenant_id=tenant, generated_at=generated_at, readiness=readiness)

    def get_completeness(self, tenant_id: int) -> MinistryReportingCompletenessResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        completeness: list[MinistryReportingCompleteness] = []
        for index, entry in enumerate(entries):
            required_data_points = 10 + (index * 2)
            completed_data_points = round((required_data_points * int(entry["completion_percentage"])) / 100)
            completeness.append(
                MinistryReportingCompleteness(
                    **entry,
                    required_data_points=required_data_points,
                    completed_data_points=min(required_data_points, completed_data_points),
                )
            )
        return MinistryReportingCompletenessResponse(tenant_id=tenant, generated_at=generated_at, completeness=completeness)

    def get_risks(self, tenant_id: int) -> MinistryReportingRiskResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        risks = [
            MinistryReportingRisk(
                **entry,
                signal_name=self._SIGNALS[index % len(self._SIGNALS)],
            )
            for index, entry in enumerate(entries)
        ]
        return MinistryReportingRiskResponse(tenant_id=tenant, generated_at=generated_at, risks=risks)
