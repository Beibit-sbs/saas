"""FastAPI router for Finance / Procurement / Asset runtime."""

from __future__ import annotations

from typing import Annotated, Any, Callable

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.modules.finance_procurement_asset import permissions, schemas, service
from app.modules.finance_procurement_asset.dependencies import get_finance_procurement_asset_db, require_finance_procurement_asset_tenant
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/finance-procurement-asset", tags=["finance-procurement-asset"])

_Tenant = Annotated[int, Depends(require_finance_procurement_asset_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_finance_procurement_asset_db)]


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _handle(exc: Exception) -> None:
    if isinstance(exc, TenantResourceNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, (DomainValidationError, ValueError)):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise exc


def _register_get(path: str, permission: str, handler: Callable[[Session, int], Any], response_model) -> None:
    def endpoint(
        actor: str = Depends(get_actor),
        permitted: None = Depends(permission_dependency(permission)),
        tenant: int = Depends(require_finance_procurement_asset_tenant),
        db: Session = Depends(get_finance_procurement_asset_db),
    ):
        try:
            del actor, permitted
            return handler(db, tenant)
        except Exception as exc:
            _handle(exc)

    endpoint.__name__ = f"get_{path.strip('/').replace('/', '_').replace('-', '_') or 'root'}"
    router.add_api_route(path, endpoint, methods=["GET"], response_model=response_model, responses={400: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}})


def _register_post(path: str, permission: str, handler: Callable[[Session, int, str, Any], Any], request_model) -> None:
    def endpoint(
        payload: dict[str, Any] = Body(...),
        actor: str = Depends(get_actor),
        permitted: None = Depends(permission_dependency(permission)),
        tenant: int = Depends(require_finance_procurement_asset_tenant),
        db: Session = Depends(get_finance_procurement_asset_db),
    ):
        try:
            del permitted
            body = _parse_payload(request_model, payload)
            return handler(db, tenant, actor, body)
        except Exception as exc:
            _handle(exc)

    endpoint.__name__ = f"post_{path.strip('/').replace('/', '_').replace('-', '_')}"
    router.add_api_route(path, endpoint, methods=["POST"], response_model=dict[str, Any], status_code=201, responses={400: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}})


_register_get("/overview", permissions.OVERVIEW_READ, service.get_overview, schemas.FpaOverviewResponse)
_register_get("/readiness", permissions.READINESS_READ, service.get_readiness, schemas.FpaReadinessResponse)
_register_get("/limitations", permissions.LIMITATIONS_READ, service.get_limitations, schemas.FpaLimitationsResponse)
_register_get("/safety-boundaries", permissions.LIMITATIONS_READ, service.get_safety_boundaries, schemas.FpaLimitationsResponse)
_register_get("/dashboard", permissions.DASHBOARD_READ, service.get_dashboard, schemas.FpaDashboardResponse)
_register_get("/billing", permissions.BILLING_READ, service.get_billing, schemas.FpaBillingVisibilityResponse)
_register_get("/receivables", permissions.RECEIVABLES_READ, service.get_receivables, schemas.FpaReceivablesMetadataResponse)
_register_get("/budget-plans", permissions.BUDGET_PLANS_READ, service.get_budget_plans, schemas.FpaBudgetPlanResponse)
_register_get("/budget-controls", permissions.BUDGET_CONTROLS_READ, service.get_budget_controls, schemas.FpaBudgetControlResponse)
_register_get("/procurement-requests", permissions.PROCUREMENT_REQUESTS_READ, service.get_procurement_requests, schemas.FpaProcurementRequestResponse)
_register_get("/procurement-reviews", permissions.PROCUREMENT_REVIEWS_READ, service.get_procurement_reviews, schemas.FpaProcurementReviewResponse)
_register_get("/vendors", permissions.VENDORS_READ, service.get_vendors, schemas.FpaVendorMetadataResponse)
_register_get("/contracts", permissions.CONTRACTS_READ, service.get_contracts, schemas.FpaContractEvidenceResponse)
_register_get("/purchase-requests", permissions.PURCHASE_REQUESTS_READ, service.get_purchase_requests, schemas.FpaPurchaseRequestResponse)
_register_get("/purchase-orders", permissions.PURCHASE_ORDERS_READ, service.get_purchase_orders, schemas.FpaPurchaseOrderMetadataResponse)
_register_get("/assets", permissions.ASSETS_READ, service.get_assets, schemas.FpaAssetVisibilityResponse)
_register_get("/asset-lifecycle", permissions.ASSET_LIFECYCLE_READ, service.get_asset_lifecycle, schemas.FpaAssetLifecycleResponse)
_register_get("/inventory-movements", permissions.INVENTORY_MOVEMENTS_READ, service.get_inventory_movements, schemas.FpaInventoryMovementMetadataResponse)
_register_get("/payment-readiness", permissions.PAYMENT_READINESS_READ, service.get_payment_readiness, schemas.FpaPaymentReadinessResponse)
_register_get("/erp-readiness", permissions.ERP_READINESS_READ, service.get_erp_readiness, schemas.FpaErpReadinessResponse)
_register_get("/bank-readiness", permissions.BANK_READINESS_READ, service.get_bank_readiness, schemas.FpaBankReadinessResponse)
_register_get("/payment-gateway-readiness", permissions.PAYMENT_GATEWAY_READINESS_READ, service.get_payment_gateway_readiness, schemas.FpaPaymentGatewayReadinessResponse)
_register_get("/provider-readiness", permissions.PROVIDER_READINESS_READ, service.get_provider_readiness, schemas.FpaProviderReadinessResponse)
_register_get("/audit-events", permissions.AUDIT_READ, service.get_audit_events, schemas.FpaAuditEventResponse)
_register_get("/evidence", permissions.EVIDENCE_READ, service.get_evidence, schemas.FpaEvidenceItemResponse)
_register_get("/bridges/executive", permissions.BRIDGES_EXECUTIVE_READ, service.get_bridge_executive, schemas.FpaBridgeResponse)
_register_get("/bridges/hr-payroll", permissions.BRIDGES_HR_PAYROLL_READ, service.get_bridge_hr_payroll, schemas.FpaBridgeResponse)
_register_get("/bridges/document-contracts", permissions.BRIDGES_DOCUMENT_CONTRACTS_READ, service.get_bridge_document_contracts, schemas.FpaBridgeResponse)
_register_get("/bridges/provider-readiness", permissions.BRIDGES_PROVIDER_READINESS_READ, service.get_bridge_provider_readiness, schemas.FpaBridgeResponse)
_register_get("/bridges/student-finance", permissions.BRIDGES_STUDENT_FINANCE_READ, service.get_bridge_student_finance, schemas.FpaBridgeResponse)
_register_get("/health", permissions.OVERVIEW_READ, service.get_health, dict[str, Any])
_register_get("/roles", permissions.METADATA_READ, service.get_roles, dict[str, Any])
_register_get("/permissions", permissions.METADATA_READ, service.get_permissions, dict[str, Any])
_register_get("/metadata-contract", permissions.METADATA_READ, service.get_metadata_contract, schemas.FpaMetadataContractResponse)

_register_post("/readiness/evidence", permissions.READINESS_READ, service.create_readiness_evidence, schemas.FpaMetadataCreateRequest)
_register_post("/billing/evidence", permissions.BILLING_EVIDENCE, service.create_billing_evidence, schemas.FpaMetadataCreateRequest)
_register_post("/receivables/metadata", permissions.RECEIVABLES_METADATA, service.create_receivables_metadata, schemas.FpaMetadataCreateRequest)
_register_post("/budget-plans", permissions.BUDGET_PLANS_MANAGE, service.create_budget_plan, schemas.FpaMetadataCreateRequest)
_register_post("/budget-controls/review", permissions.BUDGET_CONTROLS_REVIEW, service.review_budget_control, schemas.FpaReviewCreateRequest)
_register_post("/procurement-requests", permissions.PROCUREMENT_REQUESTS_MANAGE, service.create_procurement_request, schemas.FpaMetadataCreateRequest)
_register_post("/procurement-reviews", permissions.PROCUREMENT_REVIEWS_REVIEW, service.review_procurement, schemas.FpaReviewCreateRequest)
_register_post("/vendors", permissions.VENDORS_MANAGE, service.create_vendor_metadata, schemas.FpaMetadataCreateRequest)
_register_post("/contracts/evidence", permissions.CONTRACTS_EVIDENCE, service.create_contract_evidence, schemas.FpaEvidenceCreateRequest)
_register_post("/purchase-requests", permissions.PURCHASE_REQUESTS_MANAGE, service.create_purchase_request, schemas.FpaMetadataCreateRequest)
_register_post("/purchase-orders/metadata", permissions.PURCHASE_ORDERS_METADATA, service.create_purchase_order_metadata, schemas.FpaMetadataCreateRequest)
_register_post("/assets/metadata", permissions.ASSETS_METADATA, service.create_asset_metadata, schemas.FpaMetadataCreateRequest)
_register_post("/asset-lifecycle", permissions.ASSET_LIFECYCLE_MANAGE, service.create_asset_lifecycle, schemas.FpaMetadataCreateRequest)
_register_post("/inventory-movements/metadata", permissions.INVENTORY_MOVEMENTS_METADATA, service.create_inventory_movement_metadata, schemas.FpaMetadataCreateRequest)
_register_post("/payment-readiness/evidence", permissions.PAYMENT_READINESS_EVIDENCE, service.create_payment_readiness_evidence, schemas.FpaMetadataCreateRequest)
_register_post("/erp-readiness/evidence", permissions.ERP_READINESS_EVIDENCE, service.create_erp_readiness_evidence, schemas.FpaMetadataCreateRequest)
_register_post("/bank-readiness/evidence", permissions.BANK_READINESS_EVIDENCE, service.create_bank_readiness_evidence, schemas.FpaMetadataCreateRequest)
_register_post("/payment-gateway-readiness/evidence", permissions.PAYMENT_GATEWAY_READINESS_EVIDENCE, service.create_payment_gateway_readiness_evidence, schemas.FpaMetadataCreateRequest)
_register_post("/provider-readiness/evidence", permissions.PROVIDER_READINESS_EVIDENCE, service.create_provider_readiness_evidence, schemas.FpaMetadataCreateRequest)
_register_post("/evidence", permissions.EVIDENCE_WRITE, service.create_evidence, schemas.FpaEvidenceCreateRequest)
_register_post("/audit-events", permissions.AUDIT_WRITE, service.create_audit_event, schemas.FpaAuditEventCreateRequest)
