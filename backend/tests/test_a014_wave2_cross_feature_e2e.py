"""A-014.7 Wave 2 Cross-Feature E2E Tests.

Validates end-to-end signal→brain→KPI pipelines across all 5 Wave 2 feature
domains, plus cross-tenant isolation.  Each test exercises the full stack:

  1. Emit domain event(s) via event_ingestion_service.record_event()
  2. Process matching signal(s) via BrainCoreService.process_signal()
  3. Refresh KPI via kpi_service.refresh_tenant_metrics()
  4. Assert KPI card values via GET /api/analytics/kpis

These tests complement the per-feature unit tests (A-014.1 – A-014.5) and the
KPI-computation tests (A-014.6).  They do NOT test approval workflows in depth
(covered by A-014.5); they verify that the full pipeline produces the expected
KPI values.
"""
from __future__ import annotations

from uuid import uuid4

from tests.conftest import client

from app.modules.auth.token_service import create_access_token
from app.modules.brain_core.service import BrainCoreService
from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork


# ---------------------------------------------------------------------------
# Helpers (reuse same pattern as A-014.6 KPI tests)
# ---------------------------------------------------------------------------

def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(tenant["id"])


def _analytics_read_headers(*, tenant_id: int) -> dict[str, str]:
    token = create_access_token(
        user_id=f"kpi.viewer.{tenant_id}@example.com",
        roles=["student"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=["analytics.data.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def _emit_event(*, tenant_id: int, event_type: str, count: int = 1) -> None:
    for idx in range(count):
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type=event_type,
            payload={"seq": idx + 1, "source": "test-a0147"},
        )


def _process_signal(*, tenant_id: int, event_type: str, student_id: str, extra_payload: dict | None = None) -> dict:
    payload: dict = {
        "student_id": student_id,
        "source": "test-a0147",
        **(extra_payload or {}),
    }
    signal = {
        "signal_id": f"sig-{uuid4().hex[:8]}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-{uuid4().hex[:8]}",
        "event_type": event_type,
        "subject": {"student_id": student_id},
        "payload": payload,
        "metadata": {},
    }
    return BrainCoreService().process_signal(signal)


def _refresh_metrics(*, tenant_id: int) -> None:
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)


def _cards_by_key(body: dict) -> dict[str, dict]:
    return {str(item["key"]): item for item in body["kpis"]}


def _get_kpi_cards(*, tenant_id: int) -> dict[str, dict]:
    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    return _cards_by_key(response.json())


# ---------------------------------------------------------------------------
# E2E tests
# ---------------------------------------------------------------------------

def test_wave2_grade_decline_signal_to_intervention_to_kpi(reset_shared_state) -> None:
    """Full pipeline: grade_risk event + brain signal → KPI counts increment.

    Flow:
      - Emit academic.grade_risk.detected (KPI: grade_decline_risk_count +2)
      - Process grade_risk signal through brain (intervention dispatched)
      - Emit interventions.case.created (KPI: grade_intervention_cases_count +1)
      - Refresh metrics → verify both KPI cards show correct values
    """
    tenant_id = _create_tenant("e2e-grade")

    # KPI event side
    _emit_event(tenant_id=tenant_id, event_type="academic.grade_risk.detected", count=2)
    _emit_event(tenant_id=tenant_id, event_type="interventions.case.created", count=1)

    # Brain signal side
    result = _process_signal(
        tenant_id=tenant_id,
        event_type="academic.grade_risk.detected",
        student_id="STU-E2E-GRADE-1",
        extra_payload={
            "current_grade": 45.0,
            "passing_grade": 50.0,
            "course_id": "CS-101",
            "risk_level": "high",
        },
    )
    assert result["status"] == "processed"
    # grade_risk is intervention → dispatched immediately
    assert result["decision"]["status"] in ("dispatched", "approval_pending")

    _refresh_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)

    assert cards["grade_decline_risk_count"]["value"] == 2
    assert cards["grade_intervention_cases_count"]["value"] == 1


def test_wave2_thesis_delay_signal_to_kpi(reset_shared_state) -> None:
    """Full pipeline: thesis.status_changed event + brain signal → KPI counts.

    Flow:
      - Emit thesis.status_changed (KPI: thesis_completion_risk_count +3)
      - Emit interventions.case.created (KPI: thesis_intervention_cases_count +2)
      - Process thesis brain signal (thesis.status_changed) → dispatched
      - Refresh metrics → verify KPI cards
    """
    tenant_id = _create_tenant("e2e-thesis")

    _emit_event(tenant_id=tenant_id, event_type="thesis.status_changed", count=3)
    _emit_event(tenant_id=tenant_id, event_type="interventions.case.created", count=2)

    result = _process_signal(
        tenant_id=tenant_id,
        event_type="thesis.status_changed",
        student_id="STU-E2E-THESIS-1",
        extra_payload={
            "thesis_id": "THX-E2E-1",
            "to_status": "rejected",
            "from_status": "under_review",
            "days_since_last_milestone": 10,
            "source_entity_type": "thesis",
            "source_entity_id": "THX-E2E-1",
        },
    )
    assert result["status"] == "processed"
    assert result["decision"]["status"] in ("dispatched", "approval_pending")

    _refresh_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)

    assert cards["thesis_completion_risk_count"]["value"] == 3
    assert cards["thesis_intervention_cases_count"]["value"] == 2


def test_wave2_attendance_recovery_signal_to_kpi(reset_shared_state) -> None:
    """Full pipeline: attendance_risk event + brain signal → recovery KPI.

    Flow:
      - Emit academic.attendance_risk.detected (KPI: attendance_recovery_actions_count +4)
      - Process attendance_risk brain signal → dispatched
      - Refresh metrics → verify KPI card
    """
    tenant_id = _create_tenant("e2e-attend")

    _emit_event(tenant_id=tenant_id, event_type="academic.attendance_risk.detected", count=4)

    result = _process_signal(
        tenant_id=tenant_id,
        event_type="academic.attendance_risk.detected",
        student_id="STU-E2E-ATTEND-1",
        extra_payload={
            "absences": 8,
            "threshold": 5,
            "course_id": "ENG-202",
        },
    )
    assert result["status"] == "processed"
    assert result["decision"]["status"] in ("dispatched", "approval_pending")

    _refresh_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)

    assert cards["attendance_recovery_actions_count"]["value"] == 4


def test_wave2_graduation_risk_signal_to_kpi(reset_shared_state) -> None:
    """Full pipeline: graduation_risk event + brain signal → graduation KPI.

    Flow:
      - Emit degree_progress.graduation_risk.detected (KPI: graduation_risk_students_count +3)
      - Emit interventions.case.created (KPI: degree_progress_intervention_cases_count +1)
      - Process graduation_risk brain signal → approval_pending (risk decision)
      - Approve decision → dispatched
      - Refresh metrics → verify both KPI cards
    """
    tenant_id = _create_tenant("e2e-grad")

    _emit_event(tenant_id=tenant_id, event_type="degree_progress.graduation_risk.detected", count=3)
    _emit_event(tenant_id=tenant_id, event_type="interventions.case.created", count=1)

    result = _process_signal(
        tenant_id=tenant_id,
        event_type="degree_progress.graduation_risk.detected",
        student_id="STU-E2E-GRAD-1",
        extra_payload={
            "student_profile_id": "STU-E2E-GRAD-1",
            "remaining_required_items": 5,
            "credits_earned": 90,
            "minimum_credits": 120,
            "source_entity_type": "student_graduation_progress",
            "source_entity_id": "STU-E2E-GRAD-1",
        },
    )
    assert result["status"] == "processed"
    # graduation risk may require approval or dispatch immediately depending on policy
    assert result["decision"]["status"] in ("dispatched", "approval_pending")

    if result["decision"]["status"] == "approval_pending":
        service = BrainCoreService()
        approved = service.approve_decision(result["decision"]["decision_id"], actor="registrar@tenant")
        assert approved["decision"]["status"] == "dispatched"

    _refresh_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)

    assert cards["graduation_risk_students_count"]["value"] == 3
    assert cards["degree_progress_intervention_cases_count"]["value"] == 1


def test_wave2_scholarship_financial_aid_risk_signal_to_kpi(reset_shared_state) -> None:
    """Full pipeline: scholarship + financial_aid events + brain signals → KPI.

    Flow:
      - Emit scholarship.award.at_risk_detected (KPI: scholarship_risk_cases_count +2)
      - Emit financial_aid.warning.detected (KPI: financial_aid_risk_cases_count +1)
      - Process scholarship brain signal → approval_pending → approve → dispatched
      - Process financial_aid brain signal → approval_pending → approve → dispatched
      - Refresh metrics → verify both KPI cards
    """
    tenant_id = _create_tenant("e2e-finaid")

    _emit_event(tenant_id=tenant_id, event_type="scholarship.award.at_risk_detected", count=2)
    _emit_event(tenant_id=tenant_id, event_type="financial_aid.warning.detected", count=1)

    brain = BrainCoreService()

    # Scholarship signal
    sch_result = _process_signal(
        tenant_id=tenant_id,
        event_type="scholarship.award.at_risk_detected",
        student_id="STU-E2E-SCH-1",
        extra_payload={
            "award_id": "AWD-E2E-1",
            "award_code": "AWD-E2E-1",
            "current_gpa": 1.9,
            "gpa_threshold": 2.5,
            "status": "active",
            "risk_level": "high",
            "reason": "gpa_below_threshold",
            "evidence": {"current_gpa": 1.9, "gpa_threshold": 2.5},
            "source_entity_type": "scholarship_award",
            "source_entity_id": "AWD-E2E-1",
        },
    )
    assert sch_result["status"] == "processed"
    assert sch_result["decision"]["status"] == "approval_pending"
    brain.approve_decision(sch_result["decision"]["decision_id"], actor="aid-office@tenant")

    # Financial aid signal
    fin_result = _process_signal(
        tenant_id=tenant_id,
        event_type="financial_aid.warning.detected",
        student_id="STU-E2E-FIN-1",
        extra_payload={
            "aid_package_id": "AID-E2E-1",
            "aid_type": "grant",
            "warning_reason": "enrollment_dropped",
            "risk_level": "medium",
            "source_entity_type": "financial_aid_package",
            "source_entity_id": "AID-E2E-1",
        },
    )
    assert fin_result["status"] == "processed"
    assert fin_result["decision"]["status"] in ("dispatched", "approval_pending")

    if fin_result["decision"]["status"] == "approval_pending":
        brain.approve_decision(fin_result["decision"]["decision_id"], actor="aid-office@tenant")

    _refresh_metrics(tenant_id=tenant_id)
    cards = _get_kpi_cards(tenant_id=tenant_id)

    assert cards["scholarship_risk_cases_count"]["value"] == 2
    assert cards["financial_aid_risk_cases_count"]["value"] == 1


def test_wave2_cross_tenant_kpi_isolation(reset_shared_state) -> None:
    """Wave 2 KPI cards must be isolated per tenant — no cross-tenant leakage.

    Two tenants each receive different event volumes.  Verifies that Tenant A's
    metrics do not appear in Tenant B's KPI response and vice versa.
    """
    tenant_a = _create_tenant("e2e-iso-a")
    tenant_b = _create_tenant("e2e-iso-b")

    # Tenant A: 5 grade risk events
    _emit_event(tenant_id=tenant_a, event_type="academic.grade_risk.detected", count=5)
    # Tenant B: 2 thesis events
    _emit_event(tenant_id=tenant_b, event_type="thesis.status_changed", count=2)

    _refresh_metrics(tenant_id=tenant_a)
    _refresh_metrics(tenant_id=tenant_b)

    cards_a = _get_kpi_cards(tenant_id=tenant_a)
    cards_b = _get_kpi_cards(tenant_id=tenant_b)

    # Tenant A should see grade_decline_risk_count=5, thesis=0
    assert cards_a["grade_decline_risk_count"]["value"] == 5
    assert cards_a["thesis_completion_risk_count"]["value"] == 0

    # Tenant B should see thesis_completion_risk_count=2, grade=0
    assert cards_b["thesis_completion_risk_count"]["value"] == 2
    assert cards_b["grade_decline_risk_count"]["value"] == 0
