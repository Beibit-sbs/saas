from __future__ import annotations

import pytest

from tests.conftest import ADMIN_HEADERS, client


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


def test_get_course_consistency_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_get_course_consistency_report(tenant_id: int):
        assert tenant_id == 1
        return {
            "course_count": 2,
            "issue_count": 1,
            "issues": [
                {
                    "issue_type": "course_missing_program",
                    "course_id": 7002,
                    "program_id": 9999,
                }
            ],
        }

    monkeypatch.setattr(
        "app.modules.courses.router.get_course_consistency_report",
        fake_get_course_consistency_report,
    )

    response = client.get(
        "/api/admin/org/courses/consistency",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["course_count"] == 2
    assert body["issue_count"] == 1
    assert body["issues"][0]["issue_type"] == "course_missing_program"
