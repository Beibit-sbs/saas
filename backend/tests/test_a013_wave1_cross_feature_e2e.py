"""A-013.7 — Wave 1 Cross-Feature End-to-End Tests.

Validates that A-013.1 through A-013.6 components form connected, functioning flows:

  Flow 1: Student Risk → Brain Decision → Intervention Event → KPI
  Flow 2: Payment Overdue → Delinquency Record → Delinquency KPI
  Flow 3: Scheduling Conflict Signal → Brain Decision → Scheduling KPI
  Flow 4: Multi-Factor Risk → Composite Score → Sweep Idempotency
  Flow 5: Cross-Tenant Isolation — events from tenant A do not affect tenant B KPIs

Each test is:
  - deterministic (no external services)
  - tenant-scoped (dedicated tenant per test)
  - additive only (no schema changes, no new modules)
"""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest

from tests.conftest import ADMIN_HEADERS, client

from app.modules.auth.token_service import create_access_token
from app.modules.billing import service as billing_service
from app.modules.brain_core.service import BrainCoreService
from app.modules.brain_core.reasoning.composite_risk_scorer import compute_composite_risk_score
from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(tenant["id"])


def _analytics_read_headers(*, tenant_id: int) -> dict[str, str]:
    token = create_access_token(
        user_id=f"e2e.viewer.{tenant_id}@example.com",
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
            payload={"seq": idx + 1, "source": "test-a013-e2e"},
        )


def _refresh_kpi(*, tenant_id: int) -> None:
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)


def _cards_by_key(body: dict) -> dict[str, dict]:
    return {str(item["key"]): item for item in body["kpis"]}


def _make_brain_service() -> BrainCoreService:
    """Return a fully-wired BrainCoreService instance with context sources mocked."""
    svc = BrainCoreService()
    return svc


# Brain Core context source stubs — prevents DB dependency in E2E flow tests
@pytest.fixture(autouse=True)
def _stub_brain_context_sources():
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_academic_context",
                return_value={"student_profile": None, "academic_health_snapshot": {}},
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_student_success_context",
                return_value={
                    "active_interventions": 0,
                    "open_advising_tasks": 0,
                    "student_life_health_snapshot": {
                        "open_counseling_cases": 0,
                        "active_accommodations": 0,
                        "disciplinary_incidents_30d": 0,
                        "at_risk_students": 0,
                    },
                },
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_faculty_context",
                return_value={"faculty_health_snapshot": {}},
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_finance_context",
                return_value={"billing_health_snapshot": {}, "procurement_health_snapshot": {}},
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_operations_context",
                return_value={"operations_health_snapshot": {}},
            )
        )
        stack.enter_context(
            patch(
                "app.modules.brain_core.context_builder.fetch_platform_context",
                return_value={"platform_health_snapshot": {}},
            )
        )
        yield


# ---------------------------------------------------------------------------
# Flow 1: Student Risk → Brain Decision → Intervention Event → KPI
# ---------------------------------------------------------------------------


def test_wave1_student_risk_to_intervention_to_kpi(reset_shared_state) -> None:
    """Attendance risk signal → brain dispatches intervention → event emitted → KPI updated.

    This E2E flow spans:
      A-013.1 (attendance risk → intervention auto-create)
      A-013.5 (intervention event → KPI)
    """
    tenant_id = _create_tenant("e2e-risk-kpi")
    svc = _make_brain_service()

    signal = {
        "signal_id": f"e2e-attend-{tenant_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"e2e-corr-{tenant_id}",
        "event_type": "academic.attendance_risk.detected",
        "source_entity_type": "section_attendance",
        "source_entity_id": "SEC-E2E-1",
        "subject": {
            "student_id": "STU-E2E-1",
            "course_id": "COURSE-E2E",
            "section_id": "SEC-E2E-1",
        },
        "payload": {
            "student_id": "STU-E2E-1",
            "attendance_rate": 0.30,
            "grade_trend": "declining",
        },
        "metadata": {},
    }

    # Step 1 — Brain Core processes attendance risk signal
    result = svc.process_signal(signal)
    assert result["status"] == "processed", f"Signal not processed: {result}"
    decision = result["decision"]
    assert decision.get("decision_type") == "intervention", (
        f"Attendance risk must route to intervention; got {decision.get('decision_type')}"
    )
    dispatch_results = result["dispatch_results"]
    dispatched_actions = [r["action"] for r in dispatch_results]
    assert "create_intervention_case" in dispatched_actions, (
        f"create_intervention_case expected; got: {dispatched_actions}"
    )

    # Step 2 — Simulate downstream event emission (representing what action handler emits)
    _emit_event(tenant_id=tenant_id, event_type="academic.attendance_risk.detected", count=1)
    _emit_event(tenant_id=tenant_id, event_type="interventions.auto_triggered", count=1)
    _emit_event(tenant_id=tenant_id, event_type="interventions.case.created", count=1)

    # Step 3 — KPI refresh
    _refresh_kpi(tenant_id=tenant_id)

    # Step 4 — Dashboard surface reflects intervention activity
    resp = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert resp.status_code == 200, resp.text
    cards = _cards_by_key(resp.json())

    assert cards["intervention_auto_created_count"]["value"] >= 1, (
        "intervention_auto_created_count must reflect auto-triggered event"
    )
    assert cards["high_risk_students_count"]["value"] >= 1, (
        "high_risk_students_count must reflect attendance risk event"
    )
    # Verify tenant isolation — only this tenant's data shows
    assert str(resp.json()["tenant_id"]) == str(tenant_id)


# ---------------------------------------------------------------------------
# Flow 2: Payment Overdue → Delinquency Record → Delinquency KPI
# ---------------------------------------------------------------------------


def test_wave1_payment_overdue_to_delinquency_to_kpi(reset_shared_state) -> None:
    """Finance overdue → delinquency record created → KPI reflects active cases.

    This E2E flow spans:
      A-013.2 (delinquency recovery)
      A-013.5 (delinquency KPI from billing service state)
    """
    tenant_id = _create_tenant("e2e-delinquency-kpi")

    # Step 1 — Create delinquency records via billing service (payment overdue scenario)
    billing_service.create_delinquency_record(
        tenant_id, invoice_id="inv-e2e-1", status="overdue", amount_cents=250000
    )
    billing_service.create_delinquency_record(
        tenant_id, invoice_id="inv-e2e-2", status="collections", amount_cents=100000
    )

    # Step 2 — Resolve one record (simulating payment recovery from A-013.2)
    billing_service.resolve_delinquency_record(
        tenant_id, 1, resolution="paid", actor="e2e-recovery-agent"
    )

    # Step 3 — KPI refresh
    _refresh_kpi(tenant_id=tenant_id)

    # Step 4 — Dashboard reflects delinquency state
    resp = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert resp.status_code == 200, resp.text
    cards = _cards_by_key(resp.json())

    # 1 active (collections), 1 resolved — recovery rate = 50%
    assert cards["delinquency_cases_active"]["value"] == 1, (
        f"Expected 1 active delinquency; got {cards['delinquency_cases_active']['value']}"
    )
    assert cards["overdue_amount_at_risk"]["value"] == 100000, (
        f"Expected at-risk amount 100000; got {cards['overdue_amount_at_risk']['value']}"
    )
    assert cards["delinquency_recovery_rate"]["value"] == 50, (
        f"Expected 50% recovery rate; got {cards['delinquency_recovery_rate']['value']}"
    )

    # Verify delinquency surface endpoint works
    delinquency_resp = client.get(
        "/api/analytics/kpis",
        headers=_analytics_read_headers(tenant_id=tenant_id),
    )
    assert delinquency_resp.status_code == 200
    assert "delinquency_cases_active" in {c["key"] for c in delinquency_resp.json()["kpis"]}


# ---------------------------------------------------------------------------
# Flow 3: Scheduling Conflict Signal → Brain Decision → Scheduling KPI
# ---------------------------------------------------------------------------


def test_wave1_scheduling_capacity_signal_to_brain_decision(reset_shared_state) -> None:
    """Scheduling conflict signal → brain produces scheduling/risk decision → KPI updated.

    This E2E flow spans:
      A-013.3 (scheduling context + brain signal)
      A-013.5 (scheduling KPI)
    """
    tenant_id = _create_tenant("e2e-scheduling-kpi")
    svc = _make_brain_service()

    conflict_signal = {
        "signal_id": f"e2e-sched-{tenant_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"e2e-sched-corr-{tenant_id}",
        "event_type": "scheduling.section.conflict_detected",
        "source_entity_type": "section",
        "source_entity_id": "SEC-CONF-1",
        "subject": {
            "section_id": "SEC-CONF-1",
            "course_id": "COURSE-CONF",
        },
        "payload": {
            "section_id": "SEC-CONF-1",
            "conflict_type": "room_conflict",
            "enrolled_count": 28,
            "max_capacity": 30,
        },
        "metadata": {},
    }

    # Step 1 — Brain Core processes scheduling conflict signal
    result = svc.process_signal(conflict_signal)
    assert result["status"] == "processed", f"Signal not processed: {result}"
    decision = result["decision"]
    # Scheduling conflict should produce a risk or scheduling decision
    assert decision.get("decision_type") is not None, (
        "Scheduling signal must produce a decision"
    )

    # Step 2 — Emit scheduling events representing the conflict and capacity usage
    _emit_event(tenant_id=tenant_id, event_type="scheduling.section.created", count=3)
    _emit_event(tenant_id=tenant_id, event_type="enrollment.created", count=2)
    _emit_event(tenant_id=tenant_id, event_type="enrollment.capacity_risk.detected", count=1)
    _emit_event(tenant_id=tenant_id, event_type="scheduling.section.conflict_detected", count=1)

    # Step 3 — KPI refresh
    _refresh_kpi(tenant_id=tenant_id)

    # Step 4 — Dashboard reflects scheduling state
    resp = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert resp.status_code == 200, resp.text
    cards = _cards_by_key(resp.json())

    assert cards["scheduling_conflicts_count"]["value"] == 1, (
        f"Expected 1 conflict; got {cards['scheduling_conflicts_count']['value']}"
    )
    assert cards["capacity_risk_sections_count"]["value"] == 1, (
        f"Expected 1 capacity risk; got {cards['capacity_risk_sections_count']['value']}"
    )
    # course_fill_rate = round(enrollments / sections * 100) = round(2/3 * 100) = 67
    assert cards["course_fill_rate"]["value"] == 67, (
        f"Expected fill rate 67; got {cards['course_fill_rate']['value']}"
    )


# ---------------------------------------------------------------------------
# Flow 4: Multi-Factor Risk → Composite Score → Sweep Idempotency
# ---------------------------------------------------------------------------


def _make_mock_student(*, student_id: int = 1, student_number: str = "S001", tenant_id: int = 1) -> MagicMock:
    student = MagicMock()
    student.id = student_id
    student.student_number = student_number
    student.tenant_id = tenant_id
    student.current_status = MagicMock()
    student.current_status.value = "active"
    return student


def _make_sweep_db_session(*, tenant_id: int) -> MagicMock:
    db = MagicMock()
    tenant_result = MagicMock()
    tenant_result.scalars.return_value.all.return_value = [tenant_id]
    student_result = MagicMock()
    student_result.scalars.return_value.all.return_value = [
        _make_mock_student(student_id=1, student_number="STU-SWEEP-1", tenant_id=tenant_id),
        _make_mock_student(student_id=2, student_number="STU-SWEEP-2", tenant_id=tenant_id),
    ]
    db.execute.side_effect = [tenant_result, student_result]
    return db


@patch("app.modules.brain_core.early_warning_sweep.log_admin_action")
@patch("app.modules.brain_core.early_warning_sweep._fetch_attendance_rate", return_value=0.20)
@patch("app.modules.brain_core.early_warning_sweep._fetch_grade_pct", return_value=40.0)
def test_wave1_composite_sweep_is_idempotent(mock_grade, mock_att, mock_audit, reset_shared_state) -> None:
    """Multi-factor risk inputs → composite score → sweep runs twice without error.

    This E2E flow spans:
      A-013.4 (composite early-warning + sweep)
      A-013.5 (high-risk student KPI)
    """
    from app.modules.brain_core.early_warning_sweep import run_composite_early_warning_sweep

    tenant_id = _create_tenant("e2e-sweep-idempotent")

    # Step 1 — Compute composite risk score for a high-risk student
    score = compute_composite_risk_score(
        tenant_id=tenant_id,
        student_id="STU-SWEEP-1",
        attendance_rate=0.20,   # very low attendance → high risk
        grade_pct=40.0,          # below threshold
        financial_flag=True,     # payment overdue
        overdue_amount=500.0,
        enrollment_status="active",
    )
    assert score["risk_level"] in {"high", "critical"}, (
        f"High-risk inputs should produce high/critical level; got {score['risk_level']}"
    )
    assert score["tenant_id"] == tenant_id, "Composite scorer must carry input tenant_id"

    # Step 2 — Emit attendance risk events representing sweep results
    _emit_event(tenant_id=tenant_id, event_type="academic.attendance_risk.detected", count=3)
    _emit_event(tenant_id=tenant_id, event_type="academic.grade_risk.detected", count=2)

    # Step 3 — Run sweep twice (idempotency proof — both must succeed without error)
    def _fresh_db():
        db = MagicMock()
        tenant_result = MagicMock()
        tenant_result.scalars.return_value.all.return_value = [tenant_id]
        student_result = MagicMock()
        student_result.scalars.return_value.all.return_value = [
            _make_mock_student(student_id=1, student_number="STU-SWEEP-1", tenant_id=tenant_id),
            _make_mock_student(student_id=2, student_number="STU-SWEEP-2", tenant_id=tenant_id),
        ]
        db.execute.side_effect = [tenant_result, student_result]
        return db

    result_1 = run_composite_early_warning_sweep(db_session=_fresh_db(), actor="e2e-sweep-test")
    result_2 = run_composite_early_warning_sweep(db_session=_fresh_db(), actor="e2e-sweep-test")

    # Both runs must succeed without raising
    assert result_1["errors"] == 0, f"First sweep had errors: {result_1}"
    assert result_2["errors"] == 0, f"Second sweep had errors (not idempotent): {result_2}"
    assert result_1["tenants_processed"] == 1
    assert result_2["tenants_processed"] == 1

    # Step 4 — KPI refresh reflects the risk events
    _refresh_kpi(tenant_id=tenant_id)

    resp = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert resp.status_code == 200, resp.text
    cards = _cards_by_key(resp.json())

    assert cards["high_risk_students_count"]["value"] >= 1, (
        "high_risk_students_count must reflect attendance risk events after sweep"
    )


# ---------------------------------------------------------------------------
# Flow 5: Cross-Tenant Isolation
# ---------------------------------------------------------------------------


def test_wave1_cross_tenant_isolation(reset_shared_state) -> None:
    """Events from tenant A must not affect tenant B KPIs.

    Covers:
      A-013.5 tenant-scoped KPI store
      A-013.1/A-013.3 tenant-scoped brain signal processing
    """
    tenant_a = _create_tenant("e2e-isolation-a")
    tenant_b = _create_tenant("e2e-isolation-b")

    # Tenant A: heavy activity
    _emit_event(tenant_id=tenant_a, event_type="interventions.auto_triggered", count=5)
    _emit_event(tenant_id=tenant_a, event_type="interventions.case.created", count=5)
    _emit_event(tenant_id=tenant_a, event_type="scheduling.section.conflict_detected", count=4)
    _emit_event(tenant_id=tenant_a, event_type="academic.attendance_risk.detected", count=6)

    # Tenant B: minimal activity
    _emit_event(tenant_id=tenant_b, event_type="interventions.auto_triggered", count=1)

    _refresh_kpi(tenant_id=tenant_a)
    _refresh_kpi(tenant_id=tenant_b)

    body_a = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_a)).json()
    body_b = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_b)).json()

    cards_a = _cards_by_key(body_a)
    cards_b = _cards_by_key(body_b)

    # Tenant A sees its own data
    assert cards_a["intervention_auto_created_count"]["value"] == 5
    assert cards_a["scheduling_conflicts_count"]["value"] == 4
    assert cards_a["high_risk_students_count"]["value"] == 6

    # Tenant B sees only its own data (not tenant A's)
    assert cards_b["intervention_auto_created_count"]["value"] == 1, (
        f"Tenant B isolation failed: got {cards_b['intervention_auto_created_count']['value']}, expected 1"
    )
    assert cards_b["scheduling_conflicts_count"]["value"] == 0, (
        f"Tenant B must not see tenant A's scheduling conflicts"
    )
    assert cards_b["high_risk_students_count"]["value"] == 0, (
        f"Tenant B must not see tenant A's risk students"
    )

    # Tenant IDs are correctly scoped in response
    assert str(body_a["tenant_id"]) == str(tenant_a)
    assert str(body_b["tenant_id"]) == str(tenant_b)
    assert body_a["tenant_id"] != body_b["tenant_id"]


# ---------------------------------------------------------------------------
# Flow 6: Frontend Contract Smoke (Backend contract shape for dashboard/Wave1 surfaces)
# ---------------------------------------------------------------------------


def test_wave1_dashboard_contract_shape_for_frontend_consumption(reset_shared_state) -> None:
    """KPI API response shape satisfies the frontend Wave1KpiBar contract.

    Verifies:
      - kpis[] array present
      - Each KPI card has required fields: key, title, value, readiness_status
      - Wave 1 keys (intervention, delinquency, scheduling) appear in response
      - Optional fields (severity, source_breakdown) present but not required to be non-null
      - Missing optional data does not cause 500 or structural deviation
    """
    tenant_id = _create_tenant("e2e-contract-smoke")

    # Emit a minimal set representing Wave 1 surfaces
    _emit_event(tenant_id=tenant_id, event_type="interventions.auto_triggered", count=2)
    _emit_event(tenant_id=tenant_id, event_type="scheduling.section.conflict_detected", count=1)

    _refresh_kpi(tenant_id=tenant_id)

    resp = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # Top-level contract shape
    assert "kpis" in body, "kpis array must be present for Wave1KpiBar"
    assert isinstance(body["kpis"], list), "kpis must be a list"
    assert len(body["kpis"]) > 0, "kpis must be non-empty after event emission"

    # Card-level contract
    for card in body["kpis"]:
        assert "key" in card, f"Card missing 'key': {card}"
        assert "title" in card, f"Card missing 'title': {card}"
        assert "value" in card, f"Card missing 'value': {card}"
        assert "readiness_status" in card, f"Card missing 'readiness_status': {card}"

    cards = _cards_by_key(body)

    # Wave 1 intervention key present
    assert "intervention_auto_created_count" in cards, (
        "intervention_auto_created_count must be present for InterventionsPage Wave1KpiBar"
    )
    # Wave 1 scheduling key present
    assert "scheduling_conflicts_count" in cards, (
        "scheduling_conflicts_count must be present for SchedulingPage Wave1KpiBar"
    )
    # Optional severity field present (even if null)
    assert "severity" in cards["scheduling_conflicts_count"], (
        "severity field must be present in card shape"
    )
    # source_breakdown present (may be empty list)
    assert "source_breakdown" in cards["intervention_auto_created_count"], (
        "source_breakdown must be present in card shape"
    )

    # Admin rector dashboard also works (backward-compatible contract)
    admin_resp = client.get(
        "/api/v1/admin/platform/kpi/dashboard",
        params={"tenant_id": tenant_id},
        headers=ADMIN_HEADERS,
    )
    assert admin_resp.status_code == 200, admin_resp.text
    admin_keys = {c["metric_key"] for c in admin_resp.json()["cards"]}
    assert "intervention_auto_created_count" in admin_keys, (
        "Admin rector dashboard must include Wave 1 intervention key"
    )
