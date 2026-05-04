"""Phase CVII — Enrollments service hardening tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import app.modules.enrollments.service as svc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TENANT = 42


# ---------------------------------------------------------------------------
# Test 1: create_enrollment calls _record_outcome and _metric
# ---------------------------------------------------------------------------


def test_create_enrollment_records_outcome_and_metric():
    with (
        patch("app.modules.enrollments.service.create_entity_for_tenant", return_value={"id": 100}) as mock_create,
        patch("app.modules.enrollments.service.assert_billing_write_allowed") as mock_billing,
        patch("app.modules.enrollments.service.record_usage_event") as mock_metric,
        patch("app.modules.enrollments.service._record_outcome") as mock_outcome,
    ):
        payload = {
            "student_id": 50,
            "course_id": 60,
            "section_id": 70,
            "actor_id": "registrar@example.com",
        }
        result = svc.create_enrollment(payload, tenant_id=_TENANT)

    assert result["id"] == 100
    mock_billing.assert_called_once_with(_TENANT, action="enrollments.create")
    mock_outcome.assert_called_once_with(100, "enrollment_created", "registrar@example.com")
    mock_metric.assert_called_once_with(tenant_id=_TENANT, metric="enrollments_created", value=1)


# ---------------------------------------------------------------------------
# Test 2: update_enrollment calls _record_outcome and _metric
# ---------------------------------------------------------------------------


def test_update_enrollment_records_outcome_and_metric():
    with (
        patch("app.modules.enrollments.service.update_entity_for_tenant", return_value={"id": 100}) as mock_update,
        patch("app.modules.enrollments.service.record_usage_event") as mock_metric,
        patch("app.modules.enrollments.service._record_outcome") as mock_outcome,
    ):
        payload = {
            "status": "dropped",
            "actor_id": "advisor@example.com",
        }
        result = svc.update_enrollment(100, payload, tenant_id=_TENANT)

    assert result["id"] == 100
    mock_outcome.assert_called_once_with(100, "enrollment_updated", "advisor@example.com")
    mock_metric.assert_called_once_with(tenant_id=_TENANT, metric="enrollments_updated", value=1)


# ---------------------------------------------------------------------------
# Test 3: create_enrollment with missing actor_id defaults to "system"
# ---------------------------------------------------------------------------


def test_create_enrollment_defaults_actor_id_to_system():
    with (
        patch("app.modules.enrollments.service.create_entity_for_tenant", return_value={"id": 101}) as mock_create,
        patch("app.modules.enrollments.service.assert_billing_write_allowed") as mock_billing,
        patch("app.modules.enrollments.service.record_usage_event") as mock_metric,
        patch("app.modules.enrollments.service._record_outcome") as mock_outcome,
    ):
        payload = {
            "student_id": 50,
            "course_id": 60,
            "section_id": 70,
        }
        result = svc.create_enrollment(payload, tenant_id=_TENANT)

    assert result["id"] == 101
    mock_outcome.assert_called_once_with(101, "enrollment_created", "system")


# ---------------------------------------------------------------------------
# Test 4: _metric is fail-safe — exception does not propagate
# ---------------------------------------------------------------------------


def test_metric_fail_safe():
    """_metric must swallow exceptions and never propagate to caller."""
    with patch("app.modules.enrollments.service.record_usage_event", side_effect=RuntimeError("db down")):
        # Should not raise
        svc._metric(_TENANT, "enrollments_created")
