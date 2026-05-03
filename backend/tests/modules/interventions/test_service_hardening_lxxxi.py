from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.interventions.models import (
    InterventionCaseSeverity,
    InterventionCaseStatus,
)
from app.modules.interventions.schemas import (
    InterventionCaseCreateSchema,
    InterventionCaseStatusUpdateSchema,
)
from app.modules.interventions.service import InterventionService


@pytest.mark.asyncio
async def test_create_case_emits_created_event_after_persist_and_records_metric(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = MagicMock()
    committed = {"done": False}
    events: list[str] = []
    metrics: list[str] = []

    def _commit() -> None:
        committed["done"] = True

    def _emit_case_event(**kwargs) -> None:  # type: ignore[no-untyped-def]
        assert committed["done"] is True
        events.append(str(kwargs["event_type"]))

    db.commit.side_effect = _commit
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()

    service = InterventionService(db_session=db)

    monkeypatch.setattr(service, "_emit_case_event", _emit_case_event)
    monkeypatch.setattr(
        "app.modules.interventions.service.record_usage_event",
        lambda tenant_id, metric, value=1: metrics.append(str(metric)),
    )

    request = InterventionCaseCreateSchema(
        student_profile_id=None,
        severity=InterventionCaseSeverity.HIGH,
        title="Risk intervention case",
        description="Needs immediate intervention",
    )

    await service.create_case(tenant_id=1, request=request, actor="advisor@example.com")

    assert "interventions.case.created" in events
    assert "interventions_cases_created" in metrics


@pytest.mark.asyncio
async def test_update_status_emits_status_changed_after_persist_and_records_metric(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = MagicMock()
    committed = {"done": False}
    events: list[str] = []
    metrics: list[str] = []

    case = SimpleNamespace(
        id=101,
        case_type=SimpleNamespace(value="academic_risk"),
        status=InterventionCaseStatus.OPEN,
        severity=InterventionCaseSeverity.MEDIUM,
        student_profile_id=2001,
        version=2,
        resolved_at=None,
        updated_by="owner@example.com",
    )

    def _commit() -> None:
        committed["done"] = True

    def _emit_case_event(**kwargs) -> None:  # type: ignore[no-untyped-def]
        assert committed["done"] is True
        events.append(str(kwargs["event_type"]))

    db.commit.side_effect = _commit
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()

    service = InterventionService(db_session=db)

    async def _get_case(**kwargs):  # type: ignore[no-untyped-def]
        return case

    monkeypatch.setattr(service, "get_case", _get_case)
    monkeypatch.setattr(service, "_emit_case_event", _emit_case_event)
    monkeypatch.setattr(
        "app.modules.interventions.service.record_usage_event",
        lambda tenant_id, metric, value=1: metrics.append(str(metric)),
    )

    request = InterventionCaseStatusUpdateSchema(
        expected_version=2,
        status=InterventionCaseStatus.IN_PROGRESS,
        reason="Advisor took ownership",
    )
    result = await service.update_case_status(
        tenant_id=1,
        case_id=101,
        request=request,
        actor="advisor@example.com",
    )

    assert result.status == InterventionCaseStatus.IN_PROGRESS
    assert "interventions.case.status_changed" in events
    assert "interventions_case_status_updates" in metrics


@pytest.mark.asyncio
async def test_update_status_invalid_transition_raises_domain_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = MagicMock()
    events: list[str] = []

    case = SimpleNamespace(
        id=102,
        case_type=SimpleNamespace(value="academic_risk"),
        status=InterventionCaseStatus.CLOSED,
        severity=InterventionCaseSeverity.LOW,
        student_profile_id=2002,
        version=3,
        resolved_at=None,
        updated_by="owner@example.com",
    )

    service = InterventionService(db_session=db)

    async def _get_case(**kwargs):  # type: ignore[no-untyped-def]
        return case

    monkeypatch.setattr(service, "get_case", _get_case)
    monkeypatch.setattr(
        service,
        "_emit_case_event",
        lambda **kwargs: events.append(str(kwargs["event_type"])),
    )

    request = InterventionCaseStatusUpdateSchema(
        expected_version=3,
        status=InterventionCaseStatus.OPEN,
        reason="attempt reopen",
    )

    with pytest.raises(DomainValidationError, match="not allowed"):
        await service.update_case_status(
            tenant_id=1,
            case_id=102,
            request=request,
            actor="advisor@example.com",
        )

    assert events == []


@pytest.mark.asyncio
async def test_resolved_status_emits_outcome_event_records_metric_and_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = MagicMock()
    events: list[str] = []
    metrics: list[str] = []
    outcomes: list[dict] = []

    case = SimpleNamespace(
        id=103,
        case_type=SimpleNamespace(value="academic_risk"),
        status=InterventionCaseStatus.IN_PROGRESS,
        severity=InterventionCaseSeverity.HIGH,
        student_profile_id=2003,
        version=4,
        resolved_at=None,
        updated_by="owner@example.com",
    )

    service = InterventionService(
        db_session=db,
        on_case_outcome=lambda tenant_id, case_id, payload, actor="system": outcomes.append(
            {
                "tenant_id": tenant_id,
                "case_id": case_id,
                "payload": payload,
                "actor": actor,
            }
        ),
    )


    async def _get_case(**kwargs):  # type: ignore[no-untyped-def]
        return case

    monkeypatch.setattr(service, "get_case", _get_case)
    monkeypatch.setattr(
        service,
        "_emit_case_event",
        lambda **kwargs: events.append(str(kwargs["event_type"])),
    )
    monkeypatch.setattr(
        "app.modules.interventions.service.record_usage_event",
        lambda tenant_id, metric, value=1: metrics.append(str(metric)),
    )

    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    request = InterventionCaseStatusUpdateSchema(
        expected_version=4,
        status=InterventionCaseStatus.RESOLVED,
        reason="Student recovered",
    )

    result = await service.update_case_status(
        tenant_id=1,
        case_id=103,
        request=request,
        actor="advisor@example.com",
    )

    assert result.status == InterventionCaseStatus.RESOLVED
    assert "interventions.case.status_changed" in events
    assert "interventions.case_outcome.recorded" in events
    assert "interventions_case_status_updates" in metrics
    assert "interventions_case_outcomes_recorded" in metrics
    assert outcomes
    assert outcomes[0]["payload"]["outcome_type"] == "resolved"
    assert outcomes[0]["payload"]["effectiveness"] == "positive"
