"""A-031.6-RUNTIME — Rector Assignment OS Pilot Package tests.

Tests the deterministic pilot readiness package defined in
app.modules.rector_assignment_workflow.pilot_package.

Implementation mode: Option A (pure data module, no DB, no external calls).
All tests are pure Python — no DB, no fixtures, no live dispatch.

Target: 80–140 tests.
"""

from __future__ import annotations

import pytest

from app.modules.rector_assignment_workflow.pilot_package import (
    AUTONOMOUS_ESCALATION_ENABLED,
    L5_L6_ELEVATION_CLAIMED,
    LIVE_DISPATCH_ENABLED,
    PILOT_MODE,
    PILOT_PACKAGE_NAME,
    PILOT_PACKAGE_VERSION,
    PILOT_TENANT_PLACEHOLDER,
    PRODUCTION_READY_CLAIM,
    PROVIDER_INTEGRATION_ENABLED,
    REAL_PERSONAL_DATA_INCLUDED,
    get_pilot_acceptance_criteria,
    get_pilot_assignment_templates,
    get_pilot_demo_scenarios,
    get_pilot_escalation_policies,
    get_pilot_readiness_package,
    get_pilot_role_matrix,
    get_pilot_rollback_plan,
    get_pilot_seed_assignments,
    get_pilot_sla_policies,
    get_pilot_support_plan,
    get_pilot_training_guides,
    get_pilot_users,
    validate_pilot_package,
)

# ============================================================
# Section 1 — Module-level metadata constants
# ============================================================

class TestPackageMetadataConstants:
    def test_package_version(self):
        assert PILOT_PACKAGE_VERSION == "A-031.6"

    def test_package_name(self):
        assert PILOT_PACKAGE_NAME == "RECTOR_ASSIGNMENT_OS_PILOT_READINESS"

    def test_pilot_mode(self):
        assert PILOT_MODE == "CONTROLLED_PILOT_SEED_PACKAGE"

    def test_tenant_placeholder_set(self):
        assert PILOT_TENANT_PLACEHOLDER == "PILOT_TENANT_PLACEHOLDER"

    def test_live_dispatch_disabled(self):
        assert LIVE_DISPATCH_ENABLED is False

    def test_provider_integration_disabled(self):
        assert PROVIDER_INTEGRATION_ENABLED is False

    def test_no_real_personal_data(self):
        assert REAL_PERSONAL_DATA_INCLUDED is False

    def test_no_production_ready_claim(self):
        assert PRODUCTION_READY_CLAIM is False

    def test_no_l5_l6_elevation(self):
        assert L5_L6_ELEVATION_CLAIMED is False

    def test_no_autonomous_escalation(self):
        assert AUTONOMOUS_ESCALATION_ENABLED is False


# ============================================================
# Section 2 — Role matrix
# ============================================================

class TestRoleMatrix:
    def setup_method(self):
        self.matrix = get_pilot_role_matrix()

    def test_exactly_six_roles(self):
        assert len(self.matrix) == 6

    def test_all_required_roles_present(self):
        required = {
            "rector_assignment_admin",
            "rector_assignment_controller",
            "rector_assignment_reviewer",
            "rector_assignment_executor",
            "rector_assignment_auditor",
            "platform_admin",
        }
        assert set(self.matrix.keys()) == required

    def test_each_role_has_description(self):
        for name, role in self.matrix.items():
            assert role.get("description"), f"Role {name} missing description"

    def test_each_role_has_permissions(self):
        for name, role in self.matrix.items():
            assert role.get("permissions"), f"Role {name} has no permissions"

    def test_each_role_has_allowed_actions(self):
        for name, role in self.matrix.items():
            assert role.get("allowed_actions"), f"Role {name} has no allowed_actions"

    def test_each_role_has_forbidden_actions(self):
        for name, role in self.matrix.items():
            assert role.get("forbidden_actions"), f"Role {name} has no forbidden_actions"

    def test_admin_has_full_permissions(self):
        admin = self.matrix["rector_assignment_admin"]
        assert "admin.rector_assignments.create" in admin["permissions"]
        assert "admin.rector_assignments.admin" in admin["permissions"]
        assert "admin.rector_assignments.sla.manage" in admin["permissions"]
        assert "admin.rector_assignments.escalation_policy.manage" in admin["permissions"]

    def test_auditor_read_only_permissions(self):
        auditor = self.matrix["rector_assignment_auditor"]
        perms = auditor["permissions"]
        for perm in perms:
            assert "write" not in perm.lower(), f"Auditor has write perm: {perm}"
            assert "manage" not in perm.lower() or "read" in perm.lower(), f"Auditor has manage perm: {perm}"

    def test_auditor_forbidden_any_write(self):
        auditor = self.matrix["rector_assignment_auditor"]
        assert "any_write_mutation" in auditor["forbidden_actions"]

    def test_executor_forbidden_complete(self):
        executor = self.matrix["rector_assignment_executor"]
        assert "complete_assignment" in executor["forbidden_actions"]

    def test_admin_forbidden_hard_delete(self):
        admin = self.matrix["rector_assignment_admin"]
        assert "hard_delete_assignment" in admin["forbidden_actions"]

    def test_admin_forbidden_live_dispatch(self):
        admin = self.matrix["rector_assignment_admin"]
        assert "live_email_dispatch" in admin["forbidden_actions"]

    def test_pilot_user_counts_sum_to_seven(self):
        total = sum(role["pilot_user_count"] for role in self.matrix.values())
        assert total == 7

    def test_executor_pilot_count_is_two(self):
        assert self.matrix["rector_assignment_executor"]["pilot_user_count"] == 2


# ============================================================
# Section 3 — Pilot users
# ============================================================

class TestPilotUsers:
    def setup_method(self):
        self.users = get_pilot_users()

    def test_exactly_seven_users(self):
        assert len(self.users) == 7

    def test_all_required_usernames_present(self):
        usernames = {u["username"] for u in self.users}
        required = {
            "pilot_rector", "pilot_controller", "pilot_director",
            "pilot_executor_1", "pilot_executor_2", "pilot_auditor", "pilot_admin",
        }
        assert usernames == required

    def test_all_users_are_placeholders(self):
        for u in self.users:
            assert u["is_placeholder"] is True, f"{u['username']} must be placeholder"

    def test_no_user_has_password(self):
        for u in self.users:
            assert u.get("password") is None, f"{u['username']} must not have password"

    def test_no_user_has_real_phone(self):
        for u in self.users:
            assert u.get("phone") is None, f"{u['username']} must not have phone"

    def test_all_users_active(self):
        for u in self.users:
            assert u["active"] is True, f"{u['username']} must be active"

    def test_all_users_have_tenant_placeholder(self):
        for u in self.users:
            assert u["tenant_ref"] == "PILOT_TENANT_PLACEHOLDER"

    def test_user_roles_are_valid(self):
        valid_roles = {
            "rector_assignment_admin", "rector_assignment_controller",
            "rector_assignment_reviewer", "rector_assignment_executor",
            "rector_assignment_auditor", "platform_admin",
        }
        for u in self.users:
            assert u["role"] in valid_roles, f"{u['username']} has invalid role {u['role']}"

    def test_pilot_rector_is_admin_role(self):
        rector = next(u for u in self.users if u["username"] == "pilot_rector")
        assert rector["role"] == "rector_assignment_admin"

    def test_pilot_auditor_is_auditor_role(self):
        auditor = next(u for u in self.users if u["username"] == "pilot_auditor")
        assert auditor["role"] == "rector_assignment_auditor"

    def test_two_executors(self):
        executors = [u for u in self.users if u["role"] == "rector_assignment_executor"]
        assert len(executors) == 2

    def test_email_uses_pilot_local_domain(self):
        for u in self.users:
            email = u.get("email", "")
            if email:
                assert "@pilot.local" in email, f"{u['username']} email not @pilot.local: {email}"

    def test_no_real_email_domains(self):
        # Only check for clearly external real domains, not substrings of our placeholder names
        real_domains = [".edu", ".gov", ".ac.", "university"]
        for u in self.users:
            email = u.get("email", "") or ""
            for domain in real_domains:
                assert domain not in email.lower(), \
                    f"{u['username']} may have real email: {email}"


# ============================================================
# Section 4 — Assignment templates
# ============================================================

class TestAssignmentTemplates:
    def setup_method(self):
        self.templates = get_pilot_assignment_templates()

    def test_exactly_five_templates(self):
        assert len(self.templates) == 5

    def test_all_required_template_keys_present(self):
        keys = {t["template_key"] for t in self.templates}
        required = {
            "rector_weekly_report",
            "infra_issue_resolution",
            "accreditation_evidence",
            "procurement_status_update",
            "academic_kpi_followup",
        }
        assert keys == required

    def test_no_duplicate_template_keys(self):
        keys = [t["template_key"] for t in self.templates]
        assert len(keys) == len(set(keys))

    def test_all_templates_have_name(self):
        for t in self.templates:
            assert t.get("name"), f"Template {t.get('template_key')} missing name"

    def test_all_templates_have_description(self):
        for t in self.templates:
            assert t.get("description"), f"Template {t.get('template_key')} missing description"

    def test_all_priorities_are_valid(self):
        valid = {"CRITICAL", "HIGH", "NORMAL", "LOW"}
        for t in self.templates:
            assert t["priority"] in valid, f"Template {t['template_key']} invalid priority: {t['priority']}"

    def test_due_days_positive(self):
        for t in self.templates:
            assert t["default_due_days"] > 0, f"Template {t['template_key']} due_days <= 0"

    def test_all_templates_active(self):
        for t in self.templates:
            assert t["active"] is True

    def test_report_sections_non_empty(self):
        for t in self.templates:
            assert t.get("report_sections"), f"Template {t.get('template_key')} missing report_sections"

    def test_rector_weekly_report_is_normal_priority(self):
        t = next(t for t in self.templates if t["template_key"] == "rector_weekly_report")
        assert t["priority"] == "NORMAL"
        assert t["default_due_days"] == 7

    def test_infra_issue_high_priority(self):
        t = next(t for t in self.templates if t["template_key"] == "infra_issue_resolution")
        assert t["priority"] == "HIGH"
        assert t["default_due_days"] == 3

    def test_accreditation_evidence_required(self):
        t = next(t for t in self.templates if t["template_key"] == "accreditation_evidence")
        assert t["evidence_required"] is True

    def test_rector_weekly_evidence_not_required(self):
        t = next(t for t in self.templates if t["template_key"] == "rector_weekly_report")
        assert t["evidence_required"] is False


# ============================================================
# Section 5 — SLA policies
# ============================================================

class TestSlaPolicies:
    def setup_method(self):
        self.policies = get_pilot_sla_policies()

    def test_exactly_three_policies(self):
        assert len(self.policies) == 3

    def test_critical_high_normal_all_present(self):
        priorities = {p["priority"] for p in self.policies}
        assert "CRITICAL" in priorities
        assert "HIGH" in priorities
        assert "NORMAL" in priorities

    def test_no_duplicate_priorities(self):
        priorities = [p["priority"] for p in self.policies]
        assert len(priorities) == len(set(priorities))

    def test_due_days_non_negative(self):
        for p in self.policies:
            assert p["due_days"] >= 0

    def test_warning_before_hours_non_negative(self):
        for p in self.policies:
            assert p["warning_before_hours"] >= 0

    def test_overdue_after_hours_non_negative(self):
        for p in self.policies:
            assert p["overdue_after_hours"] >= 0

    def test_escalation_after_hours_gte_overdue(self):
        for p in self.policies:
            assert p["escalation_after_hours"] >= p["overdue_after_hours"], \
                f"Policy {p['policy_key']}: escalation_after_hours < overdue_after_hours"

    def test_all_policies_active(self):
        for p in self.policies:
            assert p["is_active"] is True

    def test_all_require_manual_confirmation(self):
        for p in self.policies:
            assert p["require_manual_confirmation"] is True

    def test_critical_due_one_day(self):
        p = next(p for p in self.policies if p["priority"] == "CRITICAL")
        assert p["due_days"] == 1
        assert p["warning_before_hours"] == 6
        assert p["escalation_after_hours"] == 6

    def test_high_due_three_days(self):
        p = next(p for p in self.policies if p["priority"] == "HIGH")
        assert p["due_days"] == 3
        assert p["warning_before_hours"] == 24
        assert p["escalation_after_hours"] == 24

    def test_normal_due_seven_days(self):
        p = next(p for p in self.policies if p["priority"] == "NORMAL")
        assert p["due_days"] == 7
        assert p["warning_before_hours"] == 48
        assert p["escalation_after_hours"] == 48

    def test_all_policies_have_keys(self):
        keys = {p["policy_key"] for p in self.policies}
        assert "critical_sla" in keys
        assert "high_sla" in keys
        assert "normal_sla" in keys


# ============================================================
# Section 6 — Escalation policies
# ============================================================

class TestEscalationPolicies:
    def setup_method(self):
        self.policies = get_pilot_escalation_policies()
        self.policy = self.policies[0]
        self.levels = self.policy["levels"]

    def test_at_least_one_policy(self):
        assert len(self.policies) >= 1

    def test_standard_escalation_policy_present(self):
        keys = {p["policy_key"] for p in self.policies}
        assert "standard_escalation" in keys

    def test_exactly_four_levels(self):
        assert len(self.levels) == 4

    def test_all_levels_require_manual_confirmation(self):
        for lvl in self.levels:
            assert lvl["require_manual_confirmation"] is True, \
                f"Level {lvl['level']} must require manual confirmation"

    def test_level_roles_are_valid(self):
        valid_roles = {"CONTROLLER", "PRORECTOR", "RECTOR", "PLATFORM_ADMIN"}
        for lvl in self.levels:
            assert lvl["escalate_to_role"] in valid_roles, \
                f"Level {lvl['level']} has invalid role: {lvl['escalate_to_role']}"

    def test_level_roles_in_correct_order(self):
        roles = [lvl["escalate_to_role"] for lvl in self.levels]
        assert roles[0] == "CONTROLLER"
        assert roles[1] == "PRORECTOR"
        assert roles[2] == "RECTOR"
        assert roles[3] == "PLATFORM_ADMIN"

    def test_escalation_hours_increase_by_level(self):
        hours = [lvl["escalate_after_hours"] for lvl in self.levels]
        for i in range(1, len(hours)):
            assert hours[i] > hours[i - 1], \
                f"Level {i+1} hours {hours[i]} not greater than level {i} hours {hours[i-1]}"

    def test_no_autonomous_action(self):
        for ep in self.policies:
            assert ep["autonomous_action_enabled"] is False

    def test_no_live_dispatch(self):
        for ep in self.policies:
            assert ep["live_dispatch_enabled"] is False

    def test_level_numbers_are_sequential(self):
        numbers = [lvl["level"] for lvl in self.levels]
        assert numbers == [1, 2, 3, 4]

    def test_all_levels_have_action_description(self):
        for lvl in self.levels:
            assert lvl.get("action_description"), f"Level {lvl['level']} missing action_description"


# ============================================================
# Section 7 — Seed assignments
# ============================================================

class TestSeedAssignments:
    def setup_method(self):
        self.assignments = get_pilot_seed_assignments()
        self.templates = get_pilot_assignment_templates()
        self.users = get_pilot_users()
        self.template_keys = {t["template_key"] for t in self.templates}
        self.user_usernames = {u["username"] for u in self.users}

    def test_exactly_ten_assignments(self):
        assert len(self.assignments) == 10

    def test_no_duplicate_seed_keys(self):
        keys = [a["seed_key"] for a in self.assignments]
        assert len(keys) == len(set(keys))

    def test_all_statuses_valid(self):
        valid = {
            "DRAFT", "ASSIGNED", "ACCEPTED", "IN_PROGRESS", "REPORT_SUBMITTED",
            "RETURNED_FOR_REVISION", "COMPLETED", "OVERDUE", "ESCALATED",
            "CANCELLED", "ARCHIVED",
        }
        for a in self.assignments:
            assert a["status"] in valid, f"{a['seed_key']} has invalid status: {a['status']}"

    def test_status_diversity(self):
        statuses = {a["status"] for a in self.assignments}
        # Must have at least 7 distinct statuses (good demo coverage)
        assert len(statuses) >= 7, f"Not enough status variety: {statuses}"

    def test_has_draft_status(self):
        statuses = {a["status"] for a in self.assignments}
        assert "DRAFT" in statuses

    def test_has_overdue_status(self):
        statuses = {a["status"] for a in self.assignments}
        assert "OVERDUE" in statuses

    def test_has_escalated_status(self):
        statuses = {a["status"] for a in self.assignments}
        assert "ESCALATED" in statuses

    def test_has_completed_status(self):
        statuses = {a["status"] for a in self.assignments}
        assert "COMPLETED" in statuses

    def test_all_priorities_valid(self):
        valid = {"CRITICAL", "HIGH", "NORMAL", "LOW"}
        for a in self.assignments:
            assert a["priority"] in valid

    def test_all_template_keys_valid(self):
        for a in self.assignments:
            assert a["template_key"] in self.template_keys, \
                f"{a['seed_key']} references unknown template: {a['template_key']}"

    def test_all_assigned_users_valid(self):
        for a in self.assignments:
            assert a["assigned_to_user"] in self.user_usernames, \
                f"{a['seed_key']} references unknown user: {a['assigned_to_user']}"

    def test_all_controller_users_valid(self):
        for a in self.assignments:
            assert a["controller_user"] in self.user_usernames, \
                f"{a['seed_key']} references unknown controller: {a['controller_user']}"

    def test_all_assignments_are_demo(self):
        for a in self.assignments:
            assert a["is_demo"] is True

    def test_all_assignments_have_outbox_expected_events(self):
        for a in self.assignments:
            assert a.get("outbox_expected_events"), \
                f"{a['seed_key']} missing outbox_expected_events"

    def test_all_sla_policy_keys_valid(self):
        valid_keys = {"critical_sla", "high_sla", "normal_sla"}
        for a in self.assignments:
            assert a["sla_policy_key"] in valid_keys, \
                f"{a['seed_key']} has invalid sla_policy_key: {a['sla_policy_key']}"

    def test_no_real_personal_data_in_titles(self):
        sensitive_patterns = ["@gmail", "@yahoo", "+7", "phone", "password", "ssn", "passport"]
        for a in self.assignments:
            title_lower = a.get("title", "").lower()
            for pattern in sensitive_patterns:
                assert pattern not in title_lower, \
                    f"Assignment '{a['seed_key']}' title may contain personal data: {a['title']}"


# ============================================================
# Section 8 — Demo scenarios
# ============================================================

class TestDemoScenarios:
    def setup_method(self):
        self.scenarios = get_pilot_demo_scenarios()

    def test_exactly_six_scenarios(self):
        assert len(self.scenarios) == 6

    def test_all_required_scenario_keys_present(self):
        keys = {s["scenario_key"] for s in self.scenarios}
        required = {
            "create_and_assign_from_template",
            "executor_accepts_and_submits_report",
            "review_return_and_resubmit",
            "complete_assignment_and_audit",
            "overdue_and_manual_escalation",
            "auditor_read_only_access",
        }
        assert keys == required

    def test_all_scenarios_have_steps(self):
        for s in self.scenarios:
            assert s.get("steps"), f"Scenario {s['scenario_key']} has no steps"
            assert len(s["steps"]) >= 4, f"Scenario {s['scenario_key']} has fewer than 4 steps"

    def test_all_scenarios_have_acceptance_check(self):
        for s in self.scenarios:
            assert s.get("acceptance_check"), f"Scenario {s['scenario_key']} missing acceptance_check"

    def test_all_scenarios_have_anti_fake_check(self):
        for s in self.scenarios:
            assert s.get("anti_fake_check"), f"Scenario {s['scenario_key']} missing anti_fake_check"

    def test_all_scenarios_have_actor_roles(self):
        for s in self.scenarios:
            assert s.get("actor_roles"), f"Scenario {s['scenario_key']} has no actor_roles"

    def test_escalation_scenario_mentions_manual(self):
        s = next(s for s in self.scenarios if s["scenario_key"] == "overdue_and_manual_escalation")
        anti_fake = s["anti_fake_check"].lower()
        assert "no live dispatch" in anti_fake or "pending" in anti_fake

    def test_auditor_scenario_mentions_read_only(self):
        s = next(s for s in self.scenarios if s["scenario_key"] == "auditor_read_only_access")
        acceptance = s["acceptance_check"].lower()
        assert "mutation" in acceptance or "absent" in acceptance or "read" in acceptance


# ============================================================
# Section 9 — Training guides
# ============================================================

class TestTrainingGuides:
    def setup_method(self):
        self.guides = get_pilot_training_guides()

    def test_exactly_five_guides(self):
        assert len(self.guides) == 5

    def test_all_required_guide_keys_present(self):
        keys = {g["guide_key"] for g in self.guides}
        required = {
            "rector_quick_guide",
            "controller_secretary_guide",
            "executor_guide",
            "auditor_guide",
            "admin_guide",
        }
        assert keys == required

    def test_each_guide_has_sections(self):
        for g in self.guides:
            assert g.get("sections"), f"Guide {g['guide_key']} has no sections"
            assert len(g["sections"]) >= 5, f"Guide {g['guide_key']} has fewer than 5 sections"

    def test_each_guide_has_target_roles(self):
        for g in self.guides:
            assert g.get("target_roles"), f"Guide {g['guide_key']} has no target_roles"

    def test_each_guide_has_title(self):
        for g in self.guides:
            assert g.get("title"), f"Guide {g['guide_key']} missing title"


# ============================================================
# Section 10 — Support plan
# ============================================================

class TestSupportPlan:
    def setup_method(self):
        self.plan = get_pilot_support_plan()

    def test_daily_checkin_required(self):
        assert self.plan["daily_checkin_required"] is True

    def test_has_issue_categories(self):
        cats = self.plan.get("issue_categories", [])
        assert len(cats) >= 5

    def test_has_triage_matrix(self):
        matrix = self.plan.get("triage_matrix", {})
        assert "P1" in matrix
        assert "P2" in matrix
        assert "P3" in matrix

    def test_p1_response_is_immediate(self):
        p1 = self.plan["triage_matrix"]["P1"]
        assert "1 hour" in p1["response_target"] or "Immediate" in p1["response_target"]

    def test_security_in_issue_categories(self):
        categories = self.plan.get("issue_categories", [])
        has_security = any("security" in cat.lower() for cat in categories)
        assert has_security


# ============================================================
# Section 11 — Rollback plan
# ============================================================

class TestRollbackPlan:
    def setup_method(self):
        self.plan = get_pilot_rollback_plan()

    def test_no_drop_table(self):
        assert self.plan["no_drop_table"] is True

    def test_preserve_audit_data(self):
        assert self.plan["preserve_audit_data"] is True

    def test_no_hard_delete(self):
        assert self.plan["no_hard_delete"] is True

    def test_explicit_approval_required(self):
        assert self.plan["explicit_approval_required"] is True

    def test_archive_not_delete(self):
        assert self.plan["archive_pilot_assignments"] is True

    def test_has_ordered_steps(self):
        steps = self.plan.get("steps", [])
        assert len(steps) >= 5

    def test_forbidden_rollback_actions_listed(self):
        forbidden = self.plan.get("forbidden_rollback_actions", [])
        assert len(forbidden) >= 3
        forbidden_text = " ".join(forbidden).upper()
        assert "DROP TABLE" in forbidden_text

    def test_rollback_conditions_defined(self):
        conditions = self.plan.get("rollback_conditions", [])
        assert len(conditions) >= 3


# ============================================================
# Section 12 — Acceptance criteria
# ============================================================

class TestAcceptanceCriteria:
    def setup_method(self):
        self.criteria = get_pilot_acceptance_criteria()

    def test_success_threshold_is_90_percent(self):
        assert self.criteria["success_threshold_percent"] == 90

    def test_zero_security_incidents_target(self):
        assert self.criteria["security"]["unauthorized_access_incidents"] == 0
        assert self.criteria["security"]["tenant_isolation_incidents"] == 0

    def test_zero_hard_delete_target(self):
        assert self.criteria["security"]["hard_delete_incidents"] == 0

    def test_anti_fake_criteria_defined(self):
        af = self.criteria["anti_fake"]
        assert "fake_metrics_false" in af
        assert "data_source" in af
        assert af.get("no_send_now_dispatch_button") is True

    def test_live_dispatch_zero_target(self):
        ot = self.criteria["overall_thresholds"]
        assert ot["live_email_sms_dispatched"] == 0

    def test_functional_criteria_covers_all_workflows(self):
        fc = self.criteria["functional"]
        required_keys = {
            "assignment_creation", "assignment_acceptance", "report_submission",
            "return_for_revision", "completion", "dashboard_updates",
            "sla_badge", "outbox_timeline", "audit_trail", "permission_gates",
        }
        assert required_keys.issubset(fc.keys())


# ============================================================
# Section 13 — get_pilot_readiness_package (aggregate)
# ============================================================

class TestPilotReadinessPackage:
    def setup_method(self):
        self.package = get_pilot_readiness_package()

    def test_package_is_dict(self):
        assert isinstance(self.package, dict)

    def test_package_has_metadata(self):
        assert "metadata" in self.package

    def test_package_has_role_matrix(self):
        assert "role_matrix" in self.package

    def test_package_has_users(self):
        assert "users" in self.package

    def test_package_has_assignment_templates(self):
        assert "assignment_templates" in self.package

    def test_package_has_sla_policies(self):
        assert "sla_policies" in self.package

    def test_package_has_escalation_policies(self):
        assert "escalation_policies" in self.package

    def test_package_has_seed_assignments(self):
        assert "seed_assignments" in self.package

    def test_package_has_demo_scenarios(self):
        assert "demo_scenarios" in self.package

    def test_package_has_training_guides(self):
        assert "training_guides" in self.package

    def test_package_has_support_plan(self):
        assert "support_plan" in self.package

    def test_package_has_rollback_plan(self):
        assert "rollback_plan" in self.package

    def test_package_has_acceptance_criteria(self):
        assert "acceptance_criteria" in self.package

    def test_metadata_version(self):
        assert self.package["metadata"]["package_version"] == "A-031.6"

    def test_metadata_live_dispatch_false(self):
        assert self.package["metadata"]["live_dispatch_enabled"] is False

    def test_metadata_provider_false(self):
        assert self.package["metadata"]["provider_integration_enabled"] is False

    def test_metadata_real_personal_data_false(self):
        assert self.package["metadata"]["real_personal_data_included"] is False

    def test_metadata_production_ready_false(self):
        assert self.package["metadata"]["production_ready_claim"] is False

    def test_metadata_l5_l6_false(self):
        assert self.package["metadata"]["l5_l6_elevation_claimed"] is False

    def test_metadata_autonomous_escalation_false(self):
        assert self.package["metadata"]["autonomous_escalation_enabled"] is False

    def test_users_count(self):
        assert len(self.package["users"]) == 7

    def test_templates_count(self):
        assert len(self.package["assignment_templates"]) == 5

    def test_sla_policies_count(self):
        assert len(self.package["sla_policies"]) == 3

    def test_seed_assignments_count(self):
        assert len(self.package["seed_assignments"]) == 10

    def test_demo_scenarios_count(self):
        assert len(self.package["demo_scenarios"]) == 6

    def test_training_guides_count(self):
        assert len(self.package["training_guides"]) == 5


# ============================================================
# Section 14 — validate_pilot_package
# ============================================================

class TestValidatePilotPackage:
    """Mutation tests use copy.deepcopy to avoid polluting module-level data."""

    def _fresh(self) -> dict:
        import copy
        return copy.deepcopy(get_pilot_readiness_package())

    def test_valid_package_returns_pass(self):
        result = validate_pilot_package(self._fresh())
        assert result["status"] == "PASS", \
            f"Validation failed: {result['errors']}"

    def test_valid_package_has_no_errors(self):
        result = validate_pilot_package(self._fresh())
        assert result["error_count"] == 0, f"Unexpected errors: {result['errors']}"

    def test_wrong_version_fails(self):
        pkg = self._fresh()
        pkg["metadata"]["package_version"] = "WRONG"
        result = validate_pilot_package(pkg)
        assert result["status"] == "FAIL"
        assert any("package_version" in e for e in result["errors"])

    def test_live_dispatch_true_fails(self):
        pkg = self._fresh()
        pkg["metadata"]["live_dispatch_enabled"] = True
        result = validate_pilot_package(pkg)
        assert result["status"] == "FAIL"
        assert any("live_dispatch_enabled" in e for e in result["errors"])

    def test_missing_sla_priority_fails(self):
        pkg = self._fresh()
        pkg["sla_policies"] = [p for p in pkg["sla_policies"] if p["priority"] != "CRITICAL"]
        result = validate_pilot_package(pkg)
        assert result["status"] == "FAIL"
        assert any("CRITICAL" in e for e in result["errors"])

    def test_wrong_user_count_fails(self):
        pkg = self._fresh()
        pkg["users"] = pkg["users"][:5]
        result = validate_pilot_package(pkg)
        assert result["status"] == "FAIL"

    def test_user_with_password_fails(self):
        pkg = self._fresh()
        pkg["users"][0]["password"] = "secret123"
        result = validate_pilot_package(pkg)
        assert result["status"] == "FAIL"
        assert any("password" in e for e in result["errors"])

    def test_no_drop_table_false_fails(self):
        pkg = self._fresh()
        pkg["rollback_plan"]["no_drop_table"] = False
        result = validate_pilot_package(pkg)
        assert result["status"] == "FAIL"
        assert any("no_drop_table" in e for e in result["errors"])

    def test_missing_scenario_count_fails(self):
        pkg = self._fresh()
        pkg["demo_scenarios"] = pkg["demo_scenarios"][:4]
        result = validate_pilot_package(pkg)
        assert result["status"] == "FAIL"

    def test_production_ready_true_fails(self):
        pkg = self._fresh()
        pkg["metadata"]["production_ready_claim"] = True
        result = validate_pilot_package(pkg)
        assert result["status"] == "FAIL"

    def test_sla_escalation_less_than_overdue_fails(self):
        pkg = self._fresh()
        # Force escalation < overdue (invalid)
        pkg["sla_policies"][0]["overdue_after_hours"] = 10
        pkg["sla_policies"][0]["escalation_after_hours"] = 5
        result = validate_pilot_package(pkg)
        assert result["status"] == "FAIL"

    def test_returns_error_count(self):
        result = validate_pilot_package(self._fresh())
        assert "error_count" in result
        assert isinstance(result["error_count"], int)

    def test_returns_warning_count(self):
        result = validate_pilot_package(self._fresh())
        assert "warning_count" in result
        assert isinstance(result["warning_count"], int)


# ============================================================
# Section 15 — Anti-fake / privacy scan (explicit assertions)
# ============================================================

class TestAntiFakeAndPrivacy:
    """Explicit anti-fake checks that verify no live dispatch, no secrets,
    no real personal data anywhere in the package."""

    def setup_method(self):
        self.package = get_pilot_readiness_package()

    def test_no_smtp_in_package(self):
        import json
        content = json.dumps(self.package).lower()
        assert "smtp" not in content

    def test_no_provider_call_in_package(self):
        import json
        content = json.dumps(self.package).lower()
        assert "send_email" not in content
        assert "send_sms" not in content

    def test_no_twilio_in_package(self):
        import json
        content = json.dumps(self.package).lower()
        assert "twilio" not in content

    def test_no_password_in_user_data(self):
        for user in self.package["users"]:
            assert user.get("password") is None

    def test_no_production_ready_claim_in_metadata(self):
        assert self.package["metadata"]["production_ready_claim"] is False

    def test_no_l5_l6_in_metadata(self):
        assert self.package["metadata"]["l5_l6_elevation_claimed"] is False

    def test_live_dispatch_false_in_metadata(self):
        assert self.package["metadata"]["live_dispatch_enabled"] is False

    def test_live_dispatch_false_in_escalation(self):
        for ep in self.package["escalation_policies"]:
            assert ep["live_dispatch_enabled"] is False

    def test_autonomous_escalation_false_everywhere(self):
        assert self.package["metadata"]["autonomous_escalation_enabled"] is False
        for ep in self.package["escalation_policies"]:
            assert ep["autonomous_action_enabled"] is False

    def test_no_hardcoded_production_tenant_id(self):
        import json
        content = json.dumps(self.package)
        # Should not contain real numeric tenant IDs hardcoded as production
        assert "PILOT_TENANT_PLACEHOLDER" in content
        # Ensure the placeholder is used, not a real tenant
        for user in self.package["users"]:
            assert user["tenant_ref"] == "PILOT_TENANT_PLACEHOLDER"
