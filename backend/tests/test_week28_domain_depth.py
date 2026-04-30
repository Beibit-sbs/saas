"""Week 28 — Security Operations Incident Cap + Escalation Record Side Effect.

Tests:
  W28.1 - Source guard: severity cap dict and escalation helper present
  W28.2 - Exceeding active critical incident cap returns 422
  W28.3 - Creating a critical incident auto-creates security escalation record
  W28.4 - Multiple escalation helper calls for same incident are idempotent
"""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/security-operations"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week28.security@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["operations.read", "operations.write"],
        )
    )
}


def _reset_state() -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        for key in ("security_incidents", "security_incident_escalation_records"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _create_incident(severity: str = "medium", response_team: str | None = None) -> dict:
    payload = {
        "incident_code": f"INC-{_uid()}",
        "facility_code": f"FAC-{_uid()}",
        "category": "unauthorized_access",
        "severity": severity,
        "status": "open",
    }
    if response_team is not None:
        payload["response_team"] = response_team
    resp = client.post(f"{BASE}/incidents", headers=HEADERS, json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


def test_w28_source_contains_incident_cap_and_escalation_helper() -> None:
    from app.modules.security_operations import service as security_service

    src = inspect.getsource(security_service)
    assert "_SEVERITY_MAX_ACTIVE_INCIDENTS" in src
    assert "_ensure_incident_escalation_record" in src


def test_w28_critical_incident_cap_exceeded_returns_422() -> None:
    _create_incident(severity="critical")
    _create_incident(severity="critical")

    resp = client.post(
        f"{BASE}/incidents",
        headers=HEADERS,
        json={
            "incident_code": f"INC-{_uid()}",
            "facility_code": f"FAC-{_uid()}",
            "category": "unauthorized_access",
            "severity": "critical",
            "status": "open",
        },
    )
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
    assert "cap exceeded" in resp.text.lower() or "critical" in resp.text.lower()


def test_w28_critical_incident_creates_escalation_record() -> None:
    from app.modules.university_core import shared as university_shared

    result = _create_incident(severity="critical", response_team="campus_response")
    incident_id = result["record"]["id"]

    with university_shared._state_lock:
        records = list(
            university_shared._state.data.get("security_incident_escalation_records", {}).values()
        )

    matched = [
        row
        for row in records
        if str(row.get("source_entity_id")) == str(incident_id)
        and str(row.get("integration_source")) == "security_incident_escalation"
    ]
    assert len(matched) == 1, f"Expected 1 escalation record, got {len(matched)}"
    assert matched[0]["response_team"] == "campus_response"
    assert matched[0]["status"] == "open"


def test_w28_escalation_helper_is_idempotent() -> None:
    from app.modules.security_operations.service import _ensure_incident_escalation_record
    from app.modules.university_core import shared as university_shared

    incident = {
        "id": "9901",
        "incident_code": "INC-IDEMPOTENT",
        "facility_code": "FAC-1",
        "category": "unauthorized_access",
    }

    _ensure_incident_escalation_record(incident, 1, response_team="security_command")
    _ensure_incident_escalation_record(incident, 1, response_team="security_command")
    _ensure_incident_escalation_record(incident, 1, response_team="security_command")

    with university_shared._state_lock:
        records = [
            row
            for row in university_shared._state.data.get("security_incident_escalation_records", {}).values()
            if str(row.get("source_entity_id")) == "9901"
            and str(row.get("integration_source")) == "security_incident_escalation"
        ]
    assert len(records) == 1, f"Expected exactly 1 escalation record, got {len(records)}"