"""Canonical domain registry for Communications / Notification / Community Suite."""

from dataclasses import dataclass
from typing import List


@dataclass
class CommDomainRegistryItem:
    """Registry item for a communications domain."""
    domain_key: str
    display_name: str
    purpose: str
    planned_table_group_count: int
    provider_boundary_applicable: bool
    brain_signal_applicable: bool
    workflow_status: str = "READ_ONLY_FOUNDATION"
    live_delivery_enabled: bool = False
    production_ready: bool = False


class CommDomainRegistry:
    """Static registry of all 12 A-054 communications domains."""
    
    DOMAINS: List[CommDomainRegistryItem] = [
        CommDomainRegistryItem(
            domain_key="notification_center",
            display_name="Notification Center",
            purpose="Core orchestration platform for all notification delivery, routing, and outcome tracking",
            planned_table_group_count=3,
            provider_boundary_applicable=True,
            brain_signal_applicable=True,
        ),
        CommDomainRegistryItem(
            domain_key="announcement_registry",
            display_name="Announcement Registry",
            purpose="Persistent, versioned storage for institutional announcements with visibility rules",
            planned_table_group_count=3,
            provider_boundary_applicable=False,
            brain_signal_applicable=True,
        ),
        CommDomainRegistryItem(
            domain_key="message_template_registry",
            display_name="Message Template Registry",
            purpose="Parameterized, reusable message templates for consistency and audit compliance",
            planned_table_group_count=3,
            provider_boundary_applicable=False,
            brain_signal_applicable=True,
        ),
        CommDomainRegistryItem(
            domain_key="notification_preference_registry",
            display_name="Notification Preference Registry",
            purpose="Individual recipient preferences for notification channels, frequency, and quiet hours",
            planned_table_group_count=3,
            provider_boundary_applicable=False,
            brain_signal_applicable=False,
        ),
        CommDomainRegistryItem(
            domain_key="delivery_audit_trail",
            display_name="Delivery Audit Trail",
            purpose="Complete, immutable record of notification delivery events for compliance and accountability",
            planned_table_group_count=3,
            provider_boundary_applicable=True,
            brain_signal_applicable=False,
        ),
        CommDomainRegistryItem(
            domain_key="escalation_workflow_registry",
            display_name="Escalation Workflow Registry",
            purpose="Policy-driven escalation chains for unresolved notifications and urgent situations",
            planned_table_group_count=3,
            provider_boundary_applicable=False,
            brain_signal_applicable=True,
        ),
        CommDomainRegistryItem(
            domain_key="emergency_broadcast_registry",
            display_name="Emergency Broadcast Registry",
            purpose="Controlled, policy-gated capability for emergency and crisis communications",
            planned_table_group_count=3,
            provider_boundary_applicable=True,
            brain_signal_applicable=True,
        ),
        CommDomainRegistryItem(
            domain_key="recipient_group_registry",
            display_name="Recipient Group Registry",
            purpose="Reusable, dynamic recipient groups for broadcast messaging, filtering, and targeting",
            planned_table_group_count=3,
            provider_boundary_applicable=False,
            brain_signal_applicable=True,
        ),
        CommDomainRegistryItem(
            domain_key="communication_campaign_registry",
            display_name="Communication Campaign Registry",
            purpose="Planned, trackable communication campaigns with messaging goals and outcome measurement",
            planned_table_group_count=3,
            provider_boundary_applicable=False,
            brain_signal_applicable=True,
        ),
        CommDomainRegistryItem(
            domain_key="provider_readiness_registry",
            display_name="Provider Readiness Registry",
            purpose="Inventory and readiness status of external providers without claiming live delivery",
            planned_table_group_count=3,
            provider_boundary_applicable=True,
            brain_signal_applicable=False,
        ),
        CommDomainRegistryItem(
            domain_key="brain_communication_action_registry",
            display_name="Brain Communication Action Registry",
            purpose="Bridge between Brain Core decisions and communications execution with approval gates",
            planned_table_group_count=3,
            provider_boundary_applicable=False,
            brain_signal_applicable=True,
        ),
        CommDomainRegistryItem(
            domain_key="community_parent_communication_surface",
            display_name="Community / Parent Communication Surface",
            purpose="Specialized student-parent-staff communication with moderation controls",
            planned_table_group_count=3,
            provider_boundary_applicable=False,
            brain_signal_applicable=False,
        ),
    ]
    
    @classmethod
    def get_all_domains(cls) -> List[CommDomainRegistryItem]:
        """Return all 12 registered domains."""
        return cls.DOMAINS
    
    @classmethod
    def get_domain_by_key(cls, domain_key: str) -> CommDomainRegistryItem | None:
        """Get domain by key."""
        for domain in cls.DOMAINS:
            if domain.domain_key == domain_key:
                return domain
        return None
    
    @classmethod
    def total_planned_tables(cls) -> int:
        """Return total planned tables (should be 36 = 3 per domain × 12 domains)."""
        return sum(d.planned_table_group_count for d in cls.DOMAINS)
    
    @classmethod
    def provider_boundary_domains(cls) -> List[CommDomainRegistryItem]:
        """Return domains where provider boundary is applicable."""
        return [d for d in cls.DOMAINS if d.provider_boundary_applicable]
    
    @classmethod
    def brain_signal_domains(cls) -> List[CommDomainRegistryItem]:
        """Return domains where Brain signal is applicable."""
        return [d for d in cls.DOMAINS if d.brain_signal_applicable]


# Compatibility alias used by post-commit verification probes.
COMMUNICATIONS_DOMAIN_REGISTRY = CommDomainRegistry.DOMAINS
