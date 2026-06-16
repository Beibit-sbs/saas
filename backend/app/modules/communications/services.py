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
    NotificationCenterItem,
    NotificationCenterSummaryResponse,
    NotificationListResponse,
    NotificationProviderBoundary,
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


def _notification_seed_items() -> list[NotificationCenterItem]:
    """Static read-only notification center data for A-054.6-E1."""

    now = _now()
    return [
        NotificationCenterItem(
            notification_id="comm-notif-001",
            title="Advising window reminder",
            message_preview="Course advising window opens this week.",
            source_type="readiness_static",
            internal_status="queued_internal",
            external_delivery_status="NOT_ATTEMPTED",
            created_at=now,
            provider_status_label="Provider boundary only - no external dispatch",
        ),
        NotificationCenterItem(
            notification_id="comm-notif-002",
            title="Fee statement update",
            message_preview="Monthly fee statement is ready for review.",
            source_type="readiness_static",
            internal_status="read_internal",
            external_delivery_status="NOT_CONNECTED",
            created_at=now,
            provider_status_label="Provider not connected",
        ),
        NotificationCenterItem(
            notification_id="comm-notif-003",
            title="Attendance risk signal",
            message_preview="Attendance threshold warning requires advisor attention.",
            source_type="readiness_static",
            internal_status="requires_review",
            external_delivery_status="PROVIDER_BOUNDARY_ONLY",
            created_at=now,
            provider_status_label="Boundary enforced - no live provider",
        ),
    ]


def get_notification_center_boundary(tenant_id: int) -> NotificationProviderBoundary:
    """Return anti-fake provider boundary state for notification center."""

    return NotificationProviderBoundary(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="provider_boundary_enforced",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        provider_status_label="Provider boundary only - no live channel",
    )


def get_notification_center_summary(db: Session, tenant_id: int) -> NotificationCenterSummaryResponse:
    """Return read-only notification center summary with anti-fake fields."""

    items = _notification_seed_items()
    unread = sum(1 for item in items if item.internal_status != "read_internal")
    high_priority = sum(1 for item in items if "risk" in item.title.lower())

    return NotificationCenterSummaryResponse(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="read_only_notification_center",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        total_notifications=len(items),
        unread_notifications=unread,
        high_priority_notifications=high_priority,
        boundary=get_notification_center_boundary(tenant_id),
        provider_status_label="Provider boundary only - read-only summary",
    )


def list_notifications(db: Session, tenant_id: int) -> NotificationListResponse:
    """Return read-only notification list with explicit non-delivery claims."""

    items = _notification_seed_items()
    return NotificationListResponse(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="read_only_notification_list",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        notifications=items,
        total=len(items),
        provider_status_label="Provider boundary only - no live delivery",
    )
