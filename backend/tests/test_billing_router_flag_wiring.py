from __future__ import annotations

from fastapi import FastAPI

from app.main import _register_optional_routers
from app.modules.billing.router import router as billing_module_router
from app.platform.router_admin import router as platform_admin_router


_BILLING_STATE_PATH = "/api/admin/billing/tenants/{tenant_id}/state"


def _route_paths(app: FastAPI) -> set[str]:
    return {route.path for route in app.routes}


def test_optional_billing_router_enabled_by_default_in_non_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("BILLING_MODULE_ROUTER_ENABLED", raising=False)

    app = FastAPI()
    _register_optional_routers(app)

    assert _BILLING_STATE_PATH in _route_paths(app)


def test_optional_billing_router_disabled_by_default_in_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("BILLING_MODULE_ROUTER_ENABLED", raising=False)

    app = FastAPI()
    _register_optional_routers(app)

    assert _BILLING_STATE_PATH not in _route_paths(app)


def test_optional_billing_router_enabled(monkeypatch) -> None:
    monkeypatch.setenv("BILLING_MODULE_ROUTER_ENABLED", "true")

    app = FastAPI()
    _register_optional_routers(app)

    assert _BILLING_STATE_PATH in _route_paths(app)


def test_module_billing_paths_do_not_overlap_platform_v1_billing_paths() -> None:
    module_paths = {route.path for route in billing_module_router.routes}
    platform_billing_paths = {route.path for route in platform_admin_router.routes if "/billing/" in route.path}

    assert module_paths.isdisjoint(platform_billing_paths)
