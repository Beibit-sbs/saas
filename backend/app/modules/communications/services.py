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
    AnnouncementRegistryItem,
    AnnouncementRegistryBoundary,
    AnnouncementRegistrySummaryResponse,
    AnnouncementListResponse,
    MessageTemplateRegistryItem,
    MessageTemplateRegistryBoundary,
    MessageTemplateRegistrySummaryResponse,
    MessageTemplateListResponse,
    NotificationPreferenceRegistryItem,
    NotificationPreferenceRegistryBoundary,
    NotificationPreferenceRegistrySummaryResponse,
    NotificationPreferenceListResponse,
    DeliveryAuditEventItem,
    DeliveryAuditBoundary,
    DeliveryAuditSummaryResponse,
    DeliveryAuditListResponse,
    EscalationWorkflowItem,
    EscalationWorkflowBoundary,
    EscalationWorkflowSummaryResponse,
    EscalationWorkflowListResponse,
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


def _announcement_seed_items() -> list[AnnouncementRegistryItem]:
    """Static read-only announcement registry data for A-054.7-E1."""

    now = _now()
    return [
        AnnouncementRegistryItem(
            announcement_id="comm-ann-001",
            title="Semester timeline update",
            category="academic",
            audience_scope="all_students",
            source_type="readiness_static",
            internal_status="draft_registry_state",
            external_delivery_status="NOT_ATTEMPTED",
            created_at=now,
            provider_status_label="Provider boundary only - no external publish",
        ),
        AnnouncementRegistryItem(
            announcement_id="comm-ann-002",
            title="Library schedule advisory",
            category="operations",
            audience_scope="campus_community",
            source_type="readiness_static",
            internal_status="review_registry_state",
            external_delivery_status="NOT_CONNECTED",
            created_at=now,
            provider_status_label="Provider not connected",
        ),
        AnnouncementRegistryItem(
            announcement_id="comm-ann-003",
            title="Scholarship policy reminder",
            category="finance",
            audience_scope="eligible_students",
            source_type="readiness_static",
            internal_status="approved_registry_state",
            external_delivery_status="PROVIDER_BOUNDARY_ONLY",
            created_at=now,
            provider_status_label="Boundary enforced - no live broadcast",
        ),
    ]


def get_announcement_registry_boundary(tenant_id: int) -> AnnouncementRegistryBoundary:
    """Return anti-fake provider and publish/broadcast boundary state for announcements."""

    return AnnouncementRegistryBoundary(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="provider_publish_broadcast_boundary_enforced",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        provider_status_label="Provider boundary only - publish/broadcast disabled",
    )


def get_announcement_registry_summary(db: Session, tenant_id: int) -> AnnouncementRegistrySummaryResponse:
    """Return read-only announcement registry summary with anti-fake fields."""

    items = _announcement_seed_items()
    active = sum(1 for item in items if item.internal_status in {"review_registry_state", "approved_registry_state"})
    expiring_soon = sum(1 for item in items if "policy" in item.title.lower())

    return AnnouncementRegistrySummaryResponse(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="read_only_announcement_registry",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        total_announcements=len(items),
        active_announcements=active,
        expiring_soon_announcements=expiring_soon,
        boundary=get_announcement_registry_boundary(tenant_id),
        provider_status_label="Provider boundary only - read-only summary",
    )


def list_announcements(db: Session, tenant_id: int) -> AnnouncementListResponse:
    """Return read-only announcement list with publish/broadcast boundary fields."""

    items = _announcement_seed_items()
    return AnnouncementListResponse(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="read_only_announcement_list",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        announcements=items,
        total=len(items),
        provider_status_label="Provider boundary only - no publish/broadcast",
    )


def _template_seed_items() -> list[MessageTemplateRegistryItem]:
    """Static read-only message template registry data for A-054.8-E1."""

    now = _now()
    return [
        MessageTemplateRegistryItem(
            template_id="comm-tpl-001",
            template_name="Attendance Risk Advisory",
            channel_type="email",
            locale="en-US",
            source_type="readiness_static",
            internal_status="draft_template_registry_state",
            external_delivery_status="NOT_ATTEMPTED",
            updated_at=now,
            provider_status_label="Provider boundary only - no template send",
        ),
        MessageTemplateRegistryItem(
            template_id="comm-tpl-002",
            template_name="Exam Schedule Reminder",
            channel_type="push",
            locale="en-US",
            source_type="readiness_static",
            internal_status="review_template_registry_state",
            external_delivery_status="NOT_CONNECTED",
            updated_at=now,
            provider_status_label="Provider not connected",
        ),
        MessageTemplateRegistryItem(
            template_id="comm-tpl-003",
            template_name="Scholarship Deadline Alert",
            channel_type="sms",
            locale="en-US",
            source_type="readiness_static",
            internal_status="approved_template_registry_state",
            external_delivery_status="PROVIDER_BOUNDARY_ONLY",
            updated_at=now,
            provider_status_label="Boundary enforced - send workflow disabled",
        ),
    ]


def get_template_registry_boundary(tenant_id: int) -> MessageTemplateRegistryBoundary:
    """Return anti-fake provider and template send boundary state for template registry."""

    return MessageTemplateRegistryBoundary(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="provider_template_send_boundary_enforced",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        provider_status_label="Provider boundary only - template send disabled",
    )


def get_template_registry_summary(db: Session, tenant_id: int) -> MessageTemplateRegistrySummaryResponse:
    """Return read-only template registry summary with anti-fake fields."""

    items = _template_seed_items()
    active = sum(1 for item in items if item.internal_status in {"review_template_registry_state", "approved_template_registry_state"})
    channels_covered = len({item.channel_type for item in items})

    return MessageTemplateRegistrySummaryResponse(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="read_only_template_registry",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        total_templates=len(items),
        active_templates=active,
        channels_covered=channels_covered,
        boundary=get_template_registry_boundary(tenant_id),
        provider_status_label="Provider boundary only - read-only summary",
    )


def list_message_templates(db: Session, tenant_id: int) -> MessageTemplateListResponse:
    """Return read-only message template list with template send boundary fields."""

    items = _template_seed_items()
    return MessageTemplateListResponse(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="read_only_template_list",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        templates=items,
        total=len(items),
        provider_status_label="Provider boundary only - no template send",
    )


def _preference_seed_items() -> list[NotificationPreferenceRegistryItem]:
    """Static read-only notification preference registry data for A-054.8-E1."""

    now = _now()
    return [
        NotificationPreferenceRegistryItem(
            preference_id="comm-pref-001",
            audience_type="student",
            channel_type="email",
            preference_scope="attendance_alerts",
            source_type="readiness_static",
            internal_status="default_preference_registry_state",
            external_delivery_status="NOT_ATTEMPTED",
            updated_at=now,
            provider_status_label="Provider boundary only - no subscription mutation",
        ),
        NotificationPreferenceRegistryItem(
            preference_id="comm-pref-002",
            audience_type="staff",
            channel_type="push",
            preference_scope="exam_alerts",
            source_type="readiness_static",
            internal_status="custom_preference_registry_state",
            external_delivery_status="NOT_CONNECTED",
            updated_at=now,
            provider_status_label="Provider not connected",
        ),
        NotificationPreferenceRegistryItem(
            preference_id="comm-pref-003",
            audience_type="parent",
            channel_type="sms",
            preference_scope="fee_statement_updates",
            source_type="readiness_static",
            internal_status="review_preference_registry_state",
            external_delivery_status="PROVIDER_BOUNDARY_ONLY",
            updated_at=now,
            provider_status_label="Boundary enforced - mutation workflow disabled",
        ),
    ]


def get_preference_registry_boundary(tenant_id: int) -> NotificationPreferenceRegistryBoundary:
    """Return anti-fake provider and preference mutation boundary state for preference registry."""

    return NotificationPreferenceRegistryBoundary(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="provider_preference_mutation_boundary_enforced",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        provider_status_label="Provider boundary only - preference mutation disabled",
    )


def get_preference_registry_summary(db: Session, tenant_id: int) -> NotificationPreferenceRegistrySummaryResponse:
    """Return read-only preference registry summary with anti-fake fields."""

    items = _preference_seed_items()
    defaults = sum(1 for item in items if item.internal_status == "default_preference_registry_state")
    segments = len({item.audience_type for item in items})

    return NotificationPreferenceRegistrySummaryResponse(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="read_only_preference_registry",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        total_preferences=len(items),
        default_preferences=defaults,
        audience_segments=segments,
        boundary=get_preference_registry_boundary(tenant_id),
        provider_status_label="Provider boundary only - read-only summary",
    )


def list_notification_preferences(db: Session, tenant_id: int) -> NotificationPreferenceListResponse:
    """Return read-only preference list with mutation boundary fields."""

    items = _preference_seed_items()
    return NotificationPreferenceListResponse(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="read_only_preference_list",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        preferences=items,
        total=len(items),
        provider_status_label="Provider boundary only - no preference mutation",
    )


def _delivery_audit_seed_items() -> list[DeliveryAuditEventItem]:
    """Static read-only delivery audit readiness data for A-054.9-E1."""

    now = _now()
    return [
        DeliveryAuditEventItem(
            audit_event_id="comm-audit-001",
            event_type="notification_compiled",
            channel_type="email",
            audience_scope="at_risk_students",
            source_type="readiness_static",
            internal_status="queued_internal_orchestration",
            external_delivery_status="NOT_ATTEMPTED",
            recorded_at=now,
            provider_status_label="Provider boundary only - no external delivery",
        ),
        DeliveryAuditEventItem(
            audit_event_id="comm-audit-002",
            event_type="announcement_reviewed",
            channel_type="push",
            audience_scope="campus_staff",
            source_type="readiness_static",
            internal_status="policy_review_logged",
            external_delivery_status="NOT_CONNECTED",
            recorded_at=now,
            provider_status_label="Provider not connected",
        ),
        DeliveryAuditEventItem(
            audit_event_id="comm-audit-003",
            event_type="escalation_gate_recorded",
            channel_type="sms",
            audience_scope="deans_office",
            source_type="readiness_static",
            internal_status="approval_gate_recorded",
            external_delivery_status="PROVIDER_BOUNDARY_ONLY",
            recorded_at=now,
            provider_status_label="Boundary enforced - no delivery success claim",
        ),
    ]


def get_delivery_audit_boundary(tenant_id: int) -> DeliveryAuditBoundary:
    """Return anti-fake provider and delivery-audit boundary state."""

    return DeliveryAuditBoundary(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="provider_delivery_audit_boundary_enforced",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        provider_status_label="Provider boundary only - delivery success disabled",
    )


def get_delivery_audit_summary(db: Session, tenant_id: int) -> DeliveryAuditSummaryResponse:
    """Return read-only delivery audit summary with anti-fake fields."""

    items = _delivery_audit_seed_items()
    pending = sum(1 for item in items if item.internal_status == "queued_internal_orchestration")
    policy_review = sum(1 for item in items if "policy" in item.internal_status)

    return DeliveryAuditSummaryResponse(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="read_only_delivery_audit",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        total_audit_events=len(items),
        pending_internal_events=pending,
        policy_review_events=policy_review,
        boundary=get_delivery_audit_boundary(tenant_id),
        provider_status_label="Provider boundary only - read-only summary",
    )


def list_delivery_audit_events(db: Session, tenant_id: int) -> DeliveryAuditListResponse:
    """Return read-only delivery audit event list with no delivery success claims."""

    items = _delivery_audit_seed_items()
    return DeliveryAuditListResponse(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="read_only_delivery_audit_list",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        events=items,
        total=len(items),
        provider_status_label="Provider boundary only - no delivery success",
    )


def _escalation_workflow_seed_items() -> list[EscalationWorkflowItem]:
    """Static read-only escalation workflow readiness data for A-054.9-E1."""

    now = _now()
    return [
        EscalationWorkflowItem(
            escalation_id="comm-esc-001",
            workflow_type="attendance_risk_escalation",
            approval_level="department_director",
            policy_gate="advisor_review_required",
            source_type="readiness_static",
            internal_status="approval_gated_readiness_only",
            external_delivery_status="NOT_ATTEMPTED",
            reviewed_at=now,
            provider_status_label="Provider boundary only - no escalation execution",
        ),
        EscalationWorkflowItem(
            escalation_id="comm-esc-002",
            workflow_type="financial_aid_escalation",
            approval_level="registrar",
            policy_gate="policy_validation_required",
            source_type="readiness_static",
            internal_status="human_approval_pending_readiness_only",
            external_delivery_status="NOT_CONNECTED",
            reviewed_at=now,
            provider_status_label="Provider not connected",
        ),
        EscalationWorkflowItem(
            escalation_id="comm-esc-003",
            workflow_type="academic_integrity_escalation",
            approval_level="rector",
            policy_gate="critical_multilevel_approval",
            source_type="readiness_static",
            internal_status="critical_policy_gate_recorded",
            external_delivery_status="PROVIDER_BOUNDARY_ONLY",
            reviewed_at=now,
            provider_status_label="Boundary enforced - no autonomous escalation",
        ),
    ]


def get_escalation_workflow_boundary(tenant_id: int) -> EscalationWorkflowBoundary:
    """Return anti-fake provider and escalation execution boundary state."""

    return EscalationWorkflowBoundary(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="provider_escalation_execution_boundary_enforced",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        provider_status_label="Provider boundary only - escalation execution disabled",
    )


def get_escalation_workflow_summary(db: Session, tenant_id: int) -> EscalationWorkflowSummaryResponse:
    """Return read-only escalation workflow summary with anti-fake fields."""

    items = _escalation_workflow_seed_items()
    approval_gated = sum(1 for item in items if "approval" in item.internal_status)
    critical = sum(1 for item in items if "critical" in item.internal_status or "critical" in item.policy_gate)

    return EscalationWorkflowSummaryResponse(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="read_only_escalation_workflow",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        total_workflows=len(items),
        approval_gated_workflows=approval_gated,
        critical_policy_workflows=critical,
        boundary=get_escalation_workflow_boundary(tenant_id),
        provider_status_label="Provider boundary only - read-only summary",
    )


def list_escalation_workflows(db: Session, tenant_id: int) -> EscalationWorkflowListResponse:
    """Return read-only escalation workflow list with execution boundary fields."""

    items = _escalation_workflow_seed_items()
    return EscalationWorkflowListResponse(
        tenant_id=tenant_id,
        source_type="readiness_static",
        internal_status="read_only_escalation_workflow_list",
        external_delivery_status="PROVIDER_BOUNDARY_ONLY",
        workflows=items,
        total=len(items),
        provider_status_label="Provider boundary only - no escalation execution",
    )
