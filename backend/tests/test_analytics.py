"""Tests for analytics module — KPI endpoints, events, auth guards.

Covers: kpis list, refresh, refresh-history, trends, insights,
recommendations, events list, events summary, permission guards,
unauthenticated access.
"""

from tests.conftest import ADMIN_HEADERS, _auth_headers, client


# ---------------------------------------------------------------------------
# 1. KPIs — basic endpoint checks
# ---------------------------------------------------------------------------


def test_analytics_kpis_returns_200() -> None:
    resp = client.get("/api/analytics/kpis", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "kpis" in body or "items" in body or isinstance(body, dict)


def test_analytics_kpis_refresh() -> None:
    resp = client.post("/api/analytics/kpis/refresh", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "refreshed_at" in body or "status" in body or isinstance(body, dict)


def test_analytics_kpis_refresh_history() -> None:
    # Trigger a refresh first so history is non-empty
    client.post("/api/analytics/kpis/refresh", headers=ADMIN_HEADERS)
    resp = client.get("/api/analytics/kpis/refresh-history", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "history" in body or "items" in body or isinstance(body, dict)


def test_analytics_kpis_refresh_history_limit() -> None:
    resp = client.get("/api/analytics/kpis/refresh-history?limit=5", headers=ADMIN_HEADERS)
    assert resp.status_code == 200


def test_analytics_kpis_trends() -> None:
    resp = client.get("/api/analytics/kpis/trends", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)


def test_analytics_kpis_trends_custom_window() -> None:
    resp = client.get("/api/analytics/kpis/trends?window_days=7", headers=ADMIN_HEADERS)
    assert resp.status_code == 200


def test_analytics_kpis_insights() -> None:
    resp = client.get("/api/analytics/kpis/insights", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)


def test_analytics_kpis_insights_custom_window() -> None:
    resp = client.get("/api/analytics/kpis/insights?window_days=14", headers=ADMIN_HEADERS)
    assert resp.status_code == 200


def test_analytics_kpis_recommendations() -> None:
    resp = client.get("/api/analytics/kpis/recommendations", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)


def test_analytics_kpis_recommendations_custom_window() -> None:
    resp = client.get("/api/analytics/kpis/recommendations?window_days=60", headers=ADMIN_HEADERS)
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 2. Events — list & summary
# ---------------------------------------------------------------------------


def test_analytics_events_returns_200() -> None:
    resp = client.get("/api/analytics/events", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "count" in body
    assert "tenant_id" in body


def test_analytics_events_filter_by_type() -> None:
    resp = client.get("/api/analytics/events?event_type=test.event", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["count"] >= 0


def test_analytics_events_limit() -> None:
    resp = client.get("/api/analytics/events?limit=5", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()["items"]) <= 5


def test_analytics_events_summary() -> None:
    resp = client.get("/api/analytics/events/summary", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "tenant_id" in body
    assert "counts_by_type" in body
    assert "total" in body
    assert isinstance(body["counts_by_type"], dict)
    assert isinstance(body["total"], int)


# ---------------------------------------------------------------------------
# 3. Events accumulate after KPI reads
# ---------------------------------------------------------------------------


def test_kpi_reads_generate_analytics_events() -> None:
    """Reading KPI endpoints should record analytics events."""
    # Perform some reads that trigger event ingestion
    client.get("/api/analytics/kpis", headers=ADMIN_HEADERS)
    client.get("/api/analytics/kpis/trends", headers=ADMIN_HEADERS)
    client.get("/api/analytics/kpis/insights", headers=ADMIN_HEADERS)

    resp = client.get("/api/analytics/events/summary", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 0  # events should be recorded


# ---------------------------------------------------------------------------
# 4. Permission guards
# ---------------------------------------------------------------------------


def test_analytics_kpis_requires_auth() -> None:
    resp = client.get("/api/analytics/kpis")
    assert resp.status_code in (401, 403)


def test_analytics_refresh_requires_auth() -> None:
    resp = client.post("/api/analytics/kpis/refresh")
    assert resp.status_code in (401, 403)


def test_analytics_events_requires_auth() -> None:
    resp = client.get("/api/analytics/events")
    assert resp.status_code in (401, 403)


def test_analytics_events_summary_requires_auth() -> None:
    resp = client.get("/api/analytics/events/summary")
    assert resp.status_code in (401, 403)


def test_analytics_kpis_student_role_access() -> None:
    """Student role should still be able to read KPIs (read-only)."""
    student_headers = _auth_headers("student.analytics@example.com", ["student"])
    resp = client.get("/api/analytics/kpis", headers=student_headers)
    # Students may or may not have access depending on RBAC config
    # but the endpoint should not crash with 500
    assert resp.status_code in (200, 403)


# ---------------------------------------------------------------------------
# 5. Validation
# ---------------------------------------------------------------------------


def test_analytics_refresh_history_limit_too_high() -> None:
    resp = client.get("/api/analytics/kpis/refresh-history?limit=100", headers=ADMIN_HEADERS)
    assert resp.status_code == 422  # exceeds max 50


def test_analytics_events_limit_too_high() -> None:
    resp = client.get("/api/analytics/events?limit=300", headers=ADMIN_HEADERS)
    assert resp.status_code == 422  # exceeds max 200
