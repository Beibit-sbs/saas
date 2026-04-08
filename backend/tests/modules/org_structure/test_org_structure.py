from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.main import app
from app.modules.org_structure.dependencies import get_org_structure_db
from app.modules.org_structure.models import OrgUnitModel, OrgUnitType
from app.modules.org_structure import service as org_service
from tests.conftest import ADMIN_HEADERS, _auth_headers, _configure_db_only_role_resolution, client


TENANT_A = 1
TENANT_B = 2


@pytest.fixture(autouse=True)
def _enable_org_permissions(monkeypatch: pytest.MonkeyPatch):
    _configure_db_only_role_resolution(
        monkeypatch,
        {
            "owner@example.com": ["admin"],
            "student@example.com": ["student"],
        },
    )


@pytest.fixture
def override_org_db() -> Generator[MagicMock, None, None]:
    session = MagicMock()
    app.dependency_overrides[get_org_structure_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_org_structure_db, None)


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return dict(ADMIN_HEADERS)


@pytest.fixture
def student_headers() -> dict[str, str]:
    return _auth_headers("student@example.com", ["student"])


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_unit(
    *,
    unit_id: int = 1,
    tenant_id: int = TENANT_A,
    name: str = "Faculty of Engineering",
    code: str = "ENG",
    unit_type: OrgUnitType = OrgUnitType.FACULTY,
    parent_unit_id: int | None = None,
    active: bool = True,
) -> OrgUnitModel:
    now = datetime(2026, 4, 6, 10, 0, 0, tzinfo=UTC)
    unit = MagicMock(spec=OrgUnitModel)
    unit.id = unit_id
    unit.tenant_id = tenant_id
    unit.name = name
    unit.code = code
    unit.unit_type = unit_type
    unit.parent_unit_id = parent_unit_id
    unit.active = active
    unit.head_person_id = None
    unit.email = None
    unit.phone = None
    unit.location = None
    unit.created_at = now
    unit.updated_at = now
    return unit


# ---------------------------------------------------------------------------
# POST /api/admin/org-units
# ---------------------------------------------------------------------------

class TestCreateOrgUnit:
    def test_create_returns_201(self, override_org_db: MagicMock, admin_headers: dict) -> None:
        unit = _make_unit()
        override_org_db.query.return_value.filter.return_value.first.return_value = None
        override_org_db.flush.return_value = None
        override_org_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)
        override_org_db.query.return_value.filter.return_value.all.return_value = []

        with (
            pytest.MonkeyPatch().context() as mp,
        ):
            mp.setattr(org_service, "create_org_unit", lambda db, tid, payload: unit)
            resp = client.post(
                "/api/admin/org-units",
                json={
                    "name": "Faculty of Engineering",
                    "code": "ENG",
                    "unit_type": "faculty",
                },
                headers=admin_headers,
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == "ENG"
        assert data["unit_type"] == "faculty"

    def test_create_forbidden_for_students(self, override_org_db: MagicMock, student_headers: dict) -> None:
        resp = client.post(
            "/api/admin/org-units",
            json={"name": "X", "code": "X", "unit_type": "faculty"},
            headers=student_headers,
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/admin/org-units
# ---------------------------------------------------------------------------

class TestListOrgUnits:
    def test_list_returns_units_for_tenant(self, override_org_db: MagicMock, admin_headers: dict) -> None:
        units = [_make_unit(unit_id=1), _make_unit(unit_id=2, code="MATH", name="Mathematics")]
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(org_service, "list_org_units", lambda db, tid, **kw: units)
            resp = client.get("/api/admin/org-units", headers=admin_headers)
        assert resp.status_code == 200
        result = resp.json()
        assert len(result) == 2

    def test_list_forbidden_for_students(self, student_headers: dict) -> None:
        resp = client.get("/api/admin/org-units", headers=student_headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/admin/org-units/tree
# ---------------------------------------------------------------------------

class TestOrgUnitTree:
    def test_tree_returns_nested_structure(self, override_org_db: MagicMock, admin_headers: dict) -> None:
        root = _make_unit(unit_id=1, code="ROOT", unit_type=OrgUnitType.UNIVERSITY, parent_unit_id=None)
        child = _make_unit(unit_id=2, code="ENG", unit_type=OrgUnitType.FACULTY, parent_unit_id=1)

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(org_service, "get_tree", lambda db, tid: [root, child])
            resp = client.get("/api/admin/org-units/tree", headers=admin_headers)

        assert resp.status_code == 200
        tree = resp.json()
        assert len(tree) == 1  # only root at top level
        assert tree[0]["code"] == "ROOT"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["code"] == "ENG"


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------

class TestTenantIsolation:
    def test_service_create_rejects_wrong_tenant_parent(self) -> None:
        """create_org_unit raises DomainValidationError when parent is in different tenant."""
        from app.core.module_helpers.service_validation import DomainValidationError

        session = MagicMock()
        # parent lookup returns None → parent not found in tenant scope
        session.query.return_value.filter.return_value.first.return_value = None

        payload_data = MagicMock()
        payload_data.parent_unit_id = 999
        payload_data.name = "Sub Unit"
        payload_data.code = "SUB"
        payload_data.unit_type = OrgUnitType.DEPARTMENT
        payload_data.head_person_id = None
        payload_data.email = None
        payload_data.phone = None
        payload_data.location = None

        with pytest.raises(DomainValidationError):
            org_service.create_org_unit(session, tenant_id=1, payload=payload_data)

    def test_service_get_not_found_raises(self) -> None:
        from app.core.module_helpers.service_validation import TenantResourceNotFoundError

        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(TenantResourceNotFoundError):
            org_service.get_org_unit(session, tenant_id=1, unit_id=42)

    def test_bootstrap_idempotent(self) -> None:
        """bootstrap_university_root returns existing root without inserting duplicate."""
        existing = _make_unit(unit_type=OrgUnitType.UNIVERSITY, parent_unit_id=None)
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = existing

        result = org_service.bootstrap_university_root(session, tenant_id=1, name="Test University")
        assert result is existing
        session.add.assert_not_called()
