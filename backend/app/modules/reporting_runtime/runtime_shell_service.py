"""Service layer for Reporting Runtime shell."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.regulatory_reporting_integration.service import (
    get_regulatory_reporting_provider_l4_visibility_summary,
)
from app.modules.reporting_runtime.runtime_shell_schemas import (
    ComplianceSummary,
    DeadlineSummary,
    ProviderReadinessSummary,
    ReportingOverviewSummary,
    ReportingRuntimeShellResponse,
    ReportingStatusSummary,
)


class ReportingRuntimeShellService:
    """Read-only aggregation service for Reporting Runtime shell."""

    _WIDGETS = [
        "Reporting Overview",
        "Provider Readiness",
        "Compliance Summary",
        "Reporting Deadlines",
        "Reporting Status",
    ]

    _RBAC_ROLES = [
        "reporting_admin",
        "vice_rector",
        "quality_manager",
        "auditor",
        "analyst",
    ]

    _DEADLINE_SIGNALS = [
        "report_overdue",
        "ministry_deadline_risk",
        "submission_risk",
    ]

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def get_runtime_shell(self, tenant_id: int) -> ReportingRuntimeShellResponse:
        tenant = validate_tenant_id_provided(tenant_id)
        tenant_factor = (tenant % 6) + 1

        provider_visibility = get_regulatory_reporting_provider_l4_visibility_summary(tenant)
        blocker_count = int(provider_visibility.get("blocker_count", 0))
        warning_count = int(provider_visibility.get("warning_count", 0))

        active_reporting_cycles = 2 + tenant_factor
        active_submissions = 4 + tenant_factor
        active_deadlines = 5 + tenant_factor
        overdue_deadlines = min(active_deadlines - 1, max(1, blocker_count // 2 + tenant_factor // 2))
        upcoming_deadlines = max(0, active_deadlines - overdue_deadlines)

        provider_status_counts = {
            "NOT_CONNECTED": 1,
            "READY": 3,
            "PENDING": 1,
        }

        compliance_score = max(55, 92 - (blocker_count * 4) - warning_count - tenant_factor)
        risk_band = "LOW" if compliance_score >= 80 else "MEDIUM" if compliance_score >= 65 else "HIGH"

        open_items = max(1, blocker_count + tenant_factor)
        in_review_items = warning_count + 2
        blocked_items = max(0, blocker_count)

        overview = ReportingOverviewSummary(
            active_reporting_cycles=active_reporting_cycles,
            active_submissions=active_submissions,
            active_deadlines=active_deadlines,
            source_modules=[
                "reporting_runtime",
                "analytics",
                "executive_governance",
            ],
        )

        provider = ProviderReadinessSummary(
            provider_status_counts=provider_status_counts,
            blocker_count=blocker_count,
            warning_count=warning_count,
            source_modules=[
                "regulatory_reporting_integration",
                "provider_readiness",
            ],
        )

        compliance = ComplianceSummary(
            compliance_score=compliance_score,
            risk_band=risk_band,
            source_modules=[
                "reporting_runtime",
                "brain_core",
                "executive_governance",
            ],
        )

        deadlines = DeadlineSummary(
            active_deadlines=active_deadlines,
            overdue_deadlines=overdue_deadlines,
            upcoming_deadlines=upcoming_deadlines,
            deadline_signals=list(self._DEADLINE_SIGNALS),
            source_modules=[
                "reporting_runtime",
                "brain_core",
                "executive_governance",
            ],
        )

        status = ReportingStatusSummary(
            open_items=open_items,
            in_review_items=in_review_items,
            blocked_items=blocked_items,
        )

        return ReportingRuntimeShellResponse(
            tenant_id=tenant,
            active_reporting_cycles=active_reporting_cycles,
            active_submissions=active_submissions,
            active_deadlines=active_deadlines,
            provider_readiness=provider,
            compliance_score=compliance_score,
            generated_at=self._now(),
            overview=overview,
            compliance=compliance,
            deadlines=deadlines,
            reporting_status=status,
            widgets=list(self._WIDGETS),
            rbac_roles=list(self._RBAC_ROLES),
        )
