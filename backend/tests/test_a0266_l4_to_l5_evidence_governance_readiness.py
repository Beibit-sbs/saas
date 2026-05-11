"""
A-026.6-RUNTIME Test Suite: L4→L5 Evidence / Governance / KPI / Brain-Readiness

Tests the deterministic L5-readiness contracts for 4 selected modules:
- human_approved_timetable_workflow
- timetable_approval_queue
- timetable_change_kpi_dashboard
- workload_management

Test groups:
1. Import validation
2. Tenant fail-closed validation
3. Evidence lineage contract validation
4. Governance mapping validation
5. KPI-readiness boundary validation
6. Brain boundary validation
7. Tenant/audit/security validation
8. Determinism validation
9. Anti-inflation validation
"""

import pytest

# =============================================================================
# Group 1: Import validation
# =============================================================================


def test_import_human_workflow_l5_readiness():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )

    assert callable(get_human_workflow_l5_readiness)


def test_import_approval_queue_l5_readiness():
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )

    assert callable(get_approval_queue_l5_readiness)


def test_import_kpi_dashboard_l5_readiness():
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )

    assert callable(get_kpi_dashboard_l5_readiness)


def test_import_workload_l5_readiness():
    from app.modules.workload_management.service import (
        get_workload_l5_readiness,
    )

    assert callable(get_workload_l5_readiness)


def test_import_l5_schemas():
    from app.modules.human_approved_timetable_workflow.schemas import (
        HumanWorkflowL5ReadinessSchema,
    )
    from app.modules.timetable_approval_queue.schemas import (
        ApprovalQueueL5ReadinessSchema,
    )
    from app.modules.timetable_change_kpi_dashboard.schemas import (
        KpiDashboardL5ReadinessSchema,
    )
    from app.modules.workload_management.schemas import WorkloadL5ReadinessSchema

    assert HumanWorkflowL5ReadinessSchema
    assert ApprovalQueueL5ReadinessSchema
    assert KpiDashboardL5ReadinessSchema
    assert WorkloadL5ReadinessSchema


# =============================================================================
# Group 2: Tenant fail-closed validation
# =============================================================================


@pytest.mark.parametrize(
    "fn_path,module_name",
    [
        (
            "app.modules.human_approved_timetable_workflow.service",
            "get_human_workflow_l5_readiness",
        ),
        (
            "app.modules.timetable_approval_queue.service",
            "get_approval_queue_l5_readiness",
        ),
        (
            "app.modules.timetable_change_kpi_dashboard.service",
            "get_kpi_dashboard_l5_readiness",
        ),
        (
            "app.modules.workload_management.service",
            "get_workload_l5_readiness",
        ),
    ],
)
def test_l5_readiness_rejects_none_tenant(fn_path, module_name):
    import importlib

    mod = importlib.import_module(fn_path)
    fn = getattr(mod, module_name)
    with pytest.raises((ValueError, TypeError)):
        fn(None)


@pytest.mark.parametrize(
    "fn_path,module_name",
    [
        (
            "app.modules.human_approved_timetable_workflow.service",
            "get_human_workflow_l5_readiness",
        ),
        (
            "app.modules.timetable_approval_queue.service",
            "get_approval_queue_l5_readiness",
        ),
        (
            "app.modules.timetable_change_kpi_dashboard.service",
            "get_kpi_dashboard_l5_readiness",
        ),
        (
            "app.modules.workload_management.service",
            "get_workload_l5_readiness",
        ),
    ],
)
def test_l5_readiness_rejects_zero_tenant(fn_path, module_name):
    import importlib

    mod = importlib.import_module(fn_path)
    fn = getattr(mod, module_name)
    with pytest.raises((ValueError, TypeError)):
        fn(0)


@pytest.mark.parametrize(
    "fn_path,module_name",
    [
        (
            "app.modules.human_approved_timetable_workflow.service",
            "get_human_workflow_l5_readiness",
        ),
        (
            "app.modules.timetable_approval_queue.service",
            "get_approval_queue_l5_readiness",
        ),
        (
            "app.modules.timetable_change_kpi_dashboard.service",
            "get_kpi_dashboard_l5_readiness",
        ),
        (
            "app.modules.workload_management.service",
            "get_workload_l5_readiness",
        ),
    ],
)
def test_l5_readiness_rejects_negative_tenant(fn_path, module_name):
    import importlib

    mod = importlib.import_module(fn_path)
    fn = getattr(mod, module_name)
    with pytest.raises((ValueError, TypeError)):
        fn(-1)


def test_l5_readiness_accepts_valid_tenant_workflow():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )

    result = get_human_workflow_l5_readiness(1)
    assert result["tenant_id"] == 1


def test_l5_readiness_accepts_valid_tenant_queue():
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )

    result = get_approval_queue_l5_readiness(1)
    assert result["tenant_id"] == 1


def test_l5_readiness_accepts_valid_tenant_kpi():
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )

    result = get_kpi_dashboard_l5_readiness(1)
    assert result["tenant_id"] == 1


def test_l5_readiness_accepts_valid_tenant_workload():
    from app.modules.workload_management.service import (
        get_workload_l5_readiness,
    )

    result = get_workload_l5_readiness(1)
    assert result["tenant_id"] == 1


# =============================================================================
# Group 3: Evidence lineage contract validation
# =============================================================================


def test_evidence_lineage_status_present_workflow():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )

    r = get_human_workflow_l5_readiness(1)
    assert "evidence_lineage_status" in r
    assert r["evidence_lineage_status"]


def test_evidence_sources_non_empty_workflow():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )

    r = get_human_workflow_l5_readiness(1)
    assert "evidence_sources" in r
    assert len(r["evidence_sources"]) > 0


def test_evidence_completeness_workflow():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )

    r = get_human_workflow_l5_readiness(1)
    assert "evidence_completeness" in r
    assert r["evidence_completeness"]


def test_evidence_lineage_status_present_queue():
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )

    r = get_approval_queue_l5_readiness(1)
    assert "evidence_lineage_status" in r
    assert r["evidence_lineage_status"]
    assert len(r["evidence_sources"]) > 0


def test_evidence_lineage_status_present_kpi():
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )

    r = get_kpi_dashboard_l5_readiness(1)
    assert "evidence_lineage_status" in r
    assert len(r["evidence_sources"]) > 0


def test_evidence_lineage_status_present_workload():
    from app.modules.workload_management.service import (
        get_workload_l5_readiness,
    )

    r = get_workload_l5_readiness(1)
    assert "evidence_lineage_status" in r
    assert len(r["evidence_sources"]) > 0


# =============================================================================
# Group 4: Governance mapping validation
# =============================================================================


def test_governance_category_workflow():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )

    r = get_human_workflow_l5_readiness(1)
    assert r["governance_category"] == "TIMETABLE_GOVERNANCE"
    assert r["human_review_owner"]
    assert len(r["allowed_governance_actions"]) > 0
    assert len(r["forbidden_autonomous_actions"]) > 0


def test_governance_category_queue():
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )

    r = get_approval_queue_l5_readiness(1)
    assert r["governance_category"] == "HUMAN_REVIEW_QUEUE_GOVERNANCE"
    assert r["human_review_owner"]
    assert "MANUAL_APPROVE" in r["allowed_governance_actions"]
    assert "AUTO_APPROVE" in r["forbidden_autonomous_actions"]


def test_governance_category_kpi():
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )

    r = get_kpi_dashboard_l5_readiness(1)
    assert r["governance_category"] == "KPI_GOVERNANCE_READINESS"
    assert "AUTO_GENERATE_KPI" in r["forbidden_autonomous_actions"]


def test_governance_category_workload():
    from app.modules.workload_management.service import (
        get_workload_l5_readiness,
    )

    r = get_workload_l5_readiness(1)
    assert r["governance_category"] == "WORKLOAD_GOVERNANCE"
    assert "AUTO_ASSIGN" in r["forbidden_autonomous_actions"]
    assert "AUTO_MUTATE_PAYROLL" in r["forbidden_autonomous_actions"]


def test_escalation_boundary_present_all_modules():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )
    from app.modules.workload_management.service import get_workload_l5_readiness

    for fn in [
        get_human_workflow_l5_readiness,
        get_approval_queue_l5_readiness,
        get_kpi_dashboard_l5_readiness,
        get_workload_l5_readiness,
    ]:
        r = fn(1)
        assert "escalation_boundary" in r
        assert r["escalation_boundary"]


# =============================================================================
# Group 5: KPI-readiness boundary validation
# =============================================================================


def test_kpi_readiness_status_workflow():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )

    r = get_human_workflow_l5_readiness(1)
    assert r["kpi_readiness_status"] == "KPI_READINESS_CANDIDATE_ONLY"


def test_kpi_readiness_status_queue():
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )

    r = get_approval_queue_l5_readiness(1)
    assert r["kpi_readiness_status"] == "QUEUE_GOVERNANCE_READINESS_ONLY"


def test_kpi_readiness_status_kpi():
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )

    r = get_kpi_dashboard_l5_readiness(1)
    assert r["kpi_readiness_status"] == "KPI_EVIDENCE_READY_FOR_MAPPING"


def test_kpi_readiness_status_workload():
    from app.modules.workload_management.service import get_workload_l5_readiness

    r = get_workload_l5_readiness(1)
    assert r["kpi_readiness_status"] == "WORKLOAD_EVIDENCE_READY_FOR_GOVERNANCE_MAPPING"


def test_no_fake_kpi_values_all_modules():
    """Ensure no fabricated numeric KPI values are present in outputs."""
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )
    from app.modules.workload_management.service import get_workload_l5_readiness

    for fn in [
        get_human_workflow_l5_readiness,
        get_approval_queue_l5_readiness,
        get_kpi_dashboard_l5_readiness,
        get_workload_l5_readiness,
    ]:
        r = fn(1)
        # safety_flags must explicitly state no_fake_kpi_values=True
        assert r["safety_flags"].get("no_fake_kpi_values") is True


# =============================================================================
# Group 6: Brain boundary validation
# =============================================================================


def test_brain_boundary_workflow():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )

    r = get_human_workflow_l5_readiness(1)
    assert r["brain_readiness_boundary"] == "BRAIN_CANDIDATE_ONLY_NO_EXECUTION"
    assert r["safety_flags"].get("no_brain_execution") is True


def test_brain_boundary_queue():
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )

    r = get_approval_queue_l5_readiness(1)
    assert r["brain_readiness_boundary"] == "BRAIN_CANDIDATE_ONLY_NO_EXECUTION"
    assert r["safety_flags"].get("no_brain_execution") is True


def test_brain_boundary_kpi():
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )

    r = get_kpi_dashboard_l5_readiness(1)
    assert r["brain_readiness_boundary"] == "BRAIN_CANDIDATE_ONLY_NO_EXECUTION"
    assert r["safety_flags"].get("no_brain_execution") is True


def test_brain_boundary_workload():
    from app.modules.workload_management.service import get_workload_l5_readiness

    r = get_workload_l5_readiness(1)
    assert r["brain_readiness_boundary"] == "BRAIN_CANDIDATE_ONLY_NO_EXECUTION"
    assert r["safety_flags"].get("no_brain_execution") is True


def test_no_autonomous_execution_all_modules():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )
    from app.modules.workload_management.service import get_workload_l5_readiness

    for fn in [
        get_human_workflow_l5_readiness,
        get_approval_queue_l5_readiness,
        get_kpi_dashboard_l5_readiness,
        get_workload_l5_readiness,
    ]:
        r = fn(1)
        assert r.get("no_autonomous_execution") is True
        assert r["safety_flags"].get("no_autonomous_execution") is True


# =============================================================================
# Group 7: Tenant/audit/security validation
# =============================================================================


def test_tenant_id_in_output_all_modules():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )
    from app.modules.workload_management.service import get_workload_l5_readiness

    for fn, tid in [
        (get_human_workflow_l5_readiness, 42),
        (get_approval_queue_l5_readiness, 42),
        (get_kpi_dashboard_l5_readiness, 42),
        (get_workload_l5_readiness, 42),
    ]:
        r = fn(tid)
        assert r["tenant_id"] == 42


def test_tenant_scoped_flag_all_modules():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )
    from app.modules.workload_management.service import get_workload_l5_readiness

    for fn in [
        get_human_workflow_l5_readiness,
        get_approval_queue_l5_readiness,
        get_kpi_dashboard_l5_readiness,
        get_workload_l5_readiness,
    ]:
        r = fn(1)
        assert r.get("tenant_scoped") is True
        assert r["safety_flags"].get("no_cross_tenant_evidence") is True


def test_audit_evidence_notes_present_all_modules():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )
    from app.modules.workload_management.service import get_workload_l5_readiness

    for fn in [
        get_human_workflow_l5_readiness,
        get_approval_queue_l5_readiness,
        get_kpi_dashboard_l5_readiness,
        get_workload_l5_readiness,
    ]:
        r = fn(1)
        assert "audit_evidence_notes" in r
        assert len(r["audit_evidence_notes"]) > 0


def test_human_review_required_all_modules():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )
    from app.modules.workload_management.service import get_workload_l5_readiness

    for fn in [
        get_human_workflow_l5_readiness,
        get_approval_queue_l5_readiness,
        get_kpi_dashboard_l5_readiness,
        get_workload_l5_readiness,
    ]:
        r = fn(1)
        assert r.get("human_review_required") is True
        assert r["safety_flags"].get("human_review_required") is True


# =============================================================================
# Group 8: Determinism validation
# =============================================================================


def test_determinism_workflow():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )

    r1 = get_human_workflow_l5_readiness(7)
    r2 = get_human_workflow_l5_readiness(7)
    assert r1 == r2


def test_determinism_queue():
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )

    r1 = get_approval_queue_l5_readiness(7)
    r2 = get_approval_queue_l5_readiness(7)
    assert r1 == r2


def test_determinism_kpi():
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )

    r1 = get_kpi_dashboard_l5_readiness(7)
    r2 = get_kpi_dashboard_l5_readiness(7)
    assert r1 == r2


def test_determinism_workload():
    from app.modules.workload_management.service import get_workload_l5_readiness

    r1 = get_workload_l5_readiness(7)
    r2 = get_workload_l5_readiness(7)
    assert r1 == r2


# =============================================================================
# Group 9: Anti-inflation validation
# =============================================================================


def test_readiness_level_is_l5_ready_all_modules():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )
    from app.modules.workload_management.service import get_workload_l5_readiness

    for fn in [
        get_human_workflow_l5_readiness,
        get_approval_queue_l5_readiness,
        get_kpi_dashboard_l5_readiness,
        get_workload_l5_readiness,
    ]:
        r = fn(1)
        assert r["readiness_level"] == "L5_READY"


def test_no_l6_claim_all_modules():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )
    from app.modules.workload_management.service import get_workload_l5_readiness

    for fn in [
        get_human_workflow_l5_readiness,
        get_approval_queue_l5_readiness,
        get_kpi_dashboard_l5_readiness,
        get_workload_l5_readiness,
    ]:
        r = fn(1)
        assert r.get("no_l6_claim") is True
        assert r["safety_flags"].get("no_l6_claim") is True


def test_safety_flags_complete_all_modules():
    """All 7 required safety flags must be present and True."""
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )
    from app.modules.workload_management.service import get_workload_l5_readiness

    required_flags = [
        "tenant_scoped",
        "no_cross_tenant_evidence",
        "no_fake_kpi_values",
        "no_brain_execution",
        "no_autonomous_execution",
        "no_l6_claim",
        "human_review_required",
    ]

    for fn in [
        get_human_workflow_l5_readiness,
        get_approval_queue_l5_readiness,
        get_kpi_dashboard_l5_readiness,
        get_workload_l5_readiness,
    ]:
        r = fn(1)
        for flag in required_flags:
            assert r["safety_flags"].get(flag) is True, (
                f"Missing or False safety flag '{flag}' in {r['module']}"
            )


def test_governance_mapping_status_set_all_modules():
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )
    from app.modules.workload_management.service import get_workload_l5_readiness

    for fn in [
        get_human_workflow_l5_readiness,
        get_approval_queue_l5_readiness,
        get_kpi_dashboard_l5_readiness,
        get_workload_l5_readiness,
    ]:
        r = fn(1)
        assert r.get("governance_mapping_status") == "GOVERNANCE_BOUNDARY_MAPPED"


def test_schema_validation_workflow():
    from app.modules.human_approved_timetable_workflow.schemas import (
        HumanWorkflowL5ReadinessSchema,
    )
    from app.modules.human_approved_timetable_workflow.service import (
        get_human_workflow_l5_readiness,
    )

    payload = get_human_workflow_l5_readiness(1)
    schema = HumanWorkflowL5ReadinessSchema(**payload)
    assert schema.readiness_level == "L5_READY"
    assert schema.tenant_id == 1
    assert schema.no_l6_claim is True


def test_schema_validation_queue():
    from app.modules.timetable_approval_queue.schemas import (
        ApprovalQueueL5ReadinessSchema,
    )
    from app.modules.timetable_approval_queue.service import (
        get_approval_queue_l5_readiness,
    )

    payload = get_approval_queue_l5_readiness(1)
    schema = ApprovalQueueL5ReadinessSchema(**payload)
    assert schema.readiness_level == "L5_READY"
    assert schema.human_review_required is True


def test_schema_validation_kpi():
    from app.modules.timetable_change_kpi_dashboard.schemas import (
        KpiDashboardL5ReadinessSchema,
    )
    from app.modules.timetable_change_kpi_dashboard.service import (
        get_kpi_dashboard_l5_readiness,
    )

    payload = get_kpi_dashboard_l5_readiness(1)
    schema = KpiDashboardL5ReadinessSchema(**payload)
    assert schema.readiness_level == "L5_READY"
    assert schema.no_autonomous_execution is True


def test_schema_validation_workload():
    from app.modules.workload_management.schemas import WorkloadL5ReadinessSchema
    from app.modules.workload_management.service import get_workload_l5_readiness

    payload = get_workload_l5_readiness(1)
    schema = WorkloadL5ReadinessSchema(**payload)
    assert schema.readiness_level == "L5_READY"
    assert schema.tenant_scoped is True
