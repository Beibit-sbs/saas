"""Rector Assignment OS — Controlled Pilot Package.

A-031.6-RUNTIME: Deterministic seed/template/role/SLA/escalation/demo data
for the Rector Assignment OS Controlled Institutional Pilot (CIP-001).

Implementation mode: Option A — Safe seed data module only.
- Pure Python deterministic data definitions
- No DB session, no DB writes
- No external calls, no provider calls
- No live dispatch
- No real personal data
- No passwords or secrets
- Placeholder usernames only
- No hardcoded production tenant ID

Anti-fake guarantees:
- LIVE_DISPATCH_ENABLED = False
- PROVIDER_INTEGRATION_ENABLED = False
- REAL_PERSONAL_DATA_INCLUDED = False
- PRODUCTION_READY_CLAIM = False
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Package metadata constants
# ---------------------------------------------------------------------------

PILOT_PACKAGE_VERSION = "A-031.6"
PILOT_PACKAGE_NAME = "RECTOR_ASSIGNMENT_OS_PILOT_READINESS"
PILOT_MODE = "CONTROLLED_PILOT_SEED_PACKAGE"
PILOT_TENANT_PLACEHOLDER = "PILOT_TENANT_PLACEHOLDER"

# Anti-fake / safety constants — must never be True in this module
LIVE_DISPATCH_ENABLED = False
PROVIDER_INTEGRATION_ENABLED = False
REAL_PERSONAL_DATA_INCLUDED = False
PRODUCTION_READY_CLAIM = False
L5_L6_ELEVATION_CLAIMED = False
AUTONOMOUS_ESCALATION_ENABLED = False

# ---------------------------------------------------------------------------
# Role matrix
# ---------------------------------------------------------------------------

_ROLE_MATRIX: dict[str, dict[str, Any]] = {
    "rector_assignment_admin": {
        "description": "Full control over rector assignment lifecycle, policies, and templates.",
        "allowed_routes": [
            "/console/rector-assignments",
            "/console/rector-assignments/[id]",
            "/console/rector-assignments/notifications",
            "/console/rector-assignments/sla-policies",
            "/console/rector-assignments/escalation-policies",
        ],
        "permissions": [
            "admin.rector_assignments.create",
            "admin.rector_assignments.read",
            "admin.rector_assignments.read_all",
            "admin.rector_assignments.read_department",
            "admin.rector_assignments.assign",
            "admin.rector_assignments.accept",
            "admin.rector_assignments.report.submit",
            "admin.rector_assignments.report.review",
            "admin.rector_assignments.evidence.attach",
            "admin.rector_assignments.comment",
            "admin.rector_assignments.status.change",
            "admin.rector_assignments.complete",
            "admin.rector_assignments.return",
            "admin.rector_assignments.escalate",
            "admin.rector_assignments.cancel",
            "admin.rector_assignments.archive",
            "admin.rector_assignments.audit.read",
            "admin.rector_assignments.templates.manage",
            "admin.rector_assignments.dashboard.read",
            "admin.rector_assignments.admin",
            "admin.rector_assignments.outbox.read",
            "admin.rector_assignments.outbox.manage",
            "admin.rector_assignments.sla.manage",
            "admin.rector_assignments.escalation_policy.manage",
        ],
        "allowed_actions": [
            "create_assignment", "assign", "review_report", "complete",
            "return_for_revision", "escalate", "cancel", "archive",
            "manage_templates", "manage_sla_policies", "manage_escalation_policies",
            "view_outbox", "manage_outbox", "view_dashboard", "view_audit_trail",
        ],
        "forbidden_actions": [
            "hard_delete_assignment",
            "live_email_dispatch",
            "live_sms_dispatch",
            "autonomous_escalation",
        ],
        "pilot_user_count": 1,
    },
    "rector_assignment_controller": {
        "description": "Registry monitor, template manager, SLA oversight, report review.",
        "allowed_routes": [
            "/console/rector-assignments",
            "/console/rector-assignments/[id]",
            "/console/rector-assignments/sla-policies",
        ],
        "permissions": [
            "admin.rector_assignments.read",
            "admin.rector_assignments.read_all",
            "admin.rector_assignments.report.review",
            "admin.rector_assignments.comment",
            "admin.rector_assignments.return",
            "admin.rector_assignments.escalate",
            "admin.rector_assignments.cancel",
            "admin.rector_assignments.audit.read",
            "admin.rector_assignments.templates.manage",
            "admin.rector_assignments.dashboard.read",
            "admin.rector_assignments.outbox.read",
            "admin.rector_assignments.sla.manage",
        ],
        "allowed_actions": [
            "monitor_registry", "review_reports", "track_overdue",
            "manage_templates", "manage_sla_policies", "view_dashboard",
            "view_audit_trail", "view_outbox",
        ],
        "forbidden_actions": [
            "create_assignment",
            "complete_assignment_owned_by_others",
            "hard_delete_assignment",
            "live_email_dispatch",
            "live_sms_dispatch",
            "manage_escalation_policies",
        ],
        "pilot_user_count": 1,
    },
    "rector_assignment_reviewer": {
        "description": "Department director — reviews reports and returns for revision.",
        "allowed_routes": [
            "/console/rector-assignments",
            "/console/rector-assignments/[id]",
        ],
        "permissions": [
            "admin.rector_assignments.read",
            "admin.rector_assignments.read_all",
            "admin.rector_assignments.report.review",
            "admin.rector_assignments.comment",
            "admin.rector_assignments.return",
            "admin.rector_assignments.audit.read",
            "admin.rector_assignments.dashboard.read",
        ],
        "allowed_actions": [
            "review_reports", "return_for_revision", "comment",
            "view_audit_trail", "view_dashboard",
        ],
        "forbidden_actions": [
            "create_assignment",
            "manage_templates",
            "manage_sla_policies",
            "manage_escalation_policies",
            "complete_assignment",
            "hard_delete_assignment",
            "live_email_dispatch",
            "live_sms_dispatch",
        ],
        "pilot_user_count": 1,
    },
    "rector_assignment_executor": {
        "description": "Executor — accepts assignments, submits reports, attaches evidence.",
        "allowed_routes": [
            "/console/rector-assignments/[id]",
        ],
        "permissions": [
            "admin.rector_assignments.read",
            "admin.rector_assignments.accept",
            "admin.rector_assignments.report.submit",
            "admin.rector_assignments.evidence.attach",
            "admin.rector_assignments.comment",
        ],
        "allowed_actions": [
            "accept_own_assignment",
            "submit_report",
            "attach_evidence_metadata",
            "comment_on_own_assignment",
        ],
        "forbidden_actions": [
            "create_assignment",
            "review_others_reports",
            "complete_assignment",
            "manage_policies",
            "view_all_assignments",
            "hard_delete_assignment",
            "live_email_dispatch",
            "live_sms_dispatch",
        ],
        "pilot_user_count": 2,
    },
    "rector_assignment_auditor": {
        "description": "Read-only observer — verifies audit trail and compliance.",
        "allowed_routes": [
            "/console/rector-assignments",
            "/console/rector-assignments/[id]",
        ],
        "permissions": [
            "admin.rector_assignments.read",
            "admin.rector_assignments.read_all",
            "admin.rector_assignments.audit.read",
        ],
        "allowed_actions": [
            "view_assignment_registry",
            "view_audit_trail",
            "verify_evidence_metadata",
        ],
        "forbidden_actions": [
            "create_assignment",
            "accept_assignment",
            "submit_report",
            "review_report",
            "complete_assignment",
            "return_for_revision",
            "manage_policies",
            "hard_delete_assignment",
            "any_write_mutation",
        ],
        "pilot_user_count": 1,
    },
    "platform_admin": {
        "description": "Technical platform admin — user setup, seed data, troubleshooting.",
        "allowed_routes": ["*"],
        "permissions": ["platform.admin.*"],
        "allowed_actions": [
            "assign_roles",
            "verify_seed_data_loaded",
            "troubleshoot_access",
            "execute_rollback_steps",
            "monitor_outbox",
            "daily_pilot_health_check",
        ],
        "forbidden_actions": [
            "override_rbac_silently",
            "live_email_dispatch",
            "live_sms_dispatch",
            "drop_table",
            "hard_delete_audit_logs",
        ],
        "pilot_user_count": 1,
    },
}


def get_pilot_role_matrix() -> dict[str, dict[str, Any]]:
    """Return the pilot role matrix (deterministic, no DB)."""
    return dict(_ROLE_MATRIX)


# ---------------------------------------------------------------------------
# Pilot users (placeholder only — no real personal data)
# ---------------------------------------------------------------------------

_PILOT_USERS: list[dict[str, Any]] = [
    {
        "username": "pilot_rector",
        "display_name": "Pilot Rector (Placeholder)",
        "role": "rector_assignment_admin",
        "tenant_ref": PILOT_TENANT_PLACEHOLDER,
        "active": True,
        "is_placeholder": True,
        "email": "pilot_rector@pilot.local",
        "phone": None,
        "password": None,
    },
    {
        "username": "pilot_controller",
        "display_name": "Pilot Controller (Placeholder)",
        "role": "rector_assignment_controller",
        "tenant_ref": PILOT_TENANT_PLACEHOLDER,
        "active": True,
        "is_placeholder": True,
        "email": "pilot_controller@pilot.local",
        "phone": None,
        "password": None,
    },
    {
        "username": "pilot_director",
        "display_name": "Pilot Director (Placeholder)",
        "role": "rector_assignment_reviewer",
        "tenant_ref": PILOT_TENANT_PLACEHOLDER,
        "active": True,
        "is_placeholder": True,
        "email": "pilot_director@pilot.local",
        "phone": None,
        "password": None,
    },
    {
        "username": "pilot_executor_1",
        "display_name": "Pilot Executor 1 (Placeholder)",
        "role": "rector_assignment_executor",
        "tenant_ref": PILOT_TENANT_PLACEHOLDER,
        "active": True,
        "is_placeholder": True,
        "email": "pilot_executor_1@pilot.local",
        "phone": None,
        "password": None,
    },
    {
        "username": "pilot_executor_2",
        "display_name": "Pilot Executor 2 (Placeholder)",
        "role": "rector_assignment_executor",
        "tenant_ref": PILOT_TENANT_PLACEHOLDER,
        "active": True,
        "is_placeholder": True,
        "email": "pilot_executor_2@pilot.local",
        "phone": None,
        "password": None,
    },
    {
        "username": "pilot_auditor",
        "display_name": "Pilot Auditor (Placeholder)",
        "role": "rector_assignment_auditor",
        "tenant_ref": PILOT_TENANT_PLACEHOLDER,
        "active": True,
        "is_placeholder": True,
        "email": "pilot_auditor@pilot.local",
        "phone": None,
        "password": None,
    },
    {
        "username": "pilot_admin",
        "display_name": "Pilot Platform Admin (Placeholder)",
        "role": "platform_admin",
        "tenant_ref": PILOT_TENANT_PLACEHOLDER,
        "active": True,
        "is_placeholder": True,
        "email": "pilot_admin@pilot.local",
        "phone": None,
        "password": None,
    },
]


def get_pilot_users() -> list[dict[str, Any]]:
    """Return pilot user definitions (placeholders only, no real data)."""
    return list(_PILOT_USERS)


# ---------------------------------------------------------------------------
# Assignment templates
# ---------------------------------------------------------------------------

_PILOT_ASSIGNMENT_TEMPLATES: list[dict[str, Any]] = [
    {
        "template_key": "rector_weekly_report",
        "name": "Weekly Rector Report",
        "priority": "NORMAL",
        "default_due_days": 7,
        "description": (
            "Standard weekly executive summary submitted to the Rector's office. "
            "Covers the previous week's key activities, decisions, and open issues."
        ),
        "report_sections": [
            "reporting_period",
            "summary_of_activities",
            "key_decisions_made",
            "issues_requiring_attention",
            "next_week_plan",
        ],
        "evidence_required": False,
        "evidence_description": "Optional supporting documentation.",
        "active": True,
    },
    {
        "template_key": "infra_issue_resolution",
        "name": "Infrastructure Issue Resolution",
        "priority": "HIGH",
        "default_due_days": 3,
        "description": (
            "Assigned when a campus infrastructure issue requires a documented "
            "resolution plan and confirmation of completion."
        ),
        "report_sections": [
            "issue_description",
            "root_cause_analysis",
            "resolution_steps_taken",
            "resolution_timeline",
            "responsible_unit",
            "follow_up_required",
        ],
        "evidence_required": True,
        "evidence_description": "Photos, inspection reports, or work completion certificate.",
        "active": True,
    },
    {
        "template_key": "accreditation_evidence",
        "name": "Accreditation Evidence Request",
        "priority": "HIGH",
        "default_due_days": 3,
        "description": (
            "Request for a faculty or department to compile and submit evidence "
            "packages required for institutional or programme accreditation."
        ),
        "report_sections": [
            "accreditation_cycle",
            "evidence_categories_required",
            "evidence_inventory_submitted",
            "certifying_official",
            "completeness_declaration",
        ],
        "evidence_required": True,
        "evidence_description": "Scanned accreditation documents or links to document repository.",
        "active": True,
    },
    {
        "template_key": "procurement_status_update",
        "name": "Procurement Status Update",
        "priority": "NORMAL",
        "default_due_days": 7,
        "description": (
            "Periodic status update on an open procurement order, "
            "detailing current stage, expected delivery, and any blockers."
        ),
        "report_sections": [
            "order_reference",
            "procurement_item_description",
            "current_status",
            "expected_delivery_date",
            "blockers_or_risks",
            "escalation_required",
        ],
        "evidence_required": False,
        "evidence_description": "Optional order tracking documentation.",
        "active": True,
    },
    {
        "template_key": "academic_kpi_followup",
        "name": "Academic Department KPI Follow-up",
        "priority": "NORMAL",
        "default_due_days": 7,
        "description": (
            "Follow-up on academic performance KPI targets for a department. "
            "Compares actual performance against set targets and proposes action plan."
        ),
        "report_sections": [
            "department_name",
            "reporting_period",
            "kpi_targets",
            "actual_performance_results",
            "variance_analysis",
            "action_plan_for_gaps",
        ],
        "evidence_required": False,
        "evidence_description": "Optional KPI dashboard export or supporting data.",
        "active": True,
    },
]


def get_pilot_assignment_templates() -> list[dict[str, Any]]:
    """Return the 5 standard pilot assignment templates."""
    return list(_PILOT_ASSIGNMENT_TEMPLATES)


# ---------------------------------------------------------------------------
# Default SLA policies
# ---------------------------------------------------------------------------

_PILOT_SLA_POLICIES: list[dict[str, Any]] = [
    {
        "policy_key": "critical_sla",
        "name": "Critical SLA",
        "priority": "CRITICAL",
        "due_days": 1,
        "warning_before_hours": 6,
        "overdue_after_hours": 0,
        "escalation_after_hours": 6,
        "is_active": True,
        "require_manual_confirmation": True,
        "description": "For critical-priority assignments. Due in 1 day; warning at 6h before; escalation 6h after overdue.",
    },
    {
        "policy_key": "high_sla",
        "name": "High SLA",
        "priority": "HIGH",
        "due_days": 3,
        "warning_before_hours": 24,
        "overdue_after_hours": 0,
        "escalation_after_hours": 24,
        "is_active": True,
        "require_manual_confirmation": True,
        "description": "For high-priority assignments. Due in 3 days; warning at 24h before; escalation 24h after overdue.",
    },
    {
        "policy_key": "normal_sla",
        "name": "Normal SLA",
        "priority": "NORMAL",
        "due_days": 7,
        "warning_before_hours": 48,
        "overdue_after_hours": 0,
        "escalation_after_hours": 48,
        "is_active": True,
        "require_manual_confirmation": True,
        "description": "For normal-priority assignments. Due in 7 days; warning at 48h before; escalation 48h after overdue.",
    },
]


def get_pilot_sla_policies() -> list[dict[str, Any]]:
    """Return the 3 default SLA policies for the pilot."""
    return list(_PILOT_SLA_POLICIES)


# ---------------------------------------------------------------------------
# Default escalation policy (4-level, all manual confirmation)
# ---------------------------------------------------------------------------

_PILOT_ESCALATION_POLICIES: list[dict[str, Any]] = [
    {
        "policy_key": "standard_escalation",
        "name": "Rector Assignment Standard Escalation",
        "description": (
            "4-level escalation policy for pilot. All levels require manual confirmation. "
            "No autonomous action, no live dispatch."
        ),
        "autonomous_action_enabled": False,
        "live_dispatch_enabled": False,
        "levels": [
            {
                "level": 1,
                "escalate_to_role": "CONTROLLER",
                "escalate_after_hours": 6,
                "require_manual_confirmation": True,
                "action_description": "Notify controller; manual confirmation required before any action.",
            },
            {
                "level": 2,
                "escalate_to_role": "PRORECTOR",
                "escalate_after_hours": 24,
                "require_manual_confirmation": True,
                "action_description": "Escalate to prorector; manual confirmation required.",
            },
            {
                "level": 3,
                "escalate_to_role": "RECTOR",
                "escalate_after_hours": 48,
                "require_manual_confirmation": True,
                "action_description": "Escalate to rector; manual confirmation required.",
            },
            {
                "level": 4,
                "escalate_to_role": "PLATFORM_ADMIN",
                "escalate_after_hours": 72,
                "require_manual_confirmation": True,
                "action_description": "Final escalation to platform admin; manual confirmation required.",
            },
        ],
    },
]


def get_pilot_escalation_policies() -> list[dict[str, Any]]:
    """Return the default escalation policy with 4 levels."""
    return list(_PILOT_ESCALATION_POLICIES)


# ---------------------------------------------------------------------------
# Seed assignment definitions (10 pilot assignments)
# ---------------------------------------------------------------------------

_PILOT_SEED_ASSIGNMENTS: list[dict[str, Any]] = [
    {
        "seed_key": "pilot_assign_001",
        "title": "Q1 Performance Review Report",
        "template_key": "rector_weekly_report",
        "status": "COMPLETED",
        "priority": "NORMAL",
        "assigned_to_user": "pilot_executor_1",
        "controller_user": "pilot_controller",
        "due_offset_days": -14,
        "report_state": "ACCEPTED",
        "evidence_state": None,
        "outbox_expected_events": [
            "rector_assignment.created",
            "rector_assignment.assigned",
            "rector_assignment.accepted",
            "rector_assignment.report_submitted",
            "rector_assignment.completed",
        ],
        "sla_policy_key": "normal_sla",
        "escalation_policy_key": None,
        "is_demo": True,
    },
    {
        "seed_key": "pilot_assign_002",
        "title": "Infrastructure Issue Resolution — Building A",
        "template_key": "infra_issue_resolution",
        "status": "IN_PROGRESS",
        "priority": "HIGH",
        "assigned_to_user": "pilot_executor_2",
        "controller_user": "pilot_controller",
        "due_offset_days": 2,
        "report_state": None,
        "evidence_state": None,
        "outbox_expected_events": [
            "rector_assignment.created",
            "rector_assignment.assigned",
            "rector_assignment.accepted",
        ],
        "sla_policy_key": "high_sla",
        "escalation_policy_key": None,
        "is_demo": True,
    },
    {
        "seed_key": "pilot_assign_003",
        "title": "Accreditation Evidence Package — Batch 3",
        "template_key": "accreditation_evidence",
        "status": "REPORT_SUBMITTED",
        "priority": "HIGH",
        "assigned_to_user": "pilot_executor_1",
        "controller_user": "pilot_controller",
        "due_offset_days": 1,
        "report_state": "SUBMITTED",
        "evidence_state": "ATTACHED",
        "outbox_expected_events": [
            "rector_assignment.created",
            "rector_assignment.assigned",
            "rector_assignment.accepted",
            "rector_assignment.report_submitted",
            "rector_assignment.evidence_attached",
        ],
        "sla_policy_key": "high_sla",
        "escalation_policy_key": None,
        "is_demo": True,
    },
    {
        "seed_key": "pilot_assign_004",
        "title": "Procurement Status Update — Lab Equipment",
        "template_key": "procurement_status_update",
        "status": "RETURNED_FOR_REVISION",
        "priority": "NORMAL",
        "assigned_to_user": "pilot_executor_2",
        "controller_user": "pilot_controller",
        "due_offset_days": 5,
        "report_state": "RETURNED",
        "evidence_state": None,
        "outbox_expected_events": [
            "rector_assignment.created",
            "rector_assignment.assigned",
            "rector_assignment.accepted",
            "rector_assignment.report_submitted",
            "rector_assignment.returned_for_revision",
        ],
        "sla_policy_key": "normal_sla",
        "escalation_policy_key": None,
        "is_demo": True,
    },
    {
        "seed_key": "pilot_assign_005",
        "title": "Academic Department KPI Follow-up",
        "template_key": "academic_kpi_followup",
        "status": "ASSIGNED",
        "priority": "NORMAL",
        "assigned_to_user": "pilot_executor_1",
        "controller_user": "pilot_controller",
        "due_offset_days": 7,
        "report_state": None,
        "evidence_state": None,
        "outbox_expected_events": [
            "rector_assignment.created",
            "rector_assignment.assigned",
        ],
        "sla_policy_key": "normal_sla",
        "escalation_policy_key": None,
        "is_demo": True,
    },
    {
        "seed_key": "pilot_assign_006",
        "title": "Emergency Access Control Audit",
        "template_key": "infra_issue_resolution",
        "status": "ESCALATED",
        "priority": "CRITICAL",
        "assigned_to_user": "pilot_executor_1",
        "controller_user": "pilot_controller",
        "due_offset_days": -3,
        "report_state": None,
        "evidence_state": None,
        "outbox_expected_events": [
            "rector_assignment.created",
            "rector_assignment.assigned",
            "rector_assignment.overdue_detected",
            "rector_assignment.escalated",
        ],
        "sla_policy_key": "critical_sla",
        "escalation_policy_key": "standard_escalation",
        "is_demo": True,
    },
    {
        "seed_key": "pilot_assign_007",
        "title": "Faculty Accreditation Self-Assessment",
        "template_key": "accreditation_evidence",
        "status": "OVERDUE",
        "priority": "HIGH",
        "assigned_to_user": "pilot_executor_2",
        "controller_user": "pilot_controller",
        "due_offset_days": -2,
        "report_state": None,
        "evidence_state": None,
        "outbox_expected_events": [
            "rector_assignment.created",
            "rector_assignment.assigned",
            "rector_assignment.overdue_detected",
        ],
        "sla_policy_key": "high_sla",
        "escalation_policy_key": "standard_escalation",
        "is_demo": True,
    },
    {
        "seed_key": "pilot_assign_008",
        "title": "Rector Strategy Presentation Draft",
        "template_key": "rector_weekly_report",
        "status": "ACCEPTED",
        "priority": "NORMAL",
        "assigned_to_user": "pilot_executor_1",
        "controller_user": "pilot_controller",
        "due_offset_days": 6,
        "report_state": None,
        "evidence_state": None,
        "outbox_expected_events": [
            "rector_assignment.created",
            "rector_assignment.assigned",
            "rector_assignment.accepted",
        ],
        "sla_policy_key": "normal_sla",
        "escalation_policy_key": None,
        "is_demo": True,
    },
    {
        "seed_key": "pilot_assign_009",
        "title": "IT Infrastructure Capacity Report",
        "template_key": "rector_weekly_report",
        "status": "CANCELLED",
        "priority": "NORMAL",
        "assigned_to_user": "pilot_executor_2",
        "controller_user": "pilot_controller",
        "due_offset_days": -5,
        "report_state": None,
        "evidence_state": None,
        "outbox_expected_events": [
            "rector_assignment.created",
            "rector_assignment.assigned",
        ],
        "sla_policy_key": "normal_sla",
        "escalation_policy_key": None,
        "is_demo": True,
    },
    {
        "seed_key": "pilot_assign_010",
        "title": "Annual Budget Variance Report",
        "template_key": "rector_weekly_report",
        "status": "DRAFT",
        "priority": "NORMAL",
        "assigned_to_user": "pilot_executor_1",
        "controller_user": "pilot_controller",
        "due_offset_days": 10,
        "report_state": None,
        "evidence_state": None,
        "outbox_expected_events": [
            "rector_assignment.created",
        ],
        "sla_policy_key": "normal_sla",
        "escalation_policy_key": None,
        "is_demo": True,
    },
]


def get_pilot_seed_assignments() -> list[dict[str, Any]]:
    """Return the 10 deterministic pilot seed assignment definitions."""
    return list(_PILOT_SEED_ASSIGNMENTS)


# ---------------------------------------------------------------------------
# Demo scenarios (6 scenarios)
# ---------------------------------------------------------------------------

_PILOT_DEMO_SCENARIOS: list[dict[str, Any]] = [
    {
        "scenario_key": "create_and_assign_from_template",
        "title": "Scenario 1 — Create and Assign from Template",
        "actor_roles": ["rector_assignment_admin"],
        "steps": [
            "Navigate to /console/rector-assignments",
            "Click 'New Assignment', select template 'Weekly Rector Report'",
            "Set title, assign to pilot_executor_1, set priority=NORMAL",
            "Confirm due date auto-populated from SLA policy (7 days)",
            "Submit — status transitions DRAFT → ASSIGNED",
            "Verify SLA badge visible on assignment detail",
            "Verify outbox PENDING event created (lifecycle transition)",
            "Verify audit event visible in audit log tab",
        ],
        "expected_result": "Assignment created; SLA badge green; outbox entry; audit trail entry",
        "acceptance_check": "assignment_status == ASSIGNED and sla_badge_visible and outbox_event_count >= 1 and audit_event_count >= 1",
        "anti_fake_check": "no live dispatch; outbox status PENDING only; no fake delivery status",
    },
    {
        "scenario_key": "executor_accepts_and_submits_report",
        "title": "Scenario 2 — Executor Accepts and Submits Report",
        "actor_roles": ["rector_assignment_executor"],
        "steps": [
            "Navigate to assignment detail (status ASSIGNED)",
            "Click 'Accept' — status transitions ASSIGNED → ACCEPTED",
            "Update progress section, click 'Submit Report'",
            "Attach evidence metadata (filename + description, no actual file required)",
            "Status transitions ACCEPTED → REPORT_SUBMITTED",
            "Verify outbox PENDING event created for report_submitted",
            "Verify dashboard 'report_submitted_count' increments",
        ],
        "expected_result": "Executor can accept and submit; dashboard updates from real data",
        "acceptance_check": "assignment_status == REPORT_SUBMITTED and outbox_event_count >= 2 and dashboard_report_submitted_count > 0",
        "anti_fake_check": "no live dispatch; data_source == computed_from_assignments; fake_metrics == false",
    },
    {
        "scenario_key": "review_return_and_resubmit",
        "title": "Scenario 3 — Review, Return, and Resubmit",
        "actor_roles": ["rector_assignment_reviewer", "rector_assignment_executor"],
        "steps": [
            "Reviewer navigates to assignment detail (status REPORT_SUBMITTED)",
            "Opens review tab, enters return reason",
            "Clicks 'Return for Revision'",
            "Status transitions REPORT_SUBMITTED → RETURNED_FOR_REVISION",
            "Executor sees updated status, resubmits with updated report",
            "Status transitions RETURNED_FOR_REVISION → REPORT_SUBMITTED",
            "Verify status history shows full transition chain",
            "Verify outbox intents created for both RETURNED and re-SUBMITTED events",
        ],
        "expected_result": "Return/resubmit cycle works; audit trail shows all transitions",
        "acceptance_check": "status_history_length >= 4 and returned_for_revision_event_present and report_resubmitted_event_present",
        "anti_fake_check": "no live dispatch at any transition step",
    },
    {
        "scenario_key": "complete_assignment_and_audit",
        "title": "Scenario 4 — Complete Assignment and Verify Audit Trail",
        "actor_roles": ["rector_assignment_admin", "rector_assignment_controller"],
        "steps": [
            "Navigate to REPORT_SUBMITTED assignment",
            "Review submitted report",
            "Click 'Complete' — status transitions REPORT_SUBMITTED → COMPLETED",
            "Verify dashboard completion_rate_30d updates",
            "Verify completed_count increments in dashboard",
            "Verify audit trail shows COMPLETED with actor and timestamp",
        ],
        "expected_result": "Clean completion; dashboard reflects real computed data",
        "acceptance_check": "assignment_status == COMPLETED and dashboard_completed_count > 0 and audit_completed_event_present",
        "anti_fake_check": "data_source == computed_from_assignments; no placeholder zeros used as fake data",
    },
    {
        "scenario_key": "overdue_and_manual_escalation",
        "title": "Scenario 5 — Overdue and Manual Escalation",
        "actor_roles": ["rector_assignment_admin", "rector_assignment_controller"],
        "steps": [
            "Navigate to seed assignment pilot_assign_007 (pre-seeded OVERDUE)",
            "Verify SLA badge shows overdue indicator",
            "Navigate to escalation queue panel",
            "Verify manual escalation entry visible with Level 1 (Controller) pending",
            "Verify 'Manual confirmation required' label visible",
            "Confirm no live email/SMS sent (no live dispatch)",
            "Verify outbox entry for overdue_detected event is PENDING (not DISPATCHED)",
        ],
        "expected_result": "Overdue state visible; escalation queue shows manual entry; no autonomous action",
        "acceptance_check": "assignment_status == OVERDUE and escalation_queue_entry_present and manual_confirmation_label_visible and outbox_status == PENDING",
        "anti_fake_check": "no live dispatch; no autonomous escalation action taken; PENDING only",
    },
    {
        "scenario_key": "auditor_read_only_access",
        "title": "Scenario 6 — Auditor Read-Only Access",
        "actor_roles": ["rector_assignment_auditor"],
        "steps": [
            "Navigate to /console/rector-assignments as pilot_auditor",
            "Verify assignment registry is visible (read-only)",
            "Navigate to assignment detail — verify audit log tab accessible",
            "Attempt create action — verify UI hides create button or shows permission denial",
            "Attempt complete action — verify permission denied safely",
            "Attempt return-for-revision — verify permission denied safely",
            "Verify no JavaScript errors or security information leakage",
        ],
        "expected_result": "Auditor sees full read-only view; all mutations blocked safely",
        "acceptance_check": "registry_visible == true and create_button_absent and complete_button_absent and permission_errors_are_clean",
        "anti_fake_check": "no mutation possible; no data leakage outside tenant scope",
    },
]


def get_pilot_demo_scenarios() -> list[dict[str, Any]]:
    """Return the 6 pilot demo scenarios."""
    return list(_PILOT_DEMO_SCENARIOS)


# ---------------------------------------------------------------------------
# Training guides (5 guides — outlines only)
# ---------------------------------------------------------------------------

_PILOT_TRAINING_GUIDES: list[dict[str, Any]] = [
    {
        "guide_key": "rector_quick_guide",
        "title": "Rector / Executive Sponsor Quick Guide",
        "target_roles": ["rector_assignment_admin"],
        "sections": [
            "Introduction to Rector Assignment OS",
            "Creating assignments from templates",
            "Assigning to units or individuals",
            "Reviewing submitted reports",
            "Returning for revision vs. completing",
            "Understanding SLA badges",
            "Accessing the dashboard analytics",
            "Escalation: what it means and what NOT to do",
            "Outbox timeline: intent-only (no live dispatch)",
            "Support contacts and escalation path",
        ],
    },
    {
        "guide_key": "controller_secretary_guide",
        "title": "Controller / Secretary Operational Guide",
        "target_roles": ["rector_assignment_controller"],
        "sections": [
            "Registry overview and status filters",
            "Monitoring active assignment statuses",
            "Tracking overdue items and SLA alerts",
            "Managing SLA policies",
            "Reviewing and managing templates",
            "Reading the outbox timeline (intent-only)",
            "Managing the escalation queue (manual confirmation)",
            "Daily check-in routine",
            "Issue triage and reporting",
        ],
    },
    {
        "guide_key": "executor_guide",
        "title": "Executor Field Guide",
        "target_roles": ["rector_assignment_executor"],
        "sections": [
            "Receiving assignment notifications (in-app)",
            "Accepting an assignment",
            "Submitting a progress report",
            "Attaching evidence metadata",
            "Responding to return-for-revision",
            "Understanding your SLA deadline and badge",
            "Questions, support, and escalation requests",
        ],
    },
    {
        "guide_key": "auditor_guide",
        "title": "Auditor / Observer Guide",
        "target_roles": ["rector_assignment_auditor"],
        "sections": [
            "Navigating the assignment registry",
            "Reading the assignment audit trail",
            "Verifying evidence metadata records",
            "What you can and cannot do (read-only)",
            "Reporting compliance concerns",
        ],
    },
    {
        "guide_key": "admin_guide",
        "title": "Platform Admin Guide",
        "target_roles": ["platform_admin"],
        "sections": [
            "User role assignment and verification",
            "Confirming seed data is loaded",
            "Troubleshooting access and permission issues",
            "Adding users to the pilot tenant",
            "Rollback steps (step-by-step)",
            "Monitoring the outbox queue",
            "Daily pilot health check procedure",
        ],
    },
]


def get_pilot_training_guides() -> list[dict[str, Any]]:
    """Return the 5 pilot training guide outlines."""
    return list(_PILOT_TRAINING_GUIDES)


# ---------------------------------------------------------------------------
# Support plan
# ---------------------------------------------------------------------------

_PILOT_SUPPORT_PLAN: dict[str, Any] = {
    "pilot_owner": "TBD — designated before pilot start",
    "technical_owner": "TBD — platform admin role",
    "functional_owner": "TBD — controller/secretary role",
    "daily_checkin_required": True,
    "daily_checkin_duration_minutes": 15,
    "daily_checkin_participants": ["pilot_owner", "functional_owner", "technical_owner"],
    "issue_categories": [
        "login_and_access",
        "permissions",
        "assignment_workflow",
        "report_and_evidence",
        "dashboard_data",
        "sla_and_outbox",
        "ui_bug",
        "data_quality",
        "security_concern",
    ],
    "triage_matrix": {
        "P1": {
            "label": "Security",
            "examples": ["Unauthorized access", "Tenant leakage", "Data exposure"],
            "response_target": "Immediate (< 1 hour)",
            "action": "Stop pilot if required; notify technical owner immediately",
        },
        "P2": {
            "label": "Blocker",
            "examples": ["Login broken", "Assignment creation fails", "Data loss"],
            "response_target": "Same day (< 4 hours)",
            "action": "Fix or workaround before next check-in",
        },
        "P3": {
            "label": "Functional",
            "examples": ["Workflow step not working", "Wrong status shown"],
            "response_target": "1 business day",
            "action": "Log and prioritise for next pilot cycle",
        },
        "P4": {
            "label": "UX",
            "examples": ["Display issue", "Confusing label", "Minor layout"],
            "response_target": "Next pilot cycle",
            "action": "Log; no blocking action",
        },
        "P5": {
            "label": "Feedback",
            "examples": ["Enhancement request", "Wish list"],
            "response_target": "Deferred to next spec",
            "action": "Log for A-032 or post-pilot",
        },
    },
}


def get_pilot_support_plan() -> dict[str, Any]:
    """Return the pilot support plan."""
    return dict(_PILOT_SUPPORT_PLAN)


# ---------------------------------------------------------------------------
# Rollback plan
# ---------------------------------------------------------------------------

_PILOT_ROLLBACK_PLAN: dict[str, Any] = {
    "rollback_conditions": [
        "P1 security incident (tenant leakage, unauthorized access)",
        "Critical data corruption",
        "Unrecoverable workflow blocker affecting > 50% of pilot users",
        "Explicit Pilot Owner instruction",
    ],
    "steps": [
        "Stop new assignment creation — disable create-assignment permission for pilot tenant",
        "Notify pilot users of temporary suspension",
        "Preserve audit data — do NOT delete audit logs or assignment history",
        "Export pilot data if requested — assignments, reports, audit events",
        "Archive assignments — set status to ARCHIVED, no hard delete",
        "Disable route access — remove pilot user roles via admin panel, do not drop tables",
        "Notify technical owner — confirm rollback state",
        "Root cause analysis — document incident before re-activation",
        "Reactivation only with explicit Pilot Owner approval",
    ],
    "stop_new_assignments": True,
    "preserve_audit_data": True,
    "archive_pilot_assignments": True,
    "disable_route_access_via_permissions": True,
    "no_drop_table": True,
    "no_hard_delete": True,
    "explicit_approval_required": True,
    "forbidden_rollback_actions": [
        "DROP TABLE",
        "Hard delete of assignments, reports, or audit logs",
        "Destructive migration without explicit approval",
        "Silent permission override",
    ],
}


def get_pilot_rollback_plan() -> dict[str, Any]:
    """Return the pilot rollback plan."""
    return dict(_PILOT_ROLLBACK_PLAN)


# ---------------------------------------------------------------------------
# Acceptance criteria
# ---------------------------------------------------------------------------

_PILOT_ACCEPTANCE_CRITERIA: dict[str, Any] = {
    "success_threshold_percent": 90,
    "functional": {
        "assignment_creation": "Works for all template types; due date auto-populated from SLA",
        "assignment_acceptance": "Executor can accept; status transitions correctly",
        "report_submission": "Executor can submit; evidence metadata saved",
        "return_for_revision": "Reviewer can return; executor receives and resubmits",
        "completion": "Rector/Controller can complete; audit trail updated",
        "dashboard_updates": "All 6 widgets show computed values (not fake, not static)",
        "sla_badge": "Visible on assignment detail; reflects correct state",
        "outbox_timeline": "Visible; shows lifecycle events; PENDING only",
        "audit_trail": "Shows actor, timestamp, transition for all events",
        "permission_gates": "All 23 permissions enforced; no unauthorized access",
    },
    "security": {
        "unauthorized_access_incidents": 0,
        "auditor_read_only": "100% — no mutation allowed",
        "executor_scope": "Can only act on own assignments",
        "tenant_isolation_incidents": 0,
        "hard_delete_incidents": 0,
    },
    "anti_fake": {
        "fake_metrics_false": "Confirmed in all dashboard API responses",
        "data_source": "computed_from_assignments",
        "no_send_now_dispatch_button": True,
        "live_dispatch_disabled_label": "Present on all outbox UI pages",
        "manual_confirmation_required_label": "Present on all escalation UI",
        "no_fake_kpi_placeholder_zeroes": "Unavailable state shown when no data",
    },
    "operational": {
        "pilot_users_trained": "100% of assigned roles receive guide",
        "issue_log_maintained": "Updated daily",
        "rollback_plan_known": "All technical staff can execute",
        "daily_checkin_done": "Every pilot day",
        "pilot_feedback_captured": "At least end-of-week summary",
    },
    "overall_thresholds": {
        "scenarios_completed_without_blocker_pct": 90,
        "tenant_security_incidents": 0,
        "fake_data_in_ui": 0,
        "live_email_sms_dispatched": 0,
        "all_p1_p2_issues_documented": True,
    },
}


def get_pilot_acceptance_criteria() -> dict[str, Any]:
    """Return the pilot acceptance criteria."""
    return dict(_PILOT_ACCEPTANCE_CRITERIA)


# ---------------------------------------------------------------------------
# Full pilot readiness package (aggregate)
# ---------------------------------------------------------------------------

def get_pilot_readiness_package() -> dict[str, Any]:
    """Return the complete pilot readiness package as a single dict.

    This is the canonical pilot package artifact for A-031.6-RUNTIME.
    Pure deterministic data — no DB, no external calls, no live dispatch.
    """
    return {
        "metadata": {
            "package_version": PILOT_PACKAGE_VERSION,
            "package_name": PILOT_PACKAGE_NAME,
            "pilot_mode": PILOT_MODE,
            "tenant_placeholder": PILOT_TENANT_PLACEHOLDER,
            "live_dispatch_enabled": LIVE_DISPATCH_ENABLED,
            "provider_integration_enabled": PROVIDER_INTEGRATION_ENABLED,
            "real_personal_data_included": REAL_PERSONAL_DATA_INCLUDED,
            "production_ready_claim": PRODUCTION_READY_CLAIM,
            "l5_l6_elevation_claimed": L5_L6_ELEVATION_CLAIMED,
            "autonomous_escalation_enabled": AUTONOMOUS_ESCALATION_ENABLED,
        },
        "role_matrix": get_pilot_role_matrix(),
        "users": get_pilot_users(),
        "assignment_templates": get_pilot_assignment_templates(),
        "sla_policies": get_pilot_sla_policies(),
        "escalation_policies": get_pilot_escalation_policies(),
        "seed_assignments": get_pilot_seed_assignments(),
        "demo_scenarios": get_pilot_demo_scenarios(),
        "training_guides": get_pilot_training_guides(),
        "support_plan": get_pilot_support_plan(),
        "rollback_plan": get_pilot_rollback_plan(),
        "acceptance_criteria": get_pilot_acceptance_criteria(),
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_VALID_PRIORITIES = {"CRITICAL", "HIGH", "NORMAL", "LOW"}
_VALID_STATUSES = {
    "DRAFT", "ASSIGNED", "ACCEPTED", "IN_PROGRESS", "REPORT_SUBMITTED",
    "RETURNED_FOR_REVISION", "COMPLETED", "OVERDUE", "ESCALATED",
    "CANCELLED", "ARCHIVED",
}
_VALID_ROLES = {
    "rector_assignment_admin", "rector_assignment_controller",
    "rector_assignment_reviewer", "rector_assignment_executor",
    "rector_assignment_auditor", "platform_admin",
}
_VALID_ESCALATION_ROLES = {"CONTROLLER", "PRORECTOR", "RECTOR", "PLATFORM_ADMIN"}


def validate_pilot_package(package: dict) -> dict[str, Any]:
    """Validate the pilot readiness package structure.

    Returns a validation result dict with status PASS or FAIL and details.
    Raises nothing — all failures are collected and returned.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # --- Metadata ---
    meta = package.get("metadata", {})
    if meta.get("package_version") != "A-031.6":
        errors.append("metadata.package_version must be 'A-031.6'")
    if meta.get("live_dispatch_enabled") is not False:
        errors.append("metadata.live_dispatch_enabled must be False")
    if meta.get("provider_integration_enabled") is not False:
        errors.append("metadata.provider_integration_enabled must be False")
    if meta.get("real_personal_data_included") is not False:
        errors.append("metadata.real_personal_data_included must be False")
    if meta.get("production_ready_claim") is not False:
        errors.append("metadata.production_ready_claim must be False")
    if meta.get("l5_l6_elevation_claimed") is not False:
        errors.append("metadata.l5_l6_elevation_claimed must be False")

    # --- Roles ---
    role_matrix = package.get("role_matrix", {})
    if len(role_matrix) != 6:
        errors.append(f"role_matrix must have exactly 6 roles, got {len(role_matrix)}")
    for role_name, role_def in role_matrix.items():
        if not role_def.get("permissions"):
            errors.append(f"Role '{role_name}' has no permissions defined")

    # --- Users ---
    users = package.get("users", [])
    if len(users) != 7:
        errors.append(f"users must have exactly 7 pilot users, got {len(users)}")
    for u in users:
        if not u.get("is_placeholder"):
            errors.append(f"User '{u.get('username')}' must have is_placeholder=True")
        if u.get("password") is not None:
            errors.append(f"User '{u.get('username')}' must not have a password")
        if u.get("role") not in _VALID_ROLES:
            errors.append(f"User '{u.get('username')}' has invalid role '{u.get('role')}'")
        email = u.get("email", "")
        if email and "@pilot.local" not in email and "@" in email:
            warnings.append(f"User '{u.get('username')}' email domain is not @pilot.local: {email}")

    # --- Templates ---
    templates = package.get("assignment_templates", [])
    if len(templates) != 5:
        errors.append(f"assignment_templates must have exactly 5 templates, got {len(templates)}")
    template_keys = set()
    for t in templates:
        key = t.get("template_key")
        if not key:
            errors.append("Template missing template_key")
        else:
            if key in template_keys:
                errors.append(f"Duplicate template_key: {key}")
            template_keys.add(key)
        if t.get("priority") not in _VALID_PRIORITIES:
            errors.append(f"Template '{key}' has invalid priority '{t.get('priority')}'")
        due_days = t.get("default_due_days", -1)
        if not isinstance(due_days, int) or due_days < 0:
            errors.append(f"Template '{key}' has invalid default_due_days: {due_days}")
        if not t.get("active"):
            warnings.append(f"Template '{key}' is not active")

    # --- SLA policies ---
    sla_policies = package.get("sla_policies", [])
    if len(sla_policies) != 3:
        errors.append(f"sla_policies must have exactly 3 policies, got {len(sla_policies)}")
    sla_priorities = {p.get("priority") for p in sla_policies}
    for required_priority in ("CRITICAL", "HIGH", "NORMAL"):
        if required_priority not in sla_priorities:
            errors.append(f"sla_policies missing required priority: {required_priority}")
    for p in sla_policies:
        due_days = p.get("due_days", -1)
        if not isinstance(due_days, int) or due_days < 0:
            errors.append(f"SLA policy '{p.get('policy_key')}' has invalid due_days: {due_days}")
        warning_h = p.get("warning_before_hours", -1)
        if not isinstance(warning_h, (int, float)) or warning_h < 0:
            errors.append(f"SLA policy '{p.get('policy_key')}' has invalid warning_before_hours")
        overdue_h = p.get("overdue_after_hours", -1)
        if not isinstance(overdue_h, (int, float)) or overdue_h < 0:
            errors.append(f"SLA policy '{p.get('policy_key')}' has invalid overdue_after_hours")
        esc_h = p.get("escalation_after_hours", -1)
        if not isinstance(esc_h, (int, float)) or esc_h < overdue_h:
            errors.append(
                f"SLA policy '{p.get('policy_key')}': "
                f"escalation_after_hours ({esc_h}) must be >= overdue_after_hours ({overdue_h})"
            )

    # --- Escalation policies ---
    esc_policies = package.get("escalation_policies", [])
    if len(esc_policies) < 1:
        errors.append("escalation_policies must have at least 1 policy")
    for ep in esc_policies:
        if ep.get("live_dispatch_enabled") is not False:
            errors.append(f"Escalation policy '{ep.get('policy_key')}': live_dispatch_enabled must be False")
        if ep.get("autonomous_action_enabled") is not False:
            errors.append(f"Escalation policy '{ep.get('policy_key')}': autonomous_action_enabled must be False")
        levels = ep.get("levels", [])
        if len(levels) != 4:
            errors.append(f"Escalation policy '{ep.get('policy_key')}' must have exactly 4 levels")
        for lvl in levels:
            if not lvl.get("require_manual_confirmation"):
                errors.append(
                    f"Escalation policy level {lvl.get('level')} must have require_manual_confirmation=True"
                )
            if lvl.get("escalate_to_role") not in _VALID_ESCALATION_ROLES:
                errors.append(
                    f"Escalation level {lvl.get('level')} has invalid role: {lvl.get('escalate_to_role')}"
                )

    # --- Seed assignments ---
    assignments = package.get("seed_assignments", [])
    if len(assignments) != 10:
        errors.append(f"seed_assignments must have exactly 10, got {len(assignments)}")
    assignment_keys = set()
    user_usernames = {u["username"] for u in users}
    for a in assignments:
        key = a.get("seed_key")
        if key in assignment_keys:
            errors.append(f"Duplicate seed_key: {key}")
        assignment_keys.add(key)
        if a.get("status") not in _VALID_STATUSES:
            errors.append(f"Assignment '{key}' has invalid status: {a.get('status')}")
        if a.get("priority") not in _VALID_PRIORITIES:
            errors.append(f"Assignment '{key}' has invalid priority: {a.get('priority')}")
        if a.get("template_key") not in template_keys:
            errors.append(f"Assignment '{key}' references unknown template_key: {a.get('template_key')}")
        if a.get("assigned_to_user") not in user_usernames:
            errors.append(f"Assignment '{key}' references unknown user: {a.get('assigned_to_user')}")
        if not a.get("is_demo"):
            warnings.append(f"Assignment '{key}' should have is_demo=True")

    # --- Demo scenarios ---
    scenarios = package.get("demo_scenarios", [])
    if len(scenarios) != 6:
        errors.append(f"demo_scenarios must have exactly 6, got {len(scenarios)}")
    for s in scenarios:
        if not s.get("steps"):
            errors.append(f"Scenario '{s.get('scenario_key')}' has no steps")
        if not s.get("acceptance_check"):
            errors.append(f"Scenario '{s.get('scenario_key')}' has no acceptance_check")
        if not s.get("anti_fake_check"):
            errors.append(f"Scenario '{s.get('scenario_key')}' has no anti_fake_check")

    # --- Support / rollback ---
    rollback = package.get("rollback_plan", {})
    if not rollback.get("no_drop_table"):
        errors.append("rollback_plan.no_drop_table must be True")
    if not rollback.get("preserve_audit_data"):
        errors.append("rollback_plan.preserve_audit_data must be True")
    if not rollback.get("explicit_approval_required"):
        errors.append("rollback_plan.explicit_approval_required must be True")
    if not rollback.get("no_hard_delete"):
        errors.append("rollback_plan.no_hard_delete must be True")

    # --- Training guides ---
    guides = package.get("training_guides", [])
    if len(guides) != 5:
        errors.append(f"training_guides must have exactly 5, got {len(guides)}")

    status = "PASS" if not errors else "FAIL"
    return {
        "status": status,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }
