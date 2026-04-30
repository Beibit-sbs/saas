"""Test for interventions outcome feedback to Brain Core."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.modules.interventions.models import (
    InterventionAssigneeType,
    InterventionCaseSeverity,
    InterventionCaseStatus,
    InterventionCaseType,
)
from app.modules.interventions.schemas import InterventionCaseStatusUpdateSchema
from app.modules.interventions.service import InterventionService


def _now():
    return datetime.now(UTC)


def _make_case(
    *,
    id: int = 1,
    tenant_id: int = 101,
    severity=InterventionCaseSeverity.HIGH,
    status=InterventionCaseStatus.OPEN,
    version: int = 1,
    student_profile_id: int | None = 101,
):
    case = MagicMock()
    case.id = id
    case.tenant_id = tenant_id
    case.severity = severity
    case.status = status
    case.version = version
    case.student_profile_id = student_profile_id
    case.case_type = InterventionCaseType.ACADEMIC_RISK
    case.assignee_type = InterventionAssigneeType.GROUP
    case.assignee_ref = "dean_office"
    case.due_at = _now() + timedelta(days=3)
    case.resolved_at = None
    return case


@pytest.mark.asyncio
async def test_update_case_status_to_resolved_triggers_brain_core_callback():
    """Test that resolving a case triggers Brain Core outcome callback."""
    # Setup
    db = MagicMock()
    brain_core_callback = MagicMock()
    service = InterventionService(db_session=db, on_case_outcome=brain_core_callback)

    case = _make_case(id=42, tenant_id=101, status=InterventionCaseStatus.OPEN, version=1)
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    # Patch EventPublisher to avoid actual event publishing
    with patch("app.modules.interventions.service.EventPublisher") as mock_publisher:
        mock_pub_instance = MagicMock()
        mock_publisher.return_value = mock_pub_instance

        # Execute
        request = InterventionCaseStatusUpdateSchema(
            status=InterventionCaseStatus.RESOLVED,
            reason="Student improved attendance",
            expected_version=1,
        )
        result = await service.update_case_status(
            tenant_id=101,
            case_id=42,
            request=request,
            actor="advisor@example.com",
        )

    # Verify
    assert result == case
    assert case.status == InterventionCaseStatus.RESOLVED
    assert case.resolved_at is not None

    # Verify Brain Core callback was invoked with correct params
    brain_core_callback.assert_called_once()
    call_args = brain_core_callback.call_args
    assert call_args[1]["case_id"] == "42"
    assert call_args[1]["payload"]["outcome_type"] == "resolved"
    assert call_args[1]["payload"]["effectiveness"] == "positive"
    assert call_args[1]["payload"]["notes"] == "Student improved attendance"
    assert call_args[1]["actor"] == "system"

    # Verify event was published
    mock_pub_instance.publish_event.assert_called_once()
    pub_call_args = mock_pub_instance.publish_event.call_args
    assert pub_call_args[1]["event_type"] == "interventions.case_outcome.recorded"
    assert pub_call_args[1]["aggregate_type"] == "intervention_case"


@pytest.mark.asyncio
async def test_update_case_status_to_closed_triggers_brain_core_callback():
    """Test that closing a case also triggers Brain Core callback with neutral effectiveness."""
    # Setup
    db = MagicMock()
    brain_core_callback = MagicMock()
    service = InterventionService(db_session=db, on_case_outcome=brain_core_callback)

    case = _make_case(id=43, tenant_id=102, status=InterventionCaseStatus.IN_PROGRESS, version=2)
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    # Patch EventPublisher
    with patch("app.modules.interventions.service.EventPublisher") as mock_publisher:
        mock_pub_instance = MagicMock()
        mock_publisher.return_value = mock_pub_instance

        # Execute
        request = InterventionCaseStatusUpdateSchema(
            status=InterventionCaseStatus.CLOSED,
            reason="Case archived",
            expected_version=2,
        )
        await service.update_case_status(
            tenant_id=102,
            case_id=43,
            request=request,
            actor="admin@example.com",
        )

    # Verify callback effectiveness is 'neutral' for CLOSED
    brain_core_callback.assert_called_once()
    call_args = brain_core_callback.call_args
    assert call_args[1]["payload"]["effectiveness"] == "neutral"
    assert call_args[1]["payload"]["outcome_type"] == "closed"


@pytest.mark.asyncio
async def test_update_case_status_without_callback_doesnt_fail():
    """Test that update works even if no Brain Core callback is registered."""
    # Setup without callback
    db = MagicMock()
    service = InterventionService(db_session=db, on_case_outcome=None)

    case = _make_case(id=44, tenant_id=103, status=InterventionCaseStatus.OPEN, version=1)
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    # Patch EventPublisher
    with patch("app.modules.interventions.service.EventPublisher"):
        # Execute - should not raise
        request = InterventionCaseStatusUpdateSchema(
            status=InterventionCaseStatus.RESOLVED,
            reason="Done",
            expected_version=1,
        )
        result = await service.update_case_status(
            tenant_id=103,
            case_id=44,
            request=request,
            actor="user@example.com",
        )

    # Verify
    assert result == case
    assert case.status == InterventionCaseStatus.RESOLVED


@pytest.mark.asyncio
async def test_update_case_status_with_callback_exception_logs_warning():
    """Test that exceptions in callback are caught and logged."""
    # Setup
    db = MagicMock()
    brain_core_callback = MagicMock(side_effect=ValueError("Brain Core unavailable"))
    service = InterventionService(db_session=db, on_case_outcome=brain_core_callback)

    case = _make_case(id=45, tenant_id=104, status=InterventionCaseStatus.OPEN, version=1)
    db.execute.return_value.scalar_one_or_none.return_value = case
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    db.commit = MagicMock()

    # Patch EventPublisher
    with patch("app.modules.interventions.service.EventPublisher"):
        # Execute - should not raise, just log
        request = InterventionCaseStatusUpdateSchema(
            status=InterventionCaseStatus.RESOLVED,
            reason="Done",
            expected_version=1,
        )
        result = await service.update_case_status(
            tenant_id=104,
            case_id=45,
            request=request,
            actor="user@example.com",
        )

    # Verify update still happened
    assert result == case
    assert case.status == InterventionCaseStatus.RESOLVED
    # Callback was attempted
    brain_core_callback.assert_called_once()
