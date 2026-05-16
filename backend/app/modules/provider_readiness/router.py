from typing import Annotated, Any, Callable

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.digital_signature_integration.service import (
    get_digital_signature_provider_l4_visibility_summary,
)
from app.modules.email_gateway_integration.service import (
    get_email_gateway_provider_l4_visibility_summary,
)
from app.modules.finance_erp_integration.service import (
    get_finance_erp_provider_l4_visibility_summary,
)
from app.modules.government_services_integration.service import (
    get_government_services_provider_l4_visibility_summary,
)
from app.modules.hr_payroll_integration.service import (
    get_hr_payroll_provider_l4_visibility_summary,
)
from app.modules.identity_provider_integration.service import (
    get_identity_provider_l4_visibility_summary,
)
from app.modules.learning_management_system_integration.service import (
    get_learning_management_system_provider_l4_visibility_summary,
)
from app.modules.notification_gateway_integration.service import (
    get_notification_gateway_provider_l4_visibility_summary,
)
from app.modules.payment_gateway_integration.service import (
    get_payment_gateway_provider_l4_visibility_summary,
)
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.regulatory_reporting_integration.service import (
    get_regulatory_reporting_provider_l4_visibility_summary,
)
from app.modules.student_information_system_integration.service import (
    get_student_information_system_provider_l4_visibility_summary,
)

router = APIRouter(prefix="/api/admin/provider-readiness/l4", tags=["provider-readiness-l4"])

Actor = Annotated[str, Depends(get_actor)]
TrustedTenant = Annotated[dict[str, object], Depends(get_current_tenant)]
ExpansionRead = Annotated[None, Depends(permission_dependency("admin.expansion.read"))]
SummaryBuilder = Callable[[int], dict[str, Any]]


def _build_summary_response(tenant: dict[str, object], builder: SummaryBuilder) -> dict[str, Any]:
    return builder(int(tenant["id"]))


@router.get("/student-information-system/summary")
def get_student_information_system_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_student_information_system_provider_l4_visibility_summary)


@router.get("/finance-erp/summary")
def get_finance_erp_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_finance_erp_provider_l4_visibility_summary)


@router.get("/government-services/summary")
def get_government_services_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_government_services_provider_l4_visibility_summary)


@router.get("/digital-signature/summary")
def get_digital_signature_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_digital_signature_provider_l4_visibility_summary)


@router.get("/regulatory-reporting/summary")
def get_regulatory_reporting_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_regulatory_reporting_provider_l4_visibility_summary)


@router.get("/identity-provider/summary")
def get_identity_provider_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_identity_provider_l4_visibility_summary)


@router.get("/email-gateway/summary")
def get_email_gateway_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_email_gateway_provider_l4_visibility_summary)


@router.get("/notification-gateway/summary")
def get_notification_gateway_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_notification_gateway_provider_l4_visibility_summary)


@router.get("/payment-gateway/summary")
def get_payment_gateway_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_payment_gateway_provider_l4_visibility_summary)


@router.get("/hr-payroll/summary")
def get_hr_payroll_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_hr_payroll_provider_l4_visibility_summary)


@router.get("/learning-management-system/summary")
def get_learning_management_system_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    return _build_summary_response(tenant, get_learning_management_system_provider_l4_visibility_summary)
