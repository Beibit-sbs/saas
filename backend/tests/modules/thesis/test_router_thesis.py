from __future__ import annotations

import pytest

from tests.conftest import ADMIN_HEADERS, client


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


def test_list_thesis_records_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_list_thesis_records(tenant_id: int, status=None):
        assert tenant_id == 1
        assert status is None
        return [
            {
                "id": 1,
                "tenant_id": "1",
                "thesis_code": "TH-2026-01",
                "student_id": 101,
                "title": "Adaptive Learning Paths",
                "advisor_faculty_id": "FAC-101",
                "status": "draft",
                "defense_date": None,
                "repository_url": None,
            }
        ]

    monkeypatch.setattr(
        "app.modules.thesis.router.list_thesis_records",
        fake_list_thesis_records,
    )

    response = client.get("/api/admin/thesis", headers=admin_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["items"][0]["thesis_code"] == "TH-2026-01"


def test_create_thesis_record_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_create_thesis_record(tenant_id: int, payload, actor: str):
        assert tenant_id == 1
        assert actor == "owner@example.com"
        assert payload.thesis_code == "TH-2026-02"
        return {
            "id": 2,
            "tenant_id": "1",
            "thesis_code": "TH-2026-02",
            "student_id": 202,
            "title": "Campus Knowledge Graph",
            "advisor_faculty_id": "FAC-102",
            "status": "draft",
            "defense_date": None,
            "repository_url": None,
        }

    monkeypatch.setattr(
        "app.modules.thesis.router.create_thesis_record",
        fake_create_thesis_record,
    )

    response = client.post(
        "/api/admin/thesis",
        headers=admin_headers,
        json={
            "thesis_code": "TH-2026-02",
            "student_id": 202,
            "title": "Campus Knowledge Graph",
            "advisor_faculty_id": "FAC-102",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["item"]["status"] == "draft"


def test_update_thesis_status_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_update_thesis_status(tenant_id: int, thesis_id: int, payload, actor: str):
        assert tenant_id == 1
        assert thesis_id == 2
        assert payload.status == "submitted"
        assert actor == "owner@example.com"
        return {
            "id": 2,
            "tenant_id": "1",
            "thesis_code": "TH-2026-02",
            "student_id": 202,
            "title": "Campus Knowledge Graph",
            "advisor_faculty_id": "FAC-102",
            "status": "submitted",
            "defense_date": None,
            "repository_url": None,
        }

    monkeypatch.setattr(
        "app.modules.thesis.router.update_thesis_status",
        fake_update_thesis_status,
    )

    response = client.patch(
        "/api/admin/thesis/2/status",
        headers=admin_headers,
        json={"status": "submitted"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["item"]["status"] == "submitted"
