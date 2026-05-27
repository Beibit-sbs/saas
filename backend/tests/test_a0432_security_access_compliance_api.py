from __future__ import annotations

from pathlib import Path

import pytest

from app.main import app


BASE = "/api/admin/security-access-compliance"
BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_FILE = BACKEND_DIR / "alembic" / "versions" / "sac0432rt01_a0432_security_access_compliance_tables.py"

EXPECTED_ROUTE_METHODS = {
    ("GET", f"{BASE}/overview"),
    ("GET", f"{BASE}/readiness"),
    ("GET", f"{BASE}/dashboard"),
    ("GET", f"{BASE}/limitations"),
    ("GET", f"{BASE}/roles"),
    ("GET", f"{BASE}/permissions"),
    ("GET", f"{BASE}/access-governance"),
    ("GET", f"{BASE}/rbac-evidence"),
    ("GET", f"{BASE}/abac-evidence"),
    ("GET", f"{BASE}/sessions"),
    ("GET", f"{BASE}/login-events"),
    ("GET", f"{BASE}/mfa-readiness"),
    ("GET", f"{BASE}/tenant-isolation"),
    ("GET", f"{BASE}/incidents"),
    ("GET", f"{BASE}/incident-review"),
    ("GET", f"{BASE}/remediation"),
    ("GET", f"{BASE}/risks"),
    ("GET", f"{BASE}/compliance-controls"),
    ("GET", f"{BASE}/policy-controls"),
    ("GET", f"{BASE}/audit-events"),
    ("GET", f"{BASE}/sensitive-actions"),
    ("GET", f"{BASE}/data-protection"),
    ("GET", f"{BASE}/privacy-readiness"),
    ("GET", f"{BASE}/exceptions"),
    ("GET", f"{BASE}/visitor-access"),
    ("GET", f"{BASE}/bridges/hr"),
    ("GET", f"{BASE}/bridges/finance"),
    ("GET", f"{BASE}/bridges/documents"),
    ("GET", f"{BASE}/bridges/student-services"),
    ("GET", f"{BASE}/metadata-contract"),
    ("POST", f"{BASE}/incidents/metadata"),
    ("POST", f"{BASE}/incident-review/metadata"),
    ("POST", f"{BASE}/remediation/metadata"),
    ("POST", f"{BASE}/risks/metadata"),
    ("POST", f"{BASE}/compliance-controls/metadata"),
    ("POST", f"{BASE}/policy-controls/metadata"),
    ("POST", f"{BASE}/audit-events/metadata"),
    ("POST", f"{BASE}/sensitive-actions/review"),
    ("POST", f"{BASE}/data-protection/evidence"),
    ("POST", f"{BASE}/privacy-readiness/evidence"),
    ("POST", f"{BASE}/exceptions/metadata"),
    ("POST", f"{BASE}/visitor-access/metadata"),
    ("POST", f"{BASE}/bridges/hr"),
    ("POST", f"{BASE}/bridges/finance"),
    ("POST", f"{BASE}/bridges/documents"),
    ("POST", f"{BASE}/bridges/student-services"),
    ("POST", f"{BASE}/limitations"),
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


def test_route_inventory_exact_47() -> None:
    found = {(method, path) for method, path, _ in _target_routes()}
    assert found == EXPECTED_ROUTE_METHODS
    assert len(found) == 47


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
        f"{BASE}/certify-compliance",
        f"{BASE}/certify-security",
        f"{BASE}/close-incident-officially",
        f"{BASE}/auto-block-user",
        f"{BASE}/auto-sanction-user",
        f"{BASE}/auto-delete-data",
        f"{BASE}/submit-to-regulator",
        f"{BASE}/publish-risk-score",
        f"{BASE}/hidden-user-score",
    ],
)
def test_forbidden_route_names_absent(forbidden_path: str) -> None:
    paths = {path for _, path, _ in _target_routes()}
    assert forbidden_path not in paths


def test_migration_create_drop_sets_match_24() -> None:
    namespace: dict[str, object] = {}
    exec(MIGRATION_FILE.read_text(), namespace)
    create_tables = namespace.get("CREATE_TABLES")
    assert isinstance(create_tables, list)
    assert len(create_tables) == 24
    assert len(set(create_tables)) == 24
    assert all(str(name).startswith("sac_") for name in create_tables)
