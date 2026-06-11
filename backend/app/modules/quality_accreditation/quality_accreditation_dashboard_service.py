"""Read-only deterministic dashboard runtime service for Quality / Accreditation."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.quality_accreditation.dependencies import validate_tenant_id
from app.modules.quality_accreditation.quality_accreditation_dashboard_schemas import (
    DashboardComplianceIndicatorDTO,
    DashboardKpiRollupDTO,
    DashboardRiskIndicatorDTO,
    DashboardRuntimeResponseDTO,
    DashboardSummaryCardDTO,
)


def _now() -> datetime:
    return datetime.now(UTC)


class DashboardRuntimeService:
    """Provides read-only deterministic runtime payload for dashboard rollups."""

    def get_dashboard_runtime(self, db: Session, tenant_id: int) -> DashboardRuntimeResponseDTO:
        del db
        tenant = validate_tenant_id(tenant_id)
        generated_at = _now()

        accreditation_summary = [
            DashboardSummaryCardDTO(metric_key="active_cycles", label="Active accreditation cycles", value=3, status="TRACKED"),
            DashboardSummaryCardDTO(metric_key="critical_gaps", label="Critical accreditation gaps", value=2, status="WATCH"),
        ]
        evidence_coverage_summary = [
            DashboardSummaryCardDTO(metric_key="coverage_percent", label="Evidence coverage %", value=82, status="WATCH"),
            DashboardSummaryCardDTO(metric_key="missing_artifacts", label="Missing evidence artifacts", value=27, status="AT_RISK"),
        ]
        self_assessment_status = [
            DashboardSummaryCardDTO(metric_key="completed_sections", label="Completed self-assessment sections", value=41, status="TRACKED"),
            DashboardSummaryCardDTO(metric_key="overdue_sections", label="Overdue self-assessment sections", value=5, status="WATCH"),
        ]
        corrective_action_status = [
            DashboardSummaryCardDTO(metric_key="open_actions", label="Open corrective actions", value=14, status="WATCH"),
            DashboardSummaryCardDTO(metric_key="overdue_actions", label="Overdue corrective actions", value=4, status="AT_RISK"),
        ]
        improvement_plan_status = [
            DashboardSummaryCardDTO(metric_key="on_track_initiatives", label="On-track improvement initiatives", value=6, status="TRACKED"),
            DashboardSummaryCardDTO(metric_key="delayed_initiatives", label="Delayed improvement initiatives", value=2, status="WATCH"),
        ]
        readiness_monitoring_summary = [
            DashboardSummaryCardDTO(metric_key="avg_readiness_score", label="Average readiness score", value=78, status="WATCH"),
            DashboardSummaryCardDTO(metric_key="domains_at_risk", label="Readiness domains at risk", value=1, status="AT_RISK"),
        ]
        audit_findings_summary = [
            DashboardSummaryCardDTO(metric_key="open_findings", label="Open audit findings", value=9, status="WATCH"),
            DashboardSummaryCardDTO(metric_key="high_severity_findings", label="High severity findings", value=3, status="AT_RISK"),
        ]

        executive_kpi_rollup = [
            DashboardKpiRollupDTO(kpi_group="ACCREDITATION_READINESS", score=79, threshold=85, trend="UP"),
            DashboardKpiRollupDTO(kpi_group="EVIDENCE_COMPLETENESS", score=82, threshold=90, trend="STABLE"),
            DashboardKpiRollupDTO(kpi_group="REMEDIATION_EXECUTION", score=74, threshold=80, trend="UP"),
        ]
        compliance_indicators = [
            DashboardComplianceIndicatorDTO(indicator_name="INTERNAL_CONTROL_COMPLIANCE", indicator_value=84, threshold=90, status="WATCH"),
            DashboardComplianceIndicatorDTO(indicator_name="DOCUMENTATION_CONFORMITY", indicator_value=76, threshold=85, status="AT_RISK"),
        ]
        accreditation_risk_indicators = [
            DashboardRiskIndicatorDTO(
                risk_name="Delayed closure of high-severity findings",
                risk_level="HIGH",
                impacted_area="AUDIT_FINDINGS",
                mitigation_status="IN_PROGRESS",
            ),
            DashboardRiskIndicatorDTO(
                risk_name="Evidence completeness below accreditation threshold",
                risk_level="MEDIUM",
                impacted_area="EVIDENCE_COVERAGE",
                mitigation_status="PLANNED",
            ),
        ]

        return DashboardRuntimeResponseDTO(
            tenant_id=tenant,
            generated_at=generated_at,
            accreditation_summary=accreditation_summary,
            evidence_coverage_summary=evidence_coverage_summary,
            self_assessment_status=self_assessment_status,
            corrective_action_status=corrective_action_status,
            improvement_plan_status=improvement_plan_status,
            readiness_monitoring_summary=readiness_monitoring_summary,
            audit_findings_summary=audit_findings_summary,
            executive_kpi_rollup=executive_kpi_rollup,
            compliance_indicators=compliance_indicators,
            accreditation_risk_indicators=accreditation_risk_indicators,
        )


dashboard_runtime_service = DashboardRuntimeService()
