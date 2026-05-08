"""A-019.2: Visitor Management Maturity Completion tests.

Verifies that visitor_management reaches Level 5 readiness:
  - Full visitor lifecycle FSM: REQUESTED → APPROVED/REJECTED/CANCELLED/EXPIRED
                                 APPROVED  → CHECKED_IN / CANCELLED / EXPIRED
                                 CHECKED_IN → CHECKED_OUT
  - Invalid transitions rejected deterministically
  - Missing tenant_id / required fields fail closed
  - Cross-tenant access blocked
  - Expected events emitted (visitor.* namespace)
  - Unauthorized attempt creates evidence only — no auto-ban / hardware action
  - KPI counters: visitor_visits_completed_count + visitor_visits_cancelled_count
  - Audit evidence fields present in unauthorized attempt record
  - Non-destructive policy confirmed (no hardware/physical/auto-ban side effects)
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork
from app.platform.events.publisher import EventPublisher
import app.modules.visitor_management.service as visitor_svc
from app.platform.event_ingestion.types import VALID_EVENT_TYPES


# ─── helpers ──────────────────────────────────────────────────────────────────


def _create_tenant(prefix: str = "vm") -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(tenant["id"])


def _register(tenant_id: int, **kw: object) -> dict:
    defaults = dict(name="Test Visitor", host_id="host-01", visit_date="2026-05-08")
    defaults.update(kw)
    return visitor_svc.register_visitor(tenant_id, **defaults)  # type: ignore[arg-type]


def _emit(*, tenant_id: int, event_type: str, count: int = 1) -> None:
    for i in range(count):
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type=event_type,
            payload={"idx": i, "source": "test-a0192"},
        )


# ─── Test 1: create visitor request → REQUESTED ───────────────────────────────


def test_create_visitor_request_produces_requested_status(reset_shared_state) -> None:
    tenant_id = _create_tenant("t1")
    result = _register(tenant_id)
    assert result["status"] == "REQUESTED"
    assert "visit_id" in result


# ─── Test 2: approve request → APPROVED ───────────────────────────────────────


def test_approve_visit_transitions_to_approved(reset_shared_state) -> None:
    tenant_id = _create_tenant("t2")
    visit_id = _register(tenant_id)["visit_id"]
    result = visitor_svc.approve_visit(tenant_id, visit_id=visit_id)
    assert result["status"] == "APPROVED"
    assert result["visit_id"] == visit_id


# ─── Test 3: reject request → REJECTED ────────────────────────────────────────


def test_reject_visit_transitions_to_rejected(reset_shared_state) -> None:
    tenant_id = _create_tenant("t3")
    visit_id = _register(tenant_id)["visit_id"]
    result = visitor_svc.reject_visit(tenant_id, visit_id=visit_id, reason="policy")
    assert result["status"] == "REJECTED"


# ─── Test 4: check-in approved visitor → CHECKED_IN ──────────────────────────


def test_check_in_approved_visitor(reset_shared_state) -> None:
    tenant_id = _create_tenant("t4")
    visit_id = _register(tenant_id)["visit_id"]
    visitor_svc.approve_visit(tenant_id, visit_id=visit_id)
    result = visitor_svc.check_in_visitor(tenant_id, visit_id=visit_id, badge_number="B-001")
    assert result["status"] == "CHECKED_IN"
    assert result["badge"] == "B-001"


# ─── Test 5: check-out checked-in visitor → CHECKED_OUT ──────────────────────


def test_check_out_checked_in_visitor(reset_shared_state) -> None:
    tenant_id = _create_tenant("t5")
    visit_id = _register(tenant_id)["visit_id"]
    visitor_svc.approve_visit(tenant_id, visit_id=visit_id)
    visitor_svc.check_in_visitor(tenant_id, visit_id=visit_id, badge_number="B-002")
    result = visitor_svc.check_out_visitor(tenant_id, visit_id=visit_id)
    assert result["status"] == "CHECKED_OUT"


# ─── Test 6: cancel non-final visit → CANCELLED ──────────────────────────────


def test_cancel_requested_visit(reset_shared_state) -> None:
    tenant_id = _create_tenant("t6a")
    visit_id = _register(tenant_id)["visit_id"]
    result = visitor_svc.cancel_visit(tenant_id, visit_id=visit_id, reason="guest withdrew")
    assert result["status"] == "CANCELLED"


def test_cancel_approved_visit(reset_shared_state) -> None:
    tenant_id = _create_tenant("t6b")
    visit_id = _register(tenant_id)["visit_id"]
    visitor_svc.approve_visit(tenant_id, visit_id=visit_id)
    result = visitor_svc.cancel_visit(tenant_id, visit_id=visit_id, reason="host unavailable")
    assert result["status"] == "CANCELLED"


# ─── Test 7: expire pending/approved visit → EXPIRED ─────────────────────────


def test_expire_requested_visit(reset_shared_state) -> None:
    tenant_id = _create_tenant("t7a")
    visit_id = _register(tenant_id)["visit_id"]
    result = visitor_svc.expire_visit(tenant_id, visit_id=visit_id)
    assert result["status"] == "EXPIRED"


def test_expire_approved_visit(reset_shared_state) -> None:
    tenant_id = _create_tenant("t7b")
    visit_id = _register(tenant_id)["visit_id"]
    visitor_svc.approve_visit(tenant_id, visit_id=visit_id)
    result = visitor_svc.expire_visit(tenant_id, visit_id=visit_id)
    assert result["status"] == "EXPIRED"


# ─── Test 8: invalid transition rejected deterministically ────────────────────


def test_check_in_requested_visit_rejected(reset_shared_state) -> None:
    """REQUESTED → CHECKED_IN is not a valid FSM transition."""
    tenant_id = _create_tenant("t8a")
    visit_id = _register(tenant_id)["visit_id"]
    with pytest.raises(ValueError, match="Cannot transition"):
        visitor_svc.check_in_visitor(tenant_id, visit_id=visit_id, badge_number="B-999")


def test_approve_checked_out_visit_rejected(reset_shared_state) -> None:
    """CHECKED_OUT is terminal; approve must fail."""
    tenant_id = _create_tenant("t8b")
    visit_id = _register(tenant_id)["visit_id"]
    visitor_svc.approve_visit(tenant_id, visit_id=visit_id)
    visitor_svc.check_in_visitor(tenant_id, visit_id=visit_id, badge_number="B-003")
    visitor_svc.check_out_visitor(tenant_id, visit_id=visit_id)
    with pytest.raises(ValueError):
        visitor_svc.approve_visit(tenant_id, visit_id=visit_id)


def test_expire_terminal_visit_rejected(reset_shared_state) -> None:
    """Rejected visit is already terminal; expire must fail."""
    tenant_id = _create_tenant("t8c")
    visit_id = _register(tenant_id)["visit_id"]
    visitor_svc.reject_visit(tenant_id, visit_id=visit_id)
    with pytest.raises(ValueError):
        visitor_svc.expire_visit(tenant_id, visit_id=visit_id)


# ─── Test 9: missing tenant_id fails closed ───────────────────────────────────


def test_register_visitor_missing_tenant_raises(reset_shared_state) -> None:
    with pytest.raises(ValueError, match="tenant_id"):
        visitor_svc.register_visitor(0, name="X", host_id="h", visit_date="2026-01-01")


def test_approve_visit_missing_tenant_raises(reset_shared_state) -> None:
    with pytest.raises(ValueError, match="tenant_id"):
        visitor_svc.approve_visit(0, visit_id="1")


# ─── Test 10: missing required fields rejected ────────────────────────────────


def test_register_visitor_missing_name_raises(reset_shared_state) -> None:
    tenant_id = _create_tenant("t10a")
    with pytest.raises(ValueError, match="name"):
        visitor_svc.register_visitor(tenant_id, name="", host_id="h", visit_date="2026-01-01")


def test_register_visitor_missing_host_raises(reset_shared_state) -> None:
    tenant_id = _create_tenant("t10b")
    with pytest.raises(ValueError, match="host_id"):
        visitor_svc.register_visitor(tenant_id, name="Alice", host_id="", visit_date="2026-01-01")


def test_register_visitor_missing_visit_date_raises(reset_shared_state) -> None:
    tenant_id = _create_tenant("t10c")
    with pytest.raises(ValueError, match="visit_date"):
        visitor_svc.register_visitor(tenant_id, name="Alice", host_id="h", visit_date="")


def test_check_in_missing_badge_raises(reset_shared_state) -> None:
    tenant_id = _create_tenant("t10d")
    visit_id = _register(tenant_id)["visit_id"]
    visitor_svc.approve_visit(tenant_id, visit_id=visit_id)
    with pytest.raises(ValueError, match="badge_number"):
        visitor_svc.check_in_visitor(tenant_id, visit_id=visit_id, badge_number="")


# ─── Test 11: cross-tenant access/update blocked ─────────────────────────────


def test_cross_tenant_visit_lookup_blocked(reset_shared_state) -> None:
    """A visit created for tenant A cannot be found/updated from tenant B."""
    tenant_a = _create_tenant("ta")
    tenant_b = _create_tenant("tb")
    visit_id = _register(tenant_a)["visit_id"]
    with pytest.raises(ValueError, match="not found"):
        visitor_svc.approve_visit(tenant_b, visit_id=visit_id)


# ─── Test 12: expected events emitted ────────────────────────────────────────


def test_register_emits_visitor_registered_event(reset_shared_state) -> None:
    published: list[dict] = []

    def _capture(self: object, *, tenant_id: int, event_type: str, payload: dict) -> None:
        published.append({"event_type": event_type, "tenant_id": tenant_id})

    tenant_id = _create_tenant("t12a")
    with patch.object(EventPublisher, "publish_event", _capture):
        _register(tenant_id)
    assert any(e["event_type"] == "visitor.registered" for e in published)


def test_check_in_emits_visitor_checked_in_event(reset_shared_state) -> None:
    published: list[dict] = []

    def _capture(self: object, *, tenant_id: int, event_type: str, payload: dict) -> None:
        published.append({"event_type": event_type})

    tenant_id = _create_tenant("t12b")
    visit_id = _register(tenant_id)["visit_id"]
    visitor_svc.approve_visit(tenant_id, visit_id=visit_id)
    with patch.object(EventPublisher, "publish_event", _capture):
        visitor_svc.check_in_visitor(tenant_id, visit_id=visit_id, badge_number="B-10")
    assert any(e["event_type"] == "visitor.checked_in" for e in published)


def test_check_out_emits_visitor_checked_out_event(reset_shared_state) -> None:
    published: list[dict] = []

    def _capture(self: object, *, tenant_id: int, event_type: str, payload: dict) -> None:
        published.append({"event_type": event_type})

    tenant_id = _create_tenant("t12c")
    visit_id = _register(tenant_id)["visit_id"]
    visitor_svc.approve_visit(tenant_id, visit_id=visit_id)
    visitor_svc.check_in_visitor(tenant_id, visit_id=visit_id, badge_number="B-11")
    with patch.object(EventPublisher, "publish_event", _capture):
        visitor_svc.check_out_visitor(tenant_id, visit_id=visit_id)
    assert any(e["event_type"] == "visitor.checked_out" for e in published)


def test_cancel_emits_visitor_cancelled_event(reset_shared_state) -> None:
    published: list[dict] = []

    def _capture(self: object, *, tenant_id: int, event_type: str, payload: dict) -> None:
        published.append({"event_type": event_type})

    tenant_id = _create_tenant("t12d")
    visit_id = _register(tenant_id)["visit_id"]
    with patch.object(EventPublisher, "publish_event", _capture):
        visitor_svc.cancel_visit(tenant_id, visit_id=visit_id, reason="test")
    assert any(e["event_type"] == "visitor.cancelled" for e in published)


def test_all_visitor_events_registered_in_valid_event_types() -> None:
    """All visitor.* events consumed by KPI/ingestion must be in VALID_EVENT_TYPES."""
    required = {
        "visitor.registered",
        "visitor.approved",
        "visitor.rejected",
        "visitor.checked_in",
        "visitor.checked_out",
        "visitor.cancelled",
        "visitor.expired",
        "visitor.unauthorized_attempt",
    }
    missing = required - set(VALID_EVENT_TYPES)
    assert not missing, f"Events missing from VALID_EVENT_TYPES: {missing}"


# ─── Test 13: unauthorized attempt evidence — no auto-ban ─────────────────────


def test_unauthorized_attempt_creates_evidence_not_ban(reset_shared_state) -> None:
    tenant_id = _create_tenant("t13a")
    result = visitor_svc.record_unauthorized_attempt(
        tenant_id,
        visitor_name="Unknown Person",
        zone="MAIN_GATE",
        access_point_id="AP-001",
        reason="badge not recognised",
    )
    assert result["event"] == "UNAUTHORIZED_ATTEMPT"
    assert "log_id" in result


def test_unauthorized_attempt_returns_evidence_not_disciplinary_action(reset_shared_state) -> None:
    """Return value must not include ban/lockout/disciplinary fields."""
    tenant_id = _create_tenant("t13b")
    result = visitor_svc.record_unauthorized_attempt(
        tenant_id, visitor_name="Visitor X", zone="EAST_WING"
    )
    # Non-destructive policy: response carries evidence only
    assert "ban" not in result
    assert "lockout" not in result
    assert "disciplinary" not in result
    assert "blacklist" not in result


def test_unauthorized_attempt_access_point_id_stored_in_evidence(reset_shared_state) -> None:
    """access_point_id passed to record_unauthorized_attempt ends up in event payload."""
    published: list[dict] = []

    def _capture(self: object, *, tenant_id: int, event_type: str, payload: dict) -> None:
        if event_type == "visitor.unauthorized_attempt":
            published.append(payload)

    tenant_id = _create_tenant("t13c")
    with patch.object(EventPublisher, "publish_event", _capture):
        visitor_svc.record_unauthorized_attempt(
            tenant_id,
            visitor_name="Mystery Guest",
            zone="B-BLOCK",
            access_point_id="AP-42",
            reason="no valid pass",
        )
    assert published, "No unauthorized_attempt event published"
    assert published[0].get("access_point_id") == "AP-42"
    assert published[0].get("reason") == "no valid pass"


# ─── Test 14: no hardware/physical access side effects ───────────────────────


def test_check_in_does_not_open_physical_door(reset_shared_state) -> None:
    """Check-in must not invoke any hardware ACS or door-control function."""
    tenant_id = _create_tenant("t14")
    visit_id = _register(tenant_id)["visit_id"]
    visitor_svc.approve_visit(tenant_id, visit_id=visit_id)
    # Verify service module has no hardware_acs / door_control / lock_open symbols
    import app.modules.visitor_management.service as svc_mod
    svc_source = svc_mod.__file__ or ""
    with open(svc_source) as fh:
        source_text = fh.read()
    forbidden = ["open_door", "hardware_acs", "door_control", "lock_open", "physical_access"]
    for term in forbidden:
        assert term not in source_text, f"Hardware control term found in service: {term!r}"
    # Check-in itself should still succeed
    result = visitor_svc.check_in_visitor(tenant_id, visit_id=visit_id, badge_number="B-safe")
    assert result["status"] == "CHECKED_IN"


# ─── Test 15: KPI visitor_visits_completed_count + visitor_visits_cancelled_count ──


def test_kpi_visitor_visits_completed_count(reset_shared_state) -> None:
    tenant_id = _create_tenant("t15a")
    _emit(tenant_id=tenant_id, event_type="visitor.checked_out", count=3)
    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)
    metrics = {str(r["metric_key"]): int(r["metric_value"]) for r in rows}
    assert metrics.get("visitor_visits_completed_count") == 3


def test_kpi_visitor_visits_cancelled_count(reset_shared_state) -> None:
    tenant_id = _create_tenant("t15b")
    _emit(tenant_id=tenant_id, event_type="visitor.cancelled", count=2)
    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)
    metrics = {str(r["metric_key"]): int(r["metric_value"]) for r in rows}
    assert metrics.get("visitor_visits_cancelled_count") == 2
