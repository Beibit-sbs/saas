"""Response schemas for Communications module (A-054.5-E1 - read-only)."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class CommDomainSummary(BaseModel):
    """Summary of a communications domain."""
    domain_key: str
    display_name: str
    purpose: str
    planned_table_groups: int
    provider_boundary: bool
    brain_signal_applicable: bool
    workflow_status: str
    live_delivery_enabled: bool
    production_ready: bool


class ProviderReadinessSummary(BaseModel):
    """Provider readiness summary - NO live delivery claim."""
    provider_key: str
    provider_type: str  # email, sms, push, telegram
    integration_status: str  # not_configured, connecting, degraded, available
    credential_status: str  # missing, expired, verified
    status_timestamp: datetime
    status_label: str = "Status as of [timestamp] - Readiness-Only"
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    no_live_delivery_reason: str = "A-054.5-E1 is planning-only; provider integrations deferred to A-054.12+"


class BrainActionBoundaryItem(BaseModel):
    """Brain action summary with approval gates visible."""
    source_signal_type: str
    recommended_action: str
    urgency_level: str
    approval_required: bool
    approval_status: str
    execution_status: str
    policy_gates: List[str] = Field(
        default_factory=lambda: [
            "template_compliance",
            "recipient_validation",
            "escalation_policy",
            "emergency_policy",
            "bulk_notification_policy"
        ]
    )


class CommunicationsRuntimeShellResponse(BaseModel):
    """Overall runtime shell response for communications module."""
    tenant_id: int
    generated_at: datetime
    
    # Domain inventory
    total_domains: int = 12
    total_planned_tables: int = 36
    total_core_permissions: int = 19
    
    # Foundation status
    domain_registry_loaded: bool = True
    live_delivery_enabled: bool = False
    provider_boundary_enforced: bool = True
    brain_action_boundary_enforced: bool = True
    production_ready: bool = False
    
    # Domains
    domains: List[CommDomainSummary]
    
    # Provider boundary
    provider_readiness: List[ProviderReadinessSummary]
    
    # Brain action boundary
    brain_action_samples: List[BrainActionBoundaryItem]
    
    # Safety confirmations
    safety_constraints: List[str] = Field(
        default_factory=lambda: [
            "read_only_foundation",
            "no_workflow_execution",
            "no_external_delivery",
            "no_fake_delivery_success",
            "no_provider_credentials_stored",
            "no_autonomous_critical_actions",
            "tenant_isolation_enforced",
            "rbac_permission_required",
        ]
    )


class NotificationCenterItem(BaseModel):
    """Read-only notification item for A-054.6-E1 notification center slice."""

    notification_id: str
    title: str
    message_preview: str
    source_type: str
    internal_status: str
    external_delivery_status: str
    created_at: datetime
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    no_live_delivery_reason: str = "A-054.6-E1 is read-only; live provider delivery is deferred."
    provider_status_label: str = "Provider boundary only - no live delivery"


class NotificationProviderBoundary(BaseModel):
    """Notification center provider boundary response."""

    tenant_id: int
    source_type: str = "readiness_static"
    internal_status: str = "provider_boundary_enforced"
    external_delivery_status: str = "PROVIDER_BOUNDARY_ONLY"
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    no_live_delivery_reason: str = "Provider integrations are deferred to later slices; no external delivery attempted."
    provider_status_label: str = "Readiness-only boundary"


class NotificationCenterSummaryResponse(BaseModel):
    """Read-only summary for notification center."""

    tenant_id: int
    source_type: str
    internal_status: str
    external_delivery_status: str
    total_notifications: int
    unread_notifications: int
    high_priority_notifications: int
    boundary: NotificationProviderBoundary
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    no_live_delivery_reason: str = "Notification center summary is read-only in A-054.6-E1."
    provider_status_label: str = "Provider not connected"


class NotificationListResponse(BaseModel):
    """Read-only notification list response."""

    tenant_id: int
    source_type: str
    internal_status: str
    external_delivery_status: str
    notifications: List[NotificationCenterItem]
    total: int
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    no_live_delivery_reason: str = "Notification list is generated from internal read-only slice state."
    provider_status_label: str = "Provider boundary only"


class AnnouncementRegistryItem(BaseModel):
    """Read-only announcement registry item for A-054.7-E1."""

    announcement_id: str
    title: str
    category: str
    audience_scope: str
    source_type: str
    internal_status: str
    external_delivery_status: str
    created_at: datetime
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    publish_workflow_enabled: bool = False
    broadcast_enabled: bool = False
    no_live_delivery_reason: str = "A-054.7-E1 is read-only; publish/broadcast workflows are disabled."
    provider_status_label: str = "Provider boundary only - no live delivery"


class AnnouncementRegistryBoundary(BaseModel):
    """Announcement registry boundary response."""

    tenant_id: int
    source_type: str = "readiness_static"
    internal_status: str = "provider_publish_broadcast_boundary_enforced"
    external_delivery_status: str = "PROVIDER_BOUNDARY_ONLY"
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    publish_workflow_enabled: bool = False
    broadcast_enabled: bool = False
    no_live_delivery_reason: str = "Provider delivery and publish/broadcast workflows are deferred to later slices."
    provider_status_label: str = "Readiness-only boundary"


class AnnouncementRegistrySummaryResponse(BaseModel):
    """Read-only summary for announcement registry."""

    tenant_id: int
    source_type: str
    internal_status: str
    external_delivery_status: str
    total_announcements: int
    active_announcements: int
    expiring_soon_announcements: int
    boundary: AnnouncementRegistryBoundary
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    publish_workflow_enabled: bool = False
    broadcast_enabled: bool = False
    no_live_delivery_reason: str = "Announcement registry summary is read-only in A-054.7-E1."
    provider_status_label: str = "Provider not connected"


class AnnouncementListResponse(BaseModel):
    """Read-only announcement registry list response."""

    tenant_id: int
    source_type: str
    internal_status: str
    external_delivery_status: str
    announcements: List[AnnouncementRegistryItem]
    total: int
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    publish_workflow_enabled: bool = False
    broadcast_enabled: bool = False
    no_live_delivery_reason: str = "Announcement registry list is generated from internal read-only state."
    provider_status_label: str = "Provider boundary only"


class MessageTemplateRegistryItem(BaseModel):
    """Read-only message template registry item for A-054.8-E1."""

    template_id: str
    template_name: str
    channel_type: str
    locale: str
    source_type: str
    internal_status: str
    external_delivery_status: str
    updated_at: datetime
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    template_send_enabled: bool = False
    preference_mutation_enabled: bool = False
    no_live_delivery_reason: str = "A-054.8-E1 is read-only; template send and preference mutation workflows are disabled."
    provider_status_label: str = "Provider boundary only - no live delivery"


class MessageTemplateRegistryBoundary(BaseModel):
    """Message template registry boundary response."""

    tenant_id: int
    source_type: str = "readiness_static"
    internal_status: str = "provider_template_send_boundary_enforced"
    external_delivery_status: str = "PROVIDER_BOUNDARY_ONLY"
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    template_send_enabled: bool = False
    preference_mutation_enabled: bool = False
    no_live_delivery_reason: str = "Provider delivery and template send workflows are deferred to later slices."
    provider_status_label: str = "Readiness-only boundary"


class MessageTemplateRegistrySummaryResponse(BaseModel):
    """Read-only summary for message template registry."""

    tenant_id: int
    source_type: str
    internal_status: str
    external_delivery_status: str
    total_templates: int
    active_templates: int
    channels_covered: int
    boundary: MessageTemplateRegistryBoundary
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    template_send_enabled: bool = False
    preference_mutation_enabled: bool = False
    no_live_delivery_reason: str = "Template registry summary is read-only in A-054.8-E1."
    provider_status_label: str = "Provider not connected"


class MessageTemplateListResponse(BaseModel):
    """Read-only message template list response."""

    tenant_id: int
    source_type: str
    internal_status: str
    external_delivery_status: str
    templates: List[MessageTemplateRegistryItem]
    total: int
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    template_send_enabled: bool = False
    preference_mutation_enabled: bool = False
    no_live_delivery_reason: str = "Template registry list is generated from internal read-only state."
    provider_status_label: str = "Provider boundary only"


class NotificationPreferenceRegistryItem(BaseModel):
    """Read-only notification preference registry item for A-054.8-E1."""

    preference_id: str
    audience_type: str
    channel_type: str
    preference_scope: str
    source_type: str
    internal_status: str
    external_delivery_status: str
    updated_at: datetime
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    template_send_enabled: bool = False
    preference_mutation_enabled: bool = False
    no_live_delivery_reason: str = "A-054.8-E1 is read-only; preference mutation workflows are disabled."
    provider_status_label: str = "Provider boundary only - no live delivery"


class NotificationPreferenceRegistryBoundary(BaseModel):
    """Notification preference registry boundary response."""

    tenant_id: int
    source_type: str = "readiness_static"
    internal_status: str = "provider_preference_mutation_boundary_enforced"
    external_delivery_status: str = "PROVIDER_BOUNDARY_ONLY"
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    template_send_enabled: bool = False
    preference_mutation_enabled: bool = False
    no_live_delivery_reason: str = "Provider delivery and preference mutation workflows are deferred to later slices."
    provider_status_label: str = "Readiness-only boundary"


class NotificationPreferenceRegistrySummaryResponse(BaseModel):
    """Read-only summary for notification preference registry."""

    tenant_id: int
    source_type: str
    internal_status: str
    external_delivery_status: str
    total_preferences: int
    default_preferences: int
    audience_segments: int
    boundary: NotificationPreferenceRegistryBoundary
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    template_send_enabled: bool = False
    preference_mutation_enabled: bool = False
    no_live_delivery_reason: str = "Preference registry summary is read-only in A-054.8-E1."
    provider_status_label: str = "Provider not connected"


class NotificationPreferenceListResponse(BaseModel):
    """Read-only notification preference list response."""

    tenant_id: int
    source_type: str
    internal_status: str
    external_delivery_status: str
    preferences: List[NotificationPreferenceRegistryItem]
    total: int
    live_delivery_enabled: bool = False
    provider_connected: bool = False
    external_delivery_claimed: bool = False
    template_send_enabled: bool = False
    preference_mutation_enabled: bool = False
    no_live_delivery_reason: str = "Preference registry list is generated from internal read-only state."
    provider_status_label: str = "Provider boundary only"
