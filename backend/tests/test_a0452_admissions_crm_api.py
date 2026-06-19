from __future__ import annotations

from pathlib import Path
import re

from app.main import app


BASE = "/api/admin/admissions-crm"
BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_FILE = BACKEND_DIR / "alembic" / "versions" / "acrm0452rt01_a0452_admissions_crm_batch1_tables.py"


def test_route_inventory_exact_12() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith(BASE)]
    target = {
        "/api/admin/admissions-crm/leads",
        "/api/admin/admissions-crm/leads/{lead_id}",
        "/api/admin/admissions-crm/leads/{lead_id}/qualify",
        "/api/admin/admissions-crm/leads/{lead_id}/convert-to-applicant",
        "/api/admin/admissions-crm/applicants",
        "/api/admin/admissions-crm/applicants/{applicant_id}",
        "/api/admin/admissions-crm/applications",
        "/api/admin/admissions-crm/applications/{application_id}",
        "/api/admin/admissions-crm/applications/{application_id}/submit",
    }
    matched = [route for route in routes if route.path in target]
    assert len(matched) == 12


def test_all_target_routes_are_guarded() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith(BASE)]
    for route in routes:
        dependency_calls = [getattr(dep.call, "__name__", "") for dep in route.dependant.dependencies]
        assert "get_actor" in dependency_calls
        assert len(route.dependant.dependencies) >= 3


def test_forbidden_route_names_absent() -> None:
    forbidden = {
        "/api/admin/admissions-crm/communications/threads",
        "/api/admin/admissions-crm/campaigns",
        "/api/admin/admissions-crm/interviews/sessions",
        "/api/admin/admissions-crm/decisions",
        "/api/admin/admissions-crm/handoffs",
        "/api/admin/admissions-crm/analytics/pipeline",
        "/api/admin/admissions-crm/dashboards/executive",
    }
    paths = {route.path for route in app.routes if route.path.startswith(BASE)}
    assert not (paths & forbidden)


def test_migration_create_drop_sets_match_12() -> None:
    text = MIGRATION_FILE.read_text()
    assert len(re.findall(r'op\.create_table\(\s*"acrm_', text)) == 12
    assert text.count('op.drop_table("acrm_') == 12


def test_route_methods_distribution_matches_batch1() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith(BASE)]
    methods: dict[str, set[str]] = {}
    for route in routes:
        methods.setdefault(route.path, set()).update(set(route.methods))
    assert methods["/api/admin/admissions-crm/leads"] >= {"GET", "POST"}
    assert methods["/api/admin/admissions-crm/applicants"] >= {"GET", "POST"}
    assert methods["/api/admin/admissions-crm/applications"] >= {"GET", "POST"}
