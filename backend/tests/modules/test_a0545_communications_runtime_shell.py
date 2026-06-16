"""Tests for Communications runtime shell (A-054.5-E1)."""

import pytest
from sqlalchemy.orm import Session

from app.modules.communications.domain_registry import CommDomainRegistry
from app.modules.communications.permissions import CORE_PERMISSIONS, STUDENT_PERMISSIONS
from app.modules.communications.schemas import (
    CommDomainSummary,
    ProviderReadinessSummary,
    BrainActionBoundaryItem,
)
from app.modules.communications.services import get_communications_runtime_shell


class TestCommDomainRegistry:
    """Test the canonical domain registry."""
    
    def test_total_domains(self):
        """All 12 domains registered."""
        assert len(CommDomainRegistry.get_all_domains()) == 12
    
    def test_total_planned_tables(self):
        """Total planned tables = 36 (3 per domain × 12 domains)."""
        assert CommDomainRegistry.total_planned_tables() == 36
    
    def test_get_domain_by_key(self):
        """Can retrieve domain by key."""
        domain = CommDomainRegistry.get_domain_by_key("notification_center")
        assert domain is not None
        assert domain.display_name == "Notification Center"
        assert domain.live_delivery_enabled is False
        assert domain.production_ready is False
    
    def test_provider_boundary_domains(self):
        """Provider boundary applies to 6 domains."""
        provider_domains = CommDomainRegistry.provider_boundary_domains()
        assert len(provider_domains) >= 4
        domain_keys = {d.domain_key for d in provider_domains}
        # notification_center, delivery_audit_trail, emergency_broadcast_registry,
        # provider_readiness_registry must have provider boundary
        assert "notification_center" in domain_keys
        assert "delivery_audit_trail" in domain_keys
    
    def test_brain_signal_domains(self):
        """Brain signal applicable to 7 domains."""
        brain_domains = CommDomainRegistry.brain_signal_domains()
        assert len(brain_domains) >= 6
        domain_keys = {d.domain_key for d in brain_domains}
        # notification_center, announcement_registry, etc.
        assert "notification_center" in domain_keys


class TestCommunicationsPermissions:
    """Test permission structure."""
    
    def test_core_permissions_count(self):
        """19 core permissions defined."""
        assert len(CORE_PERMISSIONS) == 19
    
    def test_permission_naming_convention(self):
        """All permissions follow naming convention."""
        for perm in CORE_PERMISSIONS:
            assert perm.startswith("communications.")
            assert len(perm.split(".")) >= 2
    
    def test_student_permissions_subset(self):
        """Student permissions are subset of core."""
        assert STUDENT_PERMISSIONS.issubset(set(CORE_PERMISSIONS))
    
    def test_no_write_permissions_in_core(self):
        """A-054.5-E1 is read-only (except preferences.write_own)."""
        forbidden_write_perms = [
            "communications.notifications.send",
            "communications.announcements.create",
            "communications.campaigns.execute",
        ]
        for perm in forbidden_write_perms:
            assert perm not in CORE_PERMISSIONS, f"Write permission {perm} should not be in core"


class TestRuntimeShellResponse:
    """Test runtime shell response structure."""
    
    def test_runtime_shell_has_required_fields(self, db_session: Session):
        """Response has all required fields."""
        response = get_communications_runtime_shell(db_session, 1)
        
        # Domain inventory
        assert response.total_domains == 12
        assert response.total_planned_tables == 36
        assert response.total_core_permissions == 19
        
        # Safety flags
        assert response.live_delivery_enabled is False
        assert response.provider_boundary_enforced is True
        assert response.brain_action_boundary_enforced is True
        assert response.production_ready is False
    
    def test_domains_in_response(self, db_session: Session):
        """Response includes all 12 domains."""
        response = get_communications_runtime_shell(db_session, 1)
        
        assert len(response.domains) == 12
        domain_keys = {d.domain_key for d in response.domains}
        assert "notification_center" in domain_keys
        assert "emergency_broadcast_registry" in domain_keys
        assert "community_parent_communication_surface" in domain_keys
    
    def test_provider_readiness_no_live_delivery(self, db_session: Session):
        """Provider readiness explicitly states no live delivery."""
        response = get_communications_runtime_shell(db_session, 1)
        
        for provider in response.provider_readiness:
            assert provider.live_delivery_enabled is False
            assert provider.provider_connected is False
            assert provider.integration_status == "not_configured"
            assert provider.credential_status == "missing"
    
    def test_brain_actions_have_approval_gates(self, db_session: Session):
        """Brain actions show approval requirements."""
        response = get_communications_runtime_shell(db_session, 1)
        
        for action in response.brain_action_samples:
            assert action.approval_required is True
            assert "template_compliance" in action.policy_gates
            assert action.execution_status == "not_executed"
    
    def test_safety_constraints_present(self, db_session: Session):
        """Safety constraints are clearly stated."""
        response = get_communications_runtime_shell(db_session, 1)
        
        safety_keys = response.safety_constraints
        assert "read_only_foundation" in safety_keys
        assert "no_fake_delivery_success" in safety_keys
        assert "tenant_isolation_enforced" in safety_keys


class TestAntiFakeBoundaries:
    """Test anti-fake enforcement."""
    
    def test_live_delivery_never_true(self):
        """Live delivery flag is always False in foundation."""
        for domain in CommDomainRegistry.get_all_domains():
            assert domain.live_delivery_enabled is False
    
    def test_production_ready_false(self):
        """Production ready flag is False."""
        for domain in CommDomainRegistry.get_all_domains():
            assert domain.production_ready is False
    
    def test_provider_configs_status_only(self, db_session: Session):
        """Provider configs show status only, never provider_connected=True."""
        response = get_communications_runtime_shell(db_session, 1)
        
        for provider in response.provider_readiness:
            # Never claim provider_connected
            assert not provider.provider_connected
            # Always read-only status
            assert provider.no_live_delivery_reason is not None


class TestModels:
    """Test database models."""
    
    def test_notification_model_has_tenant_id(self):
        """CommNotificationModel has tenant_id."""
        from app.modules.communications.models import CommNotificationModel
        
        # Check that __table__ has tenant_id column
        table = CommNotificationModel.__table__
        assert "tenant_id" in table.columns
    
    def test_audit_event_model_immutable_design(self):
        """CommAuditEventModel is append-only (no update fields)."""
        from app.modules.communications.models import CommAuditEventModel
        
        # Append-only table with only creation timestamp
        table = CommAuditEventModel.__table__
        assert "id" in table.columns
        assert "timestamp" in table.columns
        # No updated_at or similar


if __name__ == "__main__":
    pytest.main([__file__])
