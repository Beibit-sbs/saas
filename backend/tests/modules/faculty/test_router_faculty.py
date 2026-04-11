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
