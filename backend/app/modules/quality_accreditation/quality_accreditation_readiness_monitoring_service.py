"""Read-only deterministic readiness monitoring runtime service for Quality / Accreditation."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.quality_accreditation.dependencies import validate_tenant_id
from app.modules.quality_accreditation.quality_accreditation_readiness_monitoring_schemas import (
    ReadinessDomainDTO,
    ReadinessIndicatorDTO,
    ReadinessMonitoringRuntimeResponseDTO,
    ReadinessRemediationDTO,
    ReadinessRiskDTO,
    ReadinessSummaryDTO,
)


def _now() -> datetime:
    return datetime.now(UTC)


class ReadinessMonitoringRuntimeService:
    """Provides read-only deterministic runtime payload for readiness monitoring."""

    def get_readiness_monitoring_runtime(self, db: Session, tenant_id: int) -> ReadinessMonitoringRuntimeResponseDTO:
        del db
        tenant = validate_tenant_id(tenant_id)
        generated_at = _now()

        readiness_domains = [
            ReadinessDomainDTO(
                domain_id="RD-001",
                domain_name="INTERNAL_AUDIT_READINESS",
                readiness_score=83,
                threshold=90,
                status="WATCH",
                trend="UP",
            ),
            ReadinessDomainDTO(
                domain_id="RD-002",
                domain_name="EXTERNAL_REVIEW_READINESS",
                readiness_score=78,
                threshold=88,
                status="WATCH",
                trend="STABLE",
            ),
            ReadinessDomainDTO(
                domain_id="RD-003",
                domain_name="ACCREDITATION_EVIDENCE_READINESS",
                readiness_score=71,
                threshold=85,
                status="AT_RISK",
                trend="DOWN",
            ),
            ReadinessDomainDTO(
                domain_id="RD-004",
                domain_name="CLOSURE_TRACKING_READINESS",
                readiness_score=80,
                threshold=86,
                status="WATCH",
                trend="UP",
            ),
        ]

        readiness_risks = [
            ReadinessRiskDTO(
                risk_id="RR-011",
                risk_title="Delayed closure of high-severity findings",
                risk_level="HIGH",
                impacted_domain="CLOSURE_TRACKING_READINESS",
                mitigation_status="IN_PROGRESS",
            ),
            ReadinessRiskDTO(
                risk_id="RR-014",
                risk_title="Evidence normalization backlog in key standards",
                risk_level="MEDIUM",
                impacted_domain="ACCREDITATION_EVIDENCE_READINESS",
                mitigation_status="PLANNED",
            ),
        ]

        remediation_tracking = [
            ReadinessRemediationDTO(
                remediation_id="RM-201",
                remediation_title="Close unresolved internal audit checklist items",
                owner_unit="quality_accreditation",
                completion_percentage=64,
                status="IN_PROGRESS",
                due_date=datetime(2026, 8, 30, tzinfo=UTC),
            ),
            ReadinessRemediationDTO(
                remediation_id="RM-207",
                remediation_title="Standardize evidence packaging for external review",
                owner_unit="academic_operations",
                completion_percentage=48,
                status="IN_PROGRESS",
                due_date=datetime(2026, 9, 20, tzinfo=UTC),
            ),
        ]

        readiness_indicators = [
            ReadinessIndicatorDTO(
                indicator_name="READINESS_SCORE_GLOBAL",
                indicator_value=78,
                threshold=85,
                status="WATCH",
            ),
            ReadinessIndicatorDTO(
                indicator_name="HIGH_SEVERITY_CLOSURE_RATE",
                indicator_value=67,
                threshold=80,
                status="AT_RISK",
            ),
            ReadinessIndicatorDTO(
                indicator_name="EVIDENCE_COMPLETENESS_RATE",
                indicator_value=82,
                threshold=90,
                status="WATCH",
            ),
        ]

        readiness_summary = ReadinessSummaryDTO(
            monitored_domains_total=len(readiness_domains),
            domains_on_track=0,
            domains_at_risk=1,
            average_readiness_score=78,
        )

        return ReadinessMonitoringRuntimeResponseDTO(
            tenant_id=tenant,
            generated_at=generated_at,
            readiness_summary=readiness_summary,
            readiness_domains=readiness_domains,
            readiness_risks=readiness_risks,
            remediation_tracking=remediation_tracking,
            readiness_indicators=readiness_indicators,
        )


readiness_monitoring_runtime_service = ReadinessMonitoringRuntimeService()
