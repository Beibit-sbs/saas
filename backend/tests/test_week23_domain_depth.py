"""Week 23 — Domain Depth: Delinquency Collections Escalation Cap + Agent Record Side Effect.

Tests:
  W23.1 - Source guard: _ESCALATION_STAGE_MAX_ACTIVE and _ensure_collections_agent_record present
  W23.2 - Exceeding active stage_3 records for a student returns 422
  W23.3 - Creating a record with escalation_stage='stage_3' auto-creates collections_agent_records entry
  W23.4 - Multiple _ensure_collections_agent_record calls for same record_id are idempotent
"""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/delinquency-collections"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week23.delinquency@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["finance.read", "finance.write"],
        )
    )
}


def _reset_state() -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        for key in ("delinquency_records", "collections_agent_records"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _seed_enrollment_history(student_id: str) -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        university_shared._state.data.setdefault("enrollments", {})
        university_shared._state.counters.setdefault("enrollments", 0)
        university_shared._state.counters["enrollments"] += 1
        eid = university_shared._state.counters["enrollments"]
        university_shared._state.data["enrollments"][eid] = {
            "id": eid,
            "student_id": student_id,
            "course_id": 1,
            "semester": "Fall 2025",
            "status": "active",
            "tenant_id": "1",
        }


def _create_record(student_id: str, escalation_stage: str = "stage_1", status: str = "open") -> dict:
    _seed_enrollment_history(student_id)
    payload = {
        "student_id": student_id,
        "invoice_code": f"INV-{_uid()}",
        "amount_due": 500.0,
        "days_overdue": 30,
        "escalation_stage": escalation_stage,
        "status": status,
    }
    resp = client.post(BASE, headers=HEADERS, json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# W23.1 – Source guard
# ---------------------------------------------------------------------------

def test_w23_source_contains_escalation_cap_and_agent_helper() -> None:
    from app.modules.delinquency_collections import service as dc_service

    src = inspect.getsource(dc_service)
    assert "_ESCALATION_STAGE_MAX_ACTIVE" in src, (
        "_ESCALATION_STAGE_MAX_ACTIVE dict must exist in delinquency_collections service"
    )
    assert "_ensure_collections_agent_record" in src, (
        "_ensure_collections_agent_record helper must exist in delinquency_collections service"
    )


# ---------------------------------------------------------------------------
# W23.2 – Cap guard: exceeding stage_3 active records → 422
# ---------------------------------------------------------------------------

def test_w23_stage3_cap_exceeded_returns_422() -> None:
    """stage_3 max=1 per student; second record must return 422."""
    student_id = f"STU-{_uid()}"
    # first stage_3 record succeeds
    _create_record(student_id, escalation_stage="stage_3")
    # second must fail
    payload = {
        "student_id": student_id,
        "invoice_code": f"INV-{_uid()}",
        "amount_due": 800.0,
        "days_overdue": 60,
        "escalation_stage": "stage_3",
        "status": "open",
    }
    _seed_enrollment_history(student_id)
    resp = client.post(BASE, headers=HEADERS, json=payload)
    assert resp.status_code == 422, (
        f"Expected 422 when stage_3 cap exceeded, got {resp.status_code}: {resp.text}"
    )
    assert "stage_3" in resp.text.lower() or "already has" in resp.text.lower()


# ---------------------------------------------------------------------------
# W23.3 – stage_3 record creates collections_agent_records entry
# ---------------------------------------------------------------------------

def test_w23_stage3_record_creates_agent_record() -> None:
    """Creating a stage_3 record must auto-create a collections_agent_records entry."""
    from app.modules.university_core import shared as university_shared

    student_id = f"STU-{_uid()}"
    result = _create_record(student_id, escalation_stage="stage_3")
    record_id = result["item"]["id"]

    with university_shared._state_lock:
        agent_records = list(university_shared._state.data.get("collections_agent_records", {}).values())

    matching = [
        r for r in agent_records
        if str(r.get("source_entity_id")) == str(record_id)
        and str(r.get("integration_source")) == "collections_escalation"
    ]
    assert len(matching) == 1, (
        f"Expected 1 collections_agent_records entry for record_id={record_id}, found {len(matching)}"
    )
    assert matching[0]["student_id"] == student_id


# ---------------------------------------------------------------------------
# W23.4 – Idempotency: double call does not create duplicate agent record
# ---------------------------------------------------------------------------

def test_w23_ensure_agent_record_is_idempotent() -> None:
    """Calling _ensure_collections_agent_record twice for same record_id must not create duplicates."""
    from app.modules.university_core import shared as university_shared
    from app.modules.delinquency_collections.service import _ensure_collections_agent_record

    record_data = {
        "invoice_code": "INV-IDEM",
        "student_id": f"STU-{_uid()}",
        "escalation_stage": "legal",
        "amount_due": 1200.0,
    }
    tenant_id = 1
    record_id = 9991

    _ensure_collections_agent_record(tenant_id, record_id, record_data)
    _ensure_collections_agent_record(tenant_id, record_id, record_data)

    with university_shared._state_lock:
        agent_records = list(university_shared._state.data.get("collections_agent_records", {}).values())

    matching = [
        r for r in agent_records
        if str(r.get("source_entity_id")) == str(record_id)
        and str(r.get("integration_source")) == "collections_escalation"
    ]
    assert len(matching) == 1, (
        f"Idempotency violation: expected 1 entry, found {len(matching)}"
    )
