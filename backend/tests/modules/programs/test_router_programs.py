from __future__ import annotations

import pytest

from tests.conftest import ADMIN_HEADERS, client


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


def test_get_program_consistency_success(
    monkeypatch: pytest.MonkeyPatch,
    admin_headers: dict[str, str],
) -> None:
    def fake_get_program_consistency_report(tenant_id: int):
        assert tenant_id == 1
        return {
            "program_count": 2,
            "issue_count": 1,
            "issues": [
                {
                    "issue_type": "duplicate_program_code",
                    "program_id": 502,
                    "program_code": "CS-BSC",
                }
            ],
        }

    monkeypatch.setattr(
        "app.modules.programs.router.get_program_consistency_report",
        fake_get_program_consistency_report,
    )

    response = client.get(
        "/api/admin/org/programs/consistency",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["program_count"] == 2
    assert body["issue_count"] == 1
    assert body["issues"][0]["issue_type"] == "duplicate_program_code"
