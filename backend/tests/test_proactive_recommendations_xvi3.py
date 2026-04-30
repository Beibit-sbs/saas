from __future__ import annotations

from unittest.mock import patch

from tests.conftest import ADMIN_HEADERS, client
from app.modules.auth.token_service import create_access_token
from app.modules.brain_core.service import brain_core_service


def _write_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="owner@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
        permissions=["admin.dashboard.read", "admin.dashboard.write"],
    )
    return {"Authorization": f"Bearer {token}"}


def _reset() -> None:
    brain_core_service.__init__()


def _student_signal(tenant_id: int, student_id: str) -> dict:
    return {
        "signal_id": f"sig-{student_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-{student_id}",
        "event_type": "academic.attendance_risk.detected",
        "subject": {"student_id": student_id, "faculty_id": "FAC-1"},
        "payload": {
            "student_id": student_id,
            "attendance_rate": 0.4,
            "grade_trend": "declining",
            "source_entity_type": "section_attendance",
            "source_entity_id": f"SEC-{student_id}",
        },
        "metadata": {"source": "test"},
    }


def _faculty_signal(tenant_id: int, faculty_id: str) -> dict:
    return {
        "signal_id": f"sig-{faculty_id}",
        "tenant_id": tenant_id,
        "correlation_id": f"corr-{faculty_id}",
        "event_type": "faculty.workload_overload.detected",
        "subject": {"faculty_id": faculty_id},
        "payload": {
            "faculty_id": faculty_id,
            "workload_ratio": 1.8,
            "source_entity_type": "faculty_workload",
            "source_entity_id": faculty_id,
        },
        "metadata": {"source": "test"},
    }


def _seed_signal(signal: dict) -> None:
    brain_core_service._signals.append(signal)


def test_proactive_recommendations_empty_without_signals() -> None:
    _reset()
    result = brain_core_service.proactive_recommendations(101)
    assert result["total"] == 0
    assert result["items"] == []
    assert result["llm_summary"] is None


def test_proactive_recommendations_for_student_retention() -> None:
    _reset()
    _seed_signal(_student_signal(101, "STU-1"))
    _seed_signal(_student_signal(101, "STU-2"))
    result = brain_core_service.proactive_recommendations(101)
    assert result["total"] >= 1
    assert result["items"][0]["recommendation_type"] == "student_retention_playbook"


def test_proactive_recommendations_for_faculty_rebalance() -> None:
    _reset()
    _seed_signal(_faculty_signal(101, "FAC-1"))
    _seed_signal(_faculty_signal(101, "FAC-2"))
    result = brain_core_service.proactive_recommendations(101)
    assert any(item["recommendation_type"] == "faculty_capacity_rebalance" for item in result["items"])


def test_proactive_recommendations_include_llm_summary_when_enabled() -> None:
    _reset()
    brain_core_service.update_policy_profile(
        101,
        autonomy_level=3,
        require_approval_for_critical=True,
        default_approval_role="dean_office",
        enable_ai_reasoning=True,
    )
    _seed_signal(_student_signal(101, "STU-1"))
    _seed_signal(_student_signal(101, "STU-2"))
    with patch("app.modules.brain_core.service.llm_bridge.generate_explanation", return_value="LLM proactive summary"):
        result = brain_core_service.proactive_recommendations(101)
    assert result["llm_summary"] == "LLM proactive summary"
    assert result["ai_reasoning_enabled"] is True


def test_recommendations_endpoint_contract() -> None:
    _reset()
    _seed_signal(_student_signal(101, "STU-101"))
    _seed_signal(_student_signal(101, "STU-102"))
    resp = client.get("/api/admin/brain/recommendations/101", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["tenant_id"] == 101
    assert data["total"] >= 1
    assert isinstance(data["items"], list)