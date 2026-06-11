"""Read-only deterministic audit findings runtime service for Quality / Accreditation."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.quality_accreditation.dependencies import validate_tenant_id
from app.modules.quality_accreditation.quality_accreditation_audit_findings_schemas import (
    AuditFindingDTO,
    AuditFindingsRuntimeResponseDTO,
    AuditObservationDTO,
    AuditReadinessDTO,
    AuditRecommendationDTO,
    AuditRemediationStatusDTO,
    AuditRiskAnalysisDTO,
    NonConformityDTO,
)


def _now() -> datetime:
    return datetime.now(UTC)


class AuditFindingsRuntimeService:
    """Provides read-only deterministic runtime payload for audit findings."""

    def get_audit_findings_runtime(self, db: Session, tenant_id: int) -> AuditFindingsRuntimeResponseDTO:
        del db
        tenant = validate_tenant_id(tenant_id)
        generated_at = _now()

        findings = [
            AuditFindingDTO(
                finding_id="AF-INT-001",
                finding_source="INTERNAL_AUDIT",
                finding_type="INTERNAL_AUDIT_FINDING",
                finding_title="Evidence traceability gaps for curriculum revisions",
                severity="HIGH",
                impacted_standard="STD-ACADEMIC-01",
                remediation_status="IN_PROGRESS",
                closure_tracking_status="TRACKED",
                opened_at=datetime(2026, 3, 10, tzinfo=UTC),
                due_date=datetime(2026, 7, 20, tzinfo=UTC),
            ),
            AuditFindingDTO(
                finding_id="AF-EXT-004",
                finding_source="EXTERNAL_AUDIT",
                finding_type="EXTERNAL_AUDIT_FINDING",
                finding_title="Insufficient faculty development evidence bundle",
                severity="MEDIUM",
                impacted_standard="STD-FACULTY-02",
                remediation_status="IN_PROGRESS",
                closure_tracking_status="TRACKED",
                opened_at=datetime(2026, 2, 1, tzinfo=UTC),
                due_date=datetime(2026, 8, 15, tzinfo=UTC),
            ),
            AuditFindingDTO(
                finding_id="AF-ACC-009",
                finding_source="ACCREDITATION_REVIEW",
                finding_type="ACCREDITATION_FINDING",
                finding_title="Outcome mapping inconsistencies across core programs",
                severity="CRITICAL",
                impacted_standard="STD-OUTCOME-03",
                remediation_status="PARTIALLY_COMPLETE",
                closure_tracking_status="AT_RISK",
                opened_at=datetime(2026, 1, 20, tzinfo=UTC),
                due_date=datetime(2026, 6, 30, tzinfo=UTC),
            ),
        ]

        non_conformities = [
            NonConformityDTO(
                non_conformity_id="NC-001",
                category="DOCUMENT_CONTROL",
                severity="HIGH",
                affected_area="PROGRAM_REVIEW",
                status="OPEN",
            ),
            NonConformityDTO(
                non_conformity_id="NC-002",
                category="ASSESSMENT_EVIDENCE",
                severity="MEDIUM",
                affected_area="LEARNING_OUTCOMES",
                status="IN_REMEDIATION",
            ),
        ]

        observations = [
            AuditObservationDTO(
                observation_id="OBS-011",
                observation_type="PROCESS_OBSERVATION",
                summary="Variance in evidence naming conventions across faculties.",
                impact_level="MEDIUM",
            ),
            AuditObservationDTO(
                observation_id="OBS-019",
                observation_type="CONTROL_OBSERVATION",
                summary="Quarterly readiness review cadence is inconsistent.",
                impact_level="LOW",
            ),
        ]

        recommendations = [
            AuditRecommendationDTO(
                recommendation_id="REC-101",
                recommendation_title="Implement evidence naming taxonomy governance",
                priority="HIGH",
                owner_unit="quality_accreditation",
                target_date=datetime(2026, 8, 1, tzinfo=UTC),
                status="IN_PROGRESS",
            ),
            AuditRecommendationDTO(
                recommendation_id="REC-102",
                recommendation_title="Standardize internal closure checklist across units",
                priority="MEDIUM",
                owner_unit="academic_operations",
                target_date=datetime(2026, 9, 15, tzinfo=UTC),
                status="PLANNED",
            ),
        ]

        risk_severity_analysis = [
            AuditRiskAnalysisDTO(
                risk_band="CRITICAL",
                findings_count=1,
                non_conformities_count=0,
                recommendations_open=1,
            ),
            AuditRiskAnalysisDTO(
                risk_band="HIGH",
                findings_count=1,
                non_conformities_count=1,
                recommendations_open=1,
            ),
            AuditRiskAnalysisDTO(
                risk_band="MEDIUM",
                findings_count=1,
                non_conformities_count=1,
                recommendations_open=0,
            ),
        ]

        remediation_status = [
            AuditRemediationStatusDTO(
                remediation_state="IN_PROGRESS",
                findings_count=2,
                average_completion_percentage=58,
            ),
            AuditRemediationStatusDTO(
                remediation_state="PARTIALLY_COMPLETE",
                findings_count=1,
                average_completion_percentage=42,
            ),
        ]

        audit_readiness_indicators = [
            AuditReadinessDTO(
                indicator_name="AUDIT_EVIDENCE_COMPLETENESS",
                indicator_value=81,
                threshold=90,
                status="WATCH",
            ),
            AuditReadinessDTO(
                indicator_name="NON_CONFORMITY_CLOSURE_TRAJECTORY",
                indicator_value=74,
                threshold=85,
                status="WATCH",
            ),
            AuditReadinessDTO(
                indicator_name="RECOMMENDATION_EXECUTION_COVERAGE",
                indicator_value=69,
                threshold=80,
                status="AT_RISK",
            ),
        ]

        return AuditFindingsRuntimeResponseDTO(
            tenant_id=tenant,
            generated_at=generated_at,
            findings=findings,
            non_conformities=non_conformities,
            observations=observations,
            recommendations=recommendations,
            risk_severity_analysis=risk_severity_analysis,
            remediation_status=remediation_status,
            audit_readiness_indicators=audit_readiness_indicators,
        )


audit_findings_runtime_service = AuditFindingsRuntimeService()
