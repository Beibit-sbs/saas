from __future__ import annotations

import pytest

from tests.conftest import ADMIN_HEADERS, client


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


def test_get_record_consistency_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_get_record_consistency_report(tenant_id: int):
        assert tenant_id == 1
        return {
            "record_count": 3,
            "issue_count": 1,
            "issues": [
                {
                    "issue_type": "record_missing_student",
                    "record_id": 9002,
                    "student_id": 9999,
                    "course_id": 702,
                }
            ],
        }

    monkeypatch.setattr(
        "app.modules.academic_records.router.get_record_consistency_report",
        fake_get_record_consistency_report,
    )

    response = client.get(
        "/api/admin/university/records/consistency",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["record_count"] == 3
    assert body["issue_count"] == 1
    assert body["issues"][0]["issue_type"] == "record_missing_student"
