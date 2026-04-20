from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.main import app
from app.core.module_helpers.service_validation import MutationResult
from app.modules.org_structure.dependencies import get_org_structure_db
from app.modules.org_structure.models import OrgUnitModel, OrgUnitType
from app.modules.org_structure.schemas import OrgUnitReadSchema
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
            mp.setattr(org_service, "create_org_unit", lambda db, tid, payload: MutationResult(entity=OrgUnitReadSchema.model_validate(unit)))
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
        assert data["unit"]["code"] == "ENG"
        assert data["unit"]["unit_type"] == "faculty"

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

    def test_consistency_endpoint_returns_issues(self, override_org_db: MagicMock, admin_headers: dict) -> None:
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(
                org_service,
                "get_org_unit_consistency_report",
                lambda db, tid: {
                    "unit_count": 3,
                    "issue_count": 1,
                    "issues": [
                        {
                            "issue_type": "unit_missing_parent",
                            "unit_id": 3,
                            "parent_unit_id": 999,
                            "unit_type": "department",
                        }
                    ],
                },
            )
            resp = client.get("/api/admin/org-units/consistency", headers=admin_headers)

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["unit_count"] == 3
        assert payload["issue_count"] == 1
        assert payload["issues"][0]["issue_type"] == "unit_missing_parent"


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

    def test_consistency_report_detects_missing_parent_and_multiple_roots(self) -> None:
        root_a = _make_unit(unit_id=1, code="ROOT-A", unit_type=OrgUnitType.UNIVERSITY, parent_unit_id=None)
        root_b = _make_unit(unit_id=2, code="ROOT-B", unit_type=OrgUnitType.UNIVERSITY, parent_unit_id=None)
        child_orphan = _make_unit(unit_id=3, code="CS", unit_type=OrgUnitType.DEPARTMENT, parent_unit_id=999)

        session = MagicMock()
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(org_service, "get_tree", lambda db, tid: [root_a, root_b, child_orphan])
            report = org_service.get_org_unit_consistency_report(session, tenant_id=1)

        assert report.unit_count == 3
        assert report.issue_count == 7
        issue_types = [issue.issue_type for issue in report.issues]
        assert issue_types.count("multiple_root_units") == 2
        assert issue_types.count("multiple_university_roots") == 2
        assert issue_types.count("multiple_active_university_roots") == 2
        assert "unit_missing_parent" in issue_types

    def test_consistency_report_detects_multi_node_cycle(self) -> None:
        root = _make_unit(unit_id=1, code="ROOT", unit_type=OrgUnitType.UNIVERSITY, parent_unit_id=None)
        faculty = _make_unit(unit_id=2, code="ENG", unit_type=OrgUnitType.FACULTY, parent_unit_id=4)
        department = _make_unit(unit_id=3, code="CS", unit_type=OrgUnitType.DEPARTMENT, parent_unit_id=2)
        lab = _make_unit(unit_id=4, code="AI", unit_type=OrgUnitType.DEPARTMENT, parent_unit_id=3)

        session = MagicMock()
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(org_service, "get_tree", lambda db, tid: [root, faculty, department, lab])
            report = org_service.get_org_unit_consistency_report(session, tenant_id=1)

        cycle_issues = [issue for issue in report.issues if issue.issue_type == "unit_cycle_detected"]
        assert len(cycle_issues) == 3
        assert {issue.unit_id for issue in cycle_issues} == {2, 3, 4}

    def test_consistency_report_detects_invalid_parent_type(self) -> None:
        root = _make_unit(unit_id=1, code="ROOT", unit_type=OrgUnitType.UNIVERSITY, parent_unit_id=None)
        department = _make_unit(unit_id=2, code="CS", unit_type=OrgUnitType.DEPARTMENT, parent_unit_id=1)
        faculty = _make_unit(unit_id=3, code="ENG", unit_type=OrgUnitType.FACULTY, parent_unit_id=2)

        session = MagicMock()
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(org_service, "get_tree", lambda db, tid: [root, department, faculty])
            report = org_service.get_org_unit_consistency_report(session, tenant_id=1)

        type_issues = [issue for issue in report.issues if issue.issue_type == "unit_invalid_parent_type"]
        assert len(type_issues) == 2
        assert {issue.unit_id for issue in type_issues} == {2, 3}

    def test_consistency_report_detects_active_child_with_inactive_parent(self) -> None:
        root = _make_unit(
            unit_id=1,
            code="ROOT",
            unit_type=OrgUnitType.UNIVERSITY,
            parent_unit_id=None,
            active=False,
        )
        faculty = _make_unit(
            unit_id=2,
            code="ENG",
            unit_type=OrgUnitType.FACULTY,
            parent_unit_id=1,
            active=True,
        )

        session = MagicMock()
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(org_service, "get_tree", lambda db, tid: [root, faculty])
            report = org_service.get_org_unit_consistency_report(session, tenant_id=1)

        state_issues = [
            issue for issue in report.issues if issue.issue_type == "unit_active_child_inactive_parent"
        ]
        assert len(state_issues) == 1
        assert state_issues[0].unit_id == 2

    def test_consistency_report_detects_duplicate_codes(self) -> None:
        root = _make_unit(unit_id=1, code="ROOT", unit_type=OrgUnitType.UNIVERSITY, parent_unit_id=None)
        faculty_a = _make_unit(unit_id=2, code="ENG", unit_type=OrgUnitType.FACULTY, parent_unit_id=1)
        faculty_b = _make_unit(unit_id=3, code="ENG", unit_type=OrgUnitType.FACULTY, parent_unit_id=1)

        session = MagicMock()
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(org_service, "get_tree", lambda db, tid: [root, faculty_a, faculty_b])
            report = org_service.get_org_unit_consistency_report(session, tenant_id=1)

        duplicate_issues = [issue for issue in report.issues if issue.issue_type == "unit_duplicate_code"]
        assert len(duplicate_issues) == 2
        assert {issue.unit_id for issue in duplicate_issues} == {2, 3}

    def test_consistency_report_detects_missing_root_unit(self) -> None:
        a = _make_unit(unit_id=1, code="A", unit_type=OrgUnitType.FACULTY, parent_unit_id=2)
        b = _make_unit(unit_id=2, code="B", unit_type=OrgUnitType.DEPARTMENT, parent_unit_id=1)

        session = MagicMock()
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(org_service, "get_tree", lambda db, tid: [a, b])
            report = org_service.get_org_unit_consistency_report(session, tenant_id=1)

        assert any(issue.issue_type == "missing_root_unit" for issue in report.issues)

    def test_consistency_report_detects_non_university_root_unit(self) -> None:
        school_root = _make_unit(unit_id=1, code="SCH", unit_type=OrgUnitType.SCHOOL, parent_unit_id=None)
        dept = _make_unit(unit_id=2, code="CS", unit_type=OrgUnitType.DEPARTMENT, parent_unit_id=1)

        session = MagicMock()
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(org_service, "get_tree", lambda db, tid: [school_root, dept])
            report = org_service.get_org_unit_consistency_report(session, tenant_id=1)

        assert any(issue.issue_type == "non_university_root_unit" for issue in report.issues)
        assert any(issue.issue_type == "missing_university_root" for issue in report.issues)

    def test_consistency_report_detects_multiple_university_roots(self) -> None:
        root_a = _make_unit(unit_id=1, code="ROOT-A", unit_type=OrgUnitType.UNIVERSITY, parent_unit_id=None)
        root_b = _make_unit(unit_id=2, code="ROOT-B", unit_type=OrgUnitType.UNIVERSITY, parent_unit_id=None)

        session = MagicMock()
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(org_service, "get_tree", lambda db, tid: [root_a, root_b])
            report = org_service.get_org_unit_consistency_report(session, tenant_id=1)

        university_root_issues = [
            issue for issue in report.issues if issue.issue_type == "multiple_university_roots"
        ]
        assert len(university_root_issues) == 2

    def test_consistency_report_detects_inactive_university_root(self) -> None:
        root = _make_unit(
            unit_id=1,
            code="ROOT",
            unit_type=OrgUnitType.UNIVERSITY,
            parent_unit_id=None,
            active=False,
        )
        faculty = _make_unit(unit_id=2, code="ENG", unit_type=OrgUnitType.FACULTY, parent_unit_id=1)

        session = MagicMock()
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(org_service, "get_tree", lambda db, tid: [root, faculty])
            report = org_service.get_org_unit_consistency_report(session, tenant_id=1)

        issue_types = [issue.issue_type for issue in report.issues]
        assert "inactive_university_root" in issue_types
        assert "missing_active_university_root" in issue_types

    def test_consistency_report_detects_multiple_active_university_roots(self) -> None:
        root_a = _make_unit(unit_id=1, code="ROOT-A", unit_type=OrgUnitType.UNIVERSITY, parent_unit_id=None)
        root_b = _make_unit(unit_id=2, code="ROOT-B", unit_type=OrgUnitType.UNIVERSITY, parent_unit_id=None)

        session = MagicMock()
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(org_service, "get_tree", lambda db, tid: [root_a, root_b])
            report = org_service.get_org_unit_consistency_report(session, tenant_id=1)

        active_root_issues = [
            issue for issue in report.issues if issue.issue_type == "multiple_active_university_roots"
        ]
        assert len(active_root_issues) == 2

    def test_consistency_report_detects_missing_university_root_without_roots(self) -> None:
        a = _make_unit(unit_id=1, code="A", unit_type=OrgUnitType.FACULTY, parent_unit_id=2)
        b = _make_unit(unit_id=2, code="B", unit_type=OrgUnitType.DEPARTMENT, parent_unit_id=1)

        session = MagicMock()
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(org_service, "get_tree", lambda db, tid: [a, b])
            report = org_service.get_org_unit_consistency_report(session, tenant_id=1)

        assert any(issue.issue_type == "missing_university_root" for issue in report.issues)
        assert any(issue.issue_type == "missing_active_university_root" for issue in report.issues)
