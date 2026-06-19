from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantRequiredError
from app.modules.finance_procurement_asset import permissions, schemas, service


def _db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


def test_create_billing_evidence_enforces_safety_defaults() -> None:
    db = _db()
    created = SimpleNamespace(id=1, tenant_id=1, status="VISIBLE_METADATA_ONLY")
    request = schemas.FpaMetadataCreateRequest(reference_key="bill-1", title="Billing note", limitations=[])
    with (
        patch("app.modules.finance_procurement_asset.service.repository.create_family_row", return_value=created) as mock_create,
        patch("app.modules.finance_procurement_asset.service.repository.create_audit_event"),
    ):
        result = service.create_billing_evidence(db, 1, "actor-1", request)
    assert result["status"] == "VISIBLE_METADATA_ONLY"
    kwargs = mock_create.call_args.kwargs
    assert kwargs["human_review_required"] is True
    assert kwargs["payment_execution_enabled"] is False
    assert kwargs["automatic_procurement_approval_enabled"] is False
    assert "metadata_only_runtime" in kwargs["limitations_json"]


def test_create_receivables_metadata_enforces_metadata_only_defaults() -> None:
    db = _db()
    created = SimpleNamespace(id=2, tenant_id=1, status="VISIBLE_METADATA_ONLY")
    request = schemas.FpaMetadataCreateRequest(
        reference_key="student-receivable-1",
        title="Student receivable metadata",
        source_module="students",
        source_record_id=44,
        metadata={"student_profile_id": 44, "hardship_handoff_required": True},
        limitations=[],
    )
    with (
        patch("app.modules.finance_procurement_asset.service.repository.create_family_row", return_value=created) as mock_create,
        patch("app.modules.finance_procurement_asset.service.repository.create_audit_event"),
    ):
        result = service.create_receivables_metadata(db, 1, "actor-1", request)
    assert result["status"] == "VISIBLE_METADATA_ONLY"
    kwargs = mock_create.call_args.kwargs
    assert kwargs["source_module"] == "students"
    assert kwargs["source_record_id"] == 44
    assert kwargs["metadata_json"]["hardship_handoff_required"] is True
    assert kwargs["payment_execution_enabled"] is False
    assert kwargs["fake_finance_data"] is False


@pytest.mark.parametrize("tenant_id", [None, 0, -1, True, 1.2, "1", "bad"])
def test_invalid_tenant_fail_closed(tenant_id) -> None:
    db = _db()
    request = schemas.FpaMetadataCreateRequest(reference_key="vendor-1", title="Vendor")
    with pytest.raises(TenantRequiredError):
        service.create_vendor_metadata(db, tenant_id, "actor-1", request)  # type: ignore[arg-type]


def test_empty_actor_fails_closed() -> None:
    db = _db()
    request = schemas.FpaMetadataCreateRequest(reference_key="vendor-1", title="Vendor")
    with pytest.raises(DomainValidationError):
        service.create_vendor_metadata(db, 1, "", request)


def test_health_contract_is_fail_closed() -> None:
    db = _db()
    result = service.get_health(db, 1)
    assert result["provider_connected"] is False
    assert result["live_bank_sync"] is False
    assert result["live_erp_sync"] is False
    assert result["payment_execution_enabled"] is False
    assert result["automatic_decision_enabled"] is False
    assert result["hidden_score_present"] is False
    assert result["route_count"] == 57
    assert result["table_count"] == 24


def test_permissions_inventory_is_exact() -> None:
    db = _db()
    result = service.get_permissions(db, 1)
    assert result["permission_namespace"] == "finance_procurement_asset.*"
    assert result["permission_count"] == 51
    assert result["permissions"] == permissions.FINANCE_PROCUREMENT_ASSET_PERMISSIONS


def test_overview_contract_contains_counts() -> None:
    db = _db()
    result = service.get_overview(db, 1)
    assert result.selected_vertical == "Finance / Procurement / Asset Suite"
    assert result.table_count == 24
    assert result.route_count == 57
    assert result.permission_count == 51


def test_metadata_contract_contains_expected_files() -> None:
    db = _db()
    result = service.get_metadata_contract(db, 1)
    assert result.api_prefix == "/api/admin/finance-procurement-asset"
    assert len(result.module_files) == 8
    assert result.permission_count == 51


def test_create_audit_event_is_insert_only() -> None:
    db = _db()
    created = SimpleNamespace(id=7, tenant_id=1, status="RECORDED")
    request = schemas.FpaAuditEventCreateRequest(entity_type="billing", entity_id=3, action="recorded")
    with patch("app.modules.finance_procurement_asset.service.repository.create_audit_event", return_value=created) as mock_create:
        result = service.create_audit_event(db, 1, "actor-1", request)
    assert result["status"] == "RECORDED"
    assert mock_create.call_args.kwargs["human_review_required"] is True


def test_create_evidence_is_metadata_only() -> None:
    db = _db()
    created = SimpleNamespace(id=9, tenant_id=1, status="METADATA_ONLY")
    request = schemas.FpaEvidenceCreateRequest(reference_key="ev-1", title="Evidence")
    with patch("app.modules.finance_procurement_asset.service.repository.create_evidence_item", return_value=created) as mock_create:
        result = service.create_evidence(db, 1, "actor-1", request)
    assert result["status"] == "METADATA_ONLY"
    assert mock_create.call_args.kwargs["fake_payment_data"] is False
    assert mock_create.call_args.kwargs["provider_connected"] is False


def test_bridge_reads_are_metadata_only() -> None:
    db = _db()
    bridge = SimpleNamespace(
        id=1,
        tenant_id=1,
        status="METADATA_ONLY",
        reference_key="bridge-1",
        title="Executive bridge",
        source_module="procurement",
        source_record_id=10,
        metadata_json={},
        limitations_json=["metadata_only_runtime"],
        created_at=None,
        updated_at=None,
        read_only_first=True,
        mutation_allowed=False,
    )
    with patch("app.modules.finance_procurement_asset.service.repository.get_bridge_inputs", return_value=[bridge]):
        result = service.get_bridge_executive(db, 1)
    assert result.records[0].status == "METADATA_ONLY"
    assert result.payment_execution_enabled is False


def test_student_finance_bridge_reads_are_metadata_only() -> None:
    db = _db()
    bridge = SimpleNamespace(
        id=2,
        tenant_id=1,
        status="METADATA_ONLY",
        reference_key="student-finance-bridge-1",
        title="Student finance bridge",
        source_module="students",
        source_record_id=44,
        metadata_json={"student_profile_id": 44},
        limitations_json=["metadata_only_runtime", "no_payment_execution"],
        created_at=None,
        updated_at=None,
        read_only_first=True,
        mutation_allowed=False,
    )
    with patch("app.modules.finance_procurement_asset.service.repository.get_bridge_inputs", return_value=[bridge]) as mock_inputs:
        result = service.get_bridge_student_finance(db, 1)
    assert mock_inputs.call_args.args[2] == "student_finance"
    assert result.records[0].source_module == "students"
    assert result.payment_execution_enabled is False
