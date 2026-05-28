from __future__ import annotations

from pathlib import Path

import pytest

from app.main import app


BASE = "/api/admin/campus-facilities"
BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_FILE = BACKEND_DIR / "alembic" / "versions" / "cfht0442rt01_a0442_campus_facilities_housing_transport_tables.py"

EXPECTED_ROUTE_METHODS = {
    ("GET", f"{BASE}/overview"),
    ("GET", f"{BASE}/dashboard"),
    ("GET", f"{BASE}/campus"),
    ("GET", f"{BASE}/facilities"),
    ("GET", f"{BASE}/buildings"),
    ("GET", f"{BASE}/floors"),
    ("GET", f"{BASE}/rooms"),
    ("GET", f"{BASE}/room-types"),
    ("GET", f"{BASE}/availability"),
    ("GET", f"{BASE}/occupancy"),
    ("GET", f"{BASE}/dormitories"),
    ("GET", f"{BASE}/housing-units"),
    ("GET", f"{BASE}/housing-requests"),
    ("GET", f"{BASE}/maintenance"),
    ("GET", f"{BASE}/service-requests"),
    ("GET", f"{BASE}/work-orders"),
    ("GET", f"{BASE}/transport-routes"),
    ("GET", f"{BASE}/transport-vehicles"),
    ("GET", f"{BASE}/transport-schedules"),
    ("GET", f"{BASE}/responsible-units"),
    ("GET", f"{BASE}/safety-readiness"),
    ("GET", f"{BASE}/bridges/access-visitor"),
    ("GET", f"{BASE}/bridges/student-services"),
    ("GET", f"{BASE}/bridges/finance-assets"),
    ("GET", f"{BASE}/bridges/hr-staff"),
    ("GET", f"{BASE}/audit-evidence"),
    ("GET", f"{BASE}/limitations"),
    ("GET", f"{BASE}/metadata-contract"),
    ("GET", f"{BASE}/health"),
    ("GET", f"{BASE}/safety-boundaries"),
    ("POST", f"{BASE}/facilities/metadata"),
    ("POST", f"{BASE}/campus/metadata"),
    ("POST", f"{BASE}/buildings/metadata"),
    ("POST", f"{BASE}/floors/metadata"),
    ("POST", f"{BASE}/rooms/metadata"),
    ("POST", f"{BASE}/room-types/metadata"),
    ("POST", f"{BASE}/availability/metadata"),
    ("POST", f"{BASE}/occupancy/metadata"),
    ("POST", f"{BASE}/dormitories/metadata"),
    ("POST", f"{BASE}/housing-units/metadata"),
    ("POST", f"{BASE}/housing-requests/metadata"),
    ("POST", f"{BASE}/maintenance/metadata"),
    ("POST", f"{BASE}/service-requests/metadata"),
    ("POST", f"{BASE}/work-orders/metadata"),
    ("POST", f"{BASE}/transport/metadata"),
    ("POST", f"{BASE}/responsible-units/metadata"),
    ("POST", f"{BASE}/safety-readiness/evidence"),
    ("POST", f"{BASE}/bridges/access-visitor/metadata"),
    ("POST", f"{BASE}/bridges/student-services/metadata"),
    ("POST", f"{BASE}/bridges/finance-assets/metadata"),
    ("POST", f"{BASE}/bridges/hr-staff/metadata"),
    ("POST", f"{BASE}/limitations/metadata"),
}


def _target_routes():
    routes = []
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith(BASE):
            continue
        methods = {method for method in getattr(route, "methods", set()) if method not in {"HEAD", "OPTIONS"}}
        for method in methods:
            routes.append((method, path, route))
    return routes


def test_route_inventory_exact_52() -> None:
    found = {(method, path) for method, path, _ in _target_routes()}
    assert found == EXPECTED_ROUTE_METHODS
    assert len(found) == 52


@pytest.mark.parametrize("method,path", sorted(EXPECTED_ROUTE_METHODS))
def test_each_expected_route_exists(method: str, path: str) -> None:
    found = {(m, p) for m, p, _ in _target_routes()}
    assert (method, path) in found


def test_all_target_routes_are_rbac_and_tenant_guarded() -> None:
    for _, _, route in _target_routes():
        dependency_calls = [getattr(dep.call, "__name__", "") for dep in route.dependant.dependencies]
        assert "get_actor" in dependency_calls
        assert len(route.dependant.dependencies) >= 3


@pytest.mark.parametrize(
    "forbidden_path",
    [
        f"{BASE}/evictions/execute",
        f"{BASE}/housing/auto-assign",
        f"{BASE}/housing/auto-approve",
        f"{BASE}/transport/dispatch-live",
        f"{BASE}/iot/telemetry",
        f"{BASE}/gps/live",
        f"{BASE}/building-automation/control",
        f"{BASE}/access/lockdown",
        f"{BASE}/certify-campus-safety",
        f"{BASE}/provider-sync/live",
    ],
)
def test_forbidden_route_names_absent(forbidden_path: str) -> None:
    paths = {path for _, path, _ in _target_routes()}
    assert forbidden_path not in paths


def test_migration_create_drop_sets_match_26() -> None:
    namespace: dict[str, object] = {}
    exec(MIGRATION_FILE.read_text(), namespace)
    create_tables = namespace.get("CREATE_TABLES")
    assert isinstance(create_tables, list)
    assert len(create_tables) == 26
    assert len(set(create_tables)) == 26
    assert all(str(name).startswith("cfht_") for name in create_tables)
