from __future__ import annotations

from pathlib import Path

from app.modules.rbac import service as rbac_service
from app.modules.research_science import models, permissions, router as router_module


BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_FILE = BACKEND_DIR / "alembic" / "versions" / "rs37a2rt01_a0372_research_science_tables.py"

EXPECTED_TABLES = {
    "rs_research_projects",
    "rs_student_research_work",
    "rs_scientific_supervision",
    "rs_publication_registry",
    "rs_conference_participation",
    "rs_grant_applications",
    "rs_grant_deliverables",
    "rs_research_ethics_requests",
    "rs_research_ethics_amendments",
    "rs_research_evidence_metadata",
    "rs_research_bridge_metadata",
    "rs_research_dashboard_snapshots",
    "rs_research_audit_events",
    "rs_research_status_history",
    "rs_research_limitations",
}


def test_import_and_constants_sanity() -> None:
    assert models.MODULE_NAME == "research_science"
    assert models.TABLE_PREFIX == "rs_"
    assert models.TARGET_LEVEL == "L3"
    assert models.CONTRACT_VERSION == "A-037.2"
    assert models.FOUNDATION_STATUS == "RESEARCH_SCIENCE_METADATA_EVIDENCE_BACKEND_FOUNDATION"
    assert models.MASTER_MATRIX_COMMIT == "c79cc31"
    assert models.MASTER_MATRIX_ROW_COUNT == 467
    assert models.RUNTIME_MODE == "METADATA_EVIDENCE_ONLY"


def test_metadata_contains_expected_15_tables() -> None:
    rs_tables = {name for name in models.Base.metadata.tables if name.startswith("rs_")}
    assert rs_tables == EXPECTED_TABLES


def test_router_prefix_and_route_count() -> None:
    routes = [route for route in router_module.router.routes if getattr(route, "path", "").startswith(router_module.router.prefix)]
    assert router_module.router.prefix == "/api/admin/research-science"
    assert len(routes) == 43


def test_permissions_cover_runtime_slice() -> None:
    assert len(permissions.ALL_PERMISSIONS) == 40
    assert permissions.PROJECTS_CREATE in permissions.ALL_PERMISSIONS
    assert permissions.EVIDENCE_ATTACH in permissions.ALL_PERMISSIONS
    assert permissions.ADMIN_CONFIGURE in permissions.ALL_PERMISSIONS


def test_admin_superadmin_and_auditor_receive_permissions() -> None:
    assert permissions.PROJECTS_CREATE in rbac_service.BASELINE_ROLE_PERMISSIONS["admin"]
    assert permissions.BRIDGES_UPDATE in rbac_service.BASELINE_ROLE_PERMISSIONS["superadmin"]
    assert permissions.AUDIT_READ in rbac_service.BASELINE_ROLE_PERMISSIONS["auditor"]


def test_migration_contains_all_foundation_tables() -> None:
    text = MIGRATION_FILE.read_text()
    for table_name in EXPECTED_TABLES:
        assert table_name in text
    assert 'down_revision = "ao36rt52uv71"' in text
    assert "create_table" in text