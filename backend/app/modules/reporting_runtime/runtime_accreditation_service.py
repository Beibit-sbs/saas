"""Service layer for Accreditation Reporting runtime endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.regulatory_reporting_integration.service import (
    get_regulatory_reporting_provider_l4_visibility_summary,
)
from app.modules.reporting_runtime.runtime_accreditation_schemas import (
    AccreditationComplianceResponse,
    AccreditationComplianceSummary,
    AccreditationCycle,
    AccreditationCycleResponse,
    AccreditationDeadlineResponse,
    AccreditationDeadlineSummary,
    AccreditationEvidenceReadiness,
    AccreditationEvidenceReadinessResponse,
    AccreditationReportingResponse,
    AccreditationReportingSummary,
    AccreditationRiskResponse,
    AccreditationRiskSummary,
)
from app.modules.reporting_runtime.runtime_registry_service import ReportingRegistryRuntimeService


class AccreditationReportingRuntimeService:
    """Read-only aggregation service for Accreditation Reporting runtime."""

    _ACCREDITATION_CATALOG = [
        ("ACC-INST-01", "Institutional Accreditation", "INSTITUTIONAL", "National Accreditation Council", "quality_accreditation"),
        ("ACC-SPEC-01", "Specialized Accreditation", "SPECIALIZED", "Sector Accreditation Board", "quality_accreditation"),
        ("ACC-PROG-01", "Program Accreditation", "PROGRAM", "Program Accreditation Agency", "quality_accreditation"),
        ("ACC-INTL-01", "International Accreditation", "INTERNATIONAL", "International Quality Alliance", "quality_accreditation"),
        ("ACC-IQR-01", "Internal Quality Reviews", "INTERNAL_REVIEW", "Internal QA Committee", "quality_accreditation"),
        ("ACC-EVID-01", "Accreditation Evidence Packages", "EVIDENCE_PACKAGE", "Accreditation Documentation Unit", "quality_accreditation"),
    ]

    _SIGNALS = [
        "accreditation_deadline_risk",
        "accreditation_gap",
        "missing_evidence",
        "accreditation_compliance_risk",
        "accreditation_readiness_low",
    ]

    def __init__(self) -> None:
        self._registry = ReportingRegistryRuntimeService()

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _evidence_readiness(self, completion_percentage: int) -> str:
        if completion_percentage >= 88:
            return "READY"
        if completion_percentage >= 70:
            return "PARTIAL"
        return "LOW"

    def _compliance_status(self, completion_percentage: int, days_remaining: int) -> str:
        if completion_percentage >= 90 and days_remaining >= 10:
            return "COMPLIANT"
        if completion_percentage >= 70 and days_remaining >= 0:
            return "WATCH"
        return "AT_RISK"

    def _risk_level(self, completion_percentage: int, days_remaining: int, blockers: int) -> str:
        if days_remaining < 0 or completion_percentage < 55:
            return "CRITICAL"
        if days_remaining <= 7 or blockers >= 3 or completion_percentage < 70:
            return "HIGH"
        if days_remaining <= 14 or completion_percentage < 85:
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
        registry_tilt = len(registry.requirements) % 5
        tenant_factor = (tenant % 5) + 1

        entries: list[dict[str, object]] = []
        for index, (code, name, accreditation_type, agency_name, owner_module) in enumerate(self._ACCREDITATION_CATALOG):
            deadline = now + timedelta(days=6 + tenant_factor + (index * 2) - blockers)
            days_remaining = (deadline.date() - now.date()).days
            completion_percentage = max(
                35,
                min(100, 64 + (tenant_factor * 4) + (index * 4) - (blockers * 5) - warnings - registry_tilt),
            )
            evidence_readiness = self._evidence_readiness(completion_percentage)
            compliance_status = self._compliance_status(completion_percentage, days_remaining)
            risk_level = self._risk_level(completion_percentage, days_remaining, blockers)

            entries.append(
                {
                    "id": f"accreditation-{tenant}-{index + 1}",
                    "accreditation_code": code,
                    "accreditation_name": name,
                    "accreditation_type": accreditation_type,
                    "agency_name": agency_name,
                    "deadline": deadline,
                    "completion_percentage": completion_percentage,
                    "evidence_readiness": evidence_readiness,
                    "compliance_status": compliance_status,
                    "risk_level": risk_level,
                    "days_remaining": days_remaining,
                    "owner_module": owner_module,
                    "generated_at": registry_generated_at,
                }
            )

        return tenant, registry_generated_at, entries

    def get_accreditation(self, tenant_id: int) -> AccreditationReportingResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        reports = [AccreditationReportingSummary(**entry) for entry in entries]
        return AccreditationReportingResponse(
            tenant_id=tenant,
            generated_at=generated_at,
            reports=reports,
            signal_inventory=list(self._SIGNALS),
        )

    def get_cycles(self, tenant_id: int) -> AccreditationCycleResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        cycles = [
            AccreditationCycle(
                **entry,
                cycle_status="ACTIVE" if entry["days_remaining"] >= 0 else "OVERDUE",
            )
            for entry in entries
        ]
        return AccreditationCycleResponse(tenant_id=tenant, generated_at=generated_at, cycles=cycles)

    def get_readiness(self, tenant_id: int) -> AccreditationEvidenceReadinessResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        readiness = [
            AccreditationEvidenceReadiness(
                **entry,
                readiness_score=max(0, min(100, int(entry["completion_percentage"]))),
            )
            for entry in entries
        ]
        return AccreditationEvidenceReadinessResponse(tenant_id=tenant, generated_at=generated_at, readiness=readiness)

    def get_compliance(self, tenant_id: int) -> AccreditationComplianceResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        compliance = [
            AccreditationComplianceSummary(
                **entry,
                compliance_score=max(0, min(100, int(entry["completion_percentage"]) - (8 if entry["risk_level"] in {"HIGH", "CRITICAL"} else 0))),
            )
            for entry in entries
        ]
        return AccreditationComplianceResponse(tenant_id=tenant, generated_at=generated_at, compliance=compliance)

    def get_deadlines(self, tenant_id: int) -> AccreditationDeadlineResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        deadlines = [
            AccreditationDeadlineSummary(
                **entry,
                deadline_status="OVERDUE" if entry["days_remaining"] < 0 else "UPCOMING",
                overdue=entry["days_remaining"] < 0,
            )
            for entry in entries
        ]
        return AccreditationDeadlineResponse(tenant_id=tenant, generated_at=generated_at, deadlines=deadlines)

    def get_risks(self, tenant_id: int) -> AccreditationRiskResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        risks = [
            AccreditationRiskSummary(
                **entry,
                signal_name=self._SIGNALS[index % len(self._SIGNALS)],
            )
            for index, entry in enumerate(entries)
        ]
        return AccreditationRiskResponse(tenant_id=tenant, generated_at=generated_at, risks=risks)
