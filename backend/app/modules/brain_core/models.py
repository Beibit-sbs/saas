from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class BrainSignalModel(Base):
    __tablename__ = "app_brain_signals"

    signal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("app_tenants.id"), nullable=False, index=True)
    correlation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    signal_class: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_module: Mapped[str] = mapped_column(String, nullable=False)
    source_entity_type: Mapped[str] = mapped_column(String, nullable=False)
    source_entity_id: Mapped[str] = mapped_column(String, nullable=False)
    subject_student_id: Mapped[str | None] = mapped_column(String, nullable=True)
    subject_faculty_id: Mapped[str | None] = mapped_column(String, nullable=True)
    subject_course_id: Mapped[str | None] = mapped_column(String, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    status: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'received'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class BrainDecisionModel(Base):
    __tablename__ = "app_brain_decisions"

    decision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("app_tenants.id"), nullable=False, index=True)
    signal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_brain_signals.signal_id"), nullable=False)
    correlation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    decision_type: Mapped[str] = mapped_column(String, nullable=False)
    situation_type: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'draft'"))
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0"))
    severity_score: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0"))
    urgency_score: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0"))
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_by: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'brain_core'"))
    policy_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class BrainActionPlanModel(Base):
    __tablename__ = "app_brain_action_plans"

    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_brain_decisions.decision_id"), nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("app_tenants.id"), nullable=False, index=True)
    actions: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    status: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'planned'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class BrainOutcomeModel(Base):
    __tablename__ = "app_brain_outcomes"

    outcome_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_brain_decisions.decision_id"), nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("app_tenants.id"), nullable=False, index=True)
    outcome_type: Mapped[str] = mapped_column(String, nullable=False)
    outcome_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    effectiveness: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'neutral'"))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class BrainExplanationModel(Base):
    __tablename__ = "app_brain_explanations"

    explanation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("app_brain_decisions.decision_id"), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String, nullable=False)
    factors: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    policy_notes: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    expected_outcome: Mapped[str] = mapped_column(String, nullable=False, server_default=text("''"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))


class BrainPolicyProfileModel(Base):
    __tablename__ = "app_brain_policy_profiles"

    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("app_tenants.id"), nullable=False, index=True)
    autonomy_level: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'level_1'"))
    decision_type: Mapped[str] = mapped_column(String, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    approval_role: Mapped[str | None] = mapped_column(String, nullable=True)
    requires_notification: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    notification_roles: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
