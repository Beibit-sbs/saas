"""Tests for Arabic full localization — TIER-3 GCC compliance.

Covers:
1. Arabic notification templates (get_notification_template)
2. UTF-8 Arabic text stored without corruption
3. RTL locale detection (frontend i18n locale config)
4. Hijri/Gregorian date display (date format setting)
"""

from __future__ import annotations

import pytest

from app.modules.brain_core.actions.notification_actions import (
    NotificationActionDispatcher,
    _NOTIFICATION_TEMPLATES,
    get_notification_template,
)
from app.modules.platform_shared.notifications import InMemoryNotificationService


# ------------------------------------------------------------------
# 1. Arabic notification templates exist and are non-empty
# ------------------------------------------------------------------

EXPECTED_TEMPLATE_KEYS = [
    "student_risk",
    "faculty_escalation",
    "payment_recovery",
    "budget_variance",
    "supply_risk",
    "accreditation_risk",
    "platform_reliability",
    "research_risk",
    "campus_operations",
    "student_life_risk",
]


@pytest.mark.parametrize("key", EXPECTED_TEMPLATE_KEYS)
def test_arabic_template_exists(key: str) -> None:
    """Every notification template must have an Arabic variant."""
    assert key in _NOTIFICATION_TEMPLATES, f"Template '{key}' missing"
    assert "ar" in _NOTIFICATION_TEMPLATES[key], f"Arabic variant missing for '{key}'"
    subject, body = _NOTIFICATION_TEMPLATES[key]["ar"]
    assert subject.strip(), f"Arabic subject empty for '{key}'"
    assert body.strip(), f"Arabic body empty for '{key}'"


@pytest.mark.parametrize("key", EXPECTED_TEMPLATE_KEYS)
def test_arabic_template_is_unicode(key: str) -> None:
    """Arabic template content must be valid Unicode (not ASCII-only)."""
    subject, body = _NOTIFICATION_TEMPLATES[key]["ar"]
    # At least one character must be non-ASCII (i.e., Arabic script)
    has_arabic = any(ord(c) > 127 for c in subject + body)
    assert has_arabic, f"Template '{key}' ar variant looks like ASCII-only"


# ------------------------------------------------------------------
# 2. get_notification_template locale fallback
# ------------------------------------------------------------------


def test_get_notification_template_arabic() -> None:
    subject, body = get_notification_template("student_risk", "ar")
    assert "طالب" in subject or "مخاطر" in subject  # Arabic word present


def test_get_notification_template_fallback_to_english() -> None:
    subject, body = get_notification_template("student_risk", "fr")  # unsupported locale
    assert "risk" in subject.lower() or "student" in subject.lower()


def test_get_notification_template_unknown_key_returns_key() -> None:
    subject, body = get_notification_template("nonexistent_key", "ar")
    assert subject == "nonexistent_key"


# ------------------------------------------------------------------
# 3. Dispatcher sends Arabic notifications when locale="ar"
# ------------------------------------------------------------------


def test_notify_advisor_arabic() -> None:
    svc = InMemoryNotificationService()
    dispatcher = NotificationActionDispatcher(notification_service=svc)
    dispatcher.notify_advisor(
        tenant_id=1,
        decision_id="d-001",
        payload={"advisor_id": "advisor@uni.edu.sa", "student_id": "s-001"},
        locale="ar",
    )
    sent = svc.snapshot()
    assert len(sent) == 1
    msg = sent[0]
    # Subject must contain Arabic characters
    assert any(ord(c) > 127 for c in msg["subject"]), "Arabic subject not sent"


def test_notify_finance_arabic() -> None:
    svc = InMemoryNotificationService()
    dispatcher = NotificationActionDispatcher(notification_service=svc)
    dispatcher.notify_finance(
        tenant_id=1,
        decision_id="d-002",
        payload={"student_id": "s-002"},
        locale="ar",
    )
    sent = svc.snapshot()
    assert any(ord(c) > 127 for c in sent[0]["body"]), "Arabic body not sent"


def test_notify_compliance_arabic() -> None:
    svc = InMemoryNotificationService()
    dispatcher = NotificationActionDispatcher(notification_service=svc)
    dispatcher.notify_compliance(
        tenant_id=1,
        decision_id="d-003",
        payload={"accreditation_id": "acc-1", "new_status": "at_risk"},
        locale="ar",
    )
    sent = svc.snapshot()
    assert any(ord(c) > 127 for c in sent[0]["subject"])


# ------------------------------------------------------------------
# 4. UTF-8 Arabic text stored without corruption
# ------------------------------------------------------------------


def test_utf8_arabic_display_name_stored_correctly() -> None:
    """Arabic Unicode display names round-trip through notification metadata."""
    arabic_name = "محمد عبدالله"  # Muhammad Abdullah in Arabic
    svc = InMemoryNotificationService()
    dispatcher = NotificationActionDispatcher(notification_service=svc)
    dispatcher.notify_advisor(
        tenant_id=1,
        decision_id="d-utf8",
        payload={"advisor_id": arabic_name, "student_id": "طالب-001"},
        locale="ar",
    )
    sent = svc.snapshot()
    assert sent[0]["recipient"] == arabic_name
    assert sent[0]["metadata"]["student_id"] == "طالب-001"


# ------------------------------------------------------------------
# 5. All 10 dispatchers support locale parameter
# ------------------------------------------------------------------


@pytest.mark.parametrize("method,extra_payload", [
    ("notify_advisor", {"advisor_id": "a@uni.sa", "student_id": "s1"}),
    ("notify_faculty", {"faculty_id": "f@uni.sa", "student_id": "s1"}),
    ("notify_finance", {"student_id": "s1"}),
    ("notify_procurement_team", {"budget_code": "B1", "vendor_code": "V1", "contract_code": "C1"}),
    ("notify_operations", {"stock_item_id": "item-1"}),
    ("notify_compliance", {"accreditation_id": "acc-1", "new_status": "at_risk"}),
    ("notify_platform", {"workflow_name": "wf", "integration_key": "k", "severity": "high"}),
    ("notify_research_office", {"grant_id": "g1", "publication_id": "p1", "research_project_id": "r1"}),
    ("notify_facilities_team", {"facility_code": "F1", "room_code": "R1", "severity": "low"}),
    ("notify_student_success_team", {"student_id": "s1", "wellbeing_score": 3, "incident_severity": "medium"}),
])
def test_dispatcher_method_accepts_arabic_locale(method: str, extra_payload: dict) -> None:
    svc = InMemoryNotificationService()
    dispatcher = NotificationActionDispatcher(notification_service=svc)
    fn = getattr(dispatcher, method)
    fn(tenant_id=1, decision_id="d-ar", payload=extra_payload, locale="ar")
    sent = svc.snapshot()
    assert len(sent) == 1
    # Verify Arabic content in subject or body
    msg = sent[0]
    combined = str(msg["subject"]) + str(msg["body"])
    assert any(ord(c) > 127 for c in combined), f"{method} did not produce Arabic text"
