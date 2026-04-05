"""Developer/Partner Integration API - Separate Trust Zone.

This router handles third-party integrations with app credentials (X-App-Key/X-App-Secret).
NOT part of public API; requires explicit developer registration and scope validation.

Prefix: /api/dev (separate from /api/v1/public)
Auth: X-App-Key + X-App-Secret (developer credentials)
Tenant: Extracted from app_key (NOT from URL, headers, or body)
"""
from __future__ import annotations

import base64
import binascii
from datetime import date, datetime, timezone
from functools import lru_cache
import hashlib
import hmac
import json
import logging
import os
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from app.modules.observability.metrics import observe_developer_analytics_contract
from app.modules.observability.security_signals import record_security_signal

from app.platform.analytics import service as analytics_service
from app.platform.analytics.entitlements import analytics_entitlement_deny_reason, assert_analytics_read_entitled
from app.platform.billing import service as billing_service
from app.platform.analytics.schemas import (
    AnalyticsEventProjectionAppliedFiltersSchema,
    AnalyticsEventProjectionListSchema,
    AnalyticsEventProjectionRead,
    TenantKpiSnapshotRead,
)
from app.platform.developer.auth import require_developer_scope
from app.platform.developer import service as developer_service
from app.platform.developer.schemas import PublicEnrollmentReadSchema, PublicGradeReadSchema, PublicStudentReadSchema
from app.platform.kpi import service as kpi_service
from app.platform.kpi.schemas import RectorDashboardReadSchema
from app.platform.uow import UnitOfWork
from app.modules.students import service as students_service
from app.modules.enrollments import service as enrollments_service


# ============================================================================
# Developer/Partner API Router (Enterprise integrations)
# Requires X-App-Key + X-App-Secret in request headers
# ============================================================================

router = APIRouter(
    prefix="/api/dev",
    tags=["developer-api"],
    responses={
        401: {"description": "Invalid or missing app credentials"},
        403: {"description": "Insufficient scope or unauthorized"},
        429: {"description": "Rate limit exceeded"},
    },
)


_ANALYTICS_EVENTS_DEFAULT_LIMIT = 50
_ANALYTICS_EVENTS_MAX_LIMIT = 100
_ANALYTICS_EVENTS_DEFAULT_ORDERING = "created_at_desc"
_ANALYTICS_EVENTS_MAX_RANGE_DAYS = 31
_ANALYTICS_EVENTS_CURSOR_VERSION = 1
_ANALYTICS_USAGE_METRIC_EVENTS_READ = "analytics.events.read"
_ANALYTICS_USAGE_METRIC_KPI_READ = "analytics.kpi.read"


logger = logging.getLogger("app.developer.analytics")


class _CursorValidationError(ValueError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = str(reason)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    raw = str(data or "").strip()
    if not raw:
        raise _CursorValidationError("malformed_cursor")
    padding = "=" * ((4 - len(raw) % 4) % 4)
    try:
        return base64.urlsafe_b64decode((raw + padding).encode("ascii"))
    except (ValueError, binascii.Error) as exc:
        raise _CursorValidationError("malformed_cursor") from exc


@lru_cache(maxsize=1)
def _events_cursor_signing_secret() -> bytes:
    raw = os.getenv("JWT_SECRET", "").strip()
    if not raw:
        raise RuntimeError("JWT_SECRET must be configured")
    return raw.encode("utf-8")


def _sign_events_cursor(payload_b64: str) -> str:
    mac = hmac.new(_events_cursor_signing_secret(), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(mac)


def _student_row(item: dict[str, object]) -> dict[str, object]:
    """Transform student record for API response."""
    return {
        "id": int(item.get("id", 0)),
        "tenant_id": item.get("tenant_id"),
        "student_id": item.get("student_id"),
        "first_name": item.get("first_name"),
        "last_name": item.get("last_name"),
        "email": item.get("email"),
        "status": item.get("status"),
        "payload": dict(item),
    }


def _enrollment_row(item: dict[str, object]) -> dict[str, object]:
    """Transform enrollment record for API response."""
    return {
        "id": int(item.get("id", 0)),
        "tenant_id": item.get("tenant_id"),
        "student_id": item.get("student_id"),
        "course_id": item.get("course_id"),
        "semester": item.get("semester"),
        "status": item.get("status"),
        "payload": dict(item),
    }


def _decode_events_cursor(
    *,
    cursor: str | None,
    app_id: int,
    tenant_id: int,
    ordering: str,
    event_type: str | None,
    date_from: date | None,
    date_to: date | None,
) -> int | None:
    if cursor is None:
        return None
    raw = str(cursor).strip()
    if not raw:
        return None

    if "." not in raw:
        raise _CursorValidationError("malformed_cursor")
    payload_b64, signature = raw.split(".", 1)
    if not payload_b64 or not signature:
        raise _CursorValidationError("malformed_cursor")
    expected_signature = _sign_events_cursor(payload_b64)
    if not hmac.compare_digest(expected_signature.encode("ascii"), signature.encode("ascii")):
        raise _CursorValidationError("invalid_cursor_signature")

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise _CursorValidationError("malformed_cursor") from exc

    if not isinstance(payload, dict):
        raise _CursorValidationError("malformed_cursor")

    expected_filters = {
        "event_type": event_type,
        "date_from": date_from.isoformat() if date_from is not None else None,
        "date_to": date_to.isoformat() if date_to is not None else None,
    }
    if (
        payload.get("v") != _ANALYTICS_EVENTS_CURSOR_VERSION
        or int(payload.get("aid", 0)) != app_id
        or int(payload.get("tid", 0)) != tenant_id
        or str(payload.get("ord", "")) != ordering
        or payload.get("filters") != expected_filters
    ):
        raise _CursorValidationError("cursor_context_mismatch")

    try:
        anchor_id = int(payload.get("id"))
    except (TypeError, ValueError) as exc:
        raise _CursorValidationError("malformed_cursor") from exc
    if anchor_id <= 0:
        raise _CursorValidationError("malformed_cursor")
    return anchor_id


def _encode_events_cursor(
    *,
    app_id: int,
    tenant_id: int,
    ordering: str,
    anchor_id: int,
    event_type: str | None,
    date_from: date | None,
    date_to: date | None,
) -> str:
    payload = {
        "v": _ANALYTICS_EVENTS_CURSOR_VERSION,
        "aid": app_id,
        "tid": tenant_id,
        "ord": ordering,
        "id": int(anchor_id),
        "filters": {
            "event_type": event_type,
            "date_from": date_from.isoformat() if date_from is not None else None,
            "date_to": date_to.isoformat() if date_to is not None else None,
        },
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return f"{payload_b64}.{_sign_events_cursor(payload_b64)}"


def _normalize_events_ordering(ordering: str) -> str:
    normalized_ordering = str(ordering).strip().lower() or _ANALYTICS_EVENTS_DEFAULT_ORDERING
    if normalized_ordering != _ANALYTICS_EVENTS_DEFAULT_ORDERING:
        raise HTTPException(
            status_code=422,
            detail=f"unsupported ordering: {ordering}; allowed: {_ANALYTICS_EVENTS_DEFAULT_ORDERING}",
        )
    return normalized_ordering


def _normalize_events_limit(limit: int) -> int:
    return max(1, min(int(limit), _ANALYTICS_EVENTS_MAX_LIMIT))


def _validate_events_date_range(date_from: date | None, date_to: date | None) -> None:
    if date_from is not None and date_to is not None:
        if date_from > date_to:
            raise HTTPException(status_code=422, detail="date_from must be less than or equal to date_to")
        range_days = (date_to - date_from).days
        if range_days > _ANALYTICS_EVENTS_MAX_RANGE_DAYS:
            raise HTTPException(
                status_code=422,
                detail=f"date range too large; maximum is {_ANALYTICS_EVENTS_MAX_RANGE_DAYS} days",
            )


def _events_filters_metadata(*, event_type: str | None, date_from: date | None, date_to: date | None) -> dict[str, object]:
    date_span_days = None
    if date_from is not None and date_to is not None:
        date_span_days = max(0, (date_to - date_from).days)
    return {
        "event_type_applied": event_type is not None,
        "date_filter_applied": date_from is not None or date_to is not None,
        "date_span_days": date_span_days,
    }


def _classify_events_contract_error(exc: HTTPException) -> str:
    detail = str(exc.detail or "").lower()
    if exc.status_code == 400 and "invalid cursor" in detail:
        return "invalid_cursor"
    if exc.status_code == 422 and "unsupported ordering" in detail:
        return "invalid_ordering"
    if exc.status_code == 422 and (
        "date_from must be less than or equal to date_to" in detail or "date range too large" in detail
    ):
        return "invalid_date_range"
    return f"http_{exc.status_code}"


def _classify_cursor_validation_error(exc: _CursorValidationError) -> str:
    reason = str(exc.reason or "").strip().lower()
    if reason == "invalid_cursor_signature":
        return "tampered_cursor"
    if reason == "cursor_context_mismatch":
        return "cursor_context_mismatch"
    return "malformed_cursor"


def _analytics_entitlement_reason(exc: HTTPException) -> str | None:
    return analytics_entitlement_deny_reason(exc)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freshness_from_snapshot_date(*, snapshot_date: str | None, is_empty: bool = False) -> str:
    if is_empty:
        return "empty"
    if not snapshot_date:
        return "stale"
    try:
        day = date.fromisoformat(str(snapshot_date))
    except ValueError:
        return "stale"
    return "fresh" if day == datetime.now(timezone.utc).date() else "stale"


def _observe_developer_analytics_request(
    *,
    request: Request,
    app_id: int,
    tenant_id: int,
    endpoint_name: str,
    outcome: str,
    reason: str,
    status_code: int,
    result_count: int | None = None,
    filters_metadata: dict[str, object] | None = None,
    requested_limit: int | None = None,
    effective_limit: int | None = None,
) -> None:
    observe_developer_analytics_contract(endpoint=endpoint_name, outcome=outcome, reason=reason)

    if outcome == "denied":
        record_security_signal(
            signal="developer.analytics.contract_denied",
            outcome="denied",
            actor=f"app:{app_id}",
            client_ip=request.client.host if request.client else None,
            path=str(request.url.path),
            tenant_id=tenant_id,
        )

    level = logging.WARNING if outcome == "denied" else logging.INFO
    logger.log(
        level,
        (
            "developer_analytics_request "
            "endpoint=%s outcome=%s reason=%s tenant_id=%s app_id=%s result_count=%s "
            "requested_limit=%s effective_limit=%s filters=%s"
        ),
        endpoint_name,
        outcome,
        reason,
        tenant_id,
        app_id,
        result_count,
        requested_limit,
        effective_limit,
        filters_metadata or {},
        extra={
            "endpoint": str(request.url.path),
            "method": request.method,
            "status_code": int(status_code),
            "developer_app_id": int(app_id),
            "error_code": reason,
        },
    )


@router.get(
    "/students",
    response_model=list[PublicStudentReadSchema],
    summary="List students",
    description="List students for authenticated tenant. Developer scope required.",
)
def list_developer_students(
    request: Request,
    auth: dict[str, object] = Depends(require_developer_scope("students.read")),
) -> list[PublicStudentReadSchema]:
    """Get list of students for tenant.

    Security:
    - Requires X-App-Key + X-App-Secret headers
    - Requires 'students.read' scope
    - Tenant determined from app_key (not URL, headers, or body)
    - Rate limited per app_id

    Returns:
    - List of student records (no cross-tenant data)
    - 401 if credentials invalid
    - 403 if scope insufficient
    - 429 if rate limit exceeded
    """
    started = time.monotonic()
    status_code = 200
    try:
        tenant_id = int(auth["tenant_id"])
        app_id = int(auth["app_id"])

        rows = students_service.list_students(tenant_id)
        return [PublicStudentReadSchema.model_validate(_student_row(item)) for item in rows]
    except Exception:
        status_code = 500
        raise
    finally:
        # Log API usage for rate limiting and audit
        developer_service.developer_service.log_api_usage(
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )


@router.get(
    "/enrollments",
    response_model=list[PublicEnrollmentReadSchema],
    summary="List enrollments",
    description="List course enrollments for authenticated tenant.",
)
def list_developer_enrollments(
    request: Request,
    auth: dict[str, object] = Depends(require_developer_scope("enrollments.read")),
) -> list[PublicEnrollmentReadSchema]:
    """Get list of enrollments for tenant.

    Security:
    - Requires X-App-Key + X-App-Secret headers
    - Requires 'enrollments.read' scope
    - Tenant determined from app_key (not URL, headers, or body)
    - Rate limited per app_id

    Returns:
    - List of enrollment records (no cross-tenant data)
    """
    started = time.monotonic()
    status_code = 200
    try:
        tenant_id = int(auth["tenant_id"])
        app_id = int(auth["app_id"])

        rows = enrollments_service.list_enrollments(tenant_id)
        return [PublicEnrollmentReadSchema.model_validate(_enrollment_row(item)) for item in rows]
    except Exception:
        status_code = 500
        raise
    finally:
        developer_service.developer_service.log_api_usage(
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )


@router.get(
    "/grades",
    response_model=list[PublicGradeReadSchema],
    summary="List grades",
    description="List student grades for authenticated tenant.",
)
def list_developer_grades(
    request: Request,
    auth: dict[str, object] = Depends(require_developer_scope("grades.read")),
) -> list[PublicGradeReadSchema]:
    """Get list of grades for tenant.

    Security:
    - Requires X-App-Key + X-App-Secret headers
    - Requires 'grades.read' scope
    - Tenant determined from app_key
    - Rate limited per app_id
    """
    started = time.monotonic()
    status_code = 200
    try:
        tenant_id = int(auth["tenant_id"])
        app_id = int(auth["app_id"])

        rows = developer_service.developer_service.list_public_grades(
            session_factory=getattr(request.app.state, "admissions_session_factory", None),
            tenant_id=tenant_id,
        )
        return [PublicGradeReadSchema.model_validate(item) for item in rows]
    except Exception:
        status_code = 500
        raise
    finally:
        developer_service.developer_service.log_api_usage(
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )


@router.get(
    "/analytics/events",
    response_model=AnalyticsEventProjectionListSchema,
    summary="List recent analytics events",
    description="List recent analytics event projections for authenticated tenant.",
)
def list_developer_analytics_events(
    request: Request,
    event_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    cursor: str | None = None,
    ordering: str = _ANALYTICS_EVENTS_DEFAULT_ORDERING,
    limit: int = _ANALYTICS_EVENTS_DEFAULT_LIMIT,
    auth: dict[str, object] = Depends(require_developer_scope("analytics.read")),
) -> AnalyticsEventProjectionListSchema:
    tenant_id = int(auth["tenant_id"])
    app_id = int(auth["app_id"])
    started = time.monotonic()
    status_code = 200
    endpoint_name = "analytics.events"
    try:
        assert_analytics_read_entitled(tenant_id)
        normalized_ordering = _normalize_events_ordering(ordering)
        requested_limit = int(limit)
        normalized_limit = _normalize_events_limit(limit)
        _validate_events_date_range(date_from, date_to)
        cursor_id_lt = _decode_events_cursor(
            cursor=cursor,
            app_id=app_id,
            tenant_id=tenant_id,
            ordering=normalized_ordering,
            event_type=(event_type or None),
            date_from=date_from,
            date_to=date_to,
        )

        with UnitOfWork() as uow:
            items = analytics_service.list_event_projections(
                tenant_id=tenant_id,
                event_type=(event_type or None),
                date_from=date_from,
                date_to=date_to,
                cursor_id_lt=cursor_id_lt,
                ordering=normalized_ordering,
                limit=normalized_limit,
                uow=uow,
            )
        filters_metadata = _events_filters_metadata(
            event_type=(event_type or None),
            date_from=date_from,
            date_to=date_to,
        )
        if normalized_limit != requested_limit:
            _observe_developer_analytics_request(
                request=request,
                app_id=app_id,
                tenant_id=tenant_id,
                endpoint_name=endpoint_name,
                outcome="guarded",
                reason="limit_clamped",
                status_code=200,
                result_count=len(items),
                filters_metadata=filters_metadata,
                requested_limit=requested_limit,
                effective_limit=normalized_limit,
            )
        next_cursor = (
            _encode_events_cursor(
                app_id=app_id,
                tenant_id=tenant_id,
                ordering=normalized_ordering,
                anchor_id=int(items[-1]["id"]),
                event_type=(event_type or None),
                date_from=date_from,
                date_to=date_to,
            )
            if len(items) == normalized_limit
            else None
        )
        latest_event_at = str(items[0].get("created_at")) if items else None
        served_at = _utc_now_iso()
        _observe_developer_analytics_request(
            request=request,
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint_name=endpoint_name,
            outcome="success",
            reason="ok",
            status_code=200,
            result_count=len(items),
            filters_metadata=filters_metadata,
            requested_limit=requested_limit,
            effective_limit=normalized_limit,
        )
        billing_service.increment_usage(tenant_id=tenant_id, metric=_ANALYTICS_USAGE_METRIC_EVENTS_READ, value=1)
        return AnalyticsEventProjectionListSchema(
            tenant_id=tenant_id,
            total=len(items),
            limit=normalized_limit,
            ordering=normalized_ordering,
            next_cursor=next_cursor,
            data_as_of=latest_event_at,
            freshness_status=("fresh" if items else "empty"),
            served_at=served_at,
            applied_filters=AnalyticsEventProjectionAppliedFiltersSchema(
                event_type=(event_type or None),
                date_from=(date_from.isoformat() if date_from is not None else None),
                date_to=(date_to.isoformat() if date_to is not None else None),
            ),
            items=[AnalyticsEventProjectionRead.model_validate(item) for item in items],
        )
    except _CursorValidationError as exc:
        status_code = 400
        _observe_developer_analytics_request(
            request=request,
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint_name=endpoint_name,
            outcome="denied",
            reason=_classify_cursor_validation_error(exc),
            status_code=status_code,
            filters_metadata=_events_filters_metadata(
                event_type=(event_type or None),
                date_from=date_from,
                date_to=date_to,
            ),
            requested_limit=int(limit),
            effective_limit=_normalize_events_limit(limit),
        )
        raise HTTPException(status_code=400, detail="invalid cursor") from exc
    except HTTPException as exc:
        status_code = exc.status_code
        entitlement_reason = _analytics_entitlement_reason(exc)
        if entitlement_reason is not None:
            _observe_developer_analytics_request(
                request=request,
                app_id=app_id,
                tenant_id=tenant_id,
                endpoint_name=endpoint_name,
                outcome="denied",
                reason=entitlement_reason,
                status_code=status_code,
                filters_metadata=_events_filters_metadata(
                    event_type=(event_type or None),
                    date_from=date_from,
                    date_to=date_to,
                ),
                requested_limit=int(limit),
                effective_limit=_normalize_events_limit(limit),
            )
        elif status_code in {400, 422}:
            _observe_developer_analytics_request(
                request=request,
                app_id=app_id,
                tenant_id=tenant_id,
                endpoint_name=endpoint_name,
                outcome="denied",
                reason=_classify_events_contract_error(exc),
                status_code=status_code,
                filters_metadata=_events_filters_metadata(
                    event_type=(event_type or None),
                    date_from=date_from,
                    date_to=date_to,
                ),
                requested_limit=int(limit),
                effective_limit=_normalize_events_limit(limit),
            )
        raise
    except Exception:
        status_code = 500
        _observe_developer_analytics_request(
            request=request,
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint_name=endpoint_name,
            outcome="error",
            reason="internal_error",
            status_code=status_code,
            filters_metadata=_events_filters_metadata(
                event_type=(event_type or None),
                date_from=date_from,
                date_to=date_to,
            ),
            requested_limit=int(limit),
            effective_limit=_normalize_events_limit(limit),
        )
        raise
    finally:
        developer_service.developer_service.log_api_usage(
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )


@router.get(
    "/analytics/kpis/latest",
    response_model=TenantKpiSnapshotRead,
    summary="Get latest analytics KPI snapshot",
    description="Return the latest analytics KPI snapshot for authenticated tenant.",
)
def get_developer_latest_analytics_kpis(
    request: Request,
    auth: dict[str, object] = Depends(require_developer_scope("analytics.read")),
) -> TenantKpiSnapshotRead:
    tenant_id = int(auth["tenant_id"])
    app_id = int(auth["app_id"])
    started = time.monotonic()
    status_code = 200
    endpoint_name = "analytics.kpis.latest"
    try:
        assert_analytics_read_entitled(tenant_id)
        with UnitOfWork() as uow:
            snapshot = analytics_service.get_latest_tenant_kpis(tenant_id=tenant_id, uow=uow)
        if snapshot is None:
            status_code = 404
            _observe_developer_analytics_request(
                request=request,
                app_id=app_id,
                tenant_id=tenant_id,
                endpoint_name=endpoint_name,
                outcome="denied",
                reason="not_found",
                status_code=status_code,
            )
            raise HTTPException(status_code=404, detail="No KPI snapshot found for this tenant")
        _observe_developer_analytics_request(
            request=request,
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint_name=endpoint_name,
            outcome="success",
            reason="ok",
            status_code=200,
            result_count=1,
        )
        billing_service.increment_usage(tenant_id=tenant_id, metric=_ANALYTICS_USAGE_METRIC_KPI_READ, value=1)
        payload = dict(snapshot)
        payload["data_as_of"] = str(snapshot.get("updated_at")) if snapshot.get("updated_at") is not None else None
        payload["freshness_status"] = _freshness_from_snapshot_date(snapshot_date=str(snapshot.get("snapshot_date")))
        payload["served_at"] = _utc_now_iso()
        return TenantKpiSnapshotRead.model_validate(payload)
    except HTTPException as exc:
        status_code = exc.status_code
        entitlement_reason = _analytics_entitlement_reason(exc)
        if entitlement_reason is not None:
            _observe_developer_analytics_request(
                request=request,
                app_id=app_id,
                tenant_id=tenant_id,
                endpoint_name=endpoint_name,
                outcome="denied",
                reason=entitlement_reason,
                status_code=status_code,
            )
        raise
    except Exception:
        status_code = 500
        _observe_developer_analytics_request(
            request=request,
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint_name=endpoint_name,
            outcome="error",
            reason="internal_error",
            status_code=status_code,
        )
        raise
    finally:
        developer_service.developer_service.log_api_usage(
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )


@router.get(
    "/analytics/kpi",
    response_model=RectorDashboardReadSchema,
    summary="Get KPI analytics",
    description="Get KPI dashboard data for authenticated tenant.",
)
def get_developer_kpi(
    request: Request,
    auth: dict[str, object] = Depends(require_developer_scope("analytics.read")),
) -> RectorDashboardReadSchema:
    """Get KPI analytics dashboard for tenant.

    Security:
    - Requires X-App-Key + X-App-Secret headers
    - Requires 'analytics.read' scope
    - Tenant determined from app_key
    - Rate limited per app_id

    Returns:
    - KPI metrics (no cross-tenant data)
    - 401 if credentials invalid
    - 403 if scope insufficient
    """
    tenant_id = int(auth["tenant_id"])
    app_id = int(auth["app_id"])
    started = time.monotonic()
    status_code = 200
    endpoint_name = "analytics.kpi"
    try:
        assert_analytics_read_entitled(tenant_id)
        with UnitOfWork() as uow:
            payload = kpi_service.get_rector_dashboard(tenant_id=tenant_id, uow=uow)
        _observe_developer_analytics_request(
            request=request,
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint_name=endpoint_name,
            outcome="success",
            reason="ok",
            status_code=200,
            result_count=1,
        )
        billing_service.increment_usage(tenant_id=tenant_id, metric=_ANALYTICS_USAGE_METRIC_KPI_READ, value=1)
        payload_with_serving = dict(payload)
        cards = payload_with_serving.get("cards")
        is_empty = not cards
        payload_with_serving["data_as_of"] = (
            str(payload_with_serving.get("generated_at")) if payload_with_serving.get("generated_at") is not None else None
        )
        payload_with_serving["freshness_status"] = _freshness_from_snapshot_date(
            snapshot_date=(
                str(payload_with_serving.get("snapshot_date"))
                if payload_with_serving.get("snapshot_date") is not None
                else None
            ),
            is_empty=is_empty,
        )
        payload_with_serving["served_at"] = _utc_now_iso()
        return RectorDashboardReadSchema.model_validate(payload_with_serving)
    except HTTPException as exc:
        status_code = exc.status_code
        entitlement_reason = _analytics_entitlement_reason(exc)
        _observe_developer_analytics_request(
            request=request,
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint_name=endpoint_name,
            outcome="denied",
            reason=(entitlement_reason if entitlement_reason is not None else f"http_{status_code}"),
            status_code=status_code,
        )
        raise
    except Exception:
        status_code = 500
        _observe_developer_analytics_request(
            request=request,
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint_name=endpoint_name,
            outcome="error",
            reason="internal_error",
            status_code=status_code,
        )
        raise
    finally:
        developer_service.developer_service.log_api_usage(
            app_id=app_id,
            tenant_id=tenant_id,
            endpoint=str(request.url.path),
            status_code=status_code,
            latency_ms=round((time.monotonic() - started) * 1000, 2),
        )
