"""Phase CVI — Counseling service hardening tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import app.modules.counseling.service as svc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TENANT = 42


def _make_appt_record(appt_id: int = 1) -> dict:
    return {
        "id": appt_id,
        "student_id": 10,
        "counselor_id": 20,
        "session_type": "individual",
        "scheduled_at": "2025-01-15T10:00:00",
        "status": "requested",
    }


def _make_case_record(case_id: int = 5) -> dict:
    return {
        "id": case_id,
        "student_id": 10,
        "counselor_id": 20,
        "risk_level": "medium",
        "status": "open",
    }


# ---------------------------------------------------------------------------
# Test 1: request_appointment calls _record_outcome and _metric
# ---------------------------------------------------------------------------


def test_request_appointment_records_outcome_and_metric():
    with (
        patch("app.modules.counseling.service.create_entity_for_tenant", return_value={"id": 7}) as mock_create,
        patch("app.modules.counseling.service.record_usage_event") as mock_metric,
        patch("app.modules.counseling.service._record_outcome") as mock_outcome,
        patch("app.modules.counseling.service.EventPublisher") as mock_ep,
    ):
        mock_ep.return_value.publish_event = MagicMock()
        result = svc.request_appointment(
            student_id=10,
            counselor_id=20,
            session_type="individual",
            scheduled_at="2025-01-15T10:00:00",
            tenant_id=_TENANT,
        )

    assert result.appointment_id == 7
    mock_outcome.assert_called_once_with(7, "counseling_appointment_requested", "10")
    mock_metric.assert_called_once_with(tenant_id=_TENANT, metric="counseling_appointments_requested", value=1)


# ---------------------------------------------------------------------------
# Test 2: open_case calls _record_outcome and _metric
# ---------------------------------------------------------------------------


def test_open_case_records_outcome_and_metric():
    with (
        patch("app.modules.counseling.service.create_entity_for_tenant", return_value={"id": 5}) as mock_create,
        patch("app.modules.counseling.service.record_usage_event") as mock_metric,
        patch("app.modules.counseling.service._record_outcome") as mock_outcome,
        patch("app.modules.counseling.service.EventPublisher") as mock_ep,
    ):
        mock_ep.return_value.publish_event = MagicMock()
        result = svc.open_case(
            student_id=10,
            counselor_id=20,
            risk_level="medium",
            tenant_id=_TENANT,
        )

    assert result.case_id == 5
    mock_outcome.assert_called_once_with(5, "counseling_case_opened", "10")
    mock_metric.assert_called_once_with(tenant_id=_TENANT, metric="counseling_cases_opened", value=1)


# ---------------------------------------------------------------------------
# Test 3: report_crisis calls _record_outcome and _metric
# ---------------------------------------------------------------------------


def test_report_crisis_records_outcome_and_metric():
    with (
        patch("app.modules.counseling.service.create_entity_for_tenant", return_value={"id": 99}) as mock_create,
        patch("app.modules.counseling.service.record_usage_event") as mock_metric,
        patch("app.modules.counseling.service._record_outcome") as mock_outcome,
        patch("app.modules.counseling.service.EventPublisher") as mock_ep,
    ):
        mock_ep.return_value.publish_event = MagicMock()
        result = svc.report_crisis(
            student_id=10,
            risk_level="high",
            description="Severe distress reported",
            tenant_id=_TENANT,
        )

    assert result.report_id == 99
    mock_outcome.assert_called_once_with(99, "crisis_report_created", "10")
    mock_metric.assert_called_once_with(tenant_id=_TENANT, metric="crisis_reports_created", value=1)


# ---------------------------------------------------------------------------
# Test 4: _metric is fail-safe — exception does not propagate
# ---------------------------------------------------------------------------


def test_metric_fail_safe():
    """_metric must swallow exceptions and never propagate to caller."""
    with patch("app.modules.counseling.service.record_usage_event", side_effect=RuntimeError("db down")):
        # Should not raise
        svc._metric(_TENANT, "counseling_appointments_requested")
