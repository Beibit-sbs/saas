from __future__ import annotations

import pytest

from tests.conftest import ADMIN_HEADERS, client


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


def test_get_faculty_quality_kpi_default_when_no_records(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    monkeypatch.setattr(
        "app.modules.teaching_quality.service.list_teaching_quality",
        lambda tenant_id, faculty_id=None: [],
    )

    response = client.get(
        "/api/admin/teaching-quality/faculty/FAC-01/kpi?term_id=20261",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["faculty_id"] == "FAC-01"
    assert body["overall_quality_score"] == 0.0


def test_get_quality_dashboard_aggregates_scores(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    rows = [
        {
            "id": 1,
            "faculty_id": "FAC-01",
            "term_id": 20261,
            "quality_score": 80,
            "kpi_score": 78,
            "improvement_plan": "Improve rubric clarity",
        },
        {
            "id": 2,
            "faculty_id": "FAC-02",
            "term_id": 20261,
            "quality_score": 60,
            "kpi_score": 65,
            "improvement_plan": None,
        },
    ]
    monkeypatch.setattr(
        "app.modules.teaching_quality.service.list_teaching_quality",
        lambda tenant_id, faculty_id=None: rows,
    )

    response = client.get(
        "/api/admin/teaching-quality/dashboard/Engineering?term_id=20261",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["department"] == "Engineering"
    assert body["total_faculty"] == 2
    assert body["average_quality_score"] == 70.0
    assert body["above_target_count"] == 1
    assert body["below_target_count"] == 1


def test_get_quality_benchmarks_returns_two_metrics(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    rows = [
        {"id": 1, "faculty_id": "FAC-01", "term_id": 20261, "quality_score": 90, "kpi_score": 85},
        {"id": 2, "faculty_id": "FAC-02", "term_id": 20261, "quality_score": 70, "kpi_score": 75},
        {"id": 3, "faculty_id": "FAC-03", "term_id": 20261, "quality_score": 50, "kpi_score": 65},
    ]
    monkeypatch.setattr(
        "app.modules.teaching_quality.service.list_teaching_quality",
        lambda tenant_id, faculty_id=None: rows,
    )

    response = client.get(
        "/api/admin/teaching-quality/benchmarks?term_id=20261",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 2
    assert body[0]["metric_name"] == "quality_score"
    assert body[1]["metric_name"] == "kpi_score"


def test_get_faculty_improvements_filters_records(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    rows = [
        {
            "id": 11,
            "faculty_id": "FAC-01",
            "term_id": 20261,
            "improvement_plan": "Increase formative feedback frequency",
            "quality_score": 62,
            "kpi_score": 67,
        },
        {
            "id": 12,
            "faculty_id": "FAC-01",
            "term_id": 20261,
            "improvement_plan": None,
            "quality_score": 88,
            "kpi_score": 90,
        },
    ]
    monkeypatch.setattr(
        "app.modules.teaching_quality.service.list_teaching_quality",
        lambda tenant_id, faculty_id=None: rows,
    )

    response = client.get(
        "/api/admin/teaching-quality/faculty/FAC-01/improvements",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 1
    assert body[0]["record_id"] == 11


def test_post_quality_metric_maps_payload_and_creates_record(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    captured: dict[str, object] = {}

    def fake_create_teaching_quality_record(payload: dict, tenant_id: int):
        captured["payload"] = payload
        captured["tenant_id"] = tenant_id
        return {"id": 99, **payload, "tenant_id": str(tenant_id)}

    monkeypatch.setattr(
        "app.modules.teaching_quality.service.create_quality_metric",
        fake_create_teaching_quality_record,
    )

    response = client.post(
        "/api/admin/teaching-quality/faculty/FAC-09/metric",
        headers=admin_headers,
        json={
            "metric_type": "satisfaction",
            "value": 84,
            "term_id": 20261,
            "measurement_period": "Q1",
            "course_id": "CS-101",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["_record_id"] == 99
    assert captured["tenant_id"] == 1
    sent_payload = captured["payload"]
    assert isinstance(sent_payload, dict)
    assert sent_payload["faculty_id"] == "FAC-09"
    assert sent_payload["quality_score"] == 84.0
    assert sent_payload["kpi_score"] == 100.0
