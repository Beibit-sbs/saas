from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantRequiredError
from app.modules.hr_staff_governance import schemas, service


def _db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


def test_create_staff_profile_enforces_safety_defaults() -> None:
    db = _db()
    created = SimpleNamespace(id=1, staff_ref="HR-1", status="DRAFT", source_reference=None, evidence_status=None, notes=None)
    request = schemas.HRStaffProfileCreate(staff_ref="HR-1", full_name="Ada Lovelace", limitations=[])
    with (
        patch("app.modules.hr_staff_governance.service.repository.repo_create_staff_profile", return_value=created) as mock_create,
        patch("app.modules.hr_staff_governance.service.repository.repo_record_staff_status_history"),
        patch("app.modules.hr_staff_governance.service.repository.repo_create_audit_event"),
    ):
        result = service.create_staff_profile(db, 1, "actor-1", request)
    assert result is created
    kwargs = mock_create.call_args.kwargs
    assert kwargs["human_review_required"] is True
    assert kwargs["fake_data"] is False
    assert kwargs["provider_connected"] is False
    assert kwargs["status"] == "DRAFT"
    assert "metadata_only_foundation" in kwargs["limitations_json"]


@pytest.mark.parametrize("tenant_id", [None, 0, -1, True, 1.2, "1", "bad"])
def test_invalid_tenant_fail_closed(tenant_id) -> None:
    db = _db()
    request = schemas.HRStaffProfileCreate(staff_ref="HR-1", full_name="Ada Lovelace")
    with pytest.raises(TenantRequiredError):
        service.create_staff_profile(db, tenant_id, "actor-1", request)  # type: ignore[arg-type]


def test_empty_actor_fails_closed() -> None:
    db = _db()
    request = schemas.HRStaffProfileCreate(staff_ref="HR-1", full_name="Ada Lovelace")
    with pytest.raises(DomainValidationError):
        service.create_staff_profile(db, 1, "", request)


def test_health_contract_is_fail_closed() -> None:
    db = _db()
    result = service.get_health_summary(db, 1)
    assert result["provider_connected"] is False
    assert result["live_provider_sync"] is False
    assert result["payroll_execution_enabled"] is False
    assert result["automatic_decision_enabled"] is False
    assert result["hidden_score_present"] is False
    assert result["fake_metrics"] is False
    assert result["route_count"] == 62
    assert result["table_count"] == 36