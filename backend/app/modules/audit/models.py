from sqlalchemy import BigInteger, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class AuditEventModel(Base):
    __tablename__ = "app_audit_events"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    actor: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    entity: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False)
    ip: Mapped[str] = mapped_column(String, nullable=False)
    result: Mapped[str] = mapped_column(String, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String, nullable=False)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("app_tenants.id"), nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    tenant = relationship("TenantModel")
