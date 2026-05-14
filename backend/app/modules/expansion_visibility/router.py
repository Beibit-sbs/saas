from typing import Annotated, Any, Callable

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.accreditation_dashboard.service import get_accreditation_dashboard_l4_visibility_summary
from app.modules.archive_retention_management.service import get_archive_retention_management_l4_visibility_summary
from app.modules.committee_decision_registry.service import get_committee_decision_registry_l4_visibility_summary
from app.modules.compliance_calendar_dashboard.service import get_compliance_calendar_dashboard_l4_visibility_summary
from app.modules.document_template_library.service import get_document_template_library_l4_visibility_summary
from app.modules.document_workflow.service import get_document_workflow_l4_visibility_summary
from app.modules.incoming_outgoing_correspondence.service import get_incoming_outgoing_correspondence_l4_visibility_summary
from app.modules.international_office.service import get_international_office_l4_visibility_summary
from app.modules.ministry_reporting_dashboard.service import get_ministry_reporting_dashboard_l4_visibility_summary
from app.modules.order_decree_registry.service import get_order_decree_registry_l4_visibility_summary
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.rector_strategy_dashboard.service import get_rector_strategy_dashboard_l4_visibility_summary
from app.modules.rector_resolution_tracking_workflow.service import (
    get_rector_resolution_tracking_workflow_l4_visibility_summary,
)


router = APIRouter(prefix="/api/admin/expansion/l4", tags=["expansion-l4-visibility"])

Actor = Annotated[str, Depends(get_actor)]
TrustedTenant = Annotated[dict[str, object], Depends(get_current_tenant)]
ExpansionRead = Annotated[None, Depends(permission_dependency("admin.expansion.read"))]
SummaryBuilder = Callable[[int], dict[str, Any]]


def _build_summary_response(tenant: dict[str, object], builder: SummaryBuilder) -> dict[str, Any]:
    return builder(int(tenant["id"]))


@router.get("/document-workflow/summary")
def get_document_workflow_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_document_workflow_l4_visibility_summary)


@router.get("/order-decree-registry/summary")
def get_order_decree_registry_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_order_decree_registry_l4_visibility_summary)


@router.get("/committee-decision-registry/summary")
def get_committee_decision_registry_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_committee_decision_registry_l4_visibility_summary)


@router.get("/rector-resolution-tracking-workflow/summary")
def get_rector_resolution_tracking_workflow_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_rector_resolution_tracking_workflow_l4_visibility_summary)


@router.get("/compliance-calendar-dashboard/summary")
def get_compliance_calendar_dashboard_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_compliance_calendar_dashboard_l4_visibility_summary)


@router.get("/accreditation-dashboard/summary")
def get_accreditation_dashboard_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_accreditation_dashboard_l4_visibility_summary)


@router.get("/incoming-outgoing-correspondence/summary")
def get_incoming_outgoing_correspondence_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_incoming_outgoing_correspondence_l4_visibility_summary)


@router.get("/document-template-library/summary")
def get_document_template_library_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_document_template_library_l4_visibility_summary)


@router.get("/ministry-reporting-dashboard/summary")
def get_ministry_reporting_dashboard_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_ministry_reporting_dashboard_l4_visibility_summary)


@router.get("/rector-strategy-dashboard/summary")
def get_rector_strategy_dashboard_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_rector_strategy_dashboard_l4_visibility_summary)


@router.get("/archive-retention-management/summary")
def get_archive_retention_management_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_archive_retention_management_l4_visibility_summary)


@router.get("/international-office/summary")
def get_international_office_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_international_office_l4_visibility_summary)