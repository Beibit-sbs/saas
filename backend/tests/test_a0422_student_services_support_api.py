from __future__ import annotations

from pathlib import Path
import re

from app.main import app


BASE = "/api/admin/student-services"
BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_FILE = BACKEND_DIR / "alembic" / "versions" / "sss0422rt01_a0422_student_services_support_tables.py"


def test_route_inventory_exact_21() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith(BASE)]
    target = {
        "/api/admin/student-services/requests",
        "/api/admin/student-services/requests/{request_id}",
        "/api/admin/student-services/requests/{request_id}/assign",
        "/api/admin/student-services/requests/{request_id}/status",
        "/api/admin/student-services/cases",
        "/api/admin/student-services/cases/{case_id}",
        "/api/admin/student-services/cases/{case_id}/notes",
        "/api/admin/student-services/cases/{case_id}/evidence",
        "/api/admin/student-services/hardship",
        "/api/admin/student-services/hardship/from-finance-handoff",
        "/api/admin/student-services/hardship/from-finance-handoff/reviewer-queue",
        "/api/admin/student-services/hardship/from-finance-handoff/finance-office-referral-queue",
        "/api/admin/student-services/hardship/from-finance-handoff/{hardship_id}/evidence-gap",
        "/api/admin/student-services/hardship/from-finance-handoff/{hardship_id}/human-review-outcome-note",
        "/api/admin/student-services/hardship/from-finance-handoff/{hardship_id}/finance-office-referral",
        "/api/admin/student-services/accommodations",
        "/api/admin/student-services/complaints",
        "/api/admin/student-services/escalations",
        "/api/admin/student-services/dashboard/summary",
    }
    matched = [route for route in routes if route.path in target]
    assert len(matched) == 21


def test_all_target_routes_are_guarded() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith(BASE)]
    target = {
        "/api/admin/student-services/requests",
        "/api/admin/student-services/requests/{request_id}",
        "/api/admin/student-services/requests/{request_id}/assign",
        "/api/admin/student-services/requests/{request_id}/status",
        "/api/admin/student-services/cases",
        "/api/admin/student-services/cases/{case_id}",
        "/api/admin/student-services/cases/{case_id}/notes",
        "/api/admin/student-services/cases/{case_id}/evidence",
        "/api/admin/student-services/hardship",
        "/api/admin/student-services/hardship/from-finance-handoff",
        "/api/admin/student-services/hardship/from-finance-handoff/reviewer-queue",
        "/api/admin/student-services/hardship/from-finance-handoff/finance-office-referral-queue",
        "/api/admin/student-services/hardship/from-finance-handoff/{hardship_id}/evidence-gap",
        "/api/admin/student-services/hardship/from-finance-handoff/{hardship_id}/human-review-outcome-note",
        "/api/admin/student-services/hardship/from-finance-handoff/{hardship_id}/finance-office-referral",
        "/api/admin/student-services/accommodations",
        "/api/admin/student-services/complaints",
        "/api/admin/student-services/escalations",
        "/api/admin/student-services/dashboard/summary",
    }
    for route in routes:
        if route.path in target:
            dependency_calls = [getattr(dep.call, "__name__", "") for dep in route.dependant.dependencies]
            assert "get_actor" in dependency_calls
            assert len(route.dependant.dependencies) >= 3


def test_forbidden_route_names_absent() -> None:
    forbidden = {
        "/api/admin/student-services/auto-hardship-approval",
        "/api/admin/student-services/auto-accommodation-approval",
        "/api/admin/student-services/auto-complaint-close",
        "/api/admin/student-services/provider-live-sync",
        "/api/admin/student-services/brain-autonomous-decision",
        "/api/admin/student-services/hidden-score",
    }
    paths = {route.path for route in app.routes if route.path.startswith(BASE)}
    assert not (paths & forbidden)


def test_migration_create_drop_sets_match_12() -> None:
    text = MIGRATION_FILE.read_text()
    assert len(re.findall(r'op\.create_table\(\s*"sss_', text)) == 12
    assert text.count('op.drop_table("sss_') == 12
