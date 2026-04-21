from __future__ import annotations

import pytest

from tests.conftest import ADMIN_HEADERS, client


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


def test_get_faculty_consistency_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_get_faculty_consistency_report(tenant_id: int):
        assert tenant_id == 1
        return {
            "faculty_count": 3,
            "issue_count": 1,
            "issues": [
                {
                    "issue_type": "faculty_missing_email",
                    "faculty_row_id": 1002,
                    "faculty_id": "FAC-01",
                }
            ],
        }

    monkeypatch.setattr(
        "app.modules.faculty.router.get_faculty_consistency_report",
        fake_get_faculty_consistency_report,
    )

    response = client.get(
        "/api/admin/org/faculty/consistency",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["faculty_count"] == 3
    assert body["issue_count"] == 1
    assert body["issues"][0]["issue_type"] == "faculty_missing_email"


def test_get_faculty_workload_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_get_faculty_workload(tenant_id: int, faculty_id: str, term_id: int):
        assert tenant_id == 1
        assert faculty_id == "FAC-01"
        assert term_id == 20261
        return {
            "faculty_id": "FAC-01",
            "department": "Engineering",
            "term_id": 20261,
            "total_credit_hours": 9,
            "max_credit_hours": 12,
            "fte_ratio": 1.0,
            "effective_capacity": 12,
            "utilization": 0.75,
            "primary_assignments": 3,
            "assistant_assignments": 0,
            "alerts": [],
        }

    monkeypatch.setattr(
        "app.modules.faculty.router.get_faculty_workload",
        fake_get_faculty_workload,
    )

    response = client.get(
        "/api/admin/org/faculty/FAC-01/workload?term_id=20261",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["workload"]["faculty_id"] == "FAC-01"
    assert body["workload"]["total_credit_hours"] == 9


def test_get_department_workload_summary_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_get_department_workload_summary(tenant_id: int, department: str, term_id: int):
        assert tenant_id == 1
        assert department == "Engineering"
        assert term_id == 20261
        return [
            {
                "faculty_id": "FAC-01",
                "department": "Engineering",
                "term_id": 20261,
                "total_credit_hours": 9,
                "max_credit_hours": 12,
                "fte_ratio": 1.0,
                "effective_capacity": 12,
                "utilization": 0.75,
                "primary_assignments": 3,
                "assistant_assignments": 0,
                "alerts": [],
            }
        ]

    monkeypatch.setattr(
        "app.modules.faculty.router.get_department_workload_summary",
        fake_get_department_workload_summary,
    )

    response = client.get(
        "/api/admin/org/faculty/workload/department/Engineering?term_id=20261",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["workloads"]) == 1
    assert body["workloads"][0]["department"] == "Engineering"


def test_get_workload_alerts_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_list_workload_alerts(tenant_id: int, term_id: int):
        assert tenant_id == 1
        assert term_id == 20261
        return [
            {
                "faculty_id": "FAC-02",
                "department": "Engineering",
                "term_id": 20261,
                "total_credit_hours": 16,
                "max_credit_hours": 12,
                "fte_ratio": 1.0,
                "effective_capacity": 12,
                "utilization": 1.3333,
                "primary_assignments": 4,
                "assistant_assignments": 0,
                "alerts": ["overload_threshold"],
            }
        ]

    monkeypatch.setattr(
        "app.modules.faculty.router.list_workload_alerts",
        fake_list_workload_alerts,
    )

    response = client.get(
        "/api/admin/org/faculty/workload/alerts?term_id=20261",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["workloads"][0]["alerts"] == ["overload_threshold"]


def test_update_faculty_capacity_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_update_faculty_capacity(
        tenant_id: int,
        faculty_id: str,
        max_credit_hours: int,
        fte_ratio: float,
    ):
        assert tenant_id == 1
        assert faculty_id == "FAC-01"
        assert max_credit_hours == 16
        assert fte_ratio == 0.8
        return {
            "id": 5,
            "faculty_id": "FAC-01",
            "first_name": "Ann",
            "last_name": "Stone",
            "department": "Engineering",
            "email": "ann@example.edu",
            "status": "active",
            "tenant_id": "1",
        }

    monkeypatch.setattr(
        "app.modules.faculty.router.update_faculty_capacity",
        fake_update_faculty_capacity,
    )

    response = client.put(
        "/api/admin/org/faculty/FAC-01/capacity",
        headers=admin_headers,
        json={"max_credit_hours": 16, "fte_ratio": 0.8},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["faculty"]["faculty_id"] == "FAC-01"


def test_get_faculty_contracts_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_list_faculty_contracts(tenant_id: int, faculty_id: str | None = None, status: str | None = None):
        assert tenant_id == 1
        assert faculty_id is None
        assert status is None
        return [
            {
                "id": 11,
                "faculty_id": "FAC-01",
                "contract_type": "full_time",
                "start_date": "2026-09-01",
                "end_date": "2027-08-31",
                "fte_ratio": 1.0,
                "max_credit_hours": 18,
                "status": "active",
                "notes": "renewed",
                "tenant_id": "1",
            }
        ]

    monkeypatch.setattr(
        "app.modules.faculty.router.list_faculty_contracts",
        fake_list_faculty_contracts,
    )

    response = client.get("/api/admin/org/faculty/contracts", headers=admin_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["contracts"]) == 1
    assert body["contracts"][0]["faculty_id"] == "FAC-01"


def test_create_faculty_contract_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_create_faculty_contract(payload: dict[str, object], tenant_id: int):
        assert tenant_id == 1
        assert payload["faculty_id"] == "FAC-01"
        return {
            "id": 12,
            "faculty_id": "FAC-01",
            "contract_type": "full_time",
            "start_date": "2026-09-01",
            "end_date": None,
            "fte_ratio": 1.0,
            "max_credit_hours": 18,
            "status": "draft",
            "notes": None,
            "tenant_id": "1",
        }

    monkeypatch.setattr(
        "app.modules.faculty.router.create_faculty_contract",
        fake_create_faculty_contract,
    )

    response = client.post(
        "/api/admin/org/faculty/contracts",
        headers=admin_headers,
        json={
            "faculty_id": "FAC-01",
            "contract_type": "full_time",
            "start_date": "2026-09-01",
            "end_date": None,
            "fte_ratio": 1.0,
            "max_credit_hours": 18,
            "status": "draft",
            "notes": None,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract"]["id"] == 12


def test_update_faculty_contract_status_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_update_faculty_contract_status(
        contract_id: int,
        status: str,
        tenant_id: int,
        notes: str | None = None,
    ):
        assert contract_id == 12
        assert status == "active"
        assert tenant_id == 1
        assert notes == "signed"
        return {
            "id": 12,
            "faculty_id": "FAC-01",
            "contract_type": "full_time",
            "start_date": "2026-09-01",
            "end_date": None,
            "fte_ratio": 1.0,
            "max_credit_hours": 18,
            "status": "active",
            "notes": "signed",
            "tenant_id": "1",
        }

    monkeypatch.setattr(
        "app.modules.faculty.router.update_faculty_contract_status",
        fake_update_faculty_contract_status,
    )

    response = client.patch(
        "/api/admin/org/faculty/contracts/12/status",
        headers=admin_headers,
        json={"status": "active", "notes": "signed"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contract"]["status"] == "active"
