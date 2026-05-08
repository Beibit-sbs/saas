"""A-018.4 Events Management maturity closure tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import app.modules.events_management.service as em_svc
from app.modules.events_management import router as events_management_router


_PATCHES = (
    "app.modules.events_management.service.create_entity_for_tenant",
    "app.modules.events_management.service.list_entities_for_tenant",
    "app.modules.events_management.service.EventPublisher",
    "app.modules.events_management.service.log_admin_action",
    "app.modules.events_management.service.record_usage_event",
)


def _mocks(existing_events=None, existing_registrations=None):
    events = list(existing_events or [])
    registrations = list(existing_registrations or [])
    counter = {"n": 0}

    def _create(*args):
        if len(args) == 3 and isinstance(args[0], str):
            table, data, _tenant_id = args
        elif len(args) == 3:
            _tenant_id, table, data = args
        else:
            raise AssertionError(f"unexpected create args: {args!r}")

        counter["n"] += 1
        row = {"id": f"row-{counter['n']}", **dict(data)}
        if table == "campus_events":
            events.append(row)
        elif table == "event_registrations":
            registrations.append(row)
        return row

    def _list(*args):
        if len(args) == 2 and isinstance(args[0], str):
            table, _tenant_id = args
        elif len(args) == 2:
            _tenant_id, table = args
        else:
            raise AssertionError(f"unexpected list args: {args!r}")

        if table == "campus_events":
            return list(events)
        if table == "event_registrations":
            return list(registrations)
        return []

    pub = MagicMock()
    pub.return_value.publish_event = MagicMock()
    return _create, _list, pub, events, registrations


def _run(create, lst, pub, fn, *args, **kwargs):
    with patch(_PATCHES[0], create), \
        patch(_PATCHES[1], lst), \
        patch(_PATCHES[2], pub), \
        patch(_PATCHES[3]), \
        patch(_PATCHES[4]):
        return fn(*args, **kwargs)


def test_events_management_router_contract_registered() -> None:
    assert events_management_router.router.prefix == "/api/admin/events-management"


def test_create_event_emits_created_event_and_requires_organizer() -> None:
    create, lst, pub, _, _ = _mocks()
    result = _run(
        create,
        lst,
        pub,
        em_svc.create_event,
        7,
        title="Open Day",
        category_id="cat-1",
        organizer_id="org-1",
        capacity=120,
        start_time="2026-08-01T09:00:00+00:00",
        end_time="2026-08-01T13:00:00+00:00",
    )
    assert result["status"] == "DRAFT"
    emitted = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    assert "event.created" in emitted

    with pytest.raises(ValueError, match="organizer_id"):
        _run(
            create,
            lst,
            pub,
            em_svc.create_event,
            7,
            title="Open Day",
            category_id="cat-1",
            organizer_id="",
            capacity=120,
            start_time="2026-08-01T09:00:00+00:00",
            end_time="2026-08-01T13:00:00+00:00",
        )


def test_invalid_time_window_is_rejected() -> None:
    create, lst, pub, _, _ = _mocks()
    with pytest.raises(ValueError, match="start_time must be earlier"):
        _run(
            create,
            lst,
            pub,
            em_svc.create_event,
            7,
            title="Open Day",
            category_id="cat-1",
            organizer_id="org-1",
            capacity=120,
            start_time="2026-08-01T13:00:00+00:00",
            end_time="2026-08-01T09:00:00+00:00",
        )


def test_publish_open_start_complete_emit_lifecycle_events() -> None:
    events = [
        {
            "id": "e-1",
            "status": "DRAFT",
            "capacity": 10,
            "registered_count": 0,
            "category_id": "cat-1",
            "tenant_id": 7,
        }
    ]
    create, lst, pub, ev_rows, _ = _mocks(existing_events=events)

    _run(create, lst, pub, em_svc.publish_event, 7, event_id="e-1")
    _run(create, lst, pub, em_svc.open_registration, 7, event_id="e-1")
    _run(create, lst, pub, em_svc.start_event, 7, event_id="e-1")
    result = _run(create, lst, pub, em_svc.complete_event, 7, event_id="e-1")

    assert result["status"] == "COMPLETED"
    assert ev_rows[0]["status"] == "COMPLETED"
    emitted = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    for event_type in ("event.published", "event.registration_opened", "event.started", "event.completed"):
        assert event_type in emitted


def test_cancel_emits_cancelled_event_and_terminal_guard() -> None:
    create, lst, pub, _, _ = _mocks(existing_events=[{"id": "e-2", "status": "PUBLISHED", "tenant_id": 4}])
    result = _run(create, lst, pub, em_svc.cancel_event, 4, event_id="e-2")
    assert result["status"] == "CANCELLED"

    emitted = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    assert "event.cancelled" in emitted

    create2, lst2, pub2, _, _ = _mocks(existing_events=[{"id": "e-3", "status": "COMPLETED", "tenant_id": 4}])
    with pytest.raises(ValueError, match="terminal"):
        _run(create2, lst2, pub2, em_svc.cancel_event, 4, event_id="e-3")


def test_registration_duplicate_and_capacity_guards() -> None:
    base_event = {
        "id": "e-1",
        "status": "REGISTRATION_OPEN",
        "capacity": 1,
        "registered_count": 0,
        "category_id": "cat-1",
        "tenant_id": 7,
    }
    create, lst, pub, ev_rows, regs = _mocks(existing_events=[base_event])
    first = _run(create, lst, pub, em_svc.register_participant, 7, event_id="e-1", student_id="s-1")
    assert first["registration_full"] is True
    assert ev_rows[0]["registered_count"] == 1
    assert len(regs) == 1

    emitted = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    assert "event.registration_full" in emitted

    with pytest.raises(ValueError, match="already registered"):
        _run(create, lst, pub, em_svc.register_participant, 7, event_id="e-1", student_id="s-1")

    with pytest.raises(ValueError, match="capacity reached"):
        _run(create, lst, pub, em_svc.register_participant, 7, event_id="e-1", student_id="s-2")


def test_invalid_transition_rejected() -> None:
    create, lst, pub, _, _ = _mocks(existing_events=[{"id": "e-1", "status": "IN_PROGRESS", "tenant_id": 9}])
    with pytest.raises(ValueError, match="Cannot transition"):
        _run(create, lst, pub, em_svc.publish_event, 9, event_id="e-1")


def test_tenant_guard_rejects_invalid_tenant() -> None:
    create, lst, pub, _, _ = _mocks()
    with pytest.raises(ValueError, match="tenant_id"):
        _run(
            create,
            lst,
            pub,
            em_svc.create_event,
            0,
            title="Open Day",
            category_id="cat-1",
            organizer_id="org-1",
            capacity=120,
            start_time="2026-08-01T09:00:00+00:00",
            end_time="2026-08-01T13:00:00+00:00",
        )


def test_events_management_events_present_in_platform_contracts() -> None:
    from app.platform.event_ingestion.types import VALID_EVENT_TYPES
    from app.platform.events.registry import EXACT_EVENT_REGISTRY

    expected = {
        "event.created",
        "event.published",
        "event.registration_opened",
        "event.registration_full",
        "event.started",
        "event.completed",
        "event.cancelled",
    }
    for event_type in expected:
        assert event_type in VALID_EVENT_TYPES
        assert event_type in EXACT_EVENT_REGISTRY


def test_brain_core_campus_operations_covers_events_management_events() -> None:
    from app.modules.brain_core.constants import EVENTS_MANAGEMENT_EVENT_TYPES, SUPPORTED_SIGNAL_EVENT_TYPES
    from app.modules.brain_core.registry import DecisionRegistry, SignalRegistry

    assert EVENTS_MANAGEMENT_EVENT_TYPES
    assert EVENTS_MANAGEMENT_EVENT_TYPES.issubset(SUPPORTED_SIGNAL_EVENT_TYPES)

    allowed = set(DecisionRegistry.decisions["campus_operations"]["allowed_event_types"])
    assert EVENTS_MANAGEMENT_EVENT_TYPES.issubset(allowed)

    assert SignalRegistry.signals["event.published"]["scenario"] == "campus_operations"
    assert SignalRegistry.signals["event.cancelled"]["scenario"] == "campus_operations"


def test_kpi_lineage_includes_events_management_metrics() -> None:
    from app.platform.kpi.service import EVENT_DERIVED_METRIC_LINEAGE, METRIC_TITLES

    assert "events_published_count" in METRIC_TITLES
    assert "events_registration_full_count" in METRIC_TITLES

    assert "event.published" in EVENT_DERIVED_METRIC_LINEAGE["events_published_count"]
    assert "event.completed" in EVENT_DERIVED_METRIC_LINEAGE["events_completed_count"]
    assert "event.cancelled" in EVENT_DERIVED_METRIC_LINEAGE["events_cancelled_count"]


def test_list_filters_for_events_and_registrations() -> None:
    events = [
        {"id": "e-1", "status": "PUBLISHED", "category_id": "cat-1", "tenant_id": 5},
        {"id": "e-2", "status": "DRAFT", "category_id": "cat-2", "tenant_id": 5},
    ]
    regs = [
        {"id": "r-1", "event_id": "e-1", "student_id": "s-1", "tenant_id": 5},
        {"id": "r-2", "event_id": "e-2", "student_id": "s-2", "tenant_id": 5},
    ]
    create, lst, pub, _, _ = _mocks(existing_events=events, existing_registrations=regs)

    by_status = _run(create, lst, pub, em_svc.list_events, 5, status="PUBLISHED")
    by_category = _run(create, lst, pub, em_svc.list_events, 5, category_id="cat-2")
    by_student = _run(create, lst, pub, em_svc.list_registrations, 5, student_id="s-1")

    assert len(by_status) == 1
    assert by_status[0]["id"] == "e-1"
    assert len(by_category) == 1
    assert by_category[0]["id"] == "e-2"
    assert len(by_student) == 1
    assert by_student[0]["id"] == "r-1"
