"""Read-only service layer for Communications module (A-054.5-E1)."""

from datetime import UTC, datetime
from typing import List

from sqlalchemy.orm import Session

from app.modules.communications.domain_registry import CommDomainRegistry
from app.modules.communications.schemas import (
    CommDomainSummary,
    ProviderReadinessSummary,
    BrainActionBoundaryItem,
    CommunicationsRuntimeShellResponse,
)


def _now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


def get_communications_runtime_shell(db: Session, tenant_id: int) -> CommunicationsRuntimeShellResponse:
    """
    Get the communications runtime shell response.
    
    This is a read-only, safe foundation that:
    - Lists all 12 planned domains
    - Confirms live_delivery_enabled = False
    - Confirms provider readiness status only (no live delivery)
    - Shows Brain action boundaries with approval gates
    - Enforces safety constraints
    """
    
    # Build domain summaries
    domain_summaries: List[CommDomainSummary] = []
    for domain in CommDomainRegistry.get_all_domains():
        domain_summaries.append(
            CommDomainSummary(
                domain_key=domain.domain_key,
                display_name=domain.display_name,
                purpose=domain.purpose,
                planned_table_groups=domain.planned_table_group_count,
                provider_boundary=domain.provider_boundary_applicable,
                brain_signal_applicable=domain.brain_signal_applicable,
                workflow_status=domain.workflow_status,
                live_delivery_enabled=domain.live_delivery_enabled,
                production_ready=domain.production_ready,
            )
        )
    
    # Provider readiness - status-only, no live delivery
    provider_summaries: List[ProviderReadinessSummary] = [
        ProviderReadinessSummary(
            provider_key="email",
            provider_type="email",
            integration_status="not_configured",
            credential_status="missing",
            status_timestamp=_now(),
        ),
        ProviderReadinessSummary(
            provider_key="sms",
            provider_type="sms",
            integration_status="not_configured",
            credential_status="missing",
            status_timestamp=_now(),
        ),
        ProviderReadinessSummary(
            provider_key="push",
            provider_type="push",
            integration_status="not_configured",
            credential_status="missing",
            status_timestamp=_now(),
        ),
        ProviderReadinessSummary(
            provider_key="telegram",
            provider_type="telegram",
            integration_status="not_configured",
            credential_status="missing",
            status_timestamp=_now(),
        ),
    ]
    
    # Brain action boundary samples
    brain_action_samples: List[BrainActionBoundaryItem] = [
        BrainActionBoundaryItem(
            source_signal_type="academic_risk_detected",
            recommended_action="notify_student",
            urgency_level="high",
            approval_required=True,
            approval_status="pending",
            execution_status="not_executed",
        ),
        BrainActionBoundaryItem(
            source_signal_type="low_attendance_risk",
            recommended_action="notify_advisor",
            urgency_level="medium",
            approval_required=True,
            approval_status="pending",
            execution_status="not_executed",
        ),
        BrainActionBoundaryItem(
            source_signal_type="emergency_situation_alert",
            recommended_action="broadcast_emergency",
            urgency_level="critical",
            approval_required=True,
            approval_status="pending",
            execution_status="not_executed",
        ),
    ]
    
    return CommunicationsRuntimeShellResponse(
        tenant_id=tenant_id,
        generated_at=_now(),
        domains=domain_summaries,
        provider_readiness=provider_summaries,
        brain_action_samples=brain_action_samples,
    )
