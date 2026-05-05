"""Tests for Brain Core decision → UI notification (Audit item #15).

DoD: Brain decision of type risk/preventive/compliance with priority critical/high
     → a notification row is dispatched via NotificationRepository.
"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch


from app.modules.brain_core.service import BrainCoreService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service() -> BrainCoreService:
    """Build a BrainCoreService with all dependencies mocked out."""
    svc = BrainCoreService.__new__(BrainCoreService)
    svc._observability = MagicMock()
    svc._signals = []
    svc._decisions = []
    svc._explanations = {}
    svc._context_builder = MagicMock()
    svc._classifier = MagicMock()
    svc._knowledge = MagicMock()
    svc._policy_resolver = MagicMock()
    svc._reasoning = MagicMock()
    svc._planner = MagicMock()
    svc._policy_guard = MagicMock()
    svc._dispatcher = MagicMock()
    svc._explanation = MagicMock()
    svc._outcome_tracker = MagicMock()
    svc._quality_tracker = MagicMock()
    svc._policy_tuner = MagicMock()
    svc._signal_dedup_cache = {}
    return svc


def _make_decision(
    *,
    tenant_id: int = 5,
    priority: str = "high",
    decision_type: str = "risk",
    situation_type: str = "academic_risk",
) -> dict:
    return {
        "decision_id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "priority": priority,
        "decision_type": decision_type,
        "situation_type": situation_type,
        "recommended_actions": ["review_student_record"],
    }


def _make_signal(*, tenant_id: int = 5, recipient: str | None = None) -> dict:
    sig: dict = {
        "event_type": "admissions.decision.made",
        "tenant_id": tenant_id,
        "source_entity_type": "application",
        "source_entity_id": "app-42",
    }
    if recipient is not None:
        sig["recipient"] = recipient
    return sig


# ---------------------------------------------------------------------------
# Unit: _emit_decision_notification — filtering logic
# ---------------------------------------------------------------------------

class TestEmitDecisionNotificationFiltering:
    def test_returns_none_for_medium_priority(self) -> None:
        svc = _make_service()
        decision = _make_decision(priority="medium")
        result = svc._emit_decision_notification(decision=decision, signal=_make_signal())
        assert result is None

    def test_returns_none_for_low_priority(self) -> None:
        svc = _make_service()
        decision = _make_decision(priority="low")
        result = svc._emit_decision_notification(decision=decision, signal=_make_signal())
        assert result is None

    def test_returns_none_for_non_notifiable_decision_type(self) -> None:
        """Optimization decisions should not generate notifications."""
        svc = _make_service()
        decision = _make_decision(priority="high", decision_type="optimization")
        result = svc._emit_decision_notification(decision=decision, signal=_make_signal())
        assert result is None

    def test_returns_none_for_invalid_tenant_id(self) -> None:
        svc = _make_service()
        decision = _make_decision(priority="high", tenant_id=0)
        result = svc._emit_decision_notification(decision=decision, signal=_make_signal(tenant_id=0))
        assert result is None

    def test_high_priority_risk_is_notifiable(self) -> None:
        svc = _make_service()
        decision = _make_decision(priority="high", decision_type="risk")
        mock_repo = MagicMock()
        mock_repo.dispatch.return_value = {"id": 1, "status": "queued"}
        with patch("app.platform.repository.notification_repository.NotificationRepository", return_value=mock_repo):
            result = svc._emit_decision_notification(decision=decision, signal=_make_signal())
        assert result is not None

    def test_critical_priority_preventive_is_notifiable(self) -> None:
        svc = _make_service()
        decision = _make_decision(priority="critical", decision_type="preventive")
        mock_repo = MagicMock()
        mock_repo.dispatch.return_value = {"id": 2, "status": "queued"}
        with patch("app.platform.repository.notification_repository.NotificationRepository", return_value=mock_repo):
            result = svc._emit_decision_notification(decision=decision, signal=_make_signal())
        assert result is not None

    def test_high_priority_compliance_is_notifiable(self) -> None:
        svc = _make_service()
        decision = _make_decision(priority="high", decision_type="compliance")
        mock_repo = MagicMock()
        mock_repo.dispatch.return_value = {"id": 3, "status": "queued"}
        with patch("app.platform.repository.notification_repository.NotificationRepository", return_value=mock_repo):
            result = svc._emit_decision_notification(decision=decision, signal=_make_signal())
        assert result is not None


# ---------------------------------------------------------------------------
# Unit: _emit_decision_notification — dispatch payload correctness
# ---------------------------------------------------------------------------

class TestEmitDecisionNotificationPayload:
    def _dispatch_call(self, *, priority: str = "high", decision_type: str = "risk",
                       situation_type: str = "academic_risk", recipient: str | None = None) -> MagicMock:
        svc = _make_service()
        decision = _make_decision(
            tenant_id=7,
            priority=priority,
            decision_type=decision_type,
            situation_type=situation_type,
        )
        signal = _make_signal(tenant_id=7, recipient=recipient)
        mock_repo = MagicMock()
        mock_repo.dispatch.return_value = {"id": 99, "status": "queued"}
        with patch("app.platform.repository.notification_repository.NotificationRepository", return_value=mock_repo):
            svc._emit_decision_notification(decision=decision, signal=signal)
        return mock_repo.dispatch

    def test_channel_is_in_app(self) -> None:
        mock_dispatch = self._dispatch_call()
        _, kwargs = mock_dispatch.call_args
        assert kwargs["channel"] == "in_app"

    def test_tenant_id_passed_correctly(self) -> None:
        mock_dispatch = self._dispatch_call()
        _, kwargs = mock_dispatch.call_args
        assert kwargs["tenant_id"] == 7

    def test_subject_contains_priority_and_situation_type(self) -> None:
        mock_dispatch = self._dispatch_call(priority="high", situation_type="academic_risk")
        _, kwargs = mock_dispatch.call_args
        assert "HIGH" in kwargs["subject"]
        assert "Academic Risk" in kwargs["subject"]

    def test_payload_includes_decision_id(self) -> None:
        mock_dispatch = self._dispatch_call()
        _, kwargs = mock_dispatch.call_args
        assert "decision_id" in kwargs["payload"]
        assert kwargs["payload"]["decision_id"]  # non-empty

    def test_payload_includes_decision_type_and_priority(self) -> None:
        mock_dispatch = self._dispatch_call(decision_type="risk", priority="high")
        _, kwargs = mock_dispatch.call_args
        assert kwargs["payload"]["decision_type"] == "risk"
        assert kwargs["payload"]["priority"] == "high"

    def test_recipient_from_signal_used_as_target(self) -> None:
        mock_dispatch = self._dispatch_call(recipient="advisor@university.edu")
        _, kwargs = mock_dispatch.call_args
        assert kwargs["target"] == "advisor@university.edu"

    def test_default_target_when_no_recipient_in_signal(self) -> None:
        mock_dispatch = self._dispatch_call(recipient=None)
        _, kwargs = mock_dispatch.call_args
        assert kwargs["target"] == "tenant:7:admin"

    def test_observability_counter_incremented(self) -> None:
        svc = _make_service()
        decision = _make_decision(tenant_id=7, priority="high", decision_type="risk")
        signal = _make_signal(tenant_id=7)
        mock_repo = MagicMock()
        mock_repo.dispatch.return_value = {"id": 1, "status": "queued"}
        with patch("app.platform.repository.notification_repository.NotificationRepository", return_value=mock_repo):
            svc._emit_decision_notification(decision=decision, signal=signal)
        svc._observability.increment.assert_any_call("decision_notifications_emitted_total")


# ---------------------------------------------------------------------------
# Unit: _emit_decision_notification — error resilience
# ---------------------------------------------------------------------------

class TestEmitDecisionNotificationResilience:
    def test_returns_none_on_repo_exception(self) -> None:
        """A NotificationRepository failure must not propagate; service continues."""
        svc = _make_service()
        decision = _make_decision(priority="high", decision_type="risk")
        mock_repo = MagicMock()
        mock_repo.dispatch.side_effect = RuntimeError("DB unavailable")
        with patch("app.platform.repository.notification_repository.NotificationRepository", return_value=mock_repo):
            result = svc._emit_decision_notification(decision=decision, signal=_make_signal())
        assert result is None


# ---------------------------------------------------------------------------
# Integration: process_signal calls _emit_decision_notification
# ---------------------------------------------------------------------------

class TestProcessSignalTriggersNotification:
    _VALID_SIGNAL = {
        "event_type": "admissions.decision.made",
        "tenant_id": 3,
        "source_entity_type": "application",
        "source_entity_id": "app-100",
        "recipient": "dean@university.edu",
    }

    def _make_process_ready_service(self) -> BrainCoreService:
        from app.modules.brain_core.policy.tenant_policy import TenantPolicyProfile
        svc = _make_service()
        svc._context_builder.build_context.return_value = {}
        svc._classifier.classify.return_value = {
            "situation_type": "academic_risk", "severity": "high", "urgency": "high",
            "reasoning_path": "admissions_decision_high",
        }
        svc._knowledge.retrieve.return_value = {}
        svc._policy_resolver.get_profile.return_value = TenantPolicyProfile(
            tenant_id=3, autonomy_level=2, require_approval_for_critical=False,
            default_approval_role="dean_office", enable_ai_reasoning=False,
        )
        svc._reasoning.decide.return_value = {
            "decision_type": "risk",
            "priority": "high",
            "recommended_actions": ["flag_for_review"],
            "requires_approval": False,
            "confidence_score": 0.9,
            "severity_score": 0.85,
            "urgency_score": 0.80,
        }
        svc._planner.build_plan.return_value = []
        svc._policy_guard.validate.return_value = MagicMock(
            approved=True, requires_approval=False, reason="auto", approval_role=None,
        )
        svc._dispatcher.dispatch.return_value = []
        svc._explanation.build.return_value = {"summary": "Risk detected"}
        return svc

    def test_notification_emitted_on_high_risk_decision(self) -> None:
        svc = self._make_process_ready_service()
        with (
            patch.object(svc, "_check_duplicate_signal", return_value=None),
            patch.object(svc, "_try_persist_signal_to_db"),
            patch.object(svc, "_try_persist_decision_to_db"),
            patch.object(svc, "_emit_decision_notification", wraps=svc._emit_decision_notification) as mock_emit,
            patch("app.platform.repository.notification_repository.NotificationRepository") as mock_repo_cls,
        ):
            mock_repo_cls.return_value.dispatch.return_value = {"id": 55, "status": "queued"}
            result = svc.process_signal(dict(self._VALID_SIGNAL))

        assert result["status"] == "processed"
        mock_emit.assert_called_once()
        # emit was called with the decision dict and signal
        call_kwargs = mock_emit.call_args[1]
        assert call_kwargs["decision"]["decision_type"] == "risk"
        assert call_kwargs["decision"]["priority"] == "high"
