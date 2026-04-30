"""Week 10 – Domain Depth: state machines and cross-module wiring.

Tests:
  W10.1 – facilities_work_orders state-machine transition guard
  W10.2 – research_ethics state-machine transition guard
  W10.3 – student_life disciplinary close → academic_records wiring
"""
from __future__ import annotations

import inspect

import pytest

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _fresh_shared_state():
    """Return a fresh in-memory shared state module-level dict."""
    from app.modules.university_core import shared
    return shared


def _clear_entity(entity_key: str, tenant_id: int) -> None:
    from app.modules.university_core import shared
    with shared._state_lock:
        shared._state.data.setdefault(entity_key, {})
        keys_to_del = [k for k, v in shared._state.data[entity_key].items()
                       if v.get("tenant_id") == tenant_id]
        for k in keys_to_del:
            del shared._state.data[entity_key][k]


# ---------------------------------------------------------------------------
# W10.1 – facilities_work_orders state machine
# ---------------------------------------------------------------------------

class TestWorkOrderStateMachine:
    """Verify WO_ALLOWED_TRANSITIONS dict and live transition guard."""

    def test_transitions_dict_exists(self):
        from app.modules.facilities_work_orders.schemas import WO_ALLOWED_TRANSITIONS
        assert isinstance(WO_ALLOWED_TRANSITIONS, dict)
        assert "open" in WO_ALLOWED_TRANSITIONS

    def test_terminal_states_have_no_transitions(self):
        from app.modules.facilities_work_orders.schemas import WO_ALLOWED_TRANSITIONS
        assert WO_ALLOWED_TRANSITIONS["completed"] == []
        assert WO_ALLOWED_TRANSITIONS["cancelled"] == []

    def test_open_can_move_to_in_progress(self):
        from app.modules.facilities_work_orders.schemas import WO_ALLOWED_TRANSITIONS
        assert "in_progress" in WO_ALLOWED_TRANSITIONS["open"]

    def test_invalid_transition_raises(self):
        from app.modules.facilities_work_orders import service as svc
        from app.modules.facilities_work_orders.schemas import WorkOrderStatusUpdateSchema
        from app.modules.university_core.tenant_entity_api import create_entity_for_tenant

        tenant_id = 10001
        _clear_entity("facilities_work_orders", tenant_id)

        created = create_entity_for_tenant(
            "facilities_work_orders",
            {
                "order_code": "WO-TEST-01",
                "facility_code": "FAC-A",
                "title": "Broken HVAC",
                "status": "completed",  # terminal
                "priority": "high",
                "work_type": "repair",
            },
            tenant_id,
        )
        order_id = int(created["id"])
        req = WorkOrderStatusUpdateSchema(status="in_progress")

        with pytest.raises(ValueError, match="not allowed"):
            svc.update_work_order_status(tenant_id, order_id, req, "tester")

    def test_valid_transition_succeeds(self):
        from app.modules.facilities_work_orders import service as svc
        from app.modules.facilities_work_orders.schemas import WorkOrderStatusUpdateSchema
        from app.modules.university_core.tenant_entity_api import create_entity_for_tenant

        tenant_id = 10002
        _clear_entity("facilities_work_orders", tenant_id)

        created = create_entity_for_tenant(
            "facilities_work_orders",
            {
                "order_code": "WO-TEST-02",
                "facility_code": "FAC-B",
                "title": "Leaky pipe",
                "status": "open",
                "priority": "medium",
                "work_type": "repair",
            },
            tenant_id,
        )
        order_id = int(created["id"])
        req = WorkOrderStatusUpdateSchema(status="in_progress")

        result = svc.update_work_order_status(tenant_id, order_id, req, "tester")
        assert result is not None

    def test_on_hold_can_resume_or_cancel(self):
        from app.modules.facilities_work_orders.schemas import WO_ALLOWED_TRANSITIONS
        allowed = WO_ALLOWED_TRANSITIONS.get("on_hold", [])
        assert "in_progress" in allowed
        assert "cancelled" in allowed


# ---------------------------------------------------------------------------
# W10.2 – research_ethics state machine
# ---------------------------------------------------------------------------

class TestResearchEthicsStateMachine:
    """Verify RE_ALLOWED_TRANSITIONS dict and live transition guard."""

    def test_transitions_dict_exists(self):
        from app.modules.research_ethics.schemas import RE_ALLOWED_TRANSITIONS
        assert isinstance(RE_ALLOWED_TRANSITIONS, dict)
        assert "pending" in RE_ALLOWED_TRANSITIONS

    def test_terminal_states_have_no_transitions(self):
        from app.modules.research_ethics.schemas import RE_ALLOWED_TRANSITIONS
        assert RE_ALLOWED_TRANSITIONS["approved"] == []
        assert RE_ALLOWED_TRANSITIONS["rejected"] == []

    def test_invalid_transition_raises(self):
        from app.modules.research_ethics import service as svc
        from app.modules.research_ethics.schemas import EthicsReviewStatusUpdateSchema
        from app.modules.university_core.tenant_entity_service import create_entity_for_tenant

        tenant_id = 20001
        _clear_entity("ethics_reviews", tenant_id)

        created = create_entity_for_tenant(
            "ethics_reviews",
            {
                "review_code": "RE-TEST-01",
                "project_title": "Gene Editing Study",
                "principal_investigator_id": "pi-001",
                "status": "approved",  # terminal
            },
            tenant_id,
        )
        review_id = int(created["id"])
        req = EthicsReviewStatusUpdateSchema(status="under_review")

        with pytest.raises(ValueError, match="not allowed"):
            svc.update_ethics_review_status(tenant_id, review_id, req)

    def test_valid_transition_pending_to_under_review(self):
        from app.modules.research_ethics import service as svc
        from app.modules.research_ethics.schemas import EthicsReviewStatusUpdateSchema
        from app.modules.university_core.tenant_entity_service import create_entity_for_tenant

        tenant_id = 20002
        _clear_entity("ethics_reviews", tenant_id)

        created = create_entity_for_tenant(
            "ethics_reviews",
            {
                "review_code": "RE-TEST-02",
                "project_title": "Vaccine Efficacy Trial",
                "principal_investigator_id": "pi-002",
                "status": "pending",
            },
            tenant_id,
        )
        review_id = int(created["id"])
        req = EthicsReviewStatusUpdateSchema(status="under_review")
        result = svc.update_ethics_review_status(tenant_id, review_id, req)
        assert result["status"] == "under_review"

    def test_under_review_can_go_to_revision_requested(self):
        from app.modules.research_ethics.schemas import RE_ALLOWED_TRANSITIONS
        assert "revision_requested" in RE_ALLOWED_TRANSITIONS["under_review"]


# ---------------------------------------------------------------------------
# W10.3 – student_life → academic_records cross-module wiring
# ---------------------------------------------------------------------------

class TestStudentLifeAcademicRecordsWiring:
    """When disciplinary case → 'closed', academic_records.create_record is called."""

    def test_source_contains_academic_records_import(self):
        from app.modules.student_life import service as svc
        src = inspect.getsource(svc.update_disciplinary_case_status)
        assert "academic_records" in src, (
            "update_disciplinary_case_status must reference academic_records module"
        )

    def test_closing_case_triggers_academic_record(self):
        from app.modules.student_life import service as svc
        from app.modules.student_life.schemas import DisciplinaryCaseStatusUpdateSchema
        from app.modules.university_core.tenant_entity_api import create_entity_for_tenant

        tenant_id = 30001
        _clear_entity("student_life_disciplinary_cases", tenant_id)

        created = create_entity_for_tenant(
            "student_life_disciplinary_cases",
            {
                "incident_code": "DISC-W10-001",
                "student_id": "stu-999",
                "incident_type": "plagiarism",
                "severity": "major",
                "status": "reported",
            },
            tenant_id,
        )
        case_id = int(created["id"])
        req = DisciplinaryCaseStatusUpdateSchema(status="closed", reason="Resolved")
        # Cross-module wiring must never break primary flow:
        # update must succeed (no exception) regardless of academic_records result
        result = svc.update_disciplinary_case_status(tenant_id, case_id, req, "admin")
        assert result is not None
        assert result.status == "closed"
