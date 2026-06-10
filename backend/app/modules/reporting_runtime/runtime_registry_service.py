"""Service layer for Reporting Registry runtime endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.regulatory_reporting_integration.service import (
    get_regulatory_reporting_provider_l4_visibility_summary,
)
from app.modules.reporting_runtime.runtime_registry_schemas import (
    ReportingCycleResponse,
    ReportingCycleSummary,
    ReportingEvidenceResponse,
    ReportingEvidenceSummary,
    ReportingProviderResponse,
    ReportingProviderSummary,
    ReportingRegistryEntry,
    ReportingRegistryResponse,
    ReportingRequirementSummary,
    ReportingStatusSummary,
    ReportingSubmissionResponse,
    ReportingSubmissionSummary,
    ReportingTemplateResponse,
    ReportingTemplateSummary,
)


class ReportingRegistryRuntimeService:
    """Read-only aggregation service for reporting registry runtime."""

    _REPORT_SPECS = [
        ("MINISTRY", "MINISTRY-01", "Ministry Institutional Reporting", "ministry_reporting_dashboard"),
        ("ACCREDITATION", "ACCREDITATION-01", "Accreditation Readiness Reporting", "quality_accreditation"),
        ("REGULATORY", "REGULATORY-01", "Regulatory Compliance Reporting", "regulatory_reporting_integration"),
        ("QS", "QS-01", "QS Ranking Reporting", "analytics"),
        ("THE", "THE-01", "THE Ranking Reporting", "analytics"),
        ("NOBD", "NOBD-01", "NOBD Reporting", "analytics"),
        ("RECTOR", "RECTOR-01", "Rector Strategic Reporting", "executive_governance"),
        ("STATISTICAL", "STATISTICAL-01", "Government Statistical Reporting", "analytics"),
    ]

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _period(self, now: datetime, offset: int) -> str:
        month = ((now.month + offset - 1) % 12) + 1
        return f"{now.year}-Q{((month - 1) // 3) + 1}"

    def _provider_status(self, index: int) -> str:
        statuses = ["NOT_CONNECTED", "PENDING", "READY"]
        return statuses[index % len(statuses)]

    def _submission_status(self, index: int) -> str:
        statuses = ["DRAFT", "IN_REVIEW", "READY", "PENDING"]
        return statuses[index % len(statuses)]

    def _compliance_status(self, index: int) -> str:
        statuses = ["COMPLIANT", "WATCH", "REQUIRES_EVIDENCE"]
        return statuses[index % len(statuses)]

    def _build_common(self, tenant: int) -> tuple[datetime, int, int]:
        now = self._now()
        tenant_factor = (tenant % 5) + 1
        provider_visibility = get_regulatory_reporting_provider_l4_visibility_summary(tenant)
        provider_blockers = int(provider_visibility.get("blocker_count", 0))
        return now, tenant_factor, provider_blockers

    def get_registry(self, tenant_id: int) -> ReportingRegistryResponse:
        tenant = validate_tenant_id_provided(tenant_id)
        now, tenant_factor, provider_blockers = self._build_common(tenant)

        entries: list[ReportingRegistryEntry] = []
        requirements: list[ReportingRequirementSummary] = []
        statuses: list[ReportingStatusSummary] = []

        for index, (report_type, report_code, report_name, owner_module) in enumerate(self._REPORT_SPECS):
            submission_deadline = now + timedelta(days=7 + index + tenant_factor)
            submission_status = self._submission_status(index + tenant_factor)
            compliance_status = self._compliance_status(index + provider_blockers)
            provider_status = self._provider_status(index + provider_blockers)
            reporting_period = self._period(now, index)

            base = {
                "id": f"registry-{tenant}-{index + 1}",
                "report_code": report_code,
                "report_name": report_name,
                "report_type": report_type,
                "owner_module": owner_module,
                "reporting_period": reporting_period,
                "submission_deadline": submission_deadline,
                "submission_status": submission_status,
                "compliance_status": compliance_status,
                "provider_status": provider_status,
                "generated_at": now,
            }

            entries.append(ReportingRegistryEntry(**base))
            requirements.append(
                ReportingRequirementSummary(
                    **{k: v for k, v in base.items() if k != "id"},
                    id=f"requirement-{tenant}-{index + 1}",
                    requirement_code=f"REQ-{report_code}",
                    requirement_status="MET" if index % 2 == 0 else "MISSING_EVIDENCE",
                )
            )
            statuses.append(
                ReportingStatusSummary(
                    **{k: v for k, v in base.items() if k != "id"},
                    id=f"status-{tenant}-{index + 1}",
                    risk_signal="submission_risk" if submission_status in {"DRAFT", "PENDING"} else "stable",
                )
            )

        return ReportingRegistryResponse(tenant_id=tenant, generated_at=now, entries=entries, requirements=requirements, statuses=statuses)

    def get_templates(self, tenant_id: int) -> ReportingTemplateResponse:
        registry = self.get_registry(tenant_id)
        templates = [
            ReportingTemplateSummary(
                **entry.model_dump(exclude={"id"}),
                id=entry.id.replace("registry", "template"),
                template_version=f"v{(index % 3) + 1}.0",
                section_count=6 + index,
            )
            for index, entry in enumerate(registry.entries)
        ]
        return ReportingTemplateResponse(tenant_id=registry.tenant_id, generated_at=registry.generated_at, templates=templates)

    def get_cycles(self, tenant_id: int) -> ReportingCycleResponse:
        registry = self.get_registry(tenant_id)
        cycles = [
            ReportingCycleSummary(
                **entry.model_dump(exclude={"id"}),
                id=entry.id.replace("registry", "cycle"),
                cycle_stage="ACTIVE" if index % 2 == 0 else "PLANNED",
                active_days_remaining=max(0, (entry.submission_deadline - registry.generated_at).days),
            )
            for index, entry in enumerate(registry.entries)
        ]
        return ReportingCycleResponse(tenant_id=registry.tenant_id, generated_at=registry.generated_at, cycles=cycles)

    def get_submissions(self, tenant_id: int) -> ReportingSubmissionResponse:
        registry = self.get_registry(tenant_id)
        submissions = [
            ReportingSubmissionSummary(
                **entry.model_dump(exclude={"id"}),
                id=entry.id.replace("registry", "submission"),
                submission_id=f"SUB-{entry.report_code}-{registry.tenant_id}",
                reviewer_required=True,
            )
            for entry in registry.entries
        ]
        return ReportingSubmissionResponse(tenant_id=registry.tenant_id, generated_at=registry.generated_at, submissions=submissions)

    def get_evidence(self, tenant_id: int) -> ReportingEvidenceResponse:
        registry = self.get_registry(tenant_id)
        evidence = [
            ReportingEvidenceSummary(
                **entry.model_dump(exclude={"id"}),
                id=entry.id.replace("registry", "evidence"),
                evidence_count=3 + index,
                evidence_completeness=min(100, 68 + index * 4),
            )
            for index, entry in enumerate(registry.entries)
        ]
        return ReportingEvidenceResponse(tenant_id=registry.tenant_id, generated_at=registry.generated_at, evidence=evidence)

    def get_providers(self, tenant_id: int) -> ReportingProviderResponse:
        registry = self.get_registry(tenant_id)
        providers = [
            ReportingProviderSummary(
                **entry.model_dump(exclude={"id"}),
                id=entry.id.replace("registry", "provider"),
                provider_key=f"{entry.report_type}_PROVIDER_PROFILE",
                live_integrations_enabled=False,
                submission_execution_enabled=False,
            )
            for entry in registry.entries
        ]
        return ReportingProviderResponse(tenant_id=registry.tenant_id, generated_at=registry.generated_at, providers=providers)
