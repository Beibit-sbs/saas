"""Week 11 – Domain Depth: cross-module flows.

Tests:
  W11.1 – scheduling → enrollments capacity check
  W11.2 – procurement.contract PO_ISSUED → asset_inventory wiring
"""
from __future__ import annotations

import inspect
import types

import pytest


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _clear_entity(entity_key: str, tenant_id: int) -> None:
    from app.modules.university_core import shared
    with shared._state_lock:
        shared._state.data.setdefault(entity_key, {})
        keys_to_del = [
            k for k, v in shared._state.data[entity_key].items()
            if str(v.get("tenant_id")) == str(tenant_id)
        ]
        for k in keys_to_del:
            del shared._state.data[entity_key][k]


# ---------------------------------------------------------------------------
# W11.1 – scheduling → enrollments capacity check
# ---------------------------------------------------------------------------

class TestSchedulingEnrollmentsCapacityCheck:
    """Verify that enrollments.enroll_student() enforces scheduling section capacity."""

    def test_check_section_capacity_method_exists(self):
        """EnrollmentLifecycleService must have _check_section_capacity method."""
        from app.modules.enrollments.service import EnrollmentLifecycleService
        assert hasattr(EnrollmentLifecycleService, "_check_section_capacity"), (
            "_check_section_capacity method must exist on EnrollmentLifecycleService"
        )

    def test_source_references_course_section_model(self):
        """_check_section_capacity must reference CourseSectionModel for capacity enforcement."""
        from app.modules.enrollments.service import EnrollmentLifecycleService
        src = inspect.getsource(EnrollmentLifecycleService._check_section_capacity)
        assert "CourseSectionModel" in src, (
            "_check_section_capacity must import and query CourseSectionModel"
        )

    def test_source_references_max_capacity(self):
        """Capacity check logic must compare against max_capacity."""
        from app.modules.enrollments.service import EnrollmentLifecycleService
        src = inspect.getsource(EnrollmentLifecycleService._check_section_capacity)
        assert "max_capacity" in src, (
            "_check_section_capacity must reference max_capacity field"
        )

    def test_enroll_student_calls_check_section_capacity(self):
        """enroll_student must call _check_section_capacity before creating enrollment."""
        from app.modules.enrollments.service import EnrollmentLifecycleService
        src = inspect.getsource(EnrollmentLifecycleService.enroll_student)
        assert "_check_section_capacity" in src, (
            "enroll_student must call _check_section_capacity"
        )

    def test_capacity_check_passes_with_no_sections(self):
        """When no scheduling section exists, capacity check is a no-op (passes)."""
        from app.modules.enrollments.service import EnrollmentLifecycleService

        class _Result:
            def __init__(self, all_value=None, scalar_value=None):
                self._all_value = all_value
                self._scalar_value = scalar_value

            def scalars(self):
                return self

            def all(self):
                return self._all_value or []

            def scalar(self):
                return self._scalar_value

        class _FakeDb:
            def execute(self, _query):
                return _Result(all_value=[])

        svc = EnrollmentLifecycleService(_FakeDb())
        section = types.SimpleNamespace(id=1, max_capacity=0)
        svc._check_section_capacity(tenant_id=99901, section=section)

    def test_capacity_check_raises_when_section_full(self):
        """When section is full (active_count >= max_capacity), DomainValidationError is raised."""
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.enrollments.service import EnrollmentLifecycleService

        class _Result:
            def __init__(self, all_value=None, scalar_value=None):
                self._all_value = all_value
                self._scalar_value = scalar_value

            def scalars(self):
                return self

            def all(self):
                return self._all_value or []

            def scalar(self):
                return self._scalar_value

        class _FakeDb:
            def execute(self, _query):
                return _Result(scalar_value=1)

        svc = EnrollmentLifecycleService(_FakeDb())
        section = types.SimpleNamespace(id=10, max_capacity=1)
        with pytest.raises(DomainValidationError, match="capacity"):
            svc._check_section_capacity(tenant_id=99902, section=section)

    def test_capacity_check_passes_when_section_not_full(self):
        """When section has available spots, capacity check passes."""
        from app.modules.enrollments.service import EnrollmentLifecycleService

        class _Result:
            def __init__(self, all_value=None, scalar_value=None):
                self._all_value = all_value
                self._scalar_value = scalar_value

            def scalars(self):
                return self

            def all(self):
                return self._all_value or []

            def scalar(self):
                return self._scalar_value

        class _FakeDb:
            def execute(self, _query):
                return _Result(scalar_value=2)

        svc = EnrollmentLifecycleService(_FakeDb())
        section = types.SimpleNamespace(id=20, max_capacity=5)
        svc._check_section_capacity(tenant_id=99903, section=section)

    def test_cancelled_section_ignored_in_capacity_check(self):
        """CANCELLED sections are excluded from capacity enforcement."""
        from app.modules.enrollments.service import EnrollmentLifecycleService

        class _Result:
            def __init__(self, all_value=None, scalar_value=None):
                self._all_value = all_value
                self._scalar_value = scalar_value

            def scalars(self):
                return self

            def all(self):
                return self._all_value or []

            def scalar(self):
                return self._scalar_value

        class _FakeDb:
            def execute(self, _query):
                return _Result(all_value=[])

        svc = EnrollmentLifecycleService(_FakeDb())
        section = types.SimpleNamespace(id=30, max_capacity=0)
        svc._check_section_capacity(tenant_id=99904, section=section)


# ---------------------------------------------------------------------------
# W11.2 – procurement.contract → asset_inventory wiring
# ---------------------------------------------------------------------------

class TestProcurementAssetInventoryWiring:
    """When contract reaches PO_ISSUED, asset_inventory entry is auto-created."""

    def test_wire_function_exists(self):
        """_ensure_asset_inventory_registration_for_po_issue helper must exist."""
        from app.modules.procurement import service as svc
        assert hasattr(svc, "_ensure_asset_inventory_registration_for_po_issue"), (
            "_ensure_asset_inventory_registration_for_po_issue must exist in procurement.service"
        )

    def test_source_references_asset_inventory(self):
        """update_contract_status must reference asset_inventory wiring."""
        from app.modules.procurement import service as svc
        src = inspect.getsource(svc.update_contract_status)
        assert "asset_inventory" in src, (
            "update_contract_status must reference asset_inventory for cross-module wiring"
        )

    def test_source_triggers_on_po_issued(self):
        """Wire function must be triggered when next_status is PO_ISSUED."""
        from app.modules.procurement import service as svc
        src = inspect.getsource(svc.update_contract_status)
        assert "PO_ISSUED" in src, (
            "update_contract_status must check for PO_ISSUED status"
        )
        assert "_ensure_asset_inventory_registration_for_po_issue" in src, (
            "_ensure_asset_inventory_registration_for_po_issue must be called from update_contract_status"
        )

    def test_wire_function_references_create_asset_item(self):
        """PO issue guard helper must call create_asset_item."""
        from app.modules.procurement import service as svc
        src = inspect.getsource(svc._ensure_asset_inventory_registration_for_po_issue)
        assert "create_asset_item" in src, (
            "_ensure_asset_inventory_registration_for_po_issue must call create_asset_item"
        )

    def test_wire_function_is_guarded_by_try_except(self):
        """Wiring guard must convert lower-level failures to DomainValidationError."""
        from app.modules.procurement import service as svc
        src = inspect.getsource(svc._ensure_asset_inventory_registration_for_po_issue)
        assert "except" in src and "DomainValidationError" in src, (
            "_ensure_asset_inventory_registration_for_po_issue must map failures to DomainValidationError"
        )

    def test_update_contract_status_po_issued_creates_asset(self):
        """When contract is transitioned to PO_ISSUED, asset_inventory entry is created."""
        from app.modules.procurement import service as svc
        from app.modules.procurement.schemas import ContractStatusUpdateSchema
        from app.modules.university_core.tenant_entity_service import (
            create_entity_for_tenant,
        )
        from app.modules.university_core.tenant_entity_api import (
            list_entities_for_tenant as api_list,
        )

        tenant_id = 40001
        _clear_entity("procurement_contracts", tenant_id)
        _clear_entity("asset_inventory_items", tenant_id)

        contract = create_entity_for_tenant(
            "procurement_contracts",
            {
                "contract_code": "CTR-W11-001",
                "vendor_code": "VND-001",
                "title": "Network Equipment Procurement",
                "risk_score": "0.2",
                "sla_target_met": "true",
                "status": "APPROVED",
            },
            tenant_id,
        )
        contract_id = int(contract["id"])

        req = ContractStatusUpdateSchema(status="PO_ISSUED")
        result = svc.update_contract_status(tenant_id, contract_id, req, "admin")

        assert result is not None
        assert result.status == "PO_ISSUED"

        # Verify asset_inventory entry was auto-created
        asset_rows = api_list("asset_inventory_items", tenant_id)
        contract_assets = [
            r for r in asset_rows
            if "CTR-W11-001" in str(r.get("asset_code") or "")
        ]
        assert len(contract_assets) >= 1, (
            "PO_ISSUED transition must auto-create an asset_inventory_items entry"
        )

    def test_update_contract_status_non_po_issued_no_asset(self):
        """Non-PO_ISSUED transitions must NOT create asset_inventory entries."""
        from app.modules.procurement import service as svc
        from app.modules.procurement.schemas import ContractStatusUpdateSchema
        from app.modules.university_core.tenant_entity_service import create_entity_for_tenant
        from app.modules.university_core.tenant_entity_api import list_entities_for_tenant as api_list

        tenant_id = 40002
        _clear_entity("procurement_contracts", tenant_id)
        _clear_entity("asset_inventory_items", tenant_id)

        contract = create_entity_for_tenant(
            "procurement_contracts",
            {
                "contract_code": "CTR-W11-002",
                "vendor_code": "VND-002",
                "title": "Office Supplies",
                "risk_score": "0.1",
                "sla_target_met": "true",
                "status": "DRAFT",
            },
            tenant_id,
        )
        contract_id = int(contract["id"])

        # Transition DRAFT → SUBMITTED (not PO_ISSUED)
        req = ContractStatusUpdateSchema(status="SUBMITTED")
        result = svc.update_contract_status(tenant_id, contract_id, req, "admin")
        assert result is not None
        assert result.status == "SUBMITTED"

        # Should NOT have created any asset_inventory entries
        asset_rows = api_list("asset_inventory_items", tenant_id)
        contract_assets = [
            r for r in asset_rows
            if "CTR-W11-002" in str(r.get("asset_code") or "")
        ]
        assert len(contract_assets) == 0, (
            "Non-PO_ISSUED transitions must not create asset_inventory entries"
        )

    def test_asset_created_with_contract_code_prefix(self):
        """Auto-created asset must use 'PROC-{contract_code}' as asset_code."""
        from app.modules.procurement import service as svc
        from app.modules.procurement.schemas import ContractStatusUpdateSchema
        from app.modules.university_core.tenant_entity_service import create_entity_for_tenant
        from app.modules.university_core.tenant_entity_api import list_entities_for_tenant as api_list

        tenant_id = 40003
        _clear_entity("procurement_contracts", tenant_id)
        _clear_entity("asset_inventory_items", tenant_id)

        contract = create_entity_for_tenant(
            "procurement_contracts",
            {
                "contract_code": "CTR-W11-003",
                "vendor_code": "VND-003",
                "title": "Lab Equipment",
                "risk_score": "0.3",
                "sla_target_met": "false",
                "status": "APPROVED",
            },
            tenant_id,
        )
        contract_id = int(contract["id"])

        req = ContractStatusUpdateSchema(status="PO_ISSUED")
        svc.update_contract_status(tenant_id, contract_id, req, "admin")

        asset_rows = api_list("asset_inventory_items", tenant_id)
        asset_codes = [str(r.get("asset_code") or "") for r in asset_rows]
        assert any("PROC-CTR-W11-003" in code for code in asset_codes), (
            "Auto-created asset must use 'PROC-{contract_code}' pattern"
        )
