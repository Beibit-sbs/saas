"""Service layer for Compliance Monitoring runtime endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.regulatory_reporting_integration.service import (
    get_regulatory_reporting_provider_l4_visibility_summary,
)
from app.modules.reporting_runtime.runtime_compliance_schemas import (
    ComplianceControlResponse,
    ComplianceControlSummary,
    ComplianceGapResponse,
    ComplianceGapSummary,
    ComplianceMonitoringResponse,
    ComplianceMonitoringSummary,
    ComplianceReadinessResponse,
    ComplianceReadinessSummary,
    ComplianceRiskResponse,
    ComplianceRiskSummary,
)
from app.modules.reporting_runtime.runtime_registry_service import ReportingRegistryRuntimeService


class ComplianceMonitoringRuntimeService:
    """Read-only aggregation service for compliance monitoring runtime."""

    _COMPLIANCE_CONTROLS = [
        ("CMP-MINISTRY", "Ministry Compliance", "quality_accreditation"),
        ("CMP-ACCREDITATION", "Accreditation Compliance", "quality_accreditation"),
        ("CMP-NOBD", "NOBD Compliance", "student_lifecycle"),
        ("CMP-REGULATORY", "Regulatory Compliance", "executive_governance"),
        ("CMP-RANKING", "Ranking Compliance", "research_science"),
        ("CMP-POLICY", "Internal Policy Compliance", "hr"),
    ]

    _SIGNALS = [
        "compliance_gap_high",
        "compliance_readiness_low",
        "compliance_risk_high",
        "control_failure_detected",
        "mandatory_submission_missing",
    ]

    def __init__(self) -> None:
        self._registry = ReportingRegistryRuntimeService()

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _compliance_status(self, readiness_score: int, gap_count: int) -> str:
        if readiness_score >= 85 and gap_count <= 1:
            return "COMPLIANT"
        if readiness_score >= 70 and gap_count <= 3:
            return "WATCH"
        return "AT_RISK"

    def _risk_level(self, readiness_score: int, gap_count: int, blockers: int) -> str:
        if blockers > 1 or readiness_score < 65 or gap_count >= 5:
            return "HIGH"
        if readiness_score < 80 or gap_count >= 3:
            return "MEDIUM"
        return "LOW"

    def _readiness_level(self, readiness_score: int) -> str:
        if readiness_score >= 85:
            return "READY"
        if readiness_score >= 70:
            return "PARTIAL"
        return "LOW"

    def _build_entries(self, tenant_id: int) -> tuple[int, datetime, list[dict[str, object]]]:
        tenant = validate_tenant_id_provided(tenant_id)
        registry = self._registry.get_registry(tenant)
        provider_visibility = get_regulatory_reporting_provider_l4_visibility_summary(tenant)

        blockers = int(provider_visibility.get("blocker_count", 0))
        warnings = int(provider_visibility.get("warning_count", 0))
        tenant_factor = (tenant % 7) + 1
        registry_shift = len(registry.entries) % 4

        entries: list[dict[str, object]] = []
        for index, (control_code, control_name, owner_module) in enumerate(self._COMPLIANCE_CONTROLS):
            base_score = 88 - (index * 3) + tenant_factor - (blockers * 3) - warnings - registry_shift
            readiness_score = max(45, min(98, base_score))
            gap_count = max(0, (index % 3) + blockers + (warnings // 2))
            compliance_status = self._compliance_status(readiness_score, gap_count)
            risk_level = self._risk_level(readiness_score, gap_count, blockers)

            entries.append(
                {
                    "id": f"compliance-{tenant}-{index + 1}",
                    "control_code": control_code,
                    "control_name": control_name,
                    "compliance_status": compliance_status,
                    "readiness_score": readiness_score,
                    "risk_level": risk_level,
                    "gap_count": gap_count,
                    "owner_module": owner_module,
                    "generated_at": registry.generated_at,
                    "_readiness_level": self._readiness_level(readiness_score),
                    "_control_type": "MANDATORY" if index < 4 else "INTERNAL",
                    "_gap_severity": "HIGH" if gap_count >= 4 else "MEDIUM" if gap_count >= 2 else "LOW",
                }
            )

        return tenant, registry.generated_at, entries

    def get_compliance(self, tenant_id: int) -> ComplianceMonitoringResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        reports = [
            ComplianceMonitoringSummary(**{k: v for k, v in entry.items() if not k.startswith("_")})
            for entry in entries
        ]
        return ComplianceMonitoringResponse(
            tenant_id=tenant,
            generated_at=generated_at,
            reports=reports,
            signal_inventory=list(self._SIGNALS),
        )

    def get_controls(self, tenant_id: int) -> ComplianceControlResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        controls = [
            ComplianceControlSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                control_type=str(entry["_control_type"]),
            )
            for entry in entries
        ]
        return ComplianceControlResponse(tenant_id=tenant, generated_at=generated_at, controls=controls)

    def get_readiness(self, tenant_id: int) -> ComplianceReadinessResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        readiness = [
            ComplianceReadinessSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                readiness_level=str(entry["_readiness_level"]),
            )
            for entry in entries
        ]
        return ComplianceReadinessResponse(tenant_id=tenant, generated_at=generated_at, readiness=readiness)

    def get_gaps(self, tenant_id: int) -> ComplianceGapResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        gaps = [
            ComplianceGapSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                gap_severity=str(entry["_gap_severity"]),
            )
            for entry in entries
        ]
        return ComplianceGapResponse(tenant_id=tenant, generated_at=generated_at, gaps=gaps)

    def get_risks(self, tenant_id: int) -> ComplianceRiskResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        risks = [
            ComplianceRiskSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                signal_name=self._SIGNALS[index % len(self._SIGNALS)],
            )
            for index, entry in enumerate(entries)
        ]
        return ComplianceRiskResponse(tenant_id=tenant, generated_at=generated_at, risks=risks)