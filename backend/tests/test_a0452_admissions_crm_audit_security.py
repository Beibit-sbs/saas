from __future__ import annotations

from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = BACKEND_DIR / "app" / "modules" / "admissions_crm"


def _module_text() -> str:
    return "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))


def test_no_hard_delete_patterns_present() -> None:
    text = _module_text().lower()
    assert "session.delete" not in text
    assert ".delete(" not in text
    assert "delete from" not in text


def test_no_future_batch_subsystems_present() -> None:
    text = _module_text().lower()
    forbidden = [
        "communications/threads",
        "campaigns",
        "interviews/sessions",
        "decisions",
        "handoffs",
        "analytics/pipeline",
        "dashboards/executive",
        "brain",
    ]
    for marker in forbidden:
        assert marker not in text


def test_no_provider_live_or_autonomous_execution_present() -> None:
    text = _module_text().lower()
    forbidden = [
        "provider_live_enabled = true",
        "autonomous_decision_enabled = true",
        "hidden_score_present = true",
        "requests.post",
        "httpx",
    ]
    for marker in forbidden:
        assert marker not in text


def test_safety_constants_present() -> None:
    text = _module_text()
    required = [
        "FAKE_METRICS = False",
        "PROVIDER_LIVE_ENABLED = False",
        "AUTONOMOUS_DECISION_ENABLED = False",
        "HIDDEN_SCORE_PRESENT = False",
        "HUMAN_REVIEW_REQUIRED = True",
    ]
    for marker in required:
        assert marker in text
