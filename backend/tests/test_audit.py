"""Tests for audit module — events listing, export (JSON/CSV), filters,
permission guards, unauthenticated access.

Covers: GET /events, GET /export?format=json, GET /export?format=csv,
query filters (actor, action, entity), permission guards, invalid format.
"""

from tests.conftest import ADMIN_HEADERS, _auth_headers, client


# ---------------------------------------------------------------------------
# helpers — seed some audit events via feature_flags upsert (triggers log)
# ---------------------------------------------------------------------------


def _seed_audit_event() -> None:
    """Create an audit trail entry by performing a feature-flag upsert."""
    client.post(
        "/api/admin/feature-flags",
        headers=ADMIN_HEADERS,
        json={"key": "audit.seed_event", "enabled": True},
    )


# ---------------------------------------------------------------------------
# 1. Events listing
# ---------------------------------------------------------------------------


def test_audit_events_returns_200() -> None:
    resp = client.get("/api/admin/audit/events", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "events" in body
    assert isinstance(body["events"], list)


def test_audit_events_contains_seeded_event() -> None:
    _seed_audit_event()
    resp = client.get("/api/admin/audit/events", headers=ADMIN_HEADERS)
    events = resp.json()["events"]
    actions = [e.get("action") for e in events]
    assert "feature_flags.upsert" in actions


def test_audit_events_filter_by_action() -> None:
    _seed_audit_event()
    resp = client.get(
        "/api/admin/audit/events?action=feature_flags.upsert",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    for event in resp.json()["events"]:
        assert event["action"] == "feature_flags.upsert"


def test_audit_events_filter_by_entity() -> None:
    _seed_audit_event()
    resp = client.get(
        "/api/admin/audit/events?entity=feature_flags",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    for event in resp.json()["events"]:
        assert event["entity"] == "feature_flags"


def test_audit_events_filter_by_actor() -> None:
    _seed_audit_event()
    resp = client.get(
        "/api/admin/audit/events?actor=owner@example.com",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    for event in resp.json()["events"]:
        assert event["actor"] == "owner@example.com"


def test_audit_events_limit() -> None:
    _seed_audit_event()
    _seed_audit_event()
    resp = client.get(
        "/api/admin/audit/events?limit=1",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert len(resp.json()["events"]) <= 1


# ---------------------------------------------------------------------------
# 2. Export — JSON
# ---------------------------------------------------------------------------


def test_audit_export_json() -> None:
    _seed_audit_event()
    resp = client.get(
        "/api/admin/audit/export?format=json",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("content-type", "")
    body = resp.json()
    assert "events" in body


def test_audit_export_json_content_disposition() -> None:
    resp = client.get(
        "/api/admin/audit/export?format=json",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    cd = resp.headers.get("content-disposition", "")
    assert "audit-events.json" in cd


# ---------------------------------------------------------------------------
# 3. Export — CSV
# ---------------------------------------------------------------------------


def test_audit_export_csv() -> None:
    _seed_audit_event()
    resp = client.get(
        "/api/admin/audit/export?format=csv",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
    lines = resp.text.strip().split("\n")
    # Header row should be present
    assert lines[0].startswith("timestamp")


def test_audit_export_csv_content_disposition() -> None:
    resp = client.get(
        "/api/admin/audit/export?format=csv",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    cd = resp.headers.get("content-disposition", "")
    assert "audit-events.csv" in cd


# ---------------------------------------------------------------------------
# 4. Export — invalid format
# ---------------------------------------------------------------------------


def test_audit_export_invalid_format() -> None:
    resp = client.get(
        "/api/admin/audit/export?format=xml",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 400
    assert "format" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 5. Permission guards
# ---------------------------------------------------------------------------


def test_audit_events_requires_auth() -> None:
    resp = client.get("/api/admin/audit/events")
    assert resp.status_code in (401, 403)


def test_audit_export_requires_auth() -> None:
    resp = client.get("/api/admin/audit/export?format=json")
    assert resp.status_code in (401, 403)


def test_viewer_cannot_read_audit() -> None:
    viewer_headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.get("/api/admin/audit/events", headers=viewer_headers)
    assert resp.status_code == 403


def test_viewer_cannot_export_audit() -> None:
    viewer_headers = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.get("/api/admin/audit/export?format=json", headers=viewer_headers)
    assert resp.status_code == 403
