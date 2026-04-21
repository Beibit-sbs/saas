from __future__ import annotations

import pytest

from tests.conftest import ADMIN_HEADERS, client


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


def test_list_accreditation_records_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_list_accreditation_records(tenant_id: int, status=None, standard_type=None):
        assert tenant_id == 1
        assert status is None
        assert standard_type is None
        return [
            {
                "id": 1,
                "tenant_id": "1",
                "standard_code": "ACC-2026-01",
                "standard_type": "institutional",
                "title": "Institutional Mission Alignment",
                "owner_department": "Registrar",
                "review_cycle_year": 2026,
                "due_date": None,
                "evidence_summary": "Initial self-study package",
                "risk_level": "medium",
                "status": "draft",
                "reviewer_notes": None,
                "remediation_plan": None,
            }
        ]

    monkeypatch.setattr(
        "app.modules.accreditation.router.list_accreditation_records",
        fake_list_accreditation_records,
    )

    response = client.get("/api/admin/accreditation-compliance", headers=admin_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["items"][0]["standard_code"] == "ACC-2026-01"


def test_create_accreditation_record_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_create_accreditation_record(tenant_id: int, payload, actor: str):
        assert tenant_id == 1
        assert actor == "owner@example.com"
        assert payload.standard_code == "ACC-2026-02"
        return {
            "id": 2,
            "tenant_id": "1",
            "standard_code": "ACC-2026-02",
            "standard_type": "programmatic",
            "title": "Program Outcomes Evidence",
            "owner_department": "Engineering",
            "review_cycle_year": 2026,
            "due_date": None,
            "evidence_summary": "Outcome measures mapped",
            "risk_level": "high",
            "status": "draft",
            "reviewer_notes": None,
            "remediation_plan": None,
        }

    monkeypatch.setattr(
        "app.modules.accreditation.router.create_accreditation_record",
        fake_create_accreditation_record,
    )

    response = client.post(
        "/api/admin/accreditation-compliance",
        headers=admin_headers,
        json={
            "standard_code": "ACC-2026-02",
            "standard_type": "programmatic",
            "title": "Program Outcomes Evidence",
            "owner_department": "Engineering",
            "review_cycle_year": 2026,
            "evidence_summary": "Outcome measures mapped",
            "risk_level": "high",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["item"]["status"] == "draft"


def test_update_accreditation_status_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_update_accreditation_status(tenant_id: int, record_id: int, payload, actor: str):
        assert tenant_id == 1
        assert record_id == 2
        assert payload.status == "under_review"
        assert actor == "owner@example.com"
        return {
            "id": 2,
            "tenant_id": "1",
            "standard_code": "ACC-2026-02",
            "standard_type": "programmatic",
            "title": "Program Outcomes Evidence",
            "owner_department": "Engineering",
            "review_cycle_year": 2026,
            "due_date": None,
            "evidence_summary": "Outcome measures mapped",
            "risk_level": "high",
            "status": "under_review",
            "reviewer_notes": "Evidence pack complete",
            "remediation_plan": None,
        }

    monkeypatch.setattr(
        "app.modules.accreditation.router.update_accreditation_status",
        fake_update_accreditation_status,
    )

    response = client.patch(
        "/api/admin/accreditation-compliance/2/status",
        headers=admin_headers,
        json={"status": "under_review", "reviewer_notes": "Evidence pack complete"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["item"]["status"] == "under_review"
