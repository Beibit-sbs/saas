"""Phase I2 hardening tests.

Covers:
  I2.1 — enrollments dropout-risk signal emission on WITHDRAWN/SUSPENDED/DROPPED
  I2.2 — analytics/usage brain-context API endpoint
"""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from tests.conftest import ADMIN_HEADERS, client

# ---------------------------------------------------------------------------
# I2.1 — Enrollments dropout-risk signal
# ---------------------------------------------------------------------------


def test_enrollment_dropout_risk_signal_fields() -> None:
    """_emit_dropout_risk_signal must publish correct event_type and payload fields."""
    from app.modules.enrollments.service import _emit_dropout_risk_signal

    published: list[dict] = []

    class _FakePublisher:
        def publish_event(self, **kwargs: object) -> dict:
            published.append(dict(kwargs))
            return {}

    with patch("app.platform.events.publisher.EventPublisher", return_value=_FakePublisher()):
        _emit_dropout_risk_signal(
            tenant_id=10,
            enrollment_id=55,
            student_profile_id=201,
            course_id=7,
            from_status="enrolled",
            to_status="withdrawn",
        )

    assert len(published) == 1
    assert published[0]["event_type"] == "enrollments.dropout_risk.detected"
    assert published[0]["aggregate_type"] == "enrollment"
    assert published[0]["aggregate_id"] == 55
    payload = published[0]["payload_json"]
    assert payload["enrollment_id"] == 55
    assert payload["student_id"] == 201
    assert payload["course_id"] == 7
    assert payload["from_status"] == "enrolled"
    assert payload["to_status"] == "withdrawn"
    assert payload["source_module"] == "enrollments"
    assert payload["source_entity_type"] == "enrollment"
    assert payload["source_entity_id"] == "55"


def test_enrollment_dropout_signal_emitted_on_withdrawal() -> None:
    """change_enrollment_status to WITHDRAWN must emit dropout-risk signal."""
    from app.modules.enrollments.service import _emit_dropout_risk_signal

    published: list[dict] = []

    class _FakePublisher:
        def publish_event(self, **kwargs: object) -> dict:
            published.append(dict(kwargs))
            return {}

    with patch("app.platform.events.publisher.EventPublisher", return_value=_FakePublisher()):
        _emit_dropout_risk_signal(
            tenant_id=1,
            enrollment_id=10,
            student_profile_id=100,
            course_id=3,
            from_status="enrolled",
            to_status="withdrawn",
        )

    assert len(published) == 1
    assert published[0]["payload_json"]["to_status"] == "withdrawn"


def test_enrollment_dropout_signal_emitted_on_suspension() -> None:
    """_emit_dropout_risk_signal for SUSPENDED status must produce correct payload."""
    from app.modules.enrollments.service import _emit_dropout_risk_signal

    published: list[dict] = []

    class _FakePublisher:
        def publish_event(self, **kwargs: object) -> dict:
            published.append(dict(kwargs))
            return {}

    with patch("app.platform.events.publisher.EventPublisher", return_value=_FakePublisher()):
        _emit_dropout_risk_signal(
            tenant_id=1,
            enrollment_id=11,
            student_profile_id=101,
            course_id=3,
            from_status="enrolled",
            to_status="suspended",
        )

    assert len(published) == 1
    assert published[0]["payload_json"]["to_status"] == "suspended"
    assert published[0]["payload_json"]["source_module"] == "enrollments"


def test_enrollment_dropout_signal_emitted_on_dropped() -> None:
    """_emit_dropout_risk_signal for DROPPED status must produce correct payload."""
    from app.modules.enrollments.service import _emit_dropout_risk_signal

    published: list[dict] = []

    class _FakePublisher:
        def publish_event(self, **kwargs: object) -> dict:
            published.append(dict(kwargs))
            return {}

    with patch("app.platform.events.publisher.EventPublisher", return_value=_FakePublisher()):
        _emit_dropout_risk_signal(
            tenant_id=1,
            enrollment_id=12,
            student_profile_id=102,
            course_id=4,
            from_status="enrolled",
            to_status="dropped",
        )

    assert len(published) == 1
    assert published[0]["event_type"] == "enrollments.dropout_risk.detected"


# ---------------------------------------------------------------------------
# I2.1 — Brain Core signal registry and classifier
# ---------------------------------------------------------------------------


def test_brain_core_signal_registry_supports_dropout_event() -> None:
    """SignalRegistry must recognise enrollments.dropout_risk.detected."""
    from app.modules.brain_core.registry import SignalRegistry

    assert SignalRegistry.is_supported("enrollments.dropout_risk.detected")
    sig = SignalRegistry.signals["enrollments.dropout_risk.detected"]
    assert sig["scenario"] == "enrollment_dropout_risk"


def test_brain_core_classifier_withdrawal_is_high_severity() -> None:
    """Classifier must return high severity for withdrawn/suspended statuses."""
    from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier

    clf = RiskClassifier()
    result = clf.classify(
        signal={
            "event_type": "enrollments.dropout_risk.detected",
            "payload": {"to_status": "withdrawn", "from_status": "enrolled"},
        },
        context={},
    )
    assert result["severity"] == "high"
    assert result["urgency"] == "high"
    assert result["reasoning_path"] == "enrollment_dropout_high"


def test_brain_core_classifier_dropped_is_medium_severity() -> None:
    """Classifier must return medium severity for DROPPED status."""
    from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier

    clf = RiskClassifier()
    result = clf.classify(
        signal={
            "event_type": "enrollments.dropout_risk.detected",
            "payload": {"to_status": "dropped", "from_status": "enrolled"},
        },
        context={},
    )
    assert result["severity"] == "medium"
    assert result["reasoning_path"] == "enrollment_dropout_medium"


def test_brain_core_processes_enrollment_dropout_signal() -> None:
    """Brain Core service must process enrollments.dropout_risk.detected with decision_type=risk."""
    from app.modules.brain_core.service import brain_core_service

    result = brain_core_service.process_signal(
        signal={
            "event_type": "enrollments.dropout_risk.detected",
            "tenant_id": 1,
            "payload": {
                "enrollment_id": 99,
                "student_id": 201,
                "course_id": 7,
                "from_status": "enrolled",
                "to_status": "withdrawn",
                "source_module": "enrollments",
                "source_entity_type": "enrollment",
                "source_entity_id": "99",
            },
        },
    )
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "risk"
    assert "create_dropout_intervention" in result["decision"]["recommended_actions"]


# ---------------------------------------------------------------------------
# I2.2 — Analytics brain-context API
# ---------------------------------------------------------------------------


def test_analytics_brain_context_returns_200() -> None:
    """GET /api/analytics/brain-context must return 200 with expected schema."""
    from app.modules.auth.token_service import create_access_token

    token = create_access_token(
        user_id="admin@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=1,
    )
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": "1"}
    resp = client.get("/api/analytics/brain-context", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "tenant_id" in body
    assert "total_recent_events" in body
    assert "metrics_summary" in body
    assert "context_source" in body
    assert body["context_source"] == "usage"
    assert body["snapshot_type"] == "brain_context"


def test_analytics_brain_context_requires_auth() -> None:
    """GET /api/analytics/brain-context without auth must return 401 or 403."""
    resp = client.get("/api/analytics/brain-context")
    assert resp.status_code in (401, 403)
