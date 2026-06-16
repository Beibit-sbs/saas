"""Tests for A-054.7-E1 Communications Announcement Registry read-only slice."""

from app.modules.communications.domain_registry import COMMUNICATIONS_DOMAIN_REGISTRY
from app.modules.communications.permissions import COMMUNICATIONS_CORE_PERMISSIONS
from app.modules.communications.services import (
    get_announcement_registry_summary,
    list_announcements,
    get_announcement_registry_boundary,
)


def test_domain_registry_remains_12() -> None:
    """A-054.7 must preserve canonical 12-domain registry."""
    assert len(COMMUNICATIONS_DOMAIN_REGISTRY) == 12


def test_permissions_remain_19() -> None:
    """A-054.7 must preserve canonical 19 core permissions."""
    assert len(COMMUNICATIONS_CORE_PERMISSIONS) == 19


def test_permissions_used_are_read_only() -> None:
    """Announcement slice must only use read permissions."""
    assert "communications.announcements.read" in COMMUNICATIONS_CORE_PERMISSIONS
    assert "communications.summary.read" in COMMUNICATIONS_CORE_PERMISSIONS


def test_announcement_summary_has_anti_fake_fields() -> None:
    """Summary response must include anti-fake and publish/broadcast boundary fields."""
    response = get_announcement_registry_summary(db=None, tenant_id=1)

    assert response.live_delivery_enabled is False
    assert response.provider_connected is False
    assert response.external_delivery_claimed is False
    assert response.publish_workflow_enabled is False
    assert response.broadcast_enabled is False
    assert response.external_delivery_status == "PROVIDER_BOUNDARY_ONLY"
    assert response.no_live_delivery_reason
    assert response.provider_status_label


def test_announcement_list_has_no_external_delivery_claim() -> None:
    """List response must not claim external provider delivery."""
    response = list_announcements(db=None, tenant_id=1)

    assert response.live_delivery_enabled is False
    assert response.provider_connected is False
    assert response.external_delivery_claimed is False
    assert response.publish_workflow_enabled is False
    assert response.broadcast_enabled is False
    assert response.external_delivery_status == "PROVIDER_BOUNDARY_ONLY"
    assert response.total == len(response.announcements)

    for item in response.announcements:
        assert item.live_delivery_enabled is False
        assert item.provider_connected is False
        assert item.external_delivery_claimed is False
        assert item.publish_workflow_enabled is False
        assert item.broadcast_enabled is False
        assert item.external_delivery_status in {
            "NOT_CONNECTED",
            "NOT_ATTEMPTED",
            "PROVIDER_BOUNDARY_ONLY",
        }
        assert item.source_type == "readiness_static"


def test_announcement_registry_boundary_is_provider_only() -> None:
    """Boundary response must enforce provider and publish/broadcast boundaries."""
    boundary = get_announcement_registry_boundary(tenant_id=1)

    assert boundary.live_delivery_enabled is False
    assert boundary.provider_connected is False
    assert boundary.external_delivery_claimed is False
    assert boundary.publish_workflow_enabled is False
    assert boundary.broadcast_enabled is False
    assert boundary.external_delivery_status == "PROVIDER_BOUNDARY_ONLY"


def test_no_publish_or_broadcast_permissions_in_active_slice() -> None:
    """A-054.7 active slice remains read-only; publish/send/broadcast is future-gated."""
    assert "communications.notifications.send" not in COMMUNICATIONS_CORE_PERMISSIONS
    assert "communications.emergency.activate" not in COMMUNICATIONS_CORE_PERMISSIONS
    assert "communications.campaigns.execute" not in COMMUNICATIONS_CORE_PERMISSIONS
