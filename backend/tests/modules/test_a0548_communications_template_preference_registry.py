"""Tests for A-054.8-E1 Communications Template/Preference Registry read-only slice."""

from app.modules.communications.domain_registry import COMMUNICATIONS_DOMAIN_REGISTRY
from app.modules.communications.permissions import COMMUNICATIONS_CORE_PERMISSIONS
from app.modules.communications.router import router as communications_router
from app.modules.communications.services import (
    get_template_registry_summary,
    list_message_templates,
    get_template_registry_boundary,
    get_preference_registry_summary,
    list_notification_preferences,
    get_preference_registry_boundary,
)


def test_domain_registry_remains_12() -> None:
    """A-054.8 must preserve canonical 12-domain registry."""
    assert len(COMMUNICATIONS_DOMAIN_REGISTRY) == 12


def test_permissions_remain_19() -> None:
    """A-054.8 must preserve canonical 19 core permissions."""
    assert len(COMMUNICATIONS_CORE_PERMISSIONS) == 19


def test_permissions_used_are_read_only() -> None:
    """Template/preference slice must only use read permissions for new endpoints."""
    assert "communications.templates.read" in COMMUNICATIONS_CORE_PERMISSIONS
    assert "communications.preferences.read" in COMMUNICATIONS_CORE_PERMISSIONS
    assert "communications.summary.read" in COMMUNICATIONS_CORE_PERMISSIONS


def test_template_summary_has_anti_fake_fields() -> None:
    """Template summary response must include anti-fake boundary fields."""
    response = get_template_registry_summary(db=None, tenant_id=1)

    assert response.live_delivery_enabled is False
    assert response.provider_connected is False
    assert response.external_delivery_claimed is False
    assert response.template_send_enabled is False
    assert response.preference_mutation_enabled is False
    assert response.external_delivery_status == "PROVIDER_BOUNDARY_ONLY"
    assert response.no_live_delivery_reason
    assert response.provider_status_label


def test_template_list_has_no_external_delivery_claim() -> None:
    """Template list response must not claim external provider delivery."""
    response = list_message_templates(db=None, tenant_id=1)

    assert response.live_delivery_enabled is False
    assert response.provider_connected is False
    assert response.external_delivery_claimed is False
    assert response.template_send_enabled is False
    assert response.preference_mutation_enabled is False
    assert response.external_delivery_status == "PROVIDER_BOUNDARY_ONLY"
    assert response.total == len(response.templates)

    for item in response.templates:
        assert item.live_delivery_enabled is False
        assert item.provider_connected is False
        assert item.external_delivery_claimed is False
        assert item.template_send_enabled is False
        assert item.preference_mutation_enabled is False
        assert item.external_delivery_status in {
            "NOT_CONNECTED",
            "NOT_ATTEMPTED",
            "PROVIDER_BOUNDARY_ONLY",
        }
        assert item.source_type == "readiness_static"


def test_preference_summary_has_anti_fake_fields() -> None:
    """Preference summary response must include anti-fake boundary fields."""
    response = get_preference_registry_summary(db=None, tenant_id=1)

    assert response.live_delivery_enabled is False
    assert response.provider_connected is False
    assert response.external_delivery_claimed is False
    assert response.template_send_enabled is False
    assert response.preference_mutation_enabled is False
    assert response.external_delivery_status == "PROVIDER_BOUNDARY_ONLY"
    assert response.no_live_delivery_reason
    assert response.provider_status_label


def test_preference_list_has_no_provider_verification_claim() -> None:
    """Preference list response must not claim provider subscription verification."""
    response = list_notification_preferences(db=None, tenant_id=1)

    assert response.live_delivery_enabled is False
    assert response.provider_connected is False
    assert response.external_delivery_claimed is False
    assert response.template_send_enabled is False
    assert response.preference_mutation_enabled is False
    assert response.external_delivery_status == "PROVIDER_BOUNDARY_ONLY"
    assert response.total == len(response.preferences)

    for item in response.preferences:
        assert item.live_delivery_enabled is False
        assert item.provider_connected is False
        assert item.external_delivery_claimed is False
        assert item.template_send_enabled is False
        assert item.preference_mutation_enabled is False
        assert item.external_delivery_status in {
            "NOT_CONNECTED",
            "NOT_ATTEMPTED",
            "PROVIDER_BOUNDARY_ONLY",
        }
        assert item.source_type == "readiness_static"


def test_registry_boundaries_enforce_no_send_or_mutation() -> None:
    """Boundary responses must enforce provider/send/mutation constraints."""
    template_boundary = get_template_registry_boundary(tenant_id=1)
    preference_boundary = get_preference_registry_boundary(tenant_id=1)

    for boundary in (template_boundary, preference_boundary):
        assert boundary.live_delivery_enabled is False
        assert boundary.provider_connected is False
        assert boundary.external_delivery_claimed is False
        assert boundary.template_send_enabled is False
        assert boundary.preference_mutation_enabled is False
        assert boundary.external_delivery_status == "PROVIDER_BOUNDARY_ONLY"


def test_no_send_render_send_or_preference_mutation_endpoints_exist() -> None:
    """A-054.8 router must expose only read-only template/preference endpoints."""
    paths = {route.path for route in communications_router.routes}
    methods_by_path = {route.path: set(route.methods or []) for route in communications_router.routes}

    assert "/api/admin/communications/templates" in paths
    assert "/api/admin/communications/templates/summary" in paths
    assert "/api/admin/communications/templates/boundary" in paths
    assert "/api/admin/communications/preferences" in paths
    assert "/api/admin/communications/preferences/summary" in paths
    assert "/api/admin/communications/preferences/boundary" in paths

    for path in (
        "/api/admin/communications/templates",
        "/api/admin/communications/templates/summary",
        "/api/admin/communications/templates/boundary",
        "/api/admin/communications/preferences",
        "/api/admin/communications/preferences/summary",
        "/api/admin/communications/preferences/boundary",
    ):
        assert methods_by_path[path] == {"GET"}

    assert "/api/admin/communications/templates/send" not in paths
    assert "/api/admin/communications/templates/render-and-send" not in paths
    assert "/api/admin/communications/preferences/mutate" not in paths
    assert "/api/admin/communications/preferences/opt-in" not in paths
    assert "/api/admin/communications/preferences/opt-out" not in paths
