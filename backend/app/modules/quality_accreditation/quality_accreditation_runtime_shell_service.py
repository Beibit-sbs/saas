"""Read-only runtime shell service for Quality / Accreditation (A-050.5-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.quality_accreditation import repository
from app.modules.quality_accreditation.dependencies import validate_tenant_id
from app.modules.quality_accreditation.runtime_shell_schemas import (
    QualityAccreditationRuntimeSafety,
    QualityAccreditationRuntimeSection,
    QualityAccreditationRuntimeShellResponse,
)
from app.modules.quality_accreditation.service import REQUIRED_LIMITATIONS


def _now() -> datetime:
    return datetime.now(UTC)


def get_runtime_shell(db: Session, tenant_id: int) -> QualityAccreditationRuntimeShellResponse:
    tenant = validate_tenant_id(tenant_id)
    summary = repository.compute_dashboard_summary(db, tenant)

    readiness_total = sum(summary["readiness_summary"].values())
    evidence_total = sum(summary["evidence_summary"].values())
    risk_total = sum(summary["audit_summary"].values()) + sum(summary["improvement_summary"].values())
    dashboard_total = sum(summary["frameworks_summary"].values()) + sum(summary["bridge_summary"].values()) + sum(summary["brain_signal_summary"].values())

    return QualityAccreditationRuntimeShellResponse(
        tenant_id=tenant,
        generated_at=_now(),
        overview=QualityAccreditationRuntimeSection(
            owner_module="quality_accreditation",
            records=sum(summary["frameworks_summary"].values()),
            source_modules=["quality_accreditation"],
        ),
        readiness=QualityAccreditationRuntimeSection(
            owner_module="quality_accreditation",
            records=readiness_total,
            source_modules=["quality_accreditation", "academic_operations"],
        ),
        evidence=QualityAccreditationRuntimeSection(
            owner_module="quality_accreditation",
            records=evidence_total,
            source_modules=["quality_accreditation"],
        ),
        risk=QualityAccreditationRuntimeSection(
            owner_module="brain_core",
            records=risk_total,
            source_modules=["brain_core", "quality_accreditation"],
        ),
        dashboard=QualityAccreditationRuntimeSection(
            owner_module="quality_accreditation",
            records=dashboard_total,
            source_modules=["quality_accreditation", "analytics", "reporting_runtime"],
        ),
        safety=QualityAccreditationRuntimeSafety(
            limitations=list(REQUIRED_LIMITATIONS),
        ),
    )
