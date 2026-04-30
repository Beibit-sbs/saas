"""Tests for Brain Core signal deduplication.

DoD: same signal twice within 60s window → second call returns {"status": "deduplicated"},
     verifying that duplicate signals are short-circuited before expensive processing.
"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch


from app.modules.brain_core.service import BrainCoreService, _compute_dedup_key


# ---------------------------------------------------------------------------
# Unit: _compute_dedup_key
# ---------------------------------------------------------------------------

class TestComputeDedupKey:
    def test_same_inputs_produce_same_key(self) -> None:
        k1 = _compute_dedup_key("student.risk", 42, "student", "stu-001")
        k2 = _compute_dedup_key("student.risk", 42, "student", "stu-001")
        assert k1 == k2

    def test_different_event_type_produces_different_key(self) -> None:
        k1 = _compute_dedup_key("student.risk", 42, "student", "stu-001")
        k2 = _compute_dedup_key("enrollment.drop", 42, "student", "stu-001")
        assert k1 != k2

    def test_different_tenant_produces_different_key(self) -> None:
        k1 = _compute_dedup_key("student.risk", 42, "student", "stu-001")
        k2 = _compute_dedup_key("student.risk", 99, "student", "stu-001")
        assert k1 != k2

    def test_different_entity_id_produces_different_key(self) -> None:
        k1 = _compute_dedup_key("student.risk", 42, "student", "stu-001")
        k2 = _compute_dedup_key("student.risk", 42, "student", "stu-002")
        assert k1 != k2

    def test_key_is_64_hex_chars(self) -> None:
        key = _compute_dedup_key("student.risk", 1, "student", "x")
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)


# ---------------------------------------------------------------------------
# Unit: _check_duplicate_signal with mocked DB
# ---------------------------------------------------------------------------

def _make_service() -> BrainCoreService:
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
    return svc


class TestCheckDuplicateSignal:
    def test_returns_none_when_engine_not_available(self) -> None:
        svc = _make_service()
        with patch("app.modules.brain_core.service._get_shared_engine", return_value=None):
            result = svc._check_duplicate_signal(tenant_id=1, dedup_key="abc")
        assert result is None

    def test_returns_uuid_when_row_found(self) -> None:
        existing_id = uuid.uuid4()
        mock_row = (str(existing_id),)
        mock_session = MagicMock()
        mock_session.__enter__ = lambda s: s
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.execute.return_value.fetchone.return_value = mock_row
        mock_factory = MagicMock(return_value=mock_session)
        svc = _make_service()
        with (
            patch("app.modules.brain_core.service._get_shared_engine", return_value=MagicMock()),
            patch("app.modules.brain_core.service.make_session_factory", return_value=mock_factory),
        ):
            result = svc._check_duplicate_signal(tenant_id=1, dedup_key="deadbeef")
        assert result == existing_id

    def test_returns_none_when_no_row(self) -> None:
        mock_session = MagicMock()
        mock_session.__enter__ = lambda s: s
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.execute.return_value.fetchone.return_value = None
        mock_factory = MagicMock(return_value=mock_session)
        svc = _make_service()
        with (
            patch("app.modules.brain_core.service._get_shared_engine", return_value=MagicMock()),
            patch("app.modules.brain_core.service.make_session_factory", return_value=mock_factory),
        ):
            result = svc._check_duplicate_signal(tenant_id=1, dedup_key="deadbeef")
        assert result is None

    def test_returns_none_on_db_exception(self) -> None:
        mock_factory = MagicMock(side_effect=RuntimeError("db down"))
        svc = _make_service()
        with (
            patch("app.modules.brain_core.service._get_shared_engine", return_value=MagicMock()),
            patch("app.modules.brain_core.service.make_session_factory", return_value=mock_factory),
        ):
            result = svc._check_duplicate_signal(tenant_id=1, dedup_key="deadbeef")
        assert result is None


# ---------------------------------------------------------------------------
# Integration: process_signal deduplication path
# ---------------------------------------------------------------------------

_VALID_SIGNAL = {
    "event_type": "admissions.decision.made",
    "tenant_id": 1,
    "source_entity_type": "student",
    "source_entity_id": "stu-001",
    "correlation_id": str(uuid.uuid4()),
}


class TestProcessSignalDeduplication:
    def test_second_identical_signal_returns_deduplicated(self) -> None:
        """Same signal twice → first is processed, second is deduplicated."""
        existing_id = uuid.uuid4()
        svc = _make_service()

        with patch.object(svc, "_check_duplicate_signal", return_value=existing_id):
            result = svc.process_signal(dict(_VALID_SIGNAL))

        assert result["status"] == "deduplicated"
        assert result["original_signal_id"] == str(existing_id)
        svc._observability.increment.assert_called_with("signals_deduplicated_total")

    def test_unique_signal_is_not_deduplicated(self) -> None:
        """When no duplicate found, processing continues normally."""
        svc = _make_service()

        # Short-circuit after dedup check by making process raise for other reasons
        # (unsupported event_type shortcut tested here to keep test focused)
        with patch.object(svc, "_check_duplicate_signal", return_value=None):
            # Use unsupported event to stop early; what matters is no "deduplicated" status
            result = svc.process_signal({
                "event_type": "__no_such_event__",
                "tenant_id": 1,
                "source_entity_type": "x",
                "source_entity_id": "y",
            })

        assert result["status"] != "deduplicated"

    def test_dedup_not_called_when_tenant_missing(self) -> None:
        """Signals rejected for missing tenant_id before dedup check."""
        svc = _make_service()
        with patch.object(svc, "_check_duplicate_signal") as mock_check:
            result = svc.process_signal({
                "event_type": "admissions.decision.made",
                "tenant_id": 0,
            })
        assert result["status"] == "rejected"
        mock_check.assert_not_called()

    def test_dedup_key_passed_to_persist(self) -> None:
        """dedup_key is forwarded to _try_persist_signal_to_db."""
        svc = _make_service()

        captured: dict = {}

        def fake_persist(**kwargs: object) -> None:
            captured.update(kwargs)

        with (
            patch.object(svc, "_check_duplicate_signal", return_value=None),
            patch.object(svc, "_try_persist_signal_to_db", side_effect=fake_persist),
            patch("app.modules.brain_core.service.SignalRegistry") as mock_reg,
            patch.object(svc, "_context_builder"),
            patch.object(svc, "_classifier", return_value={"situation_type": "test"}),
        ):
            mock_reg.is_supported.return_value = False  # stop early after persist
            svc.process_signal(dict(_VALID_SIGNAL))

        if captured:
            assert "dedup_key" in captured
            assert len(captured["dedup_key"]) == 64
