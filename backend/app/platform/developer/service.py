from __future__ import annotations

import json
import secrets
from typing import Any
from urllib import request as urllib_request

from sqlalchemy import desc, select

from app.modules.auth.local_users_service import _hash_password, _verify_password
from app.modules.grades.models import GradeSubmissionModel
from app.platform.developer.models import DeveloperAppStatus, DeveloperInstallationStatus
from app.platform.developer.repository import DeveloperRepository
from app.platform.events.schemas import OutboxEventRead
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork


def _normalize_scopes(scopes: list[str]) -> list[str]:
    return sorted({str(scope or "").strip().lower() for scope in scopes if str(scope or "").strip()})


class DeveloperPlatformService:
    def __init__(self, repository: DeveloperRepository | None = None) -> None:
        self._repository = repository or DeveloperRepository()

    def clear_state(self) -> None:
        self._repository.clear_state()

    def create_app(
        self,
        *,
        tenant_id: int,
        name: str,
        description: str,
        owner_email: str,
        scopes: list[str],
        webhook_url: str | None = None,
    ) -> dict[str, Any]:
        app_key = f"app_{secrets.token_hex(12)}"
        app_secret = secrets.token_urlsafe(32)
        row = self._repository.create_app(
            tenant_id=int(tenant_id),
            name=str(name).strip(),
            app_key=app_key,
            app_secret_hash=_hash_password(app_secret),
            description=str(description or "").strip(),
            owner_email=str(owner_email).strip().lower(),
            status=DeveloperAppStatus.ACTIVE.value,
            webhook_url=str(webhook_url).strip() or None if webhook_url else None,
            scopes=_normalize_scopes(scopes),
        )
        return {**row, "app_secret": app_secret}

    def list_apps(self, *, tenant_id: int | None = None) -> list[dict[str, Any]]:
        return self._repository.list_apps(tenant_id=tenant_id)

    def get_app(self, app_id: int) -> dict[str, Any] | None:
        return self._repository.get_app(int(app_id))

    def rotate_secret(self, app_id: int) -> dict[str, Any]:
        app = self._repository.get_app(int(app_id))
        if app is None:
            raise ValueError(f"developer app {app_id} not found")
        app_secret = secrets.token_urlsafe(32)
        updated = self._repository.update_app_secret_hash(int(app_id), _hash_password(app_secret))
        if updated is None:
            raise ValueError(f"developer app {app_id} not found")
        return {**updated, "app_secret": app_secret}

    def install_app(self, *, app_id: int, tenant_id: int, installed_by: str) -> dict[str, Any]:
        app = self._repository.get_app(int(app_id))
        if app is None:
            raise ValueError(f"developer app {app_id} not found")
        app_tenant_id = app.get("tenant_id")
        if app_tenant_id is not None and int(app_tenant_id) != int(tenant_id):
            raise ValueError(f"developer app {app_id} not found")
        return self._repository.create_installation(
            app_id=int(app_id),
            tenant_id=int(tenant_id),
            status=DeveloperInstallationStatus.ACTIVE.value,
            installed_by=str(installed_by or "platform-admin"),
        )

    def list_installations(self, app_id: int) -> list[dict[str, Any]]:
        return self._repository.list_installations(int(app_id))

    def list_api_logs(self, app_id: int, *, limit: int = 100) -> list[dict[str, Any]]:
        return self._repository.list_api_logs(int(app_id), limit=limit)

    def subscribe_to_event(self, *, app_id: int, event_type: str) -> dict[str, Any]:
        app = self._repository.get_app(int(app_id))
        if app is None:
            raise ValueError(f"developer app {app_id} not found")
        return self._repository.create_event_subscription(app_id=int(app_id), event_type=event_type)

    def list_event_subscriptions(self, app_id: int) -> list[dict[str, Any]]:
        return self._repository.list_event_subscriptions(int(app_id))

    def validate_credentials(
        self,
        *,
        app_key: str,
        app_secret: str,
        tenant_id: int,
        required_scope: str,
    ) -> dict[str, Any]:
        app = self._repository.get_app_by_key(app_key)
        if app is None:
            raise ValueError("developer app not found")
        if str(app.get("status", "")).lower() != DeveloperAppStatus.ACTIVE.value:
            raise ValueError("developer app inactive")
        if not _verify_password(str(app_secret or ""), str(app.get("app_secret_hash", ""))):
            raise ValueError("invalid developer app secret")
        installation = self._repository.get_installation(app_id=int(app["id"]), tenant_id=int(tenant_id))
        if installation is None or str(installation.get("status", "")).lower() != DeveloperInstallationStatus.ACTIVE.value:
            raise ValueError("developer app not installed for tenant")
        scopes = list(app.get("scopes", []))
        normalized_scope = str(required_scope or "").strip().lower()
        if normalized_scope not in scopes:
            raise ValueError("developer app scope not granted")
        return {
            "app_id": int(app["id"]),
            "app_key": str(app["app_key"]),
            "tenant_id": int(tenant_id),
            "scopes": scopes,
            "installation_id": int(installation["id"]),
        }

    def log_api_usage(self, *, app_id: int, tenant_id: int, endpoint: str, status_code: int, latency_ms: float) -> dict[str, Any]:
        return self._repository.log_api_call(
            app_id=int(app_id),
            tenant_id=int(tenant_id),
            endpoint=str(endpoint),
            status_code=int(status_code),
            latency_ms=float(latency_ms),
        )

    def list_public_grades(self, *, session_factory: Any, tenant_id: int, limit: int = 100) -> list[dict[str, Any]]:
        if session_factory is None:
            return []
        with session_factory() as session:
            rows = session.execute(
                select(GradeSubmissionModel)
                .where(GradeSubmissionModel.tenant_id == int(tenant_id))
                .order_by(desc(GradeSubmissionModel.submitted_at), desc(GradeSubmissionModel.id))
                .limit(max(1, min(int(limit), 500)))
            ).scalars().all()
        return [
            {
                "id": int(row.id),
                "tenant_id": int(row.tenant_id),
                "enrollment_id": int(row.enrollment_id),
                "grade_code": str(row.grade_code),
                "grade_points": str(row.grade_points),
                "grading_scale_id": int(row.grading_scale_id),
                "submitted_by": str(row.submitted_by),
                "submitted_at": row.submitted_at.isoformat(),
            }
            for row in rows
        ]

    def dispatch_event_to_subscribed_apps(self, *, event: OutboxEventRead, uow: UnitOfWork) -> dict[str, int]:
        apps = self._repository.list_subscribed_apps_for_event(str(event.event_type), conn=uow.conn)
        delivered = 0
        failed = 0
        for app in apps:
            webhook_url = str(app.get("webhook_url") or "").strip()
            if not webhook_url:
                failed += 1
                continue
            payload = {
                "event_type": event.event_type,
                "tenant_id": event.tenant_id,
                "aggregate_type": event.aggregate_type,
                "aggregate_id": event.aggregate_id,
                "payload": event.payload_json,
                "correlation_id": event.correlation_id,
            }
            body = json.dumps(payload).encode("utf-8")
            request = urllib_request.Request(
                url=webhook_url,
                data=body,
                headers={"Content-Type": "application/json", "User-Agent": "ai-platform-developer-events/1.0"},
                method="POST",
            )
            try:
                with urllib_request.urlopen(request, timeout=5.0) as response:
                    if 200 <= int(getattr(response, "status", 500)) < 300:
                        delivered += 1
                    else:
                        failed += 1
            except Exception:
                failed += 1
        return {"attempted": len(apps), "delivered": delivered, "failed": failed}


developer_service = DeveloperPlatformService()


def clear_developer_state() -> None:
    developer_service.clear_state()