from __future__ import annotations

from app.modules.auth.token_service import create_access_token
from tests.conftest import ADMIN_HEADERS, client


def _brain_write_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="owner@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.dashboard.read", "admin.dashboard.write"],
    )
    return {"Authorization": f"Bearer {token}"}


def _reset_brain_core_state() -> None:
    from app.modules.brain_core.service import brain_core_service

    # Reinitialize singleton service so API contract tests are deterministic.
    brain_core_service.__init__()


def test_brain_health_contract() -> None:
    _reset_brain_core_state()

    resp = client.get("/api/admin/brain/health", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["status"] == "ok"
    assert data["module"] == "brain_core"
    assert "phase" in data


def test_brain_collections_contract() -> None:
    _reset_brain_core_state()

    decisions_resp = client.get("/api/admin/brain/decisions", headers=ADMIN_HEADERS)
    assert decisions_resp.status_code == 200, decisions_resp.text
    decisions = decisions_resp.json()
    assert "total" in decisions
    assert "items" in decisions
    assert isinstance(decisions["items"], list)

    outcomes_resp = client.get("/api/admin/brain/outcomes", headers=ADMIN_HEADERS)
    assert outcomes_resp.status_code == 200, outcomes_resp.text
    outcomes = outcomes_resp.json()
    assert "total" in outcomes
    assert "items" in outcomes
    assert isinstance(outcomes["items"], list)


def test_brain_policy_read_update_contract() -> None:
    _reset_brain_core_state()

    tenant_id = 101

    get_resp = client.get(f"/api/admin/brain/policy/{tenant_id}", headers=ADMIN_HEADERS)
    assert get_resp.status_code == 200, get_resp.text
    initial = get_resp.json()
    assert initial["tenant_id"] == tenant_id
    assert "autonomy_level" in initial
    assert "require_approval_for_critical" in initial
    assert "default_approval_role" in initial
    assert "enable_ai_reasoning" in initial

    put_resp = client.put(
        f"/api/admin/brain/policy/{tenant_id}",
        headers=_brain_write_headers(),
        json={
            "autonomy_level": 3,
            "require_approval_for_critical": True,
            "default_approval_role": "dean_office",
            "enable_ai_reasoning": True,
            "actor": "admin@brain",
        },
    )
    assert put_resp.status_code == 200, put_resp.text
    updated = put_resp.json()

    assert updated["status"] == "updated"
    assert updated["tenant_id"] == tenant_id
    assert updated["profile"]["autonomy_level"] == 3
    assert updated["profile"]["enable_ai_reasoning"] is True


def test_brain_explanation_endpoint_contract() -> None:
    _reset_brain_core_state()

    simulate_resp = client.post(
        "/api/admin/brain/simulate/student-risk",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "student_id": "STU-101",
            "attendance_rate": 0.55,
            "grade_trend": "declining",
            "advisor_id": "ADV-101",
            "faculty_id": "FAC-101",
        },
    )
    assert simulate_resp.status_code == 200, simulate_resp.text
    decision_id = simulate_resp.json()["decision"]["decision_id"]

    explanation_resp = client.get(
        f"/api/admin/brain/explanations/{decision_id}",
        headers=ADMIN_HEADERS,
    )
    assert explanation_resp.status_code == 200, explanation_resp.text
    explanation = explanation_resp.json()

    assert "summary" in explanation
    assert "factors" in explanation
    assert "policy_notes" in explanation
    assert "expected_outcome" in explanation
    assert "knowledge_items" in explanation
    assert isinstance(explanation["factors"], list)
    assert isinstance(explanation["knowledge_items"], list)


def test_brain_metrics_and_traces_contract() -> None:
    _reset_brain_core_state()

    metrics_resp = client.get("/api/admin/brain/metrics", headers=ADMIN_HEADERS)
    assert metrics_resp.status_code == 200, metrics_resp.text
    metrics = metrics_resp.json()
    assert "counters" in metrics
    assert "latency_ms" in metrics
    assert "traces_total" in metrics

    traces_resp = client.get("/api/admin/brain/traces?limit=10", headers=ADMIN_HEADERS)
    assert traces_resp.status_code == 200, traces_resp.text
    traces = traces_resp.json()
    assert "total" in traces
    assert "items" in traces
    assert isinstance(traces["items"], list)


def test_brain_dispatch_outcome_contract() -> None:
    _reset_brain_core_state()

    simulate_resp = client.post(
        "/api/admin/brain/simulate/student-risk",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "student_id": "STU-DISPATCH-101",
            "attendance_rate": 0.3,
            "grade_trend": "declining",
            "advisor_id": "ADV-DISPATCH-101",
            "faculty_id": "FAC-DISPATCH-101",
        },
    )
    assert simulate_resp.status_code == 200, simulate_resp.text
    decision_id = simulate_resp.json()["decision"]["decision_id"]

    approve_resp = client.post(
        f"/api/admin/brain/decisions/{decision_id}/approve",
        headers=_brain_write_headers(),
        json={"actor": "dean@brain"},
    )
    assert approve_resp.status_code == 200, approve_resp.text

    snapshot_resp = client.get("/api/admin/brain/dispatch/snapshot", headers=ADMIN_HEADERS)
    assert snapshot_resp.status_code == 200, snapshot_resp.text
    workflow_cases = snapshot_resp.json()["workflow_cases"]
    assert len(workflow_cases) >= 1
    case_id = workflow_cases[0]["case_id"]

    outcome_resp = client.post(
        f"/api/admin/brain/dispatch/workflow-cases/{case_id}/outcome",
        headers=_brain_write_headers(),
        json={
            "actor": "ops@brain",
            "outcome_type": "completed",
            "effectiveness": "positive",
            "notes": "closed_from_contract_test",
        },
    )
    assert outcome_resp.status_code == 200, outcome_resp.text
    outcome_data = outcome_resp.json()
    assert outcome_data["status"] == "recorded"
    assert outcome_data["decision"]["decision_id"] == decision_id
    assert outcome_data["case"]["status"] == "resolved"

    metrics_resp = client.get("/api/admin/brain/learning/metrics", headers=ADMIN_HEADERS)
    assert metrics_resp.status_code == 200, metrics_resp.text
    metrics = metrics_resp.json()
    assert metrics["total_outcomes"] == 1
    assert metrics["positive"] == 1


def test_brain_research_simulation_contract() -> None:
    _reset_brain_core_state()

    grant_resp = client.post(
        "/api/admin/brain/simulate/research-grant-deadline",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "grant_id": "GRANT-101",
            "research_project_id": "RP-101",
            "days_to_deadline": 12,
        },
    )
    assert grant_resp.status_code == 200, grant_resp.text
    grant_data = grant_resp.json()
    assert grant_data["status"] == "processed"
    assert grant_data["decision"]["decision_type"] == "preventive"
    assert grant_data["decision"]["priority"] == "high"

    publication_resp = client.post(
        "/api/admin/brain/simulate/research-publication-stagnant",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "publication_id": "PUB-101",
            "research_project_id": "RP-101",
            "days_without_progress": 30,
        },
    )
    assert publication_resp.status_code == 200, publication_resp.text
    publication_data = publication_resp.json()
    assert publication_data["status"] == "processed"
    assert publication_data["decision"]["decision_type"] == "preventive"
    assert publication_data["decision"]["priority"] == "medium"


def test_brain_research_advanced_intelligence_simulation_contract() -> None:
    _reset_brain_core_state()

    pipeline_resp = client.post(
        "/api/admin/brain/simulate/research-grant-pipeline-risk",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "grant_id": "GRANT-PIPE-101",
            "research_project_id": "RP-PIPE-101",
            "pipeline_risk_score": 0.84,
            "delayed_milestones": 2,
        },
    )
    assert pipeline_resp.status_code == 200, pipeline_resp.text
    pipeline_data = pipeline_resp.json()
    assert pipeline_data["status"] == "processed"
    assert pipeline_data["decision"]["decision_type"] == "preventive"
    assert pipeline_data["decision"]["priority"] == "high"

    utilization_resp = client.post(
        "/api/admin/brain/simulate/research-lab-utilization-low",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "lab_code": "LAB-101",
            "research_project_id": "RP-LAB-101",
            "utilization_rate": 0.58,
            "idle_days": 15,
        },
    )
    assert utilization_resp.status_code == 200, utilization_resp.text
    utilization_data = utilization_resp.json()
    assert utilization_data["status"] == "processed"
    assert utilization_data["decision"]["decision_type"] == "preventive"
    assert utilization_data["decision"]["priority"] == "medium"


def test_brain_operations_simulation_contract() -> None:
    _reset_brain_core_state()

    facility_resp = client.post(
        "/api/admin/brain/simulate/facility-issue",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "facility_code": "BLDG-A-HVAC",
            "issue_type": "hvac_failure",
            "severity": "high",
        },
    )
    assert facility_resp.status_code == 200, facility_resp.text
    facility_data = facility_resp.json()
    assert facility_data["status"] == "processed"
    assert facility_data["decision"]["decision_type"] == "operational"
    assert facility_data["decision"]["priority"] == "high"

    cleaning_resp = client.post(
        "/api/admin/brain/simulate/cleaning-service-missed",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "room_code": "ROOM-101",
            "building_code": "BLDG-A",
            "missed_count": 1,
        },
    )
    assert cleaning_resp.status_code == 200, cleaning_resp.text
    cleaning_data = cleaning_resp.json()
    assert cleaning_data["status"] == "processed"
    assert cleaning_data["decision"]["decision_type"] == "operational"
    assert cleaning_data["decision"]["priority"] == "medium"


def test_brain_operations_advanced_intelligence_simulation_contract() -> None:
    _reset_brain_core_state()

    maintenance_resp = client.post(
        "/api/admin/brain/simulate/maintenance-predicted-due",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "asset_code": "MA-101",
            "facility_code": "BLDG-A-HVAC",
            "asset_type": "hvac",
            "days_since_maintenance": 110,
            "expected_service_interval_days": 90,
            "health_score": 24,
        },
    )
    assert maintenance_resp.status_code == 200, maintenance_resp.text
    maintenance_data = maintenance_resp.json()
    assert maintenance_data["status"] == "processed"
    assert maintenance_data["decision"]["decision_type"] == "operational"
    assert maintenance_data["decision"]["priority"] == "high"

    utility_resp = client.post(
        "/api/admin/brain/simulate/utilities-spike",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "meter_code": "MTR-101",
            "building_code": "BLDG-A",
            "utility_type": "electricity",
            "usage_value": 135,
            "baseline_value": 100,
            "spike_ratio": 1.35,
            "affected_buildings": 1,
        },
    )
    assert utility_resp.status_code == 200, utility_resp.text
    utility_data = utility_resp.json()
    assert utility_data["status"] == "processed"
    assert utility_data["decision"]["decision_type"] == "operational"
    assert utility_data["decision"]["priority"] == "medium"


def test_brain_procurement_simulation_contract() -> None:
    _reset_brain_core_state()

    policy_resp = client.put(
        "/api/admin/brain/policy/101",
        headers=_brain_write_headers(),
        json={
            "autonomy_level": 4,
            "require_approval_for_critical": True,
            "default_approval_role": "procurement_lead",
            "enable_ai_reasoning": False,
            "actor": "admin@brain",
        },
    )
    assert policy_resp.status_code == 200, policy_resp.text

    variance_resp = client.post(
        "/api/admin/brain/simulate/budget-variance",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "budget_code": "BUD-101",
            "variance_amount": 28000,
            "variance_ratio": 0.18,
            "vendor_code": "VEN-101",
            "contract_code": "CON-101",
            "asset_code": "AST-101",
        },
    )
    assert variance_resp.status_code == 200, variance_resp.text
    variance_data = variance_resp.json()
    assert variance_data["status"] == "processed"
    assert variance_data["decision"]["decision_type"] == "procurement"
    assert variance_data["decision"]["priority"] == "high"


def test_brain_procurement_vendor_intelligence_simulation_contract() -> None:
    _reset_brain_core_state()

    vendor_resp = client.post(
        "/api/admin/brain/simulate/vendor-sla-degraded",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "vendor_code": "VEN-INTEL-101",
            "sla_breach_rate": 0.21,
            "on_time_delivery_rate": 0.74,
        },
    )
    assert vendor_resp.status_code == 200, vendor_resp.text
    vendor_data = vendor_resp.json()
    assert vendor_data["status"] == "processed"
    assert vendor_data["decision"]["decision_type"] == "procurement"
    assert vendor_data["decision"]["priority"] == "high"

    contract_resp = client.post(
        "/api/admin/brain/simulate/contract-risk-high",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "contract_code": "CON-INTEL-101",
            "vendor_code": "VEN-INTEL-101",
            "risk_score": 0.73,
            "sla_target_met": True,
        },
    )
    assert contract_resp.status_code == 200, contract_resp.text
    contract_data = contract_resp.json()
    assert contract_data["status"] == "processed"
    assert contract_data["decision"]["decision_type"] == "procurement"
    assert contract_data["decision"]["priority"] == "medium"


def test_brain_supply_forecast_simulation_contract() -> None:
    _reset_brain_core_state()

    policy_resp = client.put(
        "/api/admin/brain/policy/101",
        headers=_brain_write_headers(),
        json={
            "autonomy_level": 4,
            "require_approval_for_critical": True,
            "default_approval_role": "ops_manager",
            "enable_ai_reasoning": False,
            "actor": "admin@brain",
        },
    )
    assert policy_resp.status_code == 200, policy_resp.text

    supply_resp = client.post(
        "/api/admin/brain/simulate/supply-low",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "stock_item_id": "ITEM-201",
            "stock_level": 16,
            "threshold": 10,
            "projected_daily_usage": 3,
            "lead_time_days": 6,
            "auto_reorder": True,
        },
    )
    assert supply_resp.status_code == 200, supply_resp.text
    supply_data = supply_resp.json()
    assert supply_data["status"] == "processed"
    assert supply_data["decision"]["decision_type"] == "operational"
    assert supply_data["decision"]["priority"] == "high"


def test_brain_what_if_simulation_contract() -> None:
    _reset_brain_core_state()

    resp = client.post(
        "/api/admin/brain/simulate/what-if",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "event_type": "research.grant_pipeline.at_risk",
            "subject": {},
            "payload": {
                "grant_id": "GRANT-WHATIF-101",
                "research_project_id": "RP-WHATIF-101",
                "pipeline_risk_score": 0.86,
                "delayed_milestones": 2,
                "source_entity_type": "grant_pipeline",
                "source_entity_id": "GRANT-WHATIF-101",
            },
            "forecast_horizon_days": 45,
            "simulation_label": "grant remediation what-if",
            "policy_override": {
                "autonomy_level": 4,
                "require_approval_for_critical": True,
                "default_approval_role": "research_director",
                "enable_ai_reasoning": False,
            },
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "simulated"
    assert data["decision"]["decision_type"] == "preventive"
    assert data["decision"]["status"] == "simulated"
    assert data["context"]["knowledge"]["retrieved"] >= 1
    assert data["forecast"]["horizon_days"] == 45
    assert data["forecast"]["expected_action_count"] >= 1
    assert data["dispatch_results"] == []


def test_brain_student_life_simulation_contract() -> None:
    _reset_brain_core_state()

    wellbeing_resp = client.post(
        "/api/admin/brain/simulate/student-life-wellbeing",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "student_id": "STU-501",
            "wellbeing_score": 25,
            "concern_type": "burnout",
        },
    )
    assert wellbeing_resp.status_code == 200, wellbeing_resp.text
    wellbeing_data = wellbeing_resp.json()
    assert wellbeing_data["status"] == "processed"
    assert wellbeing_data["decision"]["decision_type"] == "risk"
    assert wellbeing_data["decision"]["priority"] == "high"

    disciplinary_resp = client.post(
        "/api/admin/brain/simulate/student-life-disciplinary",
        headers=_brain_write_headers(),
        json={
            "tenant_id": 101,
            "student_id": "STU-501",
            "incident_type": "code_of_conduct",
            "incident_severity": "medium",
            "incident_count_30d": 1,
        },
    )
    assert disciplinary_resp.status_code == 200, disciplinary_resp.text
    disciplinary_data = disciplinary_resp.json()
    assert disciplinary_data["status"] == "processed"
    assert disciplinary_data["decision"]["decision_type"] == "risk"
    assert disciplinary_data["decision"]["priority"] == "medium"
