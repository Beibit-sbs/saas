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
