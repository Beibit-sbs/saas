"""ORM models for Communications module (A-054.5-E1 - read-only foundation)."""

from datetime import datetime
from sqlalchemy import BigInteger, DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class CommNotificationModel(Base):
    """Planned: Notification Center domain - notification message storage."""
    __tablename__ = "comm_notifications"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    recipient_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    template_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CommAnnouncementModel(Base):
    """Planned: Announcement Registry domain - institutional announcements."""
    __tablename__ = "comm_announcements"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, default="normal")
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class CommMessageTemplateModel(Base):
    """Planned: Message Template Registry domain - reusable message templates."""
    __tablename__ = "comm_message_templates"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    channel_list: Mapped[str] = mapped_column(String, nullable=False)  # comma-separated
    priority_level: Mapped[str] = mapped_column(String, default="normal")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class CommPreferenceModel(Base):
    """Planned: Notification Preference Registry domain - recipient preferences."""
    __tablename__ = "comm_preferences"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    recipient_id: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)
    frequency_limit: Mapped[int] = mapped_column(default=10)
    quiet_hours_start: Mapped[str | None] = mapped_column(String, nullable=True)
    quiet_hours_end: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class CommAuditEventModel(Base):
    """Planned: Delivery Audit Trail domain - immutable audit events."""
    __tablename__ = "comm_audit_events"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)  # created, delivered, read, failed, etc.
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    details_json: Mapped[str] = mapped_column(String, default="{}")
    # IMMUTABLE: No updates allowed on this table


class CommEscalationWorkflowModel(Base):
    """Planned: Escalation Workflow Registry domain - escalation policies."""
    __tablename__ = "comm_escalation_policies"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    policy_key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    trigger_condition: Mapped[str] = mapped_column(String, nullable=False)
    notification_required: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class CommEmergencyBroadcastModel(Base):
    """Planned: Emergency Broadcast Registry domain - crisis communication templates."""
    __tablename__ = "comm_emergency_broadcast_templates"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    escalation_level: Mapped[str] = mapped_column(String, default="normal")
    requires_rector_approval: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class CommRecipientGroupModel(Base):
    """Planned: Recipient Group Registry domain - reusable recipient groups."""
    __tablename__ = "comm_recipient_groups"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    group_key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    group_type: Mapped[str] = mapped_column(String, nullable=False)
    dynamic_refresh_enabled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class CommCampaignModel(Base):
    """Planned: Communication Campaign Registry domain - planned campaigns."""
    __tablename__ = "comm_campaigns"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    campaign_key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    campaign_type: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class CommProviderConfigModel(Base):
    """Planned: Provider Readiness Registry domain - provider integration status (readiness-only)."""
    __tablename__ = "comm_provider_configs"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    provider_key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    provider_type: Mapped[str] = mapped_column(String, nullable=False)  # email, sms, push, telegram
    integration_status: Mapped[str] = mapped_column(String, default="not_configured")  # not_configured, connecting, degraded, available
    credential_status: Mapped[str] = mapped_column(String, default="missing")  # missing, expired, verified
    rate_limit: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # NO credential storage here - this is readiness-only


class CommBrainActionModel(Base):
    """Planned: Brain Communication Action Registry domain - Brain signal proposals."""
    __tablename__ = "comm_communication_actions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    source_signal_type: Mapped[str] = mapped_column(String, nullable=False)
    recommended_action: Mapped[str] = mapped_column(String, nullable=False)
    urgency_level: Mapped[str] = mapped_column(String, default="normal")
    approval_status: Mapped[str] = mapped_column(String, default="pending")  # pending, approved, denied
    execution_status: Mapped[str] = mapped_column(String, default="not_executed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class CommCommunityThreadModel(Base):
    """Planned: Community / Parent Communication Surface domain - communication threads."""
    __tablename__ = "comm_parent_communication_threads"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    parent_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
