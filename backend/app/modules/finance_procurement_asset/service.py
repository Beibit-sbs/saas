"""Finance / Procurement / Asset service layer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantRequiredError
from app.modules.finance_procurement_asset import models, permissions, repository, schemas


EXPECTED_ROUTE_COUNT = models.EXPECTED_ROUTE_COUNT
EXPECTED_TABLE_COUNT = models.EXPECTED_TABLE_COUNT
EXPECTED_PERMISSION_COUNT = models.EXPECTED_PERMISSION_COUNT

CANONICAL_MODULES = ["billing", "budget_planning", "procurement", "asset_inventory", "online_payments"]
ROLE_NAMES = [
    "FINANCE_ADMIN",
    "BUDGET_CONTROLLER",
    "PROCUREMENT_REVIEWER",
    "PROCUREMENT_OFFICER",
    "VENDOR_MANAGER",
    "CONTRACT_REVIEWER",
    "ASSET_MANAGER",
    "INVENTORY_CONTROLLER",
    "PAYMENT_READINESS_REVIEWER",
    "ERP_READINESS_REVIEWER",
    "BANK_READINESS_REVIEWER",
    "PROVIDER_READINESS_REVIEWER",
    "HR_PAYROLL_COORDINATOR",
    "AUDIT_REVIEWER",
    "READ_ONLY_VIEWER",
]
REQUIRED_LIMITATIONS = [
    "metadata_only_runtime",
    "evidence_metadata_only",
    "human_review_required",
    "no_live_bank_integration",
    "no_live_erp_sync",
    "no_payment_execution",
    "no_automatic_procurement_approval",
    "no_automatic_budget_approval",
    "no_automatic_vendor_award",
    "no_official_tax_or_regulatory_filing",
]


def _now() -> datetime:
    return datetime.now(UTC)


def _validate_tenant(tenant_id: int) -> int:
    return repository.verify_tenant_scope(tenant_id)


def _validate_actor(actor_user_id: str | int | None) -> str:
    actor = str(actor_user_id or "").strip()
    if not actor:
        raise DomainValidationError("actor_user_id is required")
    return actor


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _merge_limitations(values: list[str] | None) -> list[str]:
    merged = list(values or [])
    for limitation in REQUIRED_LIMITATIONS:
        if limitation not in merged:
            merged.append(limitation)
    return merged


def _metadata_kwargs(request: schemas.FpaMetadataCreateRequest, actor: str, *, status_default: str = "DRAFT", extra: dict[str, Any] | None = None) -> dict[str, Any]:
    data = request.model_dump(exclude_none=True)
    data["metadata_json"] = data.pop("metadata", {})
    data["limitations_json"] = _merge_limitations(data.pop("limitations", None))
    data.setdefault("status", status_default)
    data["human_review_required"] = True
    data["fake_metrics"] = False
    data["fake_finance_data"] = False
    data["fake_payment_data"] = False
    data["provider_connected"] = False
    data["live_bank_sync"] = False
    data["live_erp_sync"] = False
    data["payment_execution_enabled"] = False
    data["automatic_procurement_approval_enabled"] = False
    data["automatic_budget_approval_enabled"] = False
    data["automatic_vendor_award_enabled"] = False
    data["hidden_score_present"] = False
    data["created_by"] = actor
    data["updated_by"] = actor
    return data | (extra or {})


def _audit_event_kwargs(request: schemas.FpaAuditEventCreateRequest, actor: str) -> dict[str, Any]:
    return {
        "status": "RECORDED",
        "entity_type": request.entity_type,
        "entity_id": request.entity_id,
        "action": request.action,
        "actor_user_id": actor,
        "before_json": dict(request.before),
        "after_json": dict(request.after),
        "metadata_json": dict(request.metadata),
        "human_review_required": True,
        "hidden_score_present": False,
    }


def _record_from_model(item) -> schemas.FpaMetadataRecord:
    return schemas.FpaMetadataRecord.model_validate(
        {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "status": getattr(item, "status", "ACTIVE"),
            "reference_key": getattr(item, "reference_key", None),
            "title": getattr(item, "title", None),
            "source_module": getattr(item, "source_module", None),
            "source_record_id": getattr(item, "source_record_id", None),
            "metadata": dict(getattr(item, "metadata_json", {}) or {}),
            "limitations": list(getattr(item, "limitations_json", []) or []),
            "created_at": getattr(item, "created_at", None),
            "updated_at": getattr(item, "updated_at", None),
        }
    )


def _audit_record_from_model(item) -> schemas.FpaAuditEventRecord:
    return schemas.FpaAuditEventRecord.model_validate(
        {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "status": item.status,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "action": item.action,
            "actor_user_id": item.actor_user_id,
            "before": dict(item.before_json or {}),
            "after": dict(item.after_json or {}),
            "metadata": dict(item.metadata_json or {}),
            "created_at": item.created_at,
        }
    )


def _evidence_record_from_model(item) -> schemas.FpaEvidenceItemRecord:
    return schemas.FpaEvidenceItemRecord.model_validate(
        {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "status": item.status,
            "evidence_type": item.evidence_type,
            "title": item.title,
            "reference_uri": item.reference_uri,
            "source_module": item.source_module,
            "source_record_id": item.source_record_id,
            "metadata": dict(item.metadata_json or {}),
            "limitations": list(item.limitations_json or []),
            "created_at": item.created_at,
        }
    )


def _base_response_kwargs(tenant_id: int, limitations: list[str] | None = None) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "module": models.MODULE_NAME,
        "contract_version": models.CONTRACT_VERSION,
        "source_spec_commit": models.SOURCE_SPEC_COMMIT,
        "runtime_mode": models.RUNTIME_MODE,
        "data_source": models.DATA_SOURCE,
        "fake_metrics": False,
        "fake_finance_data": False,
        "fake_payment_data": False,
        "provider_connected": False,
        "live_bank_sync": False,
        "live_erp_sync": False,
        "payment_execution_enabled": False,
        "automatic_procurement_approval_enabled": False,
        "automatic_budget_approval_enabled": False,
        "automatic_vendor_award_enabled": False,
        "hidden_score_present": False,
        "human_review_required": True,
        "incomplete_data": True,
        "limitations": _merge_limitations(limitations),
    }


def _collection_response(schema_cls, tenant_id: int, items) -> Any:
    return schema_cls.model_validate(_base_response_kwargs(tenant_id) | {"records": [_record_from_model(item) for item in items]})


def _audit_response(tenant_id: int, items) -> schemas.FpaAuditEventResponse:
    return schemas.FpaAuditEventResponse.model_validate(_base_response_kwargs(tenant_id) | {"records": [_audit_record_from_model(item) for item in items]})


def _evidence_response(tenant_id: int, items) -> schemas.FpaEvidenceItemResponse:
    return schemas.FpaEvidenceItemResponse.model_validate(_base_response_kwargs(tenant_id) | {"records": [_evidence_record_from_model(item) for item in items]})


def get_overview(db: Session, tenant_id: int) -> schemas.FpaOverviewResponse:
    del db
    tenant_id = _validate_tenant(tenant_id)
    return schemas.FpaOverviewResponse.model_validate(
        _base_response_kwargs(tenant_id)
        | {
            "target_level": models.TARGET_LEVEL,
            "foundation_status": models.FOUNDATION_STATUS,
            "selected_vertical": models.PRODUCT_VERTICAL,
            "canonical_modules": CANONICAL_MODULES,
            "table_count": models.EXPECTED_TABLE_COUNT,
            "route_count": models.EXPECTED_ROUTE_COUNT,
            "permission_count": models.EXPECTED_PERMISSION_COUNT,
        }
    )


def get_readiness(db: Session, tenant_id: int) -> schemas.FpaReadinessResponse:
    return _collection_response(schemas.FpaReadinessResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "readiness"))


def get_limitations(db: Session, tenant_id: int) -> schemas.FpaLimitationsResponse:
    return _collection_response(schemas.FpaLimitationsResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "limitations"))


def get_safety_boundaries(db: Session, tenant_id: int) -> schemas.FpaLimitationsResponse:
    return get_limitations(db, tenant_id)


def get_dashboard(db: Session, tenant_id: int) -> schemas.FpaDashboardResponse:
    tenant_id = _validate_tenant(tenant_id)
    return schemas.FpaDashboardResponse.model_validate(_base_response_kwargs(tenant_id) | {"summary": repository.get_dashboard_inputs(db, tenant_id)})


def get_billing(db: Session, tenant_id: int) -> schemas.FpaBillingVisibilityResponse:
    return _collection_response(schemas.FpaBillingVisibilityResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "billing"))


def get_receivables(db: Session, tenant_id: int) -> schemas.FpaReceivablesMetadataResponse:
    return _collection_response(schemas.FpaReceivablesMetadataResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "receivables"))


def get_budget_plans(db: Session, tenant_id: int) -> schemas.FpaBudgetPlanResponse:
    return _collection_response(schemas.FpaBudgetPlanResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "budget_plans"))


def get_budget_controls(db: Session, tenant_id: int) -> schemas.FpaBudgetControlResponse:
    return _collection_response(schemas.FpaBudgetControlResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "budget_controls"))


def get_procurement_requests(db: Session, tenant_id: int) -> schemas.FpaProcurementRequestResponse:
    return _collection_response(schemas.FpaProcurementRequestResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "procurement_requests"))


def get_procurement_reviews(db: Session, tenant_id: int) -> schemas.FpaProcurementReviewResponse:
    return _collection_response(schemas.FpaProcurementReviewResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "procurement_reviews"))


def get_vendors(db: Session, tenant_id: int) -> schemas.FpaVendorMetadataResponse:
    return _collection_response(schemas.FpaVendorMetadataResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "vendors"))


def get_contracts(db: Session, tenant_id: int) -> schemas.FpaContractEvidenceResponse:
    return _collection_response(schemas.FpaContractEvidenceResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "contracts"))


def get_purchase_requests(db: Session, tenant_id: int) -> schemas.FpaPurchaseRequestResponse:
    return _collection_response(schemas.FpaPurchaseRequestResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "purchase_requests"))


def get_purchase_orders(db: Session, tenant_id: int) -> schemas.FpaPurchaseOrderMetadataResponse:
    return _collection_response(schemas.FpaPurchaseOrderMetadataResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "purchase_orders"))


def get_assets(db: Session, tenant_id: int) -> schemas.FpaAssetVisibilityResponse:
    return _collection_response(schemas.FpaAssetVisibilityResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "assets"))


def get_asset_lifecycle(db: Session, tenant_id: int) -> schemas.FpaAssetLifecycleResponse:
    return _collection_response(schemas.FpaAssetLifecycleResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "asset_lifecycle"))


def get_inventory_movements(db: Session, tenant_id: int) -> schemas.FpaInventoryMovementMetadataResponse:
    return _collection_response(schemas.FpaInventoryMovementMetadataResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "inventory_movements"))


def get_payment_readiness(db: Session, tenant_id: int) -> schemas.FpaPaymentReadinessResponse:
    return _collection_response(schemas.FpaPaymentReadinessResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "payment_readiness"))


def get_erp_readiness(db: Session, tenant_id: int) -> schemas.FpaErpReadinessResponse:
    return _collection_response(schemas.FpaErpReadinessResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "erp_readiness"))


def get_bank_readiness(db: Session, tenant_id: int) -> schemas.FpaBankReadinessResponse:
    return _collection_response(schemas.FpaBankReadinessResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "bank_readiness"))


def get_payment_gateway_readiness(db: Session, tenant_id: int) -> schemas.FpaPaymentGatewayReadinessResponse:
    return _collection_response(schemas.FpaPaymentGatewayReadinessResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "payment_gateway_readiness"))


def get_provider_readiness(db: Session, tenant_id: int) -> schemas.FpaProviderReadinessResponse:
    return _collection_response(schemas.FpaProviderReadinessResponse, _validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "provider_readiness"))


def get_audit_events(db: Session, tenant_id: int) -> schemas.FpaAuditEventResponse:
    return _audit_response(_validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "audit"))


def get_evidence(db: Session, tenant_id: int) -> schemas.FpaEvidenceItemResponse:
    return _evidence_response(_validate_tenant(tenant_id), repository.list_family_rows(db, tenant_id, "evidence"))


def _bridge_response(db: Session, tenant_id: int, bridge_family: str) -> schemas.FpaBridgeResponse:
    return _collection_response(schemas.FpaBridgeResponse, _validate_tenant(tenant_id), repository.get_bridge_inputs(db, tenant_id, bridge_family))


def get_bridge_executive(db: Session, tenant_id: int) -> schemas.FpaBridgeResponse:
    return _bridge_response(db, tenant_id, "executive")


def get_bridge_hr_payroll(db: Session, tenant_id: int) -> schemas.FpaBridgeResponse:
    return _bridge_response(db, tenant_id, "hr_payroll")


def get_bridge_document_contracts(db: Session, tenant_id: int) -> schemas.FpaBridgeResponse:
    return _bridge_response(db, tenant_id, "document_contracts")


def get_bridge_provider_readiness(db: Session, tenant_id: int) -> schemas.FpaBridgeResponse:
    return _bridge_response(db, tenant_id, "provider_readiness")


def get_bridge_student_finance(db: Session, tenant_id: int) -> schemas.FpaBridgeResponse:
    return _bridge_response(db, tenant_id, "student_finance")


def get_bridge_student_finance_referrals(db: Session, tenant_id: int) -> schemas.FpaBridgeResponse:
    return _bridge_response(db, tenant_id, "student_finance_referrals")


def get_health(db: Session, tenant_id: int) -> dict[str, Any]:
    del db
    tenant_id = _validate_tenant(tenant_id)
    return {
        "tenant_id": tenant_id,
        "module": models.MODULE_NAME,
        "route_count": models.EXPECTED_ROUTE_COUNT,
        "table_count": models.EXPECTED_TABLE_COUNT,
        "permission_count": models.EXPECTED_PERMISSION_COUNT,
        "provider_connected": False,
        "live_bank_sync": False,
        "live_erp_sync": False,
        "payment_execution_enabled": False,
        "automatic_decision_enabled": False,
        "hidden_score_present": False,
        "fake_metrics": False,
        "fake_finance_data": False,
        "fake_payment_data": False,
        "human_review_required": True,
        "incomplete_data": True,
    }


def get_roles(db: Session, tenant_id: int) -> dict[str, Any]:
    del db
    return {"tenant_id": _validate_tenant(tenant_id), "roles": ROLE_NAMES, "human_review_required": True}


def get_permissions(db: Session, tenant_id: int) -> dict[str, Any]:
    del db
    return {
        "tenant_id": _validate_tenant(tenant_id),
        "permission_namespace": "finance_procurement_asset.*",
        "permissions": permissions.FINANCE_PROCUREMENT_ASSET_PERMISSIONS,
        "permission_count": permissions.FINANCE_PROCUREMENT_ASSET_PERMISSION_COUNT,
        "human_review_required": True,
    }


def get_metadata_contract(db: Session, tenant_id: int) -> schemas.FpaMetadataContractResponse:
    del db
    tenant_id = _validate_tenant(tenant_id)
    return schemas.FpaMetadataContractResponse.model_validate(
        _base_response_kwargs(tenant_id)
        | {
            "api_prefix": models.API_PREFIX,
            "table_prefix": models.TABLE_PREFIX,
            "table_count": models.EXPECTED_TABLE_COUNT,
            "route_count": models.EXPECTED_ROUTE_COUNT,
            "permission_count": models.EXPECTED_PERMISSION_COUNT,
            "permission_namespace": "finance_procurement_asset.*",
            "module_files": [
                "__init__.py",
                "permissions.py",
                "dependencies.py",
                "models.py",
                "schemas.py",
                "repository.py",
                "service.py",
                "router.py",
            ],
        }
    )


def _create_metadata_record(db: Session, tenant_id: int, actor_user_id: str, family: str, request: schemas.FpaMetadataCreateRequest, *, status_default: str = "DRAFT", extra: dict[str, Any] | None = None) -> dict[str, Any]:
    tenant_id = _validate_tenant(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_family_row(db, tenant_id, family, **_metadata_kwargs(request, actor, status_default=status_default, extra=extra))
    repository.create_audit_event(
        db,
        tenant_id,
        entity_type=family,
        entity_id=entity.id,
        action=f"{family}.metadata_recorded",
        actor_user_id=actor,
        before_json={},
        after_json={"status": entity.status},
        metadata_json={"reference_key": getattr(entity, "reference_key", None)},
        human_review_required=True,
        hidden_score_present=False,
    )
    _commit(db)
    return {"id": entity.id, "tenant_id": entity.tenant_id, "status": entity.status, "human_review_required": True}


def create_readiness_evidence(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "readiness", request, status_default="PROFILE_READY_NON_LIVE")


def create_billing_evidence(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "billing", request, status_default="VISIBLE_METADATA_ONLY")


def create_receivables_metadata(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "receivables", request, status_default="VISIBLE_METADATA_ONLY")


def create_budget_plan(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "budget_plans", request, status_default="REVIEW_REQUIRED")


def review_budget_control(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaReviewCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "budget_controls", request, status_default="HUMAN_REVIEW_REQUIRED", extra={"control_state": "reviewed"})


def create_procurement_request(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "procurement_requests", request, status_default="SUBMITTED")


def review_procurement(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaReviewCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "procurement_reviews", request, status_default="HUMAN_REVIEW_REQUIRED", extra={"reviewer_id": request.reviewer_id})


def create_vendor_metadata(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "vendors", request, status_default="REVIEW_REQUIRED")


def create_contract_evidence(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaEvidenceCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "contracts", request, status_default="EVIDENCE_RECORDED", extra={"reference_uri": request.reference_uri})


def create_purchase_request(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "purchase_requests", request, status_default="SUBMITTED")


def create_purchase_order_metadata(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "purchase_orders", request, status_default="METADATA_ONLY")


def create_asset_metadata(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "assets", request, status_default="VISIBLE_METADATA_ONLY")


def create_asset_lifecycle(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "asset_lifecycle", request, status_default="HUMAN_REVIEW_REQUIRED")


def create_inventory_movement_metadata(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "inventory_movements", request, status_default="METADATA_ONLY")


def create_payment_readiness_evidence(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "payment_readiness", request, status_default="PROFILE_READY_NON_LIVE")


def create_erp_readiness_evidence(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "erp_readiness", request, status_default="PROFILE_READY_NON_LIVE")


def create_bank_readiness_evidence(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "bank_readiness", request, status_default="PROFILE_READY_NON_LIVE")


def create_payment_gateway_readiness_evidence(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "payment_gateway_readiness", request, status_default="PROFILE_READY_NON_LIVE")


def create_provider_readiness_evidence(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata_record(db, tenant_id, actor_user_id, "provider_readiness", request, status_default="PROFILE_READY_NON_LIVE")


def create_evidence(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaEvidenceCreateRequest) -> dict[str, Any]:
    tenant_id = _validate_tenant(tenant_id)
    actor = _validate_actor(actor_user_id)
    item = repository.create_evidence_item(
        db,
        tenant_id,
        status="METADATA_ONLY",
        evidence_type=request.evidence_type,
        title=request.title or request.reference_key,
        reference_uri=request.reference_uri,
        source_module=request.source_module,
        source_record_id=request.source_record_id,
        metadata_json=dict(request.metadata),
        limitations_json=_merge_limitations(request.limitations),
        human_review_required=True,
        fake_finance_data=False,
        fake_payment_data=False,
        provider_connected=False,
        created_by=actor,
    )
    _commit(db)
    return {"id": item.id, "tenant_id": item.tenant_id, "status": item.status, "human_review_required": True}


def create_audit_event(db: Session, tenant_id: int, actor_user_id: str, request: schemas.FpaAuditEventCreateRequest) -> dict[str, Any]:
    tenant_id = _validate_tenant(tenant_id)
    actor = _validate_actor(actor_user_id)
    item = repository.create_audit_event(db, tenant_id, **_audit_event_kwargs(request, actor))
    _commit(db)
    return {"id": item.id, "tenant_id": item.tenant_id, "status": item.status, "human_review_required": True}
