"""Phase III — Low-EV Module Minimum Brain-Readiness tests.

Covers:
  III.1 — alumni: get_alumni_brain_context service function + /brain-context endpoint
  III.2 — alumni: brain signal emitted on status → inactive
  III.3 — career_services: get_career_services_brain_context + /brain-context endpoint
  III.4 — career_services: brain signal emitted on status → archived
  III.5 — org_structure: get_org_structure_brain_context + /brain-context endpoint
  III.6 — tenant isolation: cross-tenant brain-context returns empty counts
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


from tests.conftest import ADMIN_HEADERS, client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakePub:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def publish_event(self, **kwargs: object) -> dict:
        self.events.append(dict(kwargs))
        return {}


def _make_alumni_row(
    id: int = 1,
    status: str = "active",
    engagement_type: str = "mentoring",
    student_id: int = 100,
    graduation_year: int = 2020,
) -> dict:
    return {
        "id": id,
        "student_id": student_id,
        "graduation_year": graduation_year,
        "status": status,
        "engagement_type": engagement_type,
        "employer": "ACME",
        "contact_email": "alumni@example.com",
        "notes": "n/a",
    }


def _make_career_row(
    id: int = 1,
    status: str = "open",
    opportunity_type: str = "internship",
    student_id: int = 200,
) -> dict:
    return {
        "id": id,
        "student_id": student_id,
        "title": "Software Engineer",
        "company": "TechCorp",
        "opportunity_type": opportunity_type,
        "status": status,
        "owner_id": "career-team",
        "start_date": "2024-09-01",
        "notes": "n/a",
    }


# ---------------------------------------------------------------------------
# III.1 — alumni brain context service (unit tests)
# ---------------------------------------------------------------------------


def test_alumni_brain_context_empty_tenant() -> None:
    """get_alumni_brain_context returns expected schema with no records."""
    from app.modules.alumni.service import get_alumni_brain_context

    with patch(
        "app.modules.alumni.service.list_entities_for_tenant",
        return_value=[],
    ):
        ctx = get_alumni_brain_context(tenant_id=1)

    assert ctx["module"] == "alumni"
    assert ctx["tenant_id"] == 1
    assert ctx["total_records"] == 0
    assert ctx["inactive_count"] == 0
    assert ctx["risk_level"] == "low"
    assert isinstance(ctx["by_status"], dict)


def test_alumni_brain_context_risk_level_high() -> None:
    """get_alumni_brain_context returns high risk when >40% are inactive."""
    from app.modules.alumni.service import get_alumni_brain_context

    rows = [_make_alumni_row(id=i, status=("inactive" if i <= 5 else "active")) for i in range(1, 11)]

    with patch(
        "app.modules.alumni.service.list_entities_for_tenant",
        return_value=rows,
    ):
        ctx = get_alumni_brain_context(tenant_id=1)

    assert ctx["total_records"] == 10
    assert ctx["inactive_count"] == 5
    assert ctx["risk_level"] == "high"


def test_alumni_brain_context_risk_level_medium() -> None:
    """get_alumni_brain_context returns medium risk when there is ≥1 inactive record (but <40%)."""
    from app.modules.alumni.service import get_alumni_brain_context

    # 1 inactive out of 10 = 10% → not high → medium because inactive > 0
    rows = [_make_alumni_row(id=i, status=("inactive" if i == 1 else "active")) for i in range(1, 11)]

    with patch(
        "app.modules.alumni.service.list_entities_for_tenant",
        return_value=rows,
    ):
        ctx = get_alumni_brain_context(tenant_id=1)

    assert ctx["risk_level"] == "medium"


def test_alumni_brain_context_by_status_counts() -> None:
    """get_alumni_brain_context correctly populates by_status dict."""
    from app.modules.alumni.service import get_alumni_brain_context

    rows = [
        _make_alumni_row(id=1, status="active"),
        _make_alumni_row(id=2, status="engaged"),
        _make_alumni_row(id=3, status="donor"),
        _make_alumni_row(id=4, status="inactive"),
    ]

    with patch(
        "app.modules.alumni.service.list_entities_for_tenant",
        return_value=rows,
    ):
        ctx = get_alumni_brain_context(tenant_id=1)

    assert ctx["by_status"].get("active") == 1
    assert ctx["by_status"].get("engaged") == 1
    assert ctx["by_status"].get("donor") == 1
    assert ctx["by_status"].get("inactive") == 1


# ---------------------------------------------------------------------------
# III.2 — alumni brain signal on status → inactive
# ---------------------------------------------------------------------------


def test_alumni_signal_emitted_on_inactive_transition() -> None:
    """update_alumni_status emits alumni.engagement.risk_detected when → inactive."""
    from app.modules.alumni.schemas import AlumniRecordStatusUpdateSchema
    from app.modules.alumni.service import update_alumni_status

    existing = _make_alumni_row(id=1, status="active", student_id=101)

    fake_pub = _FakePub()

    with (
        patch("app.modules.alumni.service.list_entities_for_tenant", return_value=[existing]),
        patch("app.modules.alumni.service.update_entity_for_tenant", return_value={**existing, "status": "inactive"}),
        patch("app.modules.alumni.service._emit_audit"),
        patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub),
    ):
        req = AlumniRecordStatusUpdateSchema(status="inactive")
        update_alumni_status(tenant_id=1, record_id=1, request=req, actor="test-actor")

    assert len(fake_pub.events) == 1
    ev = fake_pub.events[0]
    assert ev["event_type"] == "alumni.engagement.risk_detected"
    assert ev["tenant_id"] == 1


def test_alumni_signal_not_emitted_on_non_inactive_transition() -> None:
    """update_alumni_status does NOT emit a signal when transitioning to engaged."""
    from app.modules.alumni.schemas import AlumniRecordStatusUpdateSchema
    from app.modules.alumni.service import update_alumni_status

    existing = _make_alumni_row(id=2, status="active", student_id=102)

    fake_pub = _FakePub()

    with (
        patch("app.modules.alumni.service.list_entities_for_tenant", return_value=[existing]),
        patch("app.modules.alumni.service.update_entity_for_tenant", return_value={**existing, "status": "engaged"}),
        patch("app.modules.alumni.service._emit_audit"),
        patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub),
    ):
        req = AlumniRecordStatusUpdateSchema(status="engaged")
        update_alumni_status(tenant_id=1, record_id=2, request=req, actor="test-actor")

    assert len(fake_pub.events) == 0


# ---------------------------------------------------------------------------
# III.3 — alumni /brain-context endpoint
# ---------------------------------------------------------------------------


def test_alumni_brain_context_endpoint_returns_200() -> None:
    """GET /api/admin/alumni/brain-context returns 200 with expected keys."""
    resp = client.get("/api/admin/alumni/brain-context", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["module"] == "alumni"
    assert "total_records" in data
    assert "by_status" in data
    assert "risk_level" in data


def test_alumni_brain_context_endpoint_requires_auth() -> None:
    """GET /api/admin/alumni/brain-context without auth returns 401/403."""
    resp = client.get("/api/admin/alumni/brain-context")
    assert resp.status_code in {401, 403}


# ---------------------------------------------------------------------------
# III.4 — career_services brain context service (unit tests)
# ---------------------------------------------------------------------------


def test_career_services_brain_context_empty_tenant() -> None:
    """get_career_services_brain_context returns expected schema with no opportunities."""
    from app.modules.career_services.service import get_career_services_brain_context

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        return_value=[],
    ):
        ctx = get_career_services_brain_context(tenant_id=1)

    assert ctx["module"] == "career_services"
    assert ctx["tenant_id"] == 1
    assert ctx["total_opportunities"] == 0
    assert ctx["archived_count"] == 0
    assert ctx["risk_level"] == "low"
    assert isinstance(ctx["by_status"], dict)


def test_career_services_brain_context_risk_level_high() -> None:
    """get_career_services_brain_context returns high risk when >50% are archived."""
    from app.modules.career_services.service import get_career_services_brain_context

    rows = [_make_career_row(id=i, status=("archived" if i <= 6 else "open")) for i in range(1, 11)]

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        return_value=rows,
    ):
        ctx = get_career_services_brain_context(tenant_id=1)

    assert ctx["total_opportunities"] == 10
    assert ctx["archived_count"] == 6
    assert ctx["risk_level"] == "high"


def test_career_services_brain_context_risk_level_medium() -> None:
    """get_career_services_brain_context returns medium when some archived (<= 50%)."""
    from app.modules.career_services.service import get_career_services_brain_context

    rows = [_make_career_row(id=i, status=("archived" if i == 1 else "open")) for i in range(1, 5)]

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        return_value=rows,
    ):
        ctx = get_career_services_brain_context(tenant_id=1)

    assert ctx["risk_level"] == "medium"


def test_career_services_brain_context_by_status_counts() -> None:
    """get_career_services_brain_context correctly populates by_status dict."""
    from app.modules.career_services.service import get_career_services_brain_context

    rows = [
        _make_career_row(id=1, status="open"),
        _make_career_row(id=2, status="in_review"),
        _make_career_row(id=3, status="closed"),
        _make_career_row(id=4, status="archived"),
    ]

    with patch(
        "app.modules.career_services.service.list_entities_for_tenant",
        return_value=rows,
    ):
        ctx = get_career_services_brain_context(tenant_id=1)

    assert ctx["by_status"].get("open") == 1
    assert ctx["by_status"].get("in_review") == 1
    assert ctx["by_status"].get("closed") == 1
    assert ctx["by_status"].get("archived") == 1


# ---------------------------------------------------------------------------
# III.5 — career_services brain signal on status → archived
# ---------------------------------------------------------------------------


def test_career_signal_emitted_on_archived_transition() -> None:
    """update_career_opportunity_status emits career_services.opportunity.at_risk when → archived."""
    from app.modules.career_services.schemas import CareerOpportunityStatusUpdateSchema
    from app.modules.career_services.service import update_career_opportunity_status

    existing = _make_career_row(id=1, status="closed", student_id=201)

    fake_pub = _FakePub()

    with (
        patch("app.modules.career_services.service.list_entities_for_tenant", return_value=[existing]),
        patch("app.modules.career_services.service.update_entity_for_tenant", return_value={**existing, "status": "archived"}),
        patch("app.modules.career_services.service._emit_audit"),
        patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub),
    ):
        req = CareerOpportunityStatusUpdateSchema(status="archived")
        update_career_opportunity_status(tenant_id=1, opportunity_id=1, request=req, actor="test-actor")

    assert len(fake_pub.events) == 1
    ev = fake_pub.events[0]
    assert ev["event_type"] == "career_services.opportunity.at_risk"
    assert ev["tenant_id"] == 1


def test_career_signal_not_emitted_on_non_archived_transition() -> None:
    """update_career_opportunity_status does NOT emit a signal when transitioning to in_review."""
    from app.modules.career_services.schemas import CareerOpportunityStatusUpdateSchema
    from app.modules.career_services.service import update_career_opportunity_status

    existing = _make_career_row(id=2, status="open", student_id=202)

    fake_pub = _FakePub()

    with (
        patch("app.modules.career_services.service.list_entities_for_tenant", return_value=[existing]),
        patch("app.modules.career_services.service.update_entity_for_tenant", return_value={**existing, "status": "in_review"}),
        patch("app.modules.career_services.service._emit_audit"),
        patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub),
    ):
        req = CareerOpportunityStatusUpdateSchema(status="in_review")
        update_career_opportunity_status(tenant_id=1, opportunity_id=2, request=req, actor="test-actor")

    assert len(fake_pub.events) == 0


# ---------------------------------------------------------------------------
# III.6 — career_services /brain-context endpoint
# ---------------------------------------------------------------------------


def test_career_services_brain_context_endpoint_returns_200() -> None:
    """GET /api/admin/career-services/brain-context returns 200 with expected keys."""
    resp = client.get("/api/admin/career-services/brain-context", headers=ADMIN_HEADERS)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["module"] == "career_services"
    assert "total_opportunities" in data
    assert "by_status" in data
    assert "risk_level" in data


def test_career_services_brain_context_endpoint_requires_auth() -> None:
    """GET /api/admin/career-services/brain-context without auth returns 401/403."""
    resp = client.get("/api/admin/career-services/brain-context")
    assert resp.status_code in {401, 403}


# ---------------------------------------------------------------------------
# III.7 — org_structure brain context service (unit tests with mock DB)
# ---------------------------------------------------------------------------


def _make_org_unit(
    id: int = 1,
    unit_type: str = "DEPARTMENT",
    active: bool = True,
    parent_unit_id: int | None = None,
    code: str = "DEPT-1",
) -> MagicMock:
    from app.modules.org_structure.models import OrgUnitType

    unit = MagicMock()
    unit.id = id
    unit.active = active
    unit.parent_unit_id = parent_unit_id
    unit.code = code
    unit.name = f"Unit {id}"
    try:
        unit.unit_type = OrgUnitType(unit_type)
    except ValueError:
        unit.unit_type = MagicMock()
        unit.unit_type.value = unit_type
    return unit


def test_org_structure_brain_context_empty_db() -> None:
    """get_org_structure_brain_context returns expected schema with no units."""
    from app.modules.org_structure.service import get_org_structure_brain_context

    mock_db = MagicMock()

    with patch("app.modules.org_structure.service.list_org_units", return_value=[]):
        with patch("app.modules.org_structure.service.get_org_unit_consistency_report") as mock_report:
            from app.modules.org_structure.schemas import OrgUnitConsistencyReportSchema

            mock_report.return_value = OrgUnitConsistencyReportSchema(
                unit_count=0, issue_count=0, issues=[]
            )
            ctx = get_org_structure_brain_context(mock_db, tenant_id=1)

    assert ctx["module"] == "org_structure"
    assert ctx["tenant_id"] == 1
    assert ctx["total_units"] == 0
    assert ctx["consistency_issues"] == 0
    assert ctx["risk_level"] == "low"
    assert isinstance(ctx["by_type"], dict)


def test_org_structure_brain_context_with_units() -> None:
    """get_org_structure_brain_context correctly counts units and active/inactive."""
    from app.modules.org_structure.schemas import OrgUnitConsistencyReportSchema
    from app.modules.org_structure.service import get_org_structure_brain_context

    mock_db = MagicMock()
    units = [
        _make_org_unit(id=1, unit_type="university", active=True, parent_unit_id=None, code="UNI"),
        _make_org_unit(id=2, unit_type="department", active=True, parent_unit_id=1, code="DEPT-1"),
        _make_org_unit(id=3, unit_type="department", active=False, parent_unit_id=1, code="DEPT-2"),
    ]
    # Patch unit_type.value for dict lookup
    for u in units:
        u.unit_type = MagicMock()
        u.unit_type.value = ["university", "department", "department"][u.id - 1]

    with patch("app.modules.org_structure.service.list_org_units", return_value=units):
        with patch("app.modules.org_structure.service.get_org_unit_consistency_report") as mock_report:
            mock_report.return_value = OrgUnitConsistencyReportSchema(
                unit_count=3, issue_count=0, issues=[]
            )
            ctx = get_org_structure_brain_context(mock_db, tenant_id=1)

    assert ctx["total_units"] == 3
    assert ctx["active_units"] == 2
    assert ctx["consistency_issues"] == 0
    assert ctx["risk_level"] == "low"


def test_org_structure_brain_context_risk_level_high() -> None:
    """get_org_structure_brain_context returns high risk when ≥3 consistency issues."""
    from app.modules.org_structure.schemas import OrgUnitConsistencyReportSchema
    from app.modules.org_structure.service import get_org_structure_brain_context

    mock_db = MagicMock()

    with patch("app.modules.org_structure.service.list_org_units", return_value=[]):
        with patch("app.modules.org_structure.service.get_org_unit_consistency_report") as mock_report:
            mock_report.return_value = OrgUnitConsistencyReportSchema(
                unit_count=0, issue_count=5, issues=[{"issue_type": "x"}] * 5
            )
            ctx = get_org_structure_brain_context(mock_db, tenant_id=1)

    assert ctx["consistency_issues"] == 5
    assert ctx["risk_level"] == "high"


# ---------------------------------------------------------------------------
# III.8 — org_structure /brain-context endpoint
# ---------------------------------------------------------------------------


def test_org_structure_brain_context_endpoint_returns_200() -> None:
    """GET /api/admin/org-units/brain-context returns 200 with expected keys (DB mocked)."""
    from app.main import app
    from app.modules.org_structure.dependencies import get_org_structure_db
    from app.modules.org_structure.schemas import OrgUnitConsistencyReportSchema

    mock_db = MagicMock()

    def _override_db():
        yield mock_db

    app.dependency_overrides[get_org_structure_db] = _override_db
    try:
        with (
            patch("app.modules.org_structure.service.list_org_units", return_value=[]),
            patch("app.modules.org_structure.service.get_org_unit_consistency_report") as mock_report,
        ):
            mock_report.return_value = OrgUnitConsistencyReportSchema(
                unit_count=0, issue_count=0, issues=[]
            )
            resp = client.get("/api/admin/org-units/brain-context", headers=ADMIN_HEADERS)
    finally:
        app.dependency_overrides.pop(get_org_structure_db, None)

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["module"] == "org_structure"
    assert "total_units" in data
    assert "consistency_issues" in data
    assert "risk_level" in data


def test_org_structure_brain_context_endpoint_requires_auth() -> None:
    """GET /api/admin/org-units/brain-context without auth returns 401/403."""
    resp = client.get("/api/admin/org-units/brain-context")
    assert resp.status_code in {401, 403}


# ---------------------------------------------------------------------------
# III.9 — tenant isolation
# ---------------------------------------------------------------------------


def test_alumni_brain_context_tenant_isolation() -> None:
    """get_alumni_brain_context for different tenant returns isolated counts."""
    from app.modules.alumni.service import get_alumni_brain_context

    tenant_1_rows = [_make_alumni_row(id=1, status="inactive")]
    tenant_2_rows: list[dict] = []

    def fake_list(entity_type: str, tenant_id: int) -> list:
        if tenant_id == 1:
            return tenant_1_rows
        return tenant_2_rows

    with patch("app.modules.alumni.service.list_entities_for_tenant", side_effect=fake_list):
        ctx1 = get_alumni_brain_context(tenant_id=1)
        ctx2 = get_alumni_brain_context(tenant_id=2)

    assert ctx1["total_records"] == 1
    assert ctx2["total_records"] == 0


def test_career_brain_context_tenant_isolation() -> None:
    """get_career_services_brain_context for different tenant returns isolated counts."""
    from app.modules.career_services.service import get_career_services_brain_context

    tenant_1_rows = [_make_career_row(id=1, status="archived")]
    tenant_2_rows: list[dict] = []

    def fake_list(entity_type: str, tenant_id: int) -> list:
        if tenant_id == 1:
            return tenant_1_rows
        return tenant_2_rows

    with patch("app.modules.career_services.service.list_entities_for_tenant", side_effect=fake_list):
        ctx1 = get_career_services_brain_context(tenant_id=1)
        ctx2 = get_career_services_brain_context(tenant_id=2)

    assert ctx1["total_opportunities"] == 1
    assert ctx2["total_opportunities"] == 0
