"""Brain Core signal round-trip tests.

Verifies that modules can emit signals via brain_core_service.process_signal()
and that the service correctly processes (not ignores/rejects) them.
"""
from __future__ import annotations

from uuid import uuid4

import pytest


def _reset() -> None:
    from app.modules.brain_core.service import brain_core_service

    brain_core_service.__init__()


# ---------------------------------------------------------------------------
# Registry registration checks
# ---------------------------------------------------------------------------


def test_new_event_types_registered_in_registry() -> None:
    """admissions.decision.made and scheduling.section.scheduled must be in SignalRegistry."""
    from app.modules.brain_core.registry import SignalRegistry

    assert SignalRegistry.is_supported("admissions.decision.made")
    assert SignalRegistry.is_supported("scheduling.section.scheduled")


# ---------------------------------------------------------------------------
# process_signal round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "event_type,source_entity_type",
    [
        ("admissions.decision.made", "application_decision"),
        ("enrollments.dropout_risk.detected", "enrollment"),
        ("academic.grade_risk.detected", "grade_submission"),
        ("scheduling.section.scheduled", "section_schedule"),
        ("academic.attendance_risk.detected", "student_profile"),
    ],
)
def test_process_signal_accepted(event_type: str, source_entity_type: str) -> None:
    """Each module event type must be accepted (status != ignored/rejected)."""
    _reset()

    from app.modules.brain_core.service import brain_core_service

    result = brain_core_service.process_signal({
        "event_type": event_type,
        "tenant_id": 1,
        "correlation_id": str(uuid4()),
        "source_entity_type": source_entity_type,
        "source_entity_id": "42",
        "payload": {"test": True},
    })

    assert result.get("status") not in {"ignored", "rejected"}, (
        f"Signal '{event_type}' was {result.get('status')}: {result}"
    )
    assert len(brain_core_service._signals) >= 1


def test_process_signal_appends_to_signal_store() -> None:
    """After processing a valid signal, it must be stored in the internal signal list."""
    _reset()

    from app.modules.brain_core.service import brain_core_service

    assert len(brain_core_service._signals) == 0

    brain_core_service.process_signal({
        "event_type": "academic.grade_risk.detected",
        "tenant_id": 99,
        "correlation_id": str(uuid4()),
        "source_entity_type": "grade_submission",
        "source_entity_id": "7",
        "payload": {"risk_level": "high", "current_grade": 1.5},
    })

    assert len(brain_core_service._signals) == 1
    assert brain_core_service._signals[0]["event_type"] == "academic.grade_risk.detected"


def test_unknown_event_type_is_ignored() -> None:
    """An unregistered event type must be silently ignored (never raise)."""
    _reset()

    from app.modules.brain_core.service import brain_core_service

    result = brain_core_service.process_signal({
        "event_type": "totally.unknown.event",
        "tenant_id": 1,
        "correlation_id": str(uuid4()),
        "source_entity_type": "anything",
        "source_entity_id": "1",
        "payload": {},
    })

    assert result["status"] == "ignored"
    assert len(brain_core_service._signals) == 0
