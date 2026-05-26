from __future__ import annotations

from pathlib import Path

from app.main import app


BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_FILE = BACKEND_DIR / "alembic" / "versions" / "ddc0412rt01_a0412_document_decree_correspondence_tables.py"


def test_route_inventory_exact_53() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith("/api/admin/document-decree-correspondence")]
    assert len(routes) == 53


def test_route_methods_cover_get_and_post() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith("/api/admin/document-decree-correspondence")]
    methods = set()
    for route in routes:
        methods |= set(route.methods or set())
    assert "GET" in methods
    assert "POST" in methods


def test_all_routes_are_actor_and_permission_guarded() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith("/api/admin/document-decree-correspondence")]
    assert len(routes) == 53
    for route in routes:
        dependency_calls = [getattr(dep.call, "__name__", "") for dep in route.dependant.dependencies]
        assert "get_actor" in dependency_calls
        assert len(route.dependant.dependencies) >= 4


def test_forbidden_route_names_absent() -> None:
    forbidden = {
        "/api/admin/document-decree-correspondence/sign-document",
        "/api/admin/document-decree-correspondence/issue-official-decree",
        "/api/admin/document-decree-correspondence/approve-decree-auto",
        "/api/admin/document-decree-correspondence/rector-decision-auto",
        "/api/admin/document-decree-correspondence/submit-to-ministry",
        "/api/admin/document-decree-correspondence/send-external-delivery",
        "/api/admin/document-decree-correspondence/confirm-legal-archive",
        "/api/admin/document-decree-correspondence/hidden-score",
    }
    paths = {route.path for route in app.routes if route.path.startswith("/api/admin/document-decree-correspondence")}
    assert not (paths & forbidden)


def test_migration_create_drop_sets_match_26() -> None:
    text = MIGRATION_FILE.read_text()
    assert text.count('op.create_table("ddc_') == 26
    assert text.count('op.drop_table("ddc_') == 26
