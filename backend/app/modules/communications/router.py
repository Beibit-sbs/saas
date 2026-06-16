"""Read-only router for Communications module runtime shell (A-054.5-E1)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.communications.dependencies import (
    get_communications_db,
    require_communications_tenant,
)
from app.modules.communications.services import get_communications_runtime_shell
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/communications", tags=["communications-runtime-shell"])

_Tenant = Annotated[int, Depends(require_communications_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_communications_db)]


@router.get("/overview")
def get_overview(
    _actor: _Actor,
    _: Annotated[None, Depends(permission_dependency("communications.summary.read"))],
    tenant: _Tenant,
    db: _DB,
):
    """Get communications overview dashboard (foundation)."""
    return get_communications_runtime_shell(db, tenant)


@router.get("/domains")
def get_domains(
    _actor: _Actor,
    _: Annotated[None, Depends(permission_dependency("communications.summary.read"))],
    tenant: _Tenant,
):
    """Get canonical domain registry."""
    from app.modules.communications.domain_registry import CommDomainRegistry
    
    return {
        "tenant_id": tenant,
        "total_domains": len(CommDomainRegistry.get_all_domains()),
        "total_planned_tables": CommDomainRegistry.total_planned_tables(),
        "domains": [
            {
                "domain_key": d.domain_key,
                "display_name": d.display_name,
                "purpose": d.purpose,
                "planned_table_groups": d.planned_table_group_count,
                "workflow_status": d.workflow_status,
                "live_delivery_enabled": d.live_delivery_enabled,
                "production_ready": d.production_ready,
            }
            for d in CommDomainRegistry.get_all_domains()
        ]
    }


@router.get("/provider-readiness")
def get_provider_readiness(
    _actor: _Actor,
    _: Annotated[None, Depends(permission_dependency("communications.providers.read"))],
    tenant: _Tenant,
):
    """Get provider readiness status (readiness-only, no live delivery)."""
    return {
        "tenant_id": tenant,
        "status_label": "Provider Readiness - A-054.5-E1 (Planning-Only)",
        "live_delivery_enabled": False,
        "providers": [
            {
                "provider_key": "email",
                "integration_status": "not_configured",
                "credential_status": "missing",
                "live_delivery": False,
            },
            {
                "provider_key": "sms",
                "integration_status": "not_configured",
                "credential_status": "missing",
                "live_delivery": False,
            },
            {
                "provider_key": "push",
                "integration_status": "not_configured",
                "credential_status": "missing",
                "live_delivery": False,
            },
            {
                "provider_key": "telegram",
                "integration_status": "not_configured",
                "credential_status": "missing",
                "live_delivery": False,
            },
        ]
    }


@router.get("/brain-actions")
def get_brain_actions(
    _actor: _Actor,
    _: Annotated[None, Depends(permission_dependency("communications.brain_actions.read"))],
    tenant: _Tenant,
):
    """Get Brain communication action boundary with approval gates."""
    return {
        "tenant_id": tenant,
        "brain_action_boundary": "Policy-Gated with Approval Requirements",
        "samples": [
            {
                "source_signal_type": "academic_risk_detected",
                "approval_required": True,
                "policy_gates": [
                    "template_compliance",
                    "recipient_validation",
                    "escalation_policy"
                ],
            },
            {
                "source_signal_type": "emergency_situation_alert",
                "approval_required": True,
                "approval_level": "rector",
                "policy_gates": [
                    "emergency_policy",
                    "multi_level_approval"
                ],
            },
        ]
    }
