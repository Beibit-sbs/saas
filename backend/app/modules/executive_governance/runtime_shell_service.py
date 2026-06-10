"""Service layer for Executive Governance runtime shell."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.executive_governance.runtime_shell_schemas import (
    DevelopmentProgramSummary,
    ExecutiveAssignmentEntry,
    ExecutiveAssignmentSummary,
    ExecutiveControlTowerSummary,
    ExecutiveDecisionExecutionSummary,
    ExecutiveDecisionRegistryEntry,
    ExecutiveDecisionRegistrySummary,
    ExecutiveKpiOverview,
    ExecutiveExecutionMetrics,
    ExecutiveGovernanceDashboardSummary,
    ExecutiveMeetingEntry,
    ExecutiveMeetingSummary,
    ExecutiveProtocolEntry,
    ExecutiveProtocolExecutionSummary,
    ExecutiveProtocolSummary,
    ExecutiveGovernanceRuntimeOverview,
    ExecutiveGovernanceRuntimeSummary,
    ExecutiveGovernanceSignalSummary,
    ExecutivePerformanceMetrics,
    ExecutiveRiskOverview,
    RectorDashboardRuntimeSummary,
    StrategicInitiativeEntry,
    StrategicInitiativeMetrics,
    StrategicInitiativeSummary,
)


class ExecutiveDecisionRegistryAggregatorService:
    """Read-only aggregator over decision canonicals without ownership transfer."""

    _DECISION_SOURCES = ["committee_decision_registry", "order_decree_registry"]
    _EXECUTION_SOURCE = "rector_assignment_workflow"
    _SIGNAL_FAMILIES = [
        "decision_stagnation",
        "overdue_assignment",
        "execution_delay",
        "escalation_risk",
        "protocol_non_execution",
    ]
    _EXECUTION_STATUSES = [
        "NOT_STARTED",
        "IN_PROGRESS",
        "AT_RISK",
        "ESCALATED",
        "OVERDUE",
        "COMPLETED",
        "CLOSED",
    ]

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _validate_tenant(self, tenant_id: int) -> int:
        return validate_tenant_id_provided(tenant_id)

    def _build_entries(self, tenant_id: int) -> list[ExecutiveDecisionRegistryEntry]:
        tenant = self._validate_tenant(tenant_id)
        tenant_factor = (tenant % 7) + 1
        today = self._now()
        entries: list[ExecutiveDecisionRegistryEntry] = []
        for idx, status in enumerate(self._EXECUTION_STATUSES):
            source = self._DECISION_SOURCES[idx % len(self._DECISION_SOURCES)]
            is_overdue = status == "OVERDUE"
            is_escalated = status == "ESCALATED"
            entries.append(
                ExecutiveDecisionRegistryEntry(
                    decision_id=f"EGD-{tenant:02d}-{idx + 1:03d}",
                    decision_type="committee_decision" if source == "committee_decision_registry" else "order_decree",
                    decision_source=source,
                    decision_title=f"Executive decision item {idx + 1}",
                    decision_status="ACTIVE" if status not in {"COMPLETED", "CLOSED"} else "FINALIZED",
                    decision_date=today,
                    execution_status=status,
                    execution_progress=min(100, 10 * (idx + tenant_factor)),
                    assigned_units=["rectorate", "strategy-office"] if idx % 2 == 0 else ["chief-of-staff-office"],
                    overdue_flag=is_overdue,
                    escalation_flag=is_escalated,
                )
            )
        return entries

    def get_decisions(self, tenant_id: int) -> list[ExecutiveDecisionRegistryEntry]:
        return self._build_entries(tenant_id)

    def get_decisions_summary(self, tenant_id: int) -> ExecutiveDecisionRegistrySummary:
        tenant = self._validate_tenant(tenant_id)
        entries = self._build_entries(tenant)
        source_counts = {source: 0 for source in self._DECISION_SOURCES}
        status_counts = {status: 0 for status in self._EXECUTION_STATUSES}
        for entry in entries:
            source_counts[entry.decision_source] += 1
            status_counts[entry.execution_status] += 1
        return ExecutiveDecisionRegistrySummary(
            tenant_id=tenant,
            entries=entries,
            total_decisions=len(entries),
            decision_sources=source_counts,
            execution_status_counts=status_counts,
            owner_modules=[*self._DECISION_SOURCES, self._EXECUTION_SOURCE],
            generated_at=self._now(),
        )

    def get_decision_execution_summary(self, tenant_id: int) -> ExecutiveDecisionExecutionSummary:
        tenant = self._validate_tenant(tenant_id)
        entries = self._build_entries(tenant)
        status_counts = {status: 0 for status in self._EXECUTION_STATUSES}
        overdue_items = 0
        escalated_items = 0
        for entry in entries:
            status_counts[entry.execution_status] += 1
            overdue_items += 1 if entry.overdue_flag else 0
            escalated_items += 1 if entry.escalation_flag else 0
        return ExecutiveDecisionExecutionSummary(
            tenant_id=tenant,
            total_decisions=len(entries),
            execution_status_counts=status_counts,
            overdue_items=overdue_items,
            escalated_items=escalated_items,
            signal_families=list(self._SIGNAL_FAMILIES),
            generated_at=self._now(),
        )


class ExecutiveMeetingRegistryRuntimeService:
    """Read-only meeting registry runtime service."""

    _MEETING_STATUSES = ["SCHEDULED", "CONDUCTED", "APPROVED", "CLOSED"]
    _EXECUTION_STATUSES = ["NOT_STARTED", "IN_PROGRESS", "AT_RISK", "COMPLETED"]

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _validate_tenant(self, tenant_id: int) -> int:
        return validate_tenant_id_provided(tenant_id)

    def _build_entries(self, tenant_id: int) -> list[ExecutiveMeetingEntry]:
        tenant = self._validate_tenant(tenant_id)
        tenant_factor = (tenant % 5) + 1
        entries: list[ExecutiveMeetingEntry] = []
        for idx, status in enumerate(self._MEETING_STATUSES):
            entries.append(
                ExecutiveMeetingEntry(
                    meeting_id=f"MEET-{tenant:02d}-{idx + 1:03d}",
                    meeting_type="executive_board" if idx % 2 == 0 else "protocol_committee",
                    meeting_title=f"Executive governance meeting {idx + 1}",
                    meeting_date=self._now(),
                    meeting_status=status,
                    chairperson="rector" if idx % 2 == 0 else "chief_of_staff",
                    participants_count=6 + tenant_factor + idx,
                    protocol_count=1 + (idx % 2),
                    decision_count=2 + idx,
                    execution_status=self._EXECUTION_STATUSES[idx],
                )
            )
        return entries

    def get_meetings(self, tenant_id: int) -> list[ExecutiveMeetingEntry]:
        return self._build_entries(tenant_id)

    def get_meetings_summary(self, tenant_id: int) -> ExecutiveMeetingSummary:
        tenant = self._validate_tenant(tenant_id)
        entries = self._build_entries(tenant)
        status_counts = {status: 0 for status in self._MEETING_STATUSES}
        total_protocols = 0
        total_decisions = 0
        for entry in entries:
            status_counts[entry.meeting_status] += 1
            total_protocols += entry.protocol_count
            total_decisions += entry.decision_count
        return ExecutiveMeetingSummary(
            tenant_id=tenant,
            entries=entries,
            total_meetings=len(entries),
            meeting_status_counts=status_counts,
            total_protocols=total_protocols,
            total_decisions=total_decisions,
            generated_at=self._now(),
        )


class ExecutiveProtocolRegistryRuntimeService:
    """Read-only protocol registry runtime service."""

    _PROTOCOL_STATUSES = ["DRAFT", "APPROVED", "IN_EXECUTION", "COMPLETED", "CLOSED"]
    _SIGNAL_FAMILIES = [
        "protocol_non_execution",
        "execution_delay",
        "overdue_assignment",
        "escalation_risk",
        "decision_stagnation",
    ]

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _validate_tenant(self, tenant_id: int) -> int:
        return validate_tenant_id_provided(tenant_id)

    def _build_entries(self, tenant_id: int) -> list[ExecutiveProtocolEntry]:
        tenant = self._validate_tenant(tenant_id)
        tenant_factor = (tenant % 6) + 1
        entries: list[ExecutiveProtocolEntry] = []
        for idx, status in enumerate(self._PROTOCOL_STATUSES):
            progress = min(100, (idx + tenant_factor) * 15)
            overdue = 1 if status in {"IN_EXECUTION", "APPROVED"} and idx % 2 == 0 else 0
            escalated = 1 if status == "IN_EXECUTION" and idx % 2 == 1 else 0
            entries.append(
                ExecutiveProtocolEntry(
                    protocol_id=f"PROT-{tenant:02d}-{idx + 1:03d}",
                    protocol_number=f"PG-{tenant:02d}-{100 + idx}",
                    protocol_title=f"Executive protocol item {idx + 1}",
                    protocol_date=self._now(),
                    protocol_status=status,
                    decision_count=2 + idx,
                    assignment_count=3 + idx,
                    execution_progress=progress,
                    overdue_items=overdue,
                    escalated_items=escalated,
                )
            )
        return entries

    def get_protocols(self, tenant_id: int) -> list[ExecutiveProtocolEntry]:
        return self._build_entries(tenant_id)

    def get_protocols_summary(self, tenant_id: int) -> ExecutiveProtocolSummary:
        tenant = self._validate_tenant(tenant_id)
        entries = self._build_entries(tenant)
        status_counts = {status: 0 for status in self._PROTOCOL_STATUSES}
        total_decisions = 0
        total_assignments = 0
        total_progress = 0
        overdue_items = 0
        escalated_items = 0
        for entry in entries:
            status_counts[entry.protocol_status] += 1
            total_decisions += entry.decision_count
            total_assignments += entry.assignment_count
            total_progress += entry.execution_progress
            overdue_items += entry.overdue_items
            escalated_items += entry.escalated_items
        avg_progress = total_progress // len(entries) if entries else 0
        return ExecutiveProtocolSummary(
            tenant_id=tenant,
            entries=entries,
            total_protocols=len(entries),
            protocol_status_counts=status_counts,
            total_decisions=total_decisions,
            total_assignments=total_assignments,
            average_execution_progress=avg_progress,
            overdue_items=overdue_items,
            escalated_items=escalated_items,
            generated_at=self._now(),
        )

    def get_protocols_execution(self, tenant_id: int) -> ExecutiveProtocolExecutionSummary:
        tenant = self._validate_tenant(tenant_id)
        summary = self.get_protocols_summary(tenant)
        completion_status = {
            "COMPLETED": summary.protocol_status_counts.get("COMPLETED", 0),
            "CLOSED": summary.protocol_status_counts.get("CLOSED", 0),
            "IN_EXECUTION": summary.protocol_status_counts.get("IN_EXECUTION", 0),
        }
        linkage_inventory = {
            "meeting_registry": summary.total_protocols,
            "protocol_registry": summary.total_protocols,
            "decision_registry": summary.total_decisions,
            "rector_assignment_workflow": summary.total_assignments,
        }
        return ExecutiveProtocolExecutionSummary(
            tenant_id=tenant,
            total_protocols=summary.total_protocols,
            average_execution_progress=summary.average_execution_progress,
            overdue_items=summary.overdue_items,
            escalated_items=summary.escalated_items,
            completion_status=completion_status,
            linkage_inventory=linkage_inventory,
            signal_families=list(self._SIGNAL_FAMILIES),
            generated_at=self._now(),
        )


class ExecutiveAssignmentExecutionRuntimeService:
    """Read-only assignment execution aggregator runtime service."""

    _ASSIGNMENT_SOURCES = [
        "rector_assignment_workflow",
        "protocol_registry",
        "decision_registry",
    ]
    _ASSIGNMENT_TYPES = [
        "RECTOR_ASSIGNMENT",
        "PROTOCOL_ASSIGNMENT",
        "DECISION_ASSIGNMENT",
    ]
    _EXECUTION_STATUSES = [
        "NOT_STARTED",
        "IN_PROGRESS",
        "AT_RISK",
        "ESCALATED",
        "OVERDUE",
        "COMPLETED",
        "CLOSED",
    ]
    _RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    _SIGNAL_FAMILIES = [
        "overdue_assignment",
        "execution_delay",
        "escalation_risk",
        "assignment_stagnation",
        "workload_imbalance",
        "strategic_goal_slippage",
        "ministry_deadline_risk",
    ]

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _validate_tenant(self, tenant_id: int) -> int:
        return validate_tenant_id_provided(tenant_id)

    def _build_entries(self, tenant_id: int) -> list[ExecutiveAssignmentEntry]:
        tenant = self._validate_tenant(tenant_id)
        tenant_factor = (tenant % 7) + 1
        now = self._now()
        entries: list[ExecutiveAssignmentEntry] = []
        for idx, status in enumerate(self._EXECUTION_STATUSES):
            risk_level = self._RISK_LEVELS[min(len(self._RISK_LEVELS) - 1, idx // 2)]
            overdue = status == "OVERDUE"
            escalated = status == "ESCALATED"
            entries.append(
                ExecutiveAssignmentEntry(
                    assignment_id=f"EGA-{tenant:02d}-{idx + 1:03d}",
                    assignment_title=f"Executive assignment item {idx + 1}",
                    assignment_source=self._ASSIGNMENT_SOURCES[idx % len(self._ASSIGNMENT_SOURCES)],
                    assignment_type=self._ASSIGNMENT_TYPES[idx % len(self._ASSIGNMENT_TYPES)],
                    assigned_unit="strategy-office" if idx % 2 == 0 else "chief-of-staff-office",
                    assigned_person=f"exec.user.{tenant_factor + idx}",
                    created_at=now,
                    due_date=now,
                    completion_percent=min(100, (idx + tenant_factor) * 12),
                    execution_status=status,
                    risk_level=risk_level,
                    overdue_flag=overdue,
                    escalation_flag=escalated,
                )
            )
        return entries

    def get_assignments(self, tenant_id: int) -> list[ExecutiveAssignmentEntry]:
        return self._build_entries(tenant_id)

    def get_assignments_summary(self, tenant_id: int) -> ExecutiveAssignmentSummary:
        tenant = self._validate_tenant(tenant_id)
        entries = self._build_entries(tenant)
        total_assignments = len(entries)
        active_assignments = sum(1 for item in entries if item.execution_status not in {"COMPLETED", "CLOSED"})
        completed_assignments = sum(1 for item in entries if item.execution_status in {"COMPLETED", "CLOSED"})
        overdue_assignments = sum(1 for item in entries if item.overdue_flag)
        escalated_assignments = sum(1 for item in entries if item.escalation_flag)
        execution_performance = sum(item.completion_percent for item in entries) // total_assignments if total_assignments else 0
        execution_trend = "IMPROVING" if execution_performance >= 65 else "DECLINING" if overdue_assignments > 1 else "STABLE"
        return ExecutiveAssignmentSummary(
            tenant_id=tenant,
            entries=entries,
            total_assignments=total_assignments,
            active_assignments=active_assignments,
            completed_assignments=completed_assignments,
            overdue_assignments=overdue_assignments,
            escalated_assignments=escalated_assignments,
            execution_performance=execution_performance,
            execution_trend=execution_trend,
            owner_modules=["rector_assignment_workflow", "decision_registry", "protocol_registry", "analytics"],
            generated_at=self._now(),
        )

    def get_assignments_execution(self, tenant_id: int) -> ExecutiveExecutionMetrics:
        tenant = self._validate_tenant(tenant_id)
        summary = self.get_assignments_summary(tenant)
        status_counts = {status: 0 for status in self._EXECUTION_STATUSES}
        escalation_inventory = {"high": 0, "critical": 0, "overdue": 0}
        high_risk_assignments: list[ExecutiveAssignmentEntry] = []
        for entry in summary.entries:
            status_counts[entry.execution_status] += 1
            if entry.risk_level in {"HIGH", "CRITICAL"}:
                high_risk_assignments.append(entry)
            if entry.risk_level == "HIGH":
                escalation_inventory["high"] += 1
            if entry.risk_level == "CRITICAL":
                escalation_inventory["critical"] += 1
            if entry.overdue_flag:
                escalation_inventory["overdue"] += 1
        escalation_summary = {
            "total_escalations": summary.escalated_assignments,
            "high_risk": escalation_inventory["high"] + escalation_inventory["critical"],
            "overdue": summary.overdue_assignments,
        }
        return ExecutiveExecutionMetrics(
            tenant_id=tenant,
            total_assignments=summary.total_assignments,
            execution_status_counts=status_counts,
            overdue_assignments=summary.overdue_assignments,
            escalated_assignments=summary.escalated_assignments,
            execution_performance=summary.execution_performance,
            execution_trend=summary.execution_trend,
            escalation_inventory=escalation_inventory,
            escalation_summary=escalation_summary,
            escalation_trends=["weekly_stable", "monthly_improving"],
            high_risk_assignments=high_risk_assignments,
            signal_families=list(self._SIGNAL_FAMILIES),
            generated_at=self._now(),
        )

    def get_assignments_risks(self, tenant_id: int) -> ExecutiveExecutionMetrics:
        tenant = self._validate_tenant(tenant_id)
        metrics = self.get_assignments_execution(tenant)
        metrics.execution_trend = "DECLINING" if metrics.overdue_assignments > 1 else metrics.execution_trend
        metrics.escalation_trends = ["high_risk_watchlist_active", "escalation_rate_stable"]
        return metrics


class ExecutiveControlTowerRuntimeService:
    """Read-only executive control tower aggregation service."""

    _CONTROL_SIGNALS = [
        "executive_workload",
        "strategic_goal_slippage",
        "execution_delay",
        "escalation_risk",
        "ministry_deadline_risk",
        "overdue_assignment",
        "kpi_drift",
    ]

    _UNITS = ["rectorate", "strategy-office", "chief-of-staff-office", "academic-affairs", "operations"]

    def __init__(
        self,
        decisions: ExecutiveDecisionRegistryAggregatorService,
        assignments: ExecutiveAssignmentExecutionRuntimeService,
        meetings: ExecutiveMeetingRegistryRuntimeService,
        protocols: ExecutiveProtocolRegistryRuntimeService,
    ) -> None:
        self._decisions = decisions
        self._assignments = assignments
        self._meetings = meetings
        self._protocols = protocols

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _validate_tenant(self, tenant_id: int) -> int:
        return validate_tenant_id_provided(tenant_id)

    def _base_metrics(self, tenant_id: int) -> tuple[int, int, ExecutiveAssignmentSummary, ExecutiveExecutionMetrics]:
        tenant = self._validate_tenant(tenant_id)
        decision_summary = self._decisions.get_decisions_summary(tenant)
        protocol_summary = self._protocols.get_protocols_summary(tenant)
        assignment_summary = self._assignments.get_assignments_summary(tenant)
        assignment_exec = self._assignments.get_assignments_execution(tenant)
        return decision_summary.total_decisions, protocol_summary.total_protocols, assignment_summary, assignment_exec

    def get_control_tower(self, tenant_id: int) -> ExecutiveControlTowerSummary:
        tenant = self._validate_tenant(tenant_id)
        total_decisions, total_protocols, assignment_summary, assignment_exec = self._base_metrics(tenant)
        risk_score = min(100, 30 + (assignment_summary.overdue_assignments * 8) + (assignment_summary.escalated_assignments * 10))
        kpi_score = max(0, min(100, assignment_exec.execution_performance + 12 - (assignment_summary.overdue_assignments * 6)))
        executive_workload = max(1, assignment_summary.active_assignments * 10)
        return ExecutiveControlTowerSummary(
            tenant_id=tenant,
            total_decisions=total_decisions,
            total_protocols=total_protocols,
            total_assignments=assignment_summary.total_assignments,
            active_assignments=assignment_summary.active_assignments,
            completed_assignments=assignment_summary.completed_assignments,
            overdue_assignments=assignment_summary.overdue_assignments,
            escalated_assignments=assignment_summary.escalated_assignments,
            execution_rate=assignment_exec.execution_performance,
            risk_score=risk_score,
            kpi_score=kpi_score,
            executive_workload=executive_workload,
            strategic_initiatives={"on_track": 4, "at_risk": 2, "delayed": 1},
            generated_at=self._now(),
        )

    def get_control_tower_summary(self, tenant_id: int) -> RectorDashboardRuntimeSummary:
        tenant = self._validate_tenant(tenant_id)
        overview = self.get_control_tower(tenant)
        perf = self.get_control_tower_escalations(tenant)
        risks = self.get_control_tower_risks(tenant)
        kpis = self.get_control_tower_kpis(tenant)
        return RectorDashboardRuntimeSummary(
            tenant_id=tenant,
            rector_overview=overview,
            university_execution_status=perf,
            strategic_initiatives=overview.strategic_initiatives,
            executive_risks=risks,
            kpi_performance=kpis,
            escalation_summary={
                "overdue_assignments": overview.overdue_assignments,
                "escalated_assignments": overview.escalated_assignments,
                "escalation_rate": perf.escalation_rate,
            },
            generated_at=self._now(),
        )

    def get_control_tower_risks(self, tenant_id: int) -> ExecutiveRiskOverview:
        tenant = self._validate_tenant(tenant_id)
        overview = self.get_control_tower(tenant)
        assignment_risks = self._assignments.get_assignments_risks(tenant)
        risk_distribution = {
            "low": max(0, overview.total_assignments - len(assignment_risks.high_risk_assignments) - 2),
            "medium": 2,
            "high": assignment_risks.escalation_inventory.get("high", 0),
            "critical": assignment_risks.escalation_inventory.get("critical", 0),
        }
        return ExecutiveRiskOverview(
            tenant_id=tenant,
            risk_score=overview.risk_score,
            risk_distribution=risk_distribution,
            high_risk_assignments=assignment_risks.high_risk_assignments,
            high_risk_units={"chief-of-staff-office": 2, "strategy-office": 1},
            high_risk_initiatives={"strategic_reform_track": 1, "deadline_recovery": 1},
            escalation_hotspots={"chief-of-staff-office": 2, "operations": 1},
            overdue_hotspots={"strategy-office": 1, "operations": 1},
            signal_families=list(self._CONTROL_SIGNALS),
            generated_at=self._now(),
        )

    def get_control_tower_kpis(self, tenant_id: int) -> ExecutiveKpiOverview:
        tenant = self._validate_tenant(tenant_id)
        overview = self.get_control_tower(tenant)
        _, _, assignment_summary, assignment_exec = self._base_metrics(tenant)
        completion_rate = (assignment_summary.completed_assignments * 100) // max(1, assignment_summary.total_assignments)
        escalation_rate = (assignment_summary.escalated_assignments * 100) // max(1, assignment_summary.total_assignments)
        return ExecutiveKpiOverview(
            tenant_id=tenant,
            kpi_score=overview.kpi_score,
            kpi_distribution={"green": 5, "amber": 2, "red": 1},
            execution_rate=assignment_exec.execution_performance,
            completion_rate=completion_rate,
            escalation_rate=escalation_rate,
            unit_performance={unit: max(50, 78 - (idx * 5)) for idx, unit in enumerate(self._UNITS)},
            strategic_initiative_status=overview.strategic_initiatives,
            signal_families=list(self._CONTROL_SIGNALS),
            generated_at=self._now(),
        )

    def get_control_tower_escalations(self, tenant_id: int) -> ExecutivePerformanceMetrics:
        tenant = self._validate_tenant(tenant_id)
        overview = self.get_control_tower(tenant)
        completion_rate = (overview.completed_assignments * 100) // max(1, overview.total_assignments)
        escalation_rate = (overview.escalated_assignments * 100) // max(1, overview.total_assignments)
        workload_distribution = {unit: max(1, (overview.active_assignments + idx) // 2) for idx, unit in enumerate(self._UNITS)}
        return ExecutivePerformanceMetrics(
            tenant_id=tenant,
            total_decisions=overview.total_decisions,
            total_protocols=overview.total_protocols,
            total_assignments=overview.total_assignments,
            active_assignments=overview.active_assignments,
            completed_assignments=overview.completed_assignments,
            overdue_assignments=overview.overdue_assignments,
            escalated_assignments=overview.escalated_assignments,
            execution_rate=overview.execution_rate,
            completion_rate=completion_rate,
            escalation_rate=escalation_rate,
            workload_distribution=workload_distribution,
            unit_performance={unit: max(48, 80 - (idx * 6)) for idx, unit in enumerate(self._UNITS)},
            strategic_initiative_status=overview.strategic_initiatives,
            generated_at=self._now(),
        )


class StrategicInitiativeRuntimeService:
    """Read-only strategic initiative runtime aggregation service."""

    _STATUSES = ["PLANNED", "ACTIVE", "AT_RISK", "DELAYED", "COMPLETED", "ON_HOLD"]
    _SIGNAL_FAMILIES = [
        "strategic_goal_slippage",
        "roadmap_delay",
        "initiative_stagnation",
        "kpi_deviation",
        "execution_gap",
        "strategic_risk",
        "transformation_delay",
    ]
    _RBAC_ROLES = [
        "rector",
        "vice_rector",
        "chief_of_staff",
        "executive_manager",
        "strategic_office",
        "auditor",
        "administrator",
    ]

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _validate_tenant(self, tenant_id: int) -> int:
        return validate_tenant_id_provided(tenant_id)

    def _build_entries(self, tenant_id: int) -> list[StrategicInitiativeEntry]:
        tenant = self._validate_tenant(tenant_id)
        tenant_factor = (tenant % 6) + 1
        now = self._now()
        entries: list[StrategicInitiativeEntry] = []
        for idx, status in enumerate(self._STATUSES):
            risk_level = "CRITICAL" if status == "DELAYED" else "HIGH" if status == "AT_RISK" else "MEDIUM" if status in {"ACTIVE", "ON_HOLD"} else "LOW"
            entries.append(
                StrategicInitiativeEntry(
                    initiative_id=f"SI-{tenant:02d}-{idx + 1:03d}",
                    initiative_code=f"INIT-{tenant_factor}-{idx + 1}",
                    initiative_title=f"Strategic initiative {idx + 1}",
                    initiative_owner="strategic_office" if idx % 2 == 0 else "rectorate",
                    initiative_status=status,
                    start_date=now,
                    target_date=now,
                    completion_percent=min(100, (idx + tenant_factor) * 14),
                    linked_kpi_count=2 + (idx % 3),
                    linked_assignment_count=3 + idx,
                    risk_level=risk_level,
                    escalation_flag=status in {"AT_RISK", "DELAYED"},
                )
            )
        return entries

    def get_strategic_initiatives(self, tenant_id: int) -> list[StrategicInitiativeEntry]:
        return self._build_entries(tenant_id)

    def get_strategic_initiatives_summary(self, tenant_id: int) -> StrategicInitiativeSummary:
        tenant = self._validate_tenant(tenant_id)
        initiatives = self._build_entries(tenant)
        total = len(initiatives)
        active = sum(1 for i in initiatives if i.initiative_status in {"ACTIVE", "AT_RISK", "DELAYED", "ON_HOLD"})
        completed = sum(1 for i in initiatives if i.initiative_status == "COMPLETED")
        at_risk = sum(1 for i in initiatives if i.initiative_status == "AT_RISK")
        delayed = sum(1 for i in initiatives if i.initiative_status == "DELAYED")
        linked_kpis = sum(i.linked_kpi_count for i in initiatives)
        initiative_kpi_coverage = (linked_kpis * 100) // max(1, total * 4)
        kpi_completion_alignment = sum(i.completion_percent for i in initiatives) // max(1, total)
        return StrategicInitiativeSummary(
            tenant_id=tenant,
            initiatives=initiatives,
            total_initiatives=total,
            active_initiatives=active,
            completed_initiatives=completed,
            at_risk_initiatives=at_risk,
            delayed_initiatives=delayed,
            initiative_kpi_coverage=initiative_kpi_coverage,
            kpi_completion_alignment=kpi_completion_alignment,
            kpi_deviation_visibility={"low": 2, "medium": 2, "high": 1},
            kpi_ownership_visibility={"analytics": linked_kpis, "executive_control_tower": total},
            roadmap_visibility={"on_track": 3, "behind": 2, "blocked": 1},
            strategic_signal_families=list(self._SIGNAL_FAMILIES),
            rbac_roles=list(self._RBAC_ROLES),
            generated_at=self._now(),
        )

    def get_strategic_initiatives_risks(self, tenant_id: int) -> StrategicInitiativeMetrics:
        tenant = self._validate_tenant(tenant_id)
        initiatives = self._build_entries(tenant)
        delayed = [i for i in initiatives if i.initiative_status == "DELAYED"]
        high_risk = [i for i in initiatives if i.risk_level in {"HIGH", "CRITICAL"}]
        risk_distribution = {
            "low": sum(1 for i in initiatives if i.risk_level == "LOW"),
            "medium": sum(1 for i in initiatives if i.risk_level == "MEDIUM"),
            "high": sum(1 for i in initiatives if i.risk_level == "HIGH"),
            "critical": sum(1 for i in initiatives if i.risk_level == "CRITICAL"),
        }
        return StrategicInitiativeMetrics(
            tenant_id=tenant,
            delayed_initiatives=delayed,
            high_risk_initiatives=high_risk,
            kpi_deviation_hotspots={"strategy-office": 2, "operations": 1},
            strategic_bottlenecks={"procurement_dependency": 1, "cross_unit_coordination": 1},
            execution_blockers={"resource_gap": 1, "deadline_conflict": 1},
            risk_distribution=risk_distribution,
            strategic_signal_families=list(self._SIGNAL_FAMILIES),
            generated_at=self._now(),
        )

    def get_development_program(self, tenant_id: int) -> DevelopmentProgramSummary:
        tenant = self._validate_tenant(tenant_id)
        summary = self.get_strategic_initiatives_summary(tenant)
        overall_progress = sum(i.completion_percent for i in summary.initiatives) // max(1, summary.total_initiatives)
        return DevelopmentProgramSummary(
            tenant_id=tenant,
            program_name="University Transformation Program",
            program_year=self._now().year,
            initiative_count=summary.total_initiatives,
            active_initiatives=summary.active_initiatives,
            completed_initiatives=summary.completed_initiatives,
            at_risk_initiatives=summary.at_risk_initiatives,
            delayed_initiatives=summary.delayed_initiatives,
            overall_progress=overall_progress,
            strategic_signal_families=list(self._SIGNAL_FAMILIES),
            generated_at=self._now(),
        )

    def get_development_program_summary(self, tenant_id: int) -> DevelopmentProgramSummary:
        return self.get_development_program(tenant_id)


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
        "workload_imbalance": "analytics",
        "ministry_deadline_risk": "order_decree_registry",
        "protocol_non_execution": "order_decree_registry",
        "decision_stagnation": "committee_decision_registry",
        "assignment_stagnation": "rector_assignment_workflow",
        "roadmap_delay": "analytics",
        "initiative_stagnation": "executive_control_tower",
        "kpi_deviation": "analytics",
        "execution_gap": "rector_assignment_workflow",
        "strategic_risk": "brain_core",
        "transformation_delay": "executive_control_tower",
    }

    _RBAC_ROLES = [
        "rector",
        "vice_rector",
        "chief_of_staff",
        "executive_manager",
        "auditor",
        "administrator",
    ]

    _decision_aggregator = ExecutiveDecisionRegistryAggregatorService()
    _assignment_execution = ExecutiveAssignmentExecutionRuntimeService()
    _meeting_registry = ExecutiveMeetingRegistryRuntimeService()
    _protocol_registry = ExecutiveProtocolRegistryRuntimeService()
    _control_tower = ExecutiveControlTowerRuntimeService(
        decisions=_decision_aggregator,
        assignments=_assignment_execution,
        meetings=_meeting_registry,
        protocols=_protocol_registry,
    )
    _strategic_initiatives = StrategicInitiativeRuntimeService()

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

    def get_decisions(self, tenant_id: int) -> list[ExecutiveDecisionRegistryEntry]:
        return self._decision_aggregator.get_decisions(tenant_id)

    def get_decisions_summary(self, tenant_id: int) -> ExecutiveDecisionRegistrySummary:
        return self._decision_aggregator.get_decisions_summary(tenant_id)

    def get_decision_execution_summary(self, tenant_id: int) -> ExecutiveDecisionExecutionSummary:
        return self._decision_aggregator.get_decision_execution_summary(tenant_id)

    def get_assignments(self, tenant_id: int) -> list[ExecutiveAssignmentEntry]:
        return self._assignment_execution.get_assignments(tenant_id)

    def get_assignments_summary(self, tenant_id: int) -> ExecutiveAssignmentSummary:
        return self._assignment_execution.get_assignments_summary(tenant_id)

    def get_assignments_execution(self, tenant_id: int) -> ExecutiveExecutionMetrics:
        return self._assignment_execution.get_assignments_execution(tenant_id)

    def get_assignments_risks(self, tenant_id: int) -> ExecutiveExecutionMetrics:
        return self._assignment_execution.get_assignments_risks(tenant_id)

    def get_meetings(self, tenant_id: int) -> list[ExecutiveMeetingEntry]:
        return self._meeting_registry.get_meetings(tenant_id)

    def get_meetings_summary(self, tenant_id: int) -> ExecutiveMeetingSummary:
        return self._meeting_registry.get_meetings_summary(tenant_id)

    def get_protocols(self, tenant_id: int) -> list[ExecutiveProtocolEntry]:
        return self._protocol_registry.get_protocols(tenant_id)

    def get_protocols_summary(self, tenant_id: int) -> ExecutiveProtocolSummary:
        return self._protocol_registry.get_protocols_summary(tenant_id)

    def get_protocols_execution(self, tenant_id: int) -> ExecutiveProtocolExecutionSummary:
        return self._protocol_registry.get_protocols_execution(tenant_id)

    def get_control_tower(self, tenant_id: int) -> ExecutiveControlTowerSummary:
        return self._control_tower.get_control_tower(tenant_id)

    def get_control_tower_summary(self, tenant_id: int) -> RectorDashboardRuntimeSummary:
        return self._control_tower.get_control_tower_summary(tenant_id)

    def get_control_tower_risks(self, tenant_id: int) -> ExecutiveRiskOverview:
        return self._control_tower.get_control_tower_risks(tenant_id)

    def get_control_tower_kpis(self, tenant_id: int) -> ExecutiveKpiOverview:
        return self._control_tower.get_control_tower_kpis(tenant_id)

    def get_control_tower_escalations(self, tenant_id: int) -> ExecutivePerformanceMetrics:
        return self._control_tower.get_control_tower_escalations(tenant_id)

    def get_strategic_initiatives(self, tenant_id: int) -> list[StrategicInitiativeEntry]:
        return self._strategic_initiatives.get_strategic_initiatives(tenant_id)

    def get_strategic_initiatives_summary(self, tenant_id: int) -> StrategicInitiativeSummary:
        return self._strategic_initiatives.get_strategic_initiatives_summary(tenant_id)

    def get_strategic_initiatives_risks(self, tenant_id: int) -> StrategicInitiativeMetrics:
        return self._strategic_initiatives.get_strategic_initiatives_risks(tenant_id)

    def get_development_program(self, tenant_id: int) -> DevelopmentProgramSummary:
        return self._strategic_initiatives.get_development_program(tenant_id)

    def get_development_program_summary(self, tenant_id: int) -> DevelopmentProgramSummary:
        return self._strategic_initiatives.get_development_program_summary(tenant_id)
