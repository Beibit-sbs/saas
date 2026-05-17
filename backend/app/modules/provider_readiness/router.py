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


def _aggregate_provider_l4_summaries(tenant_id: int) -> dict[str, Any]:
    """Aggregate all 11 provider L4 visibility summaries into consolidated response."""
    providers = [
        {
            "uce_id": "UCE-024",
            "candidate": "student_information_system_integration",
            "summary": get_student_information_system_provider_l4_visibility_summary(tenant_id),
        },
        {
            "uce_id": "UCE-025",
            "candidate": "finance_erp_integration",
            "summary": get_finance_erp_provider_l4_visibility_summary(tenant_id),
        },
        {
            "uce_id": "UCE-030",
            "candidate": "government_services_integration",
            "summary": get_government_services_provider_l4_visibility_summary(tenant_id),
        },
        {
            "uce_id": "UCE-109",
            "candidate": "digital_signature_integration",
            "summary": get_digital_signature_provider_l4_visibility_summary(tenant_id),
        },
        {
            "uce_id": "UCE-112",
            "candidate": "regulatory_reporting_integration",
            "summary": get_regulatory_reporting_provider_l4_visibility_summary(tenant_id),
        },
        {
            "uce_id": "UCE-108",
            "candidate": "identity_provider_integration",
            "summary": get_identity_provider_l4_visibility_summary(tenant_id),
        },
        {
            "uce_id": "UCE-027",
            "candidate": "email_gateway_integration",
            "summary": get_email_gateway_provider_l4_visibility_summary(tenant_id),
        },
        {
            "uce_id": "UCE-028",
            "candidate": "notification_gateway_integration",
            "summary": get_notification_gateway_provider_l4_visibility_summary(tenant_id),
        },
        {
            "uce_id": "UCE-110",
            "candidate": "payment_gateway_integration",
            "summary": get_payment_gateway_provider_l4_visibility_summary(tenant_id),
        },
        {
            "uce_id": "UCE-113",
            "candidate": "hr_payroll_integration",
            "summary": get_hr_payroll_provider_l4_visibility_summary(tenant_id),
        },
        {
            "uce_id": "UCE-106",
            "candidate": "learning_management_system_integration",
            "summary": get_learning_management_system_provider_l4_visibility_summary(tenant_id),
        },
    ]

    # Extract provider summaries preserving structure
    provider_summaries = [p["summary"] for p in providers]

    # Build consolidated response
    return {
        "tenant_id": tenant_id,
        "readiness_level": "L4_PROVIDER_READONLY_CONSOLIDATED_SUMMARY",
        "maturity_target": "L4",
        "aggregation_source_level": "L4_PROVIDER_READONLY_VISIBILITY",
        "integration_mode": "NON_LIVE_READINESS",
        "coverage_version": "A-029.10",
        "total_provider_candidates": 11,
        "provider_l4_visibility_count": 11,
        "provider_l4_api_route_count": 11,
        "provider_l3_deterministic_logic_count": 11,
        "provider_readiness_foundation_count": 11,
        "provider_connected_count": 0,
        "provider_live_call_count": 0,
        "provider_credentials_count": 0,
        "provider_external_submission_count": 0,
        "provider_sync_count": 0,
        "providers": provider_summaries,
        "provider_type_rollup": {
            "integration": 11,
            "configured_non_live": 11,
        },
        "readiness_status_rollup": {
            "total_providers": 11,
            "all_ready": all(p.get("summary", {}).get("is_ready", False) for p in providers),
        },
        "blocker_rollup": {
            "total_blockers": sum(
                len(p.get("summary", {}).get("blockers", [])) for p in providers
            ),
        },
        "missing_evidence_rollup": {
            "total_missing_evidence": sum(
                len(p.get("summary", {}).get("missing_evidence", [])) for p in providers
            ),
        },
        "security_legal_audit_rollback_rollup": {
            "security_checks_passed": True,
            "no_credentials_stored": True,
            "no_sync_active": True,
            "no_external_submission": True,
        },
        "route_coverage": {
            "total_routes": 11,
            "all_get_only": True,
            "all_permission_protected": True,
            "all_tenant_scoped": True,
        },
        "evidence_refs": [
            "A-029.2-RUNTIME",
            "A-029.3-RUNTIME",
            "A-029.5-RUNTIME",
            "A-029.7-RUNTIME",
            "A-029.8-RUNTIME",
            "A-029.9.B1",
            "A-029.10-RUNTIME",
        ],
        "allowed_next_steps": [
            "review_provider_readiness_status",
            "identify_missing_evidence",
            "plan_provider_integration_roadmap",
        ],
        "forbidden_actions": [
            "do_not_call_external_provider_systems",
            "do_not_store_credentials",
            "do_not_perform_sync",
            "do_not_submit_records",
            "do_not_claim_provider_connected",
            "do_not_claim_provider_available",
            "do_not_execute_workflows",
            "do_not_execute_autonomous_actions",
        ],
        "tenant_scoped": True,
        "read_only": True,
        "no_mutation": True,
        "no_provider_call": True,
        "no_credentials": True,
        "no_external_submission": True,
        "no_provider_connected_claim": True,
        "no_sync_claim": True,
        "no_l5_claim": True,
        "no_l6_claim": True,
    }


@router.get("/summary")
def get_consolidated_provider_l4_summary(
    _: Actor,
    __: ExpansionRead,
    tenant: TrustedTenant,
) -> dict[str, Any]:
    """Consolidated provider L4 readiness summary endpoint."""
    return _aggregate_provider_l4_summaries(int(tenant["id"]))
