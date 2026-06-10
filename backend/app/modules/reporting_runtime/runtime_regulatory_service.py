"""Service layer for Regulatory Reporting runtime endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.regulatory_reporting_integration.service import (
    get_regulatory_reporting_provider_l4_visibility_summary,
)
from app.modules.reporting_runtime.runtime_registry_service import ReportingRegistryRuntimeService
from app.modules.reporting_runtime.runtime_regulatory_schemas import (
    RegulatoryComplianceResponse,
    RegulatoryComplianceSummary,
    RegulatoryDeadlineResponse,
    RegulatoryDeadlineSummary,
    RegulatoryDocumentResponse,
    RegulatoryDocumentStatus,
    RegulatoryReportingResponse,
    RegulatoryReportingSummary,
    RegulatoryRequirementResponse,
    RegulatoryRequirementSummary,
    RegulatoryRiskResponse,
    RegulatoryRiskSummary,
)


class RegulatoryReportingRuntimeService:
    """Read-only aggregation service for Regulatory Reporting runtime."""

    _REGULATORY_CATALOG = [
        ("REG-LIC-01", "Licensing Requirements", "National Licensing Authority", "regulatory_reporting_integration"),
        ("REG-EDU-01", "Educational Activity Requirements", "Ministry of Education Regulator", "regulatory_reporting_integration"),
        ("REG-SCI-01", "Scientific Activity Requirements", "Science and Research Regulator", "research_science"),
        ("REG-INFSEC-01", "Information Security Requirements", "National Cybersecurity Authority", "security_access_compliance"),
        ("REG-PD-01", "Personal Data Requirements", "Personal Data Protection Authority", "security_access_compliance"),
        ("REG-LAB-01", "Labor Requirements", "Labor Compliance Authority", "hr_staff_governance"),
        ("REG-FIN-01", "Financial Requirements", "Financial Supervisory Authority", "finance_procurement_asset"),
        ("REG-INT-01", "Internal Regulatory Requirements", "University Internal Compliance Office", "executive_governance"),
    ]

    _SIGNALS = [
        "regulatory_deadline_risk",
        "compliance_violation_risk",
        "missing_required_document",
        "licensing_gap",
        "regulatory_readiness_low",
    ]

    def __init__(self) -> None:
        self._registry = ReportingRegistryRuntimeService()

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _compliance_status(self, completion_score: int, days_remaining: int) -> str:
        if completion_score >= 90 and days_remaining >= 12:
            return "COMPLIANT"
        if completion_score >= 72 and days_remaining >= 0:
            return "WATCH"
        return "AT_RISK"

    def _risk_level(self, completion_score: int, days_remaining: int, blockers: int) -> str:
        if days_remaining < 0 or completion_score < 55:
            return "CRITICAL"
        if days_remaining <= 7 or blockers >= 3 or completion_score < 70:
            return "HIGH"
        if days_remaining <= 14 or completion_score < 85:
            return "MEDIUM"
        return "LOW"

    def _document_status(self, completion_score: int) -> str:
        if completion_score >= 90:
            return "COMPLETE"
        if completion_score >= 70:
            return "PARTIAL"
        return "MISSING"

    def _build_entries(self, tenant_id: int) -> tuple[int, datetime, list[dict[str, object]]]:
        tenant = validate_tenant_id_provided(tenant_id)
        now = self._now()

        provider_visibility = get_regulatory_reporting_provider_l4_visibility_summary(tenant)
        blockers = int(provider_visibility.get("blocker_count", 0))
        warnings = int(provider_visibility.get("warning_count", 0))

        registry = self._registry.get_registry(tenant)
        registry_generated_at = registry.generated_at

        tenant_factor = (tenant % 5) + 1
        registry_tilt = len(registry.statuses) % 4

        entries: list[dict[str, object]] = []
        for index, (code, name, regulator_name, owner_module) in enumerate(self._REGULATORY_CATALOG):
            deadline = now + timedelta(days=5 + tenant_factor + (index * 2) - blockers)
            days_remaining = (deadline.date() - now.date()).days
            completion_score = max(
                35,
                min(100, 60 + (tenant_factor * 5) + (index * 4) - (blockers * 5) - warnings - registry_tilt),
            )
            compliance_status = self._compliance_status(completion_score, days_remaining)
            risk_level = self._risk_level(completion_score, days_remaining, blockers)
            document_status = self._document_status(completion_score)

            entries.append(
                {
                    "id": f"regulatory-{tenant}-{index + 1}",
                    "requirement_code": code,
                    "requirement_name": name,
                    "regulator_name": regulator_name,
                    "compliance_status": compliance_status,
                    "deadline": deadline,
                    "days_remaining": days_remaining,
                    "risk_level": risk_level,
                    "document_status": document_status,
                    "owner_module": owner_module,
                    "generated_at": registry_generated_at,
                    "_completion_score": completion_score,
                }
            )

        return tenant, registry_generated_at, entries

    def get_regulatory(self, tenant_id: int) -> RegulatoryReportingResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        reports = [
            RegulatoryReportingSummary(**{k: v for k, v in entry.items() if not k.startswith("_")})
            for entry in entries
        ]
        return RegulatoryReportingResponse(
            tenant_id=tenant,
            generated_at=generated_at,
            reports=reports,
            signal_inventory=list(self._SIGNALS),
        )

    def get_requirements(self, tenant_id: int) -> RegulatoryRequirementResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        requirements = [
            RegulatoryRequirementSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                requirement_status="SATISFIED" if entry["compliance_status"] == "COMPLIANT" else "OPEN",
            )
            for entry in entries
        ]
        return RegulatoryRequirementResponse(tenant_id=tenant, generated_at=generated_at, requirements=requirements)

    def get_compliance(self, tenant_id: int) -> RegulatoryComplianceResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        compliance = [
            RegulatoryComplianceSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                compliance_score=max(0, min(100, int(entry["_completion_score"]))),
            )
            for entry in entries
        ]
        return RegulatoryComplianceResponse(tenant_id=tenant, generated_at=generated_at, compliance=compliance)

    def get_deadlines(self, tenant_id: int) -> RegulatoryDeadlineResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        deadlines = [
            RegulatoryDeadlineSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                deadline_status="OVERDUE" if entry["days_remaining"] < 0 else "UPCOMING",
                overdue=entry["days_remaining"] < 0,
            )
            for entry in entries
        ]
        return RegulatoryDeadlineResponse(tenant_id=tenant, generated_at=generated_at, deadlines=deadlines)

    def get_documents(self, tenant_id: int) -> RegulatoryDocumentResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        documents = [
            RegulatoryDocumentStatus(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                document_name=f"{entry['requirement_code']}-PRIMARY-DOC",
                document_completeness=max(0, min(100, int(entry["_completion_score"]))),
            )
            for entry in entries
        ]
        return RegulatoryDocumentResponse(tenant_id=tenant, generated_at=generated_at, documents=documents)

    def get_risks(self, tenant_id: int) -> RegulatoryRiskResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        risks = [
            RegulatoryRiskSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                signal_name=self._SIGNALS[index % len(self._SIGNALS)],
            )
            for index, entry in enumerate(entries)
        ]
        return RegulatoryRiskResponse(tenant_id=tenant, generated_at=generated_at, risks=risks)
