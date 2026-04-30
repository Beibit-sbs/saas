from __future__ import annotations

import os
from uuid import uuid4

import pytest

from app.core.db import clear_shared_engine
from app.modules.auth.token_service import create_access_token
from tests.conftest import client


pytestmark = pytest.mark.integration

_DATABASE_URL: str = os.getenv("DATABASE_URL", "")


def _enable_real_db(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _DATABASE_URL:
        pytest.skip("DATABASE_URL not set - skipping faculty KPI integration tests")
    monkeypatch.setenv("DATABASE_URL", _DATABASE_URL)
    clear_shared_engine()


def _headers(*permissions: str) -> dict[str, str]:
    token = create_access_token(
        user_id="faculty.kpi.integration@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=list(permissions),
    )
    return {"Authorization": f"Bearer {token}"}


def _payload(suffix: str, *, status: str = "satisfactory") -> dict[str, object]:
    return {
        "faculty_id": f"FAC-KPI-{suffix[:6]}",
        "name": f"Faculty KPI {suffix}",
        "department_id": f"DEPT-{suffix[:4]}",
        "kpi_period": "2026-Q2",
        "teaching_score": 82.0,
        "research_score": 77.0,
        "service_score": 88.0,
        "overall_score": 82.3,
        "status": status,
    }


def test_faculty_kpi_create_get_list_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_real_db(monkeypatch)
    headers = _headers("faculty.read", "faculty.write", "faculty_kpis.read", "faculty_kpis.write")

    suffix = uuid4().hex[:8]
    create_resp = client.post(
        "/api/admin/faculty-performance-kpis",
        headers=headers,
        json=_payload(suffix),
    )
    assert create_resp.status_code == 200, create_resp.text
    created = create_resp.json()["item"]

    get_resp = client.get(
        f"/api/admin/faculty-performance-kpis/{created['id']}",
        headers=headers,
    )
    assert get_resp.status_code == 200, get_resp.text
    assert get_resp.json()["item"]["faculty_id"] == created["faculty_id"]

    list_resp = client.get("/api/admin/faculty-performance-kpis", headers=headers)
    assert list_resp.status_code == 200, list_resp.text
    assert any(int(item["id"]) == int(created["id"]) for item in list_resp.json()["items"])


def test_faculty_kpi_status_update_persists(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_real_db(monkeypatch)
    headers = _headers("faculty.read", "faculty.write", "faculty_kpis.read", "faculty_kpis.write")

    suffix = uuid4().hex[:8]
    create_resp = client.post(
        "/api/admin/faculty-performance-kpis",
        headers=headers,
        json=_payload(suffix, status="satisfactory"),
    )
    assert create_resp.status_code == 200, create_resp.text
    kpi_id = int(create_resp.json()["item"]["id"])

    patch_resp = client.patch(
        f"/api/admin/faculty-performance-kpis/{kpi_id}/status",
        headers=headers,
        json={"status": "needs_improvement"},
    )
    assert patch_resp.status_code == 200, patch_resp.text
    assert patch_resp.json()["item"]["status"] == "needs_improvement"

    get_resp = client.get(f"/api/admin/faculty-performance-kpis/{kpi_id}", headers=headers)
    assert get_resp.status_code == 200, get_resp.text
    assert get_resp.json()["item"]["status"] == "needs_improvement"


def test_faculty_kpi_list_filters_by_department_and_status(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_real_db(monkeypatch)
    headers = _headers("faculty.read", "faculty.write", "faculty_kpis.read", "faculty_kpis.write")

    suffix = uuid4().hex[:8]
    dept = f"DEPT-FLT-{suffix[:3]}"

    good_payload = _payload(suffix, status="on_probation")
    good_payload["department_id"] = dept

    noise_payload = _payload(uuid4().hex[:8], status="satisfactory")
    noise_payload["department_id"] = f"DEPT-OTHER-{suffix[:2]}"

    resp1 = client.post("/api/admin/faculty-performance-kpis", headers=headers, json=good_payload)
    assert resp1.status_code == 200, resp1.text
    good_id = int(resp1.json()["item"]["id"])

    resp2 = client.post("/api/admin/faculty-performance-kpis", headers=headers, json=noise_payload)
    assert resp2.status_code == 200, resp2.text

    filtered = client.get(
        f"/api/admin/faculty-performance-kpis?department_id={dept}&status=on_probation",
        headers=headers,
    )
    assert filtered.status_code == 200, filtered.text
    ids = {int(item["id"]) for item in filtered.json()["items"]}
    assert good_id in ids


def test_faculty_kpi_get_unknown_returns_404(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_real_db(monkeypatch)
    headers = _headers("faculty.read", "faculty_kpis.read")

    resp = client.get("/api/admin/faculty-performance-kpis/99999999", headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json().get("detail") == "Faculty KPI record not found"
