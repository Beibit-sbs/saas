from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app

REQUIRED_DOCS = [
    ROOT_DIR / "README.md",
    ROOT_DIR / "docs/project-status.md",
    ROOT_DIR / "docs/templates/project-context-template.md",
    ROOT_DIR / "docs/templates/template-sync-playbook.md",
    ROOT_DIR / "docs/templates/platform-maturity-matrix.md",
    ROOT_DIR / "docs/templates/template-contracts.md",
    ROOT_DIR / ".ai/rules.md",
    ROOT_DIR / ".ai/workflow.md",
    ROOT_DIR / ".ai/master-orchestrator.md",
]

REQUIRED_MODULE_PATHS = [
    ROOT_DIR / "backend/app/modules/auth",
    ROOT_DIR / "backend/app/modules/rbac",
    ROOT_DIR / "backend/app/modules/audit",
    ROOT_DIR / "backend/app/modules/integrations",
    ROOT_DIR / "backend/app/modules/ai_gateway",
    ROOT_DIR / "backend/app/modules/feature_flags",
    ROOT_DIR / "backend/app/modules/example_slice",
    ROOT_DIR / "backend/app/modules/backup",
    ROOT_DIR / "backend/app/modules/i18n",
    ROOT_DIR / "backend/app/modules/observability",
    ROOT_DIR / "frontend/app/admin/page.tsx",
]

REQUIRED_ROUTE_PATHS = {
    "/health",
    "/api/health",
    "/api/auth/modes",
    "/api/admin/dashboard",
    "/api/admin/local-users",
    "/api/admin/rbac/roles",
    "/api/admin/integrations/ldap",
    "/api/admin/ai/providers",
    "/api/admin/feature-flags",
    "/api/admin/example-slice/reference-items",
    "/api/admin/backups/settings",
    "/api/admin/audit/events",
    "/api/i18n/languages",
}


def test_required_template_docs_exist() -> None:
    missing = [str(path.relative_to(ROOT_DIR)) for path in REQUIRED_DOCS if not path.exists()]
    assert not missing, f"missing required template docs: {missing}"


def test_required_template_modules_exist() -> None:
    missing = [str(path.relative_to(ROOT_DIR)) for path in REQUIRED_MODULE_PATHS if not path.exists()]
    assert not missing, f"missing required template modules: {missing}"


def test_bootstrap_instructions_exist() -> None:
    readme_text = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    playbook_text = (ROOT_DIR / "docs/templates/template-sync-playbook.md").read_text(encoding="utf-8")

    assert "## Template Bootstrap" in readme_text
    assert "make template-validate" in readme_text
    assert "Derived Project Bootstrap Flow" in playbook_text


def test_required_routes_exist() -> None:
    route_paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    missing = sorted(
        path
        for path in REQUIRED_ROUTE_PATHS
        if path not in route_paths and f"{path}/" not in route_paths
    )
    assert not missing, f"missing required routes: {missing}"


def test_minimal_health_checks_pass() -> None:
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    api_response = client.get("/api/health")
    assert api_response.status_code == 200
    assert api_response.json()["status"] == "ok"