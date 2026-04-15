from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import is_platform_self_service_enabled
from app.modules.audit.service import log_admin_action
from app.modules.auth.local_users_service import local_user_store
from app.modules.billing.service import ensure_tenant_subscription, get_tenant_billing_state
from app.modules.rbac.service import sync_user_roles_from_trusted_source
from app.modules.tenants.provisioning_service import TenantProvisioningService
from app.modules.tenants.service import force_delete_tenant, get_tenant_by_slug
from app.platform.uow import UnitOfWork


router = APIRouter(prefix="/api/platform", tags=["platform-self-service"])
SELF_SERVICE_OPERATION = "platform_tenant_self_service"
IDEMPOTENCY_SCOPE_TENANT_ID = 1


class SelfServiceTenantCreatePayload(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=255)
    admin_login: str = Field(min_length=3, max_length=128)
    admin_password: str = Field(min_length=6, max_length=128)
    admin_display_name: str = Field(default="Tenant Administrator", min_length=2, max_length=128)
    admin_email: str | None = Field(default=None, max_length=255)
    plan_code: str = Field(default="free", min_length=2, max_length=64)


def _hash_request(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _normalize_optional_email(value: str | None) -> str | None:
    normalized = str(value or "").strip().lower()
    return normalized or None


def _self_service_response(
    *,
    payload: SelfServiceTenantCreatePayload,
    request: Request,
    retry_mode: bool,
) -> dict[str, object]:
    actor = "self-service"
    normalized_plan = payload.plan_code.strip().lower()
    normalized_login = payload.admin_login.strip().lower()
    normalized_email = _normalize_optional_email(payload.admin_email)
    admin_contact_email = normalized_email or normalized_login
    slug = TenantProvisioningService.derive_tenant_slug(payload.tenant_name)

    created_new_tenant = False
    created_new_user = False
    tenant_id: int | None = None
    created_user_id: str | None = None

    existing_tenant = get_tenant_by_slug(slug)
    if existing_tenant is not None and not retry_mode:
        raise HTTPException(status_code=409, detail=f"tenant slug '{slug}' already exists")

    existing_login_user = local_user_store.find_user_by_login(normalized_login)
    if existing_login_user is not None and existing_tenant is None:
        raise HTTPException(status_code=409, detail="login already exists")

    existing_email_user = local_user_store.find_user_by_email(admin_contact_email) if admin_contact_email and "@" in admin_contact_email else None
    if existing_email_user is not None and existing_tenant is None:
        raise HTTPException(status_code=409, detail="email already exists")

    try:
        if existing_tenant is None:
            result = TenantProvisioningService.create_tenant_with_defaults(
                tenant_name=payload.tenant_name,
                admin_email=admin_contact_email,
                plan_code=normalized_plan,
                actor=actor,
                slug=slug,
                allow_existing_slug=False,
            )
            created_new_tenant = True
        else:
            result = TenantProvisioningService.create_tenant_with_defaults(
                tenant_name=payload.tenant_name,
                admin_email=admin_contact_email,
                plan_code=normalized_plan,
                actor=actor,
                slug=slug,
                allow_existing_slug=True,
            )

        tenant = result["tenant"]
        tenant_id = int(tenant["id"])

        existing_login_user = local_user_store.find_user_by_login(normalized_login)
        if existing_login_user is not None:
            existing_login_tenant_id = int(existing_login_user.get("tenant_id") or 0)
            if existing_login_tenant_id != tenant_id:
                raise HTTPException(status_code=409, detail="login already exists")
            if normalized_email:
                existing_email = str(existing_login_user.get("email", "")).strip().lower()
                if existing_email and existing_email != normalized_email:
                    raise HTTPException(status_code=409, detail="email already exists")
            admin_user = local_user_store.get_public_user(str(existing_login_user.get("user_id", "")))
            if admin_user is None:
                raise HTTPException(status_code=500, detail="failed to load existing admin user")
        else:
            existing_email_user = local_user_store.find_user_by_email(admin_contact_email) if admin_contact_email and "@" in admin_contact_email else None
            if existing_email_user is not None:
                raise HTTPException(status_code=409, detail="email already exists")

            admin_user = local_user_store.create_user(
                login=normalized_login,
                password=payload.admin_password,
                display_name=payload.admin_display_name,
                roles=["admin"],
                default_language="ru",
                tenant_id=tenant_id,
                email=normalized_email,
            )
            created_new_user = True
            created_user_id = str(admin_user["user_id"])

        sync_user_roles_from_trusted_source(str(admin_user["user_id"]), ["admin"], tenant_id=tenant_id)

        subscription = ensure_tenant_subscription(
            tenant_id,
            plan_code=normalized_plan,
            status="trial",
        )

        billing_state = get_tenant_billing_state(tenant_id)

        log_admin_action(
            actor=actor,
            tenant_id=tenant_id,
            action="platform.tenants.self_service.create",
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "unknown",
            correlation_id=getattr(request.state, "request_id", None),
            entity="platform",
            result="success",
            metadata={
                "tenant_id": tenant_id,
                "tenant_name": payload.tenant_name,
                "tenant_slug": slug,
                "plan_code": normalized_plan,
                "admin_login": normalized_login,
                "admin_email": normalized_email,
            },
        )

        return {
            "tenant": tenant,
            "admin_user": admin_user,
            "plan": result["plan"],
            "subscription": subscription,
            "billing_state": billing_state,
        }
    except HTTPException:
        if created_new_user and created_user_id and tenant_id:
            try:
                local_user_store.delete_user(created_user_id, tenant_id=tenant_id)
            except Exception:
                pass
        if created_new_tenant and tenant_id:
            force_delete_tenant(tenant_id)
        raise
    except Exception as exc:
        if created_new_user and created_user_id and tenant_id:
            try:
                local_user_store.delete_user(created_user_id, tenant_id=tenant_id)
            except Exception:
                pass
        if created_new_tenant and tenant_id:
            force_delete_tenant(tenant_id)
        detail = str(exc)
        status_code = 409 if "already exists" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post("/tenants", status_code=201)
def create_platform_tenant_self_service(
    payload: SelfServiceTenantCreatePayload,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, object]:
    if not is_platform_self_service_enabled():
        raise HTTPException(status_code=403, detail="self-service tenant provisioning disabled")

    normalized_key = str(idempotency_key or "").strip()
    if not normalized_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")

    normalized_login = payload.admin_login.strip().lower()
    normalized_email = _normalize_optional_email(payload.admin_email)
    slug = TenantProvisioningService.derive_tenant_slug(payload.tenant_name)
    request_payload = {
        "tenant_name": payload.tenant_name.strip(),
        "tenant_slug": slug,
        "admin_login": normalized_login,
        "admin_email": normalized_email,
        "plan_code": payload.plan_code.strip().lower(),
    }
    request_hash = _hash_request(request_payload)

    with UnitOfWork() as uow:
        try:
            existing = uow.idempotency_repository.get(
                IDEMPOTENCY_SCOPE_TENANT_ID,
                normalized_key,
                SELF_SERVICE_OPERATION,
                conn=uow.conn,
            )
        except Exception as exc:
            if "prepared statement" in str(exc).lower():
                return _self_service_response(
                    payload=payload,
                    request=request,
                    retry_mode=False,
                )
            raise

        if existing is not None:
            if str(existing.get("request_hash", "")) != request_hash:
                raise HTTPException(status_code=409, detail="idempotency key reuse with different payload")
            if str(existing.get("status", "")).lower() == "completed":
                snapshot = dict(existing.get("response_snapshot") or {})
                return snapshot
        else:
            uow.idempotency_repository.create_pending(
                IDEMPOTENCY_SCOPE_TENANT_ID,
                normalized_key,
                SELF_SERVICE_OPERATION,
                request_hash,
                conn=uow.conn,
            )

        try:
            response = _self_service_response(
                payload=payload,
                request=request,
                retry_mode=existing is not None,
            )
            uow.idempotency_repository.complete(
                IDEMPOTENCY_SCOPE_TENANT_ID,
                normalized_key,
                SELF_SERVICE_OPERATION,
                response,
                conn=uow.conn,
            )
            return response
        except HTTPException as exc:
            uow.idempotency_repository.fail(
                IDEMPOTENCY_SCOPE_TENANT_ID,
                normalized_key,
                SELF_SERVICE_OPERATION,
                {"error": str(exc.detail)},
                conn=uow.conn,
            )
            raise
        except Exception as exc:
            uow.idempotency_repository.fail(
                IDEMPOTENCY_SCOPE_TENANT_ID,
                normalized_key,
                SELF_SERVICE_OPERATION,
                {"error": str(exc)},
                conn=uow.conn,
            )
            raise
