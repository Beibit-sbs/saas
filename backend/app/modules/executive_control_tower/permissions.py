"""Executive Control Tower permission constants."""

from __future__ import annotations

READ = "admin.executive_control_tower.read"
SUMMARY_READ = "admin.executive_control_tower.summary.read"
ASSIGNMENTS_READ = "admin.executive_control_tower.assignments.read"
DOCUMENTS_READ = "admin.executive_control_tower.documents.read"
SLA_RISK_READ = "admin.executive_control_tower.sla_risk.read"
STRATEGY_READ = "admin.executive_control_tower.strategy.read"
AUDIT_READ = "admin.executive_control_tower.audit.read"
DEPARTMENT_READ = "admin.executive_control_tower.department.read"
METRIC_REGISTRY_READ = "admin.executive_control_tower.metric_registry.read"

EXECUTIVE_CONTROL_TOWER_PERMISSIONS = frozenset(
    {
        READ,
        SUMMARY_READ,
        ASSIGNMENTS_READ,
        DOCUMENTS_READ,
        SLA_RISK_READ,
        STRATEGY_READ,
        AUDIT_READ,
        DEPARTMENT_READ,
        METRIC_REGISTRY_READ,
    }
)

EXECUTIVE_CONTROL_TOWER_READ_PERMISSIONS = frozenset(EXECUTIVE_CONTROL_TOWER_PERMISSIONS)

EXECUTIVE_CONTROL_TOWER_PERMISSION_DESCRIPTIONS = {
    READ: "Read executive control tower foundation endpoints.",
    SUMMARY_READ: "Read executive control tower overview summaries.",
    ASSIGNMENTS_READ: "Read assignment execution control tower summaries.",
    DOCUMENTS_READ: "Read document, decree, and correspondence control tower summaries.",
    SLA_RISK_READ: "Read SLA, risk, and bottleneck control tower summaries.",
    STRATEGY_READ: "Read future-contract strategy KPI control tower summaries.",
    AUDIT_READ: "Read audit and compliance control tower summaries.",
    DEPARTMENT_READ: "Read department performance control tower summaries.",
    METRIC_REGISTRY_READ: "Read executive control tower metric registry metadata.",
}