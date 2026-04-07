from __future__ import annotations

from typing import Callable

from fastapi import Header, HTTPException

from app.platform.developer.service import developer_service


def require_developer_scope(scope: str) -> Callable:
    def _dependency(
        x_app_key: str | None = Header(default=None, alias="X-App-Key"),
        x_app_secret: str | None = Header(default=None, alias="X-App-Secret"),
        x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    ) -> dict[str, object]:
        if not x_app_key or not x_app_secret:
            raise HTTPException(status_code=401, detail="developer app credentials are required")
        if x_tenant_id is not None:
            raise HTTPException(status_code=400, detail="manual tenant override is forbidden for developer API")
        try:
            return developer_service.validate_credentials(
                app_key=x_app_key,
                app_secret=x_app_secret,
                required_scope=scope,
            )
        except ValueError as exc:
            message = str(exc)
            if "scope" in message:
                raise HTTPException(status_code=403, detail=message) from exc
            raise HTTPException(status_code=401, detail=message) from exc

    return _dependency