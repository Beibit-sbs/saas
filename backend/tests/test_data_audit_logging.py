from __future__ import annotations

import asyncio

import pytest

from app.modules.audit import service as audit_service
from app.modules.rbac.abac import AbacDenyError
from app.modules.rbac.abac import validate_student_ownership


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _clear_audit_events() -> None:
    audit_service.clear_audit_events()


def _find_data_access_events(tenant_id: int) -> list[dict]:
    return [
        event
        for event in audit_service.list_admin_actions(limit=100, tenant_id=tenant_id)
        if event.get("action") == "data.access"
    ]


def test_data_access_format_read_write_delete() -> None:
    audit_service.log_data_access_event(
        actor_id="owner@example.com",
        tenant_id=1,
        resource="student",
        resource_id="1001",
        action="read",
        result="success",
    )
    audit_service.log_data_access_event(
        actor_id="owner@example.com",
        tenant_id=1,
        resource="student",
        resource_id="1001",
        action="update",
        result="success",
    )
    audit_service.log_data_access_event(
        actor_id="owner@example.com",
        tenant_id=1,
        resource="student",
        resource_id="1001",
        action="delete",
        result="success",
    )

    events = _find_data_access_events(tenant_id=1)
    assert len(events) >= 3

    for event in events[:3]:
        payload = event["metadata"]
        assert payload["event"] == "data.access"
        assert payload["actor_id"] == "owner@example.com"
        assert payload["tenant_id"] == "1"
        assert payload["resource"] == "student"
        assert payload["resource_id"] == "1001"
        assert payload["action"] in {"read", "update", "delete"}
        assert payload["result"] == "success"
        assert "timestamp" in payload


def test_abac_denied_produces_data_access_audit_event() -> None:
    with pytest.raises(AbacDenyError):
        run(
            validate_student_ownership(
                actor_id="student_a@example.com",
                student_id=1002,
                tenant_id=1,
                student_owner_id="student_b@example.com",
                actor_roles=["student"],
            )
        )

    events = _find_data_access_events(tenant_id=1)
    assert len(events) >= 1

    denied = events[0]["metadata"]
    assert denied["event"] == "data.access"
    assert denied["resource"] == "student"
    assert denied["action"] == "read"
    assert denied["result"] == "denied"
    assert denied["reason"] == "ownership_mismatch"


def test_data_access_logs_metadata_only_no_sensitive_payload() -> None:
    audit_service.log_data_access_event(
        actor_id="owner@example.com",
        tenant_id=1,
        resource="grade",
        resource_id="7001",
        action="write",
        result="success",
        reason="ownership_mismatch",
    )

    events = _find_data_access_events(tenant_id=1)
    payload = events[0]["metadata"]

    assert set(payload.keys()) == {
        "event",
        "actor_id",
        "tenant_id",
        "resource",
        "resource_id",
        "action",
        "result",
        "reason",
        "timestamp",
    }
