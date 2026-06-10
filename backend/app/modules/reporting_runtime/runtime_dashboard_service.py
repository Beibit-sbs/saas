"""Service layer for Reporting Dashboard runtime endpoints."""

from __future__ import annotations

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.reporting_runtime.runtime_accreditation_service import AccreditationReportingRuntimeService
from app.modules.reporting_runtime.runtime_compliance_service import ComplianceMonitoringRuntimeService
from app.modules.reporting_runtime.runtime_dashboard_schemas import (
    ReportingDashboardResponse,
    ReportingDashboardSummary,
    ReportingReadinessResponse,
    ReportingReadinessSummary,
    ReportingRiskResponse,
    ReportingRiskSummary,
    ReportingSignalResponse,
    ReportingSignalSummary,
    ReportingWorkloadResponse,
    ReportingWorkloadSummary,
)
from app.modules.reporting_runtime.runtime_ministry_service import MinistryReportingRuntimeService
from app.modules.reporting_runtime.runtime_nobd_service import NobdReportingRuntimeService
from app.modules.reporting_runtime.runtime_ranking_service import RankingReportingRuntimeService
from app.modules.reporting_runtime.runtime_registry_service import ReportingRegistryRuntimeService
from app.modules.reporting_runtime.runtime_regulatory_service import RegulatoryReportingRuntimeService


class ReportingDashboardRuntimeService:
    """Read-only aggregation service for executive reporting dashboard runtime."""

    _SIGNALS = [
        "reporting_readiness_low",
        "reporting_workload_high",
        "reporting_risk_high",
        "reporting_submission_delay",
        "reporting_attention_required",
    ]

    _DASHBOARD_CATALOG = [
        ("DASH-MINISTRY", "Ministry Reporting", "ministry_reporting_dashboard"),
        ("DASH-ACCREDITATION", "Accreditation Reporting", "quality_accreditation"),
        ("DASH-REGULATORY", "Regulatory Reporting", "regulatory_reporting_integration"),
        ("DASH-RANKING", "Ranking Reporting", "research_science"),
        ("DASH-NOBD", "NOBD Reporting", "student_lifecycle"),
        ("DASH-COMPLIANCE", "Compliance Monitoring", "brain_core"),
    ]

    def __init__(self) -> None:
        self._registry = ReportingRegistryRuntimeService()
        self._ministry = MinistryReportingRuntimeService()
        self._accreditation = AccreditationReportingRuntimeService()
        self._regulatory = RegulatoryReportingRuntimeService()
        self._ranking = RankingReportingRuntimeService()
        self._nobd = NobdReportingRuntimeService()
        self._compliance = ComplianceMonitoringRuntimeService()

    def _status(self, readiness_score: int, risk_score: int, workload_score: int) -> str:
        if readiness_score >= 85 and risk_score <= 35 and workload_score <= 65:
            return "READY"
        if readiness_score >= 70 and risk_score <= 55 and workload_score <= 80:
            return "WATCH"
        return "ATTENTION"

    def _risk_from_levels(self, levels: list[str]) -> int:
        if not levels:
            return 40
        score = 0
        for level in levels:
            if level == "CRITICAL":
                score += 95
            elif level == "HIGH":
                score += 80
            elif level == "MEDIUM":
                score += 55
            else:
                score += 30
        return max(0, min(100, int(score / len(levels))))

    def _build_entries(self, tenant_id: int) -> tuple[int, object, list[dict[str, object]]]:
        tenant = validate_tenant_id_provided(tenant_id)

        registry = self._registry.get_registry(tenant)
        submissions = self._registry.get_submissions(tenant)
        cycles = self._registry.get_cycles(tenant)

        ministry_readiness = self._ministry.get_readiness(tenant)
        ministry_risks = self._ministry.get_risks(tenant)

        accreditation_readiness = self._accreditation.get_readiness(tenant)
        accreditation_risks = self._accreditation.get_risks(tenant)

        regulatory_compliance = self._regulatory.get_compliance(tenant)
        regulatory_risks = self._regulatory.get_risks(tenant)

        ranking_readiness = self._ranking.get_readiness(tenant)
        ranking_risks = self._ranking.get_risks(tenant)

        nobd_completeness = self._nobd.get_completeness(tenant)
        nobd_risks = self._nobd.get_risks(tenant)

        compliance_readiness = self._compliance.get_readiness(tenant)
        compliance_risks = self._compliance.get_risks(tenant)

        entries: list[dict[str, object]] = []

        ministry_readiness_score = int(
            sum(item.readiness_score for item in ministry_readiness.readiness) / max(1, len(ministry_readiness.readiness))
        )
        ministry_risk_score = self._risk_from_levels([item.risk_level for item in ministry_risks.risks])
        ministry_workload = min(100, (len(ministry_readiness.readiness) * 8) + (len(submissions.submissions) * 3))
        entries.append(
            {
                "id": f"reporting-dashboard-{tenant}-1",
                "dashboard_code": self._DASHBOARD_CATALOG[0][0],
                "dashboard_name": self._DASHBOARD_CATALOG[0][1],
                "status": self._status(ministry_readiness_score, ministry_risk_score, ministry_workload),
                "readiness_score": ministry_readiness_score,
                "risk_score": ministry_risk_score,
                "workload_score": ministry_workload,
                "signal_count": len(ministry_risks.risks),
                "owner_module": self._DASHBOARD_CATALOG[0][2],
                "generated_at": registry.generated_at,
            }
        )

        accreditation_readiness_score = int(
            sum(item.readiness_score for item in accreditation_readiness.readiness)
            / max(1, len(accreditation_readiness.readiness))
        )
        accreditation_risk_score = self._risk_from_levels([item.risk_level for item in accreditation_risks.risks])
        accreditation_workload = min(100, (len(accreditation_readiness.readiness) * 9) + (len(cycles.cycles) * 2))
        entries.append(
            {
                "id": f"reporting-dashboard-{tenant}-2",
                "dashboard_code": self._DASHBOARD_CATALOG[1][0],
                "dashboard_name": self._DASHBOARD_CATALOG[1][1],
                "status": self._status(accreditation_readiness_score, accreditation_risk_score, accreditation_workload),
                "readiness_score": accreditation_readiness_score,
                "risk_score": accreditation_risk_score,
                "workload_score": accreditation_workload,
                "signal_count": len(accreditation_risks.risks),
                "owner_module": self._DASHBOARD_CATALOG[1][2],
                "generated_at": registry.generated_at,
            }
        )

        regulatory_readiness_score = int(
            sum(item.compliance_score for item in regulatory_compliance.compliance)
            / max(1, len(regulatory_compliance.compliance))
        )
        regulatory_risk_score = self._risk_from_levels([item.risk_level for item in regulatory_risks.risks])
        regulatory_workload = min(100, (len(regulatory_compliance.compliance) * 8) + (len(registry.requirements) * 2))
        entries.append(
            {
                "id": f"reporting-dashboard-{tenant}-3",
                "dashboard_code": self._DASHBOARD_CATALOG[2][0],
                "dashboard_name": self._DASHBOARD_CATALOG[2][1],
                "status": self._status(regulatory_readiness_score, regulatory_risk_score, regulatory_workload),
                "readiness_score": regulatory_readiness_score,
                "risk_score": regulatory_risk_score,
                "workload_score": regulatory_workload,
                "signal_count": len(regulatory_risks.risks),
                "owner_module": self._DASHBOARD_CATALOG[2][2],
                "generated_at": registry.generated_at,
            }
        )

        ranking_readiness_score = int(
            sum(item.readiness_score for item in ranking_readiness.readiness)
            / max(1, len(ranking_readiness.readiness))
        )
        ranking_risk_score = self._risk_from_levels([item.risk_level for item in ranking_risks.risks])
        ranking_workload = min(100, (len(ranking_readiness.readiness) * 6) + 20)
        entries.append(
            {
                "id": f"reporting-dashboard-{tenant}-4",
                "dashboard_code": self._DASHBOARD_CATALOG[3][0],
                "dashboard_name": self._DASHBOARD_CATALOG[3][1],
                "status": self._status(ranking_readiness_score, ranking_risk_score, ranking_workload),
                "readiness_score": ranking_readiness_score,
                "risk_score": ranking_risk_score,
                "workload_score": ranking_workload,
                "signal_count": len(ranking_risks.risks),
                "owner_module": self._DASHBOARD_CATALOG[3][2],
                "generated_at": registry.generated_at,
            }
        )

        nobd_readiness_score = int(
            sum(item.completeness_percentage for item in nobd_completeness.completeness)
            / max(1, len(nobd_completeness.completeness))
        )
        nobd_risk_score = self._risk_from_levels([item.risk_level for item in nobd_risks.risks])
        nobd_workload = min(100, (len(nobd_completeness.completeness) * 7) + (len(registry.entries) * 2))
        entries.append(
            {
                "id": f"reporting-dashboard-{tenant}-5",
                "dashboard_code": self._DASHBOARD_CATALOG[4][0],
                "dashboard_name": self._DASHBOARD_CATALOG[4][1],
                "status": self._status(nobd_readiness_score, nobd_risk_score, nobd_workload),
                "readiness_score": nobd_readiness_score,
                "risk_score": nobd_risk_score,
                "workload_score": nobd_workload,
                "signal_count": len(nobd_risks.risks),
                "owner_module": self._DASHBOARD_CATALOG[4][2],
                "generated_at": registry.generated_at,
            }
        )

        compliance_readiness_score = int(
            sum(item.readiness_score for item in compliance_readiness.readiness)
            / max(1, len(compliance_readiness.readiness))
        )
        compliance_risk_score = self._risk_from_levels([item.risk_level for item in compliance_risks.risks])
        compliance_workload = min(100, (len(compliance_readiness.readiness) * 10) + (len(registry.statuses) * 2))
        entries.append(
            {
                "id": f"reporting-dashboard-{tenant}-6",
                "dashboard_code": self._DASHBOARD_CATALOG[5][0],
                "dashboard_name": self._DASHBOARD_CATALOG[5][1],
                "status": self._status(compliance_readiness_score, compliance_risk_score, compliance_workload),
                "readiness_score": compliance_readiness_score,
                "risk_score": compliance_risk_score,
                "workload_score": compliance_workload,
                "signal_count": len(compliance_risks.risks),
                "owner_module": self._DASHBOARD_CATALOG[5][2],
                "generated_at": registry.generated_at,
            }
        )

        return tenant, registry.generated_at, entries

    def get_dashboard(self, tenant_id: int) -> ReportingDashboardResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        dashboards = [ReportingDashboardSummary(**entry) for entry in entries]
        return ReportingDashboardResponse(
            tenant_id=tenant,
            generated_at=generated_at,
            dashboards=dashboards,
            signal_inventory=list(self._SIGNALS),
        )

    def get_readiness(self, tenant_id: int) -> ReportingReadinessResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        readiness = [ReportingReadinessSummary(**entry) for entry in entries]
        return ReportingReadinessResponse(tenant_id=tenant, generated_at=generated_at, readiness=readiness)

    def get_workload(self, tenant_id: int) -> ReportingWorkloadResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        workload = [ReportingWorkloadSummary(**entry) for entry in entries]
        return ReportingWorkloadResponse(tenant_id=tenant, generated_at=generated_at, workload=workload)

    def get_risks(self, tenant_id: int) -> ReportingRiskResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        risks = [ReportingRiskSummary(**entry) for entry in entries]
        return ReportingRiskResponse(tenant_id=tenant, generated_at=generated_at, risks=risks)

    def get_signals(self, tenant_id: int) -> ReportingSignalResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        signals = [ReportingSignalSummary(**entry) for entry in entries]
        return ReportingSignalResponse(tenant_id=tenant, generated_at=generated_at, signals=signals)
