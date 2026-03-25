from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _imports(path: str) -> set[str]:
    tree = ast.parse(_read(path))
    imported: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)

    return imported


def _assert_no_prefix(imports: set[str], forbidden_prefixes: set[str]) -> None:
    offenders = sorted(
        imp
        for imp in imports
        if any(imp == prefix or imp.startswith(prefix + ".") for prefix in forbidden_prefixes)
    )
    assert not offenders, f"forbidden imports found: {offenders}"


def test_public_router_does_not_import_internal_or_admin_routers() -> None:
    imports = _imports("backend/app/platform/router_public.py")
    _assert_no_prefix(imports, {"app.platform.router_admin", "app.platform.router_internal"})


def test_developer_auth_does_not_depend_on_admin_or_internal_router_modules() -> None:
    imports = _imports("backend/app/platform/developer/auth.py")
    _assert_no_prefix(imports, {"app.platform.router_admin", "app.platform.router_internal"})


def test_ai_layer_retrieval_module_uses_approved_platform_services_only() -> None:
    imports = _imports("backend/app/platform/ai/retrieval.py")

    # AI retrieval is intentionally read-oriented through approved platform services.
    required = {
        "app.platform.analytics",
        "app.platform.kpi",
        "app.platform.context",
        "app.platform.automation",
        "app.platform.education_graph",
    }
    for req in required:
        assert any(imp == req or imp.startswith(req + ".") for imp in imports), (
            f"missing expected retrieval dependency prefix: {req}"
        )

    # Block direct domain service coupling from the AI retrieval layer.
    forbidden_domain_prefixes = {
        "app.modules.students",
        "app.modules.enrollments",
        "app.modules.grades",
        "app.modules.scheduling",
        "app.modules.transcripts",
        "app.modules.degree_progress",
    }
    _assert_no_prefix(imports, forbidden_domain_prefixes)


def test_automation_engine_executes_side_effects_via_action_registry_entrypoint() -> None:
    source = _read("backend/app/platform/automation/service.py")
    assert "from app.platform.automation.actions import execute_action" in source
    assert "result = execute_action(action, event, uow=uow)" in source
    assert "app.platform.education_graph" not in source


def test_ai_service_does_not_bypass_retrieval_for_education_graph_access() -> None:
    imports = _imports("backend/app/platform/ai/service.py")
    _assert_no_prefix(imports, {"app.platform.education_graph.service"})


def test_platform_admin_router_keeps_actor_dependency_guard_pattern() -> None:
    source = _read("backend/app/platform/router_admin.py")
    assert "Actor = Annotated[str, Depends(get_actor)]" in source


def test_public_router_uses_developer_scope_guards_for_public_data_endpoints() -> None:
    source = _read("backend/app/platform/router_public.py")
    # students, enrollments, grades, analytics/kpi
    assert source.count("Depends(require_developer_scope(") >= 4
