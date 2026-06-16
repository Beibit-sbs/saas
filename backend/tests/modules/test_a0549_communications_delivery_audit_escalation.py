"""Tests for A-054.9-E1 Communications Delivery Audit / Escalation read-only slice."""

from app.modules.communications.domain_registry import COMMUNICATIONS_DOMAIN_REGISTRY
from app.modules.communications.permissions import COMMUNICATIONS_CORE_PERMISSIONS
from app.modules.communications.router import router as communications_router
from app.modules.communications.services import (
    get_delivery_audit_summary,
    list_delivery_audit_events,
    get_delivery_audit_boundary,
    get_escalation_workflow_summary,
    list_escalation_workflows,
    get_escalation_workflow_boundary,
)


def test_domain_registry_remains_12() -> None:
    """A-054.9 must preserve canonical 12-domain registry."""
    assert len(COMMUNICATIONS_DOMAIN_REGISTRY) == 12


def test_permissions_remain_19() -> None:
    """A-054.9 must preserve canonical 19 core permissions."""
    assert len(COMMUNICATIONS_CORE_PERMISSIONS) == 19


def test_permissions_used_are_read_only() -> None:
    """Delivery audit / escalation slice must use only read permissions."""
    assert "communications.audit.read" in COMMUNICATIONS_CORE_PERMISSIONS
    assert "communications.escalations.read" in COMMUNICATIONS_CORE_PERMISSIONS
    assert "communications.summary.read" in COMMUNICATIONS_CORE_PERMISSIONS


def test_delivery_audit_summary_has_anti_fake_fields() -> None:
    """Delivery audit summary must expose anti-fake boundary fields."""
    response = get_delivery_audit_summary(db=None, tenant_id=1)

    assert response.live_delivery_enabled is False
    assert response.provider_connected is False
    assert response.external_delivery_claimed is False
    assert response.delivery_success_claimed is False
    assert response.escalation_execution_enabled is False
    assert response.autonomous_escalation_enabled is False
    assert response.external_delivery_status == "PROVIDER_BOUNDARY_ONLY"
    assert response.no_live_delivery_reason
    assert response.provider_status_label


def test_delivery_audit_list_has_no_external_delivery_success_claim() -> None:
    """Delivery audit list must not claim external delivery success."""
    response = list_delivery_audit_events(db=None, tenant_id=1)

    assert response.live_delivery_enabled is False
    assert response.provider_connected is False
    assert response.external_delivery_claimed is False
    assert response.delivery_success_claimed is False
    assert response.escalation_execution_enabled is False
    assert response.autonomous_escalation_enabled is False
    assert response.external_delivery_status == "PROVIDER_BOUNDARY_ONLY"
    assert response.total == len(response.events)

    for item in response.events:
        assert item.live_delivery_enabled is False
        assert item.provider_connected is False
        assert item.external_delivery_claimed is False
        assert item.delivery_success_claimed is False
        assert item.escalation_execution_enabled is False
        assert item.autonomous_escalation_enabled is False
        assert item.external_delivery_status in {
            "NOT_CONNECTED",
            "NOT_ATTEMPTED",
            "PROVIDER_BOUNDARY_ONLY",
        }
        assert item.source_type == "readiness_static"


def test_escalation_workflow_summary_is_read_only() -> None:
    """Escalation workflow summary must remain read-only and execution-free."""
    response = get_escalation_workflow_summary(db=None, tenant_id=1)

    assert response.live_delivery_enabled is False
    assert response.provider_connected is False
    assert response.external_delivery_claimed is False
    assert response.delivery_success_claimed is False
    assert response.escalation_execution_enabled is False
    assert response.autonomous_escalation_enabled is False
    assert response.external_delivery_status == "PROVIDER_BOUNDARY_ONLY"
    assert response.no_live_delivery_reason
    assert response.provider_status_label


def test_escalation_workflow_list_has_no_execution_claim() -> None:
    """Escalation workflow list must not claim execution or autonomy."""
    response = list_escalation_workflows(db=None, tenant_id=1)

    assert response.live_delivery_enabled is False
    assert response.provider_connected is False
    assert response.external_delivery_claimed is False
    assert response.delivery_success_claimed is False
    assert response.escalation_execution_enabled is False
    assert response.autonomous_escalation_enabled is False
    assert response.external_delivery_status == "PROVIDER_BOUNDARY_ONLY"
    assert response.total == len(response.workflows)

    for item in response.workflows:
        assert item.live_delivery_enabled is False
        assert item.provider_connected is False
        assert item.external_delivery_claimed is False
        assert item.delivery_success_claimed is False
        assert item.escalation_execution_enabled is False
        assert item.autonomous_escalation_enabled is False
        assert item.external_delivery_status in {
            "NOT_CONNECTED",
            "NOT_ATTEMPTED",
            "PROVIDER_BOUNDARY_ONLY",
        }
        assert item.source_type == "readiness_static"


def test_registry_boundaries_enforce_no_delivery_success_or_execution() -> None:
    """Boundary responses must enforce delivery-success and escalation-execution constraints."""
    audit_boundary = get_delivery_audit_boundary(tenant_id=1)
    escalation_boundary = get_escalation_workflow_boundary(tenant_id=1)

    for boundary in (audit_boundary, escalation_boundary):
        assert boundary.live_delivery_enabled is False
        assert boundary.provider_connected is False
        assert boundary.external_delivery_claimed is False
        assert boundary.delivery_success_claimed is False
        assert boundary.escalation_execution_enabled is False
        assert boundary.autonomous_escalation_enabled is False
        assert boundary.external_delivery_status == "PROVIDER_BOUNDARY_ONLY"


def test_no_send_retry_or_escalate_endpoints_exist() -> None:
    """A-054.9 router must expose only read-only delivery-audit/escalation endpoints."""
    paths = {route.path for route in communications_router.routes}
    methods_by_path = {route.path: set(route.methods or []) for route in communications_router.routes}

    assert "/api/admin/communications/delivery-audit" in paths
    assert "/api/admin/communications/delivery-audit/summary" in paths
    assert "/api/admin/communications/delivery-audit/boundary" in paths
    assert "/api/admin/communications/escalations" in paths
    assert "/api/admin/communications/escalations/summary" in paths
    assert "/api/admin/communications/escalations/boundary" in paths

    for path in (
        "/api/admin/communications/delivery-audit",
        "/api/admin/communications/delivery-audit/summary",
        "/api/admin/communications/delivery-audit/boundary",
        "/api/admin/communications/escalations",
        "/api/admin/communications/escalations/summary",
        "/api/admin/communications/escalations/boundary",
    ):
        assert methods_by_path[path] == {"GET"}

    assert "/api/admin/communications/delivery-audit/retry" not in paths
    assert "/api/admin/communications/delivery-audit/execute" not in paths
    assert "/api/admin/communications/escalations/execute" not in paths
    assert "/api/admin/communications/escalations/auto-escalate" not in paths
