from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AiCopilotQueryLogModel(Base):
    __tablename__ = "app_platform_ai_copilot_query_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("app_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    question: Mapped[str] = mapped_column(String(2000), nullable=False)
    query_type: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieved_sources_json: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    answer_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    __table_args__ = (
        Index("ix_platform_ai_copilot_logs_tenant", "tenant_id"),
        Index("ix_platform_ai_copilot_logs_created_at", "created_at"),
    )
