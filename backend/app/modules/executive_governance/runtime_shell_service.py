"""Service layer for Executive Governance runtime shell."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.executive_governance.runtime_shell_schemas import (
    ExecutiveGovernanceDashboardSummary,
    ExecutiveGovernanceRuntimeOverview,
    ExecutiveGovernanceRuntimeSummary,
    ExecutiveGovernanceSignalSummary,
)


class ExecutiveGovernanceRuntimeService:
    """Read-only Executive Governance runtime contract service."""

    _CANONICAL_MODULES = [
        "executive_control_tower",
        "rector_assignment_workflow",
        "committee_decision_registry",
        "order_decree_registry",
        "analytics",
        "brain_core",
    ]

    _SIGNAL_SOURCES: dict[str, str] = {
        "overdue_assignment": "rector_assignment_workflow",
        "execution_delay": "rector_assignment_workflow",
        "resolution_risk": "committee_decision_registry",
        "kpi_drift": "analytics",
        "escalation_risk": "rector_assignment_workflow",
        "strategic_goal_slippage": "analytics",
        "executive_workload": "executive_control_tower",
        "ministry_deadline_risk": "order_decree_registry",
        "protocol_non_execution": "order_decree_registry",
        "decision_stagnation": "committee_decision_registry",
    }

    _RBAC_ROLES = [
        "rector",
        "vice_rector",
        "chief_of_staff",
        "executive_manager",
        "auditor",
        "administrator",
    ]

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _validate_tenant(self, tenant_id: int) -> int:
        return validate_tenant_id_provided(tenant_id)

    def _build_counts(self, tenant_id: int) -> dict[str, int]:
        tenant_factor = (tenant_id % 7) + 1
        executive_assignments = 16 + tenant_factor
        executive_decisions = 9 + tenant_factor
        executive_protocols = 6 + (tenant_factor // 2)
        executive_meetings = 4 + (tenant_factor // 3)
        overdue_items = max(1, tenant_factor - 1)
        escalated_items = max(1, tenant_factor - 2)
        strategic_items = 5 + (tenant_factor // 2)
        executive_signals = len(self._SIGNAL_SOURCES)
        return {
            "executive_assignments": executive_assignments,
            "executive_decisions": executive_decisions,
            "executive_protocols": executive_protocols,
            "executive_meetings": executive_meetings,
            "overdue_items": overdue_items,
            "escalated_items": escalated_items,
            "strategic_items": strategic_items,
            "executive_signals": executive_signals,
        }

    def get_overview(self, tenant_id: int) -> ExecutiveGovernanceRuntimeOverview:
        tenant = self._validate_tenant(tenant_id)
        counts = self._build_counts(tenant)
        return ExecutiveGovernanceRuntimeOverview(
            tenant_id=tenant,
            canonical_modules=list(self._CANONICAL_MODULES),
            generated_at=self._now(),
            **counts,
        )

    def get_summary(self, tenant_id: int) -> ExecutiveGovernanceRuntimeSummary:
        tenant = self._validate_tenant(tenant_id)
        counts = self._build_counts(tenant)
        return ExecutiveGovernanceRuntimeSummary(
            tenant_id=tenant,
            owner_modules=list(self._CANONICAL_MODULES),
            generated_at=self._now(),
            **counts,
        )

    def get_signals(self, tenant_id: int) -> list[ExecutiveGovernanceSignalSummary]:
        tenant = self._validate_tenant(tenant_id)
        tenant_factor = (tenant % 7) + 1
        signals: list[ExecutiveGovernanceSignalSummary] = []
        for index, (family, source_module) in enumerate(self._SIGNAL_SOURCES.items(), start=1):
            signals.append(
                ExecutiveGovernanceSignalSummary(
                    signal_family=family,
                    source_module=source_module,
                    observed_items=index + tenant_factor,
                    notes="Read-only governance signal consumed from brain_core ownership.",
                )
            )
        return signals

    def get_dashboard(self, tenant_id: int) -> ExecutiveGovernanceDashboardSummary:
        tenant = self._validate_tenant(tenant_id)
        counts = self._build_counts(tenant)
        return ExecutiveGovernanceDashboardSummary(
            tenant_id=tenant,
            widgets=[
                "Executive Overview",
                "Decision Summary",
                "Assignment Summary",
                "Protocol Summary",
                "Signal Summary",
                "Dashboard Summary",
            ],
            signal_summaries=self.get_signals(tenant),
            rbac_roles=list(self._RBAC_ROLES),
            generated_at=self._now(),
            **counts,
        )
