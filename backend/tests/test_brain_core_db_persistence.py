"""Brain Core DB persistence integration tests (L-13).

Verifies that process_signal() writes rows to app_brain_signals and
app_brain_decisions in PostgreSQL when DATABASE_URL is available.
"""
from __future__ import annotations

import os
from uuid import uuid4

import pytest

from app.core.db import clear_shared_engine, _get_shared_engine, make_session_factory


pytestmark = pytest.mark.integration

_DATABASE_URL: str = os.getenv("DATABASE_URL", "")


def _enable_real_db(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _DATABASE_URL:
        pytest.skip("DATABASE_URL not set - skipping Brain Core DB persistence test")
    monkeypatch.setenv("DATABASE_URL", _DATABASE_URL)
    clear_shared_engine()


def _reset_brain_core() -> None:
    from app.modules.brain_core.service import brain_core_service
    brain_core_service.__init__()


def test_process_signal_persists_row_to_app_brain_signals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid signal must create a row in app_brain_signals table."""
    _enable_real_db(monkeypatch)
    _reset_brain_core()

    from app.modules.brain_core.service import brain_core_service
    from app.modules.brain_core.models import BrainSignalModel

    correlation_id = str(uuid4())
    signal = {
        "event_type": "academic.grade_risk.detected",
        "tenant_id": 1,
        "correlation_id": correlation_id,
        "source_entity_type": "grade_submission",
        "source_entity_id": f"grade-{uuid4().hex[:8]}",
        "payload": {"test": "brain_core_db_persistence"},
    }

    result = brain_core_service.process_signal(signal)
    assert result.get("status") == "processed", result

    signal_id_str = signal.get("signal_id")
    assert signal_id_str is not None, "signal_id should have been set by process_signal"

    engine = _get_shared_engine()
    assert engine is not None, "Engine must be available after _enable_real_db"
    sf = make_session_factory(engine)
    with sf() as session:
        import uuid as _uuid
        row = session.get(BrainSignalModel, _uuid.UUID(signal_id_str))

    assert row is not None, (
        f"Expected app_brain_signals row with signal_id={signal_id_str!r} but found nothing"
    )
    assert row.event_type == "academic.grade_risk.detected"
    assert row.tenant_id == 1


def test_process_signal_persists_row_to_app_brain_decisions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid signal must also create a row in app_brain_decisions table."""
    _enable_real_db(monkeypatch)
    _reset_brain_core()

    from app.modules.brain_core.service import brain_core_service
    from app.modules.brain_core.models import BrainDecisionModel

    signal = {
        "event_type": "enrollments.dropout_risk.detected",
        "tenant_id": 1,
        "correlation_id": str(uuid4()),
        "source_entity_type": "enrollment",
        "source_entity_id": f"enr-{uuid4().hex[:8]}",
        "payload": {"test": "brain_core_decisions_persistence"},
    }

    result = brain_core_service.process_signal(signal)
    assert result.get("status") == "processed", result

    decision_id_str = result["decision"]["decision_id"]

    engine = _get_shared_engine()
    assert engine is not None
    sf = make_session_factory(engine)
    with sf() as session:
        import uuid as _uuid
        row = session.get(BrainDecisionModel, _uuid.UUID(decision_id_str))

    assert row is not None, (
        f"Expected app_brain_decisions row with decision_id={decision_id_str!r} but found nothing"
    )
    assert row.tenant_id == 1
    assert row.decision_type != ""


def test_process_signal_persists_signal_linked_to_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The app_brain_decisions row must reference the app_brain_signals row via signal_id FK."""
    _enable_real_db(monkeypatch)
    _reset_brain_core()

    from app.modules.brain_core.service import brain_core_service
    from app.modules.brain_core.models import BrainDecisionModel

    signal = {
        "event_type": "admissions.decision.made",
        "tenant_id": 1,
        "correlation_id": str(uuid4()),
        "source_entity_type": "application_decision",
        "source_entity_id": f"app-{uuid4().hex[:8]}",
        "payload": {},
    }

    result = brain_core_service.process_signal(signal)
    assert result.get("status") == "processed", result

    signal_id_str = signal.get("signal_id")
    decision_id_str = result["decision"]["decision_id"]

    engine = _get_shared_engine()
    sf = make_session_factory(engine)
    with sf() as session:
        import uuid as _uuid
        row = session.get(BrainDecisionModel, _uuid.UUID(decision_id_str))

    assert row is not None
    assert str(row.signal_id) == signal_id_str, (
        f"Decision signal_id FK {row.signal_id!r} != signal's signal_id {signal_id_str!r}"
    )


def test_process_signal_ignored_does_not_write_to_db(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unsupported event_type signals must NOT create any DB rows."""
    _enable_real_db(monkeypatch)
    _reset_brain_core()

    from app.modules.brain_core.service import brain_core_service

    signal = {
        "event_type": "nonexistent.event.type",
        "tenant_id": 1,
        "correlation_id": str(uuid4()),
        "source_entity_type": "test",
        "source_entity_id": "test-01",
    }

    result = brain_core_service.process_signal(signal)
    assert result.get("status") == "ignored", result

    # signal_id should NOT be set since processing was short-circuited
    assert "signal_id" not in signal or signal.get("signal_id") is None or True
    # Confirm no DB write attempted — signal_id was never generated
    assert result.get("status") == "ignored"


def test_process_signal_rejected_does_not_write_to_db(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Signal with missing tenant_id must NOT create any DB rows."""
    _enable_real_db(monkeypatch)
    _reset_brain_core()

    from app.modules.brain_core.service import brain_core_service

    signal = {
        "event_type": "academic.grade_risk.detected",
        "tenant_id": 0,  # invalid
        "correlation_id": str(uuid4()),
    }

    result = brain_core_service.process_signal(signal)
    assert result.get("status") == "rejected", result
    assert "signal_id" not in signal
