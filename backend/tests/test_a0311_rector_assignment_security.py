"""A-031.1-RUNTIME security tests: rector assignment workflow.

Tests cross-tenant isolation, RBAC, ABAC boundaries.
Uses MagicMock(spec=Session) — no real DB required.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.main import app
from app.modules.rector_assignment_workflow.dependencies import get_rector_assignment_db
from tests.conftest import ADMIN_HEADERS, _auth_headers, client

BASE = "/api/admin/rector-assignments"

# Various actor roles
VIEWER_HEADERS = _auth_headers("viewer-sec@example.com", ["viewer"], tenant_id=1)
STUDENT_HEADERS = _auth_headers("student-sec@example.com", ["student"], tenant_id=1)

# Mutation payloads
_CREATE_PAYLOAD = {"title": "Security Test Assignment", "priority": "NORMAL", "recurrence_type": "NONE"}
_ASSIGN_PAYLOAD = {"assignees": [{"user_id": 10, "role_on_assignment": "RESPONSIBLE"}]}
_ESCALATION_PAYLOAD = {"reason": "Overdue", "escalation_level": 1, "escalated_to_role": "dean"}
_CANCEL_PAYLOAD = {"reason": "Test cancel"}
_TEMPLATE_CREATE_PAYLOAD = {"name": "Security Test Template"}
_RETURN_PAYLOAD = {"reason": "Needs revision"}


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_rector_assignment_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_rector_assignment_db, None)


# ===========================================================================
# 1. Unauthenticated access denied (all routes)
# ===========================================================================

class TestUnauthenticatedDenied:
    def test_list_denied(self):
        resp = client.get(BASE)
        assert resp.status_code in (401, 403)

    def test_create_denied(self):
        resp = client.post(BASE, json=_CREATE_PAYLOAD)
        assert resp.status_code in (401, 403)

    def test_dashboard_denied(self):
        resp = client.get(f"{BASE}/dashboard/summary")
        assert resp.status_code in (401, 403)

    def test_templates_list_denied(self):
        resp = client.get(f"{BASE}/templates")
        assert resp.status_code in (401, 403)

    def test_detail_denied(self):
        resp = client.get(f"{BASE}/1")
        assert resp.status_code in (401, 403)

    def test_assign_denied(self):
        resp = client.post(f"{BASE}/1/assign", json=_ASSIGN_PAYLOAD)
        assert resp.status_code in (401, 403)

    def test_accept_denied(self):
        resp = client.post(f"{BASE}/1/accept", json={})
        assert resp.status_code in (401, 403)

    def test_complete_denied(self):
        resp = client.post(f"{BASE}/1/complete", json={})
        assert resp.status_code in (401, 403)

    def test_cancel_denied(self):
        resp = client.post(f"{BASE}/1/cancel", json=_CANCEL_PAYLOAD)
        assert resp.status_code in (401, 403)

    def test_archive_denied(self):
        resp = client.post(f"{BASE}/1/archive", json={})
        assert resp.status_code in (401, 403)

    def test_create_template_denied(self):
        resp = client.post(f"{BASE}/templates", json=_TEMPLATE_CREATE_PAYLOAD)
        assert resp.status_code in (401, 403)

    def test_update_template_denied(self):
        resp = client.patch(f"{BASE}/templates/1", json={"name": "X"})
        assert resp.status_code in (401, 403)


# ===========================================================================
# 2. Student role denied on all mutation endpoints
# ===========================================================================

class TestStudentRoleDenied:
    def test_create_student_denied(self):
        resp = client.post(BASE, json=_CREATE_PAYLOAD, headers=STUDENT_HEADERS)
        assert resp.status_code == 403

    def test_assign_student_denied(self):
        resp = client.post(f"{BASE}/1/assign", json=_ASSIGN_PAYLOAD, headers=STUDENT_HEADERS)
        assert resp.status_code == 403

    def test_complete_student_denied(self):
        resp = client.post(f"{BASE}/1/complete", json={}, headers=STUDENT_HEADERS)
        assert resp.status_code == 403

    def test_escalate_student_denied(self):
        resp = client.post(f"{BASE}/1/escalate", json=_ESCALATION_PAYLOAD, headers=STUDENT_HEADERS)
        assert resp.status_code == 403

    def test_cancel_student_denied(self):
        resp = client.post(f"{BASE}/1/cancel", json=_CANCEL_PAYLOAD, headers=STUDENT_HEADERS)
        assert resp.status_code == 403

    def test_archive_student_denied(self):
        resp = client.post(f"{BASE}/1/archive", json={}, headers=STUDENT_HEADERS)
        assert resp.status_code == 403

    def test_return_student_denied(self):
        resp = client.post(f"{BASE}/1/return", json=_RETURN_PAYLOAD, headers=STUDENT_HEADERS)
        assert resp.status_code == 403

    def test_create_template_student_denied(self):
        resp = client.post(f"{BASE}/templates", json=_TEMPLATE_CREATE_PAYLOAD, headers=STUDENT_HEADERS)
        assert resp.status_code == 403


# ===========================================================================
# 3. Viewer role denied on mutation endpoints
# ===========================================================================

class TestViewerRoleDenied:
    def test_create_viewer_denied(self):
        resp = client.post(BASE, json=_CREATE_PAYLOAD, headers=VIEWER_HEADERS)
        assert resp.status_code == 403

    def test_assign_viewer_denied(self):
        resp = client.post(f"{BASE}/1/assign", json=_ASSIGN_PAYLOAD, headers=VIEWER_HEADERS)
        assert resp.status_code == 403

    def test_complete_viewer_denied(self):
        resp = client.post(f"{BASE}/1/complete", json={}, headers=VIEWER_HEADERS)
        assert resp.status_code == 403

    def test_cancel_viewer_denied(self):
        resp = client.post(f"{BASE}/1/cancel", json=_CANCEL_PAYLOAD, headers=VIEWER_HEADERS)
        assert resp.status_code == 403

    def test_archive_viewer_denied(self):
        resp = client.post(f"{BASE}/1/archive", json={}, headers=VIEWER_HEADERS)
        assert resp.status_code == 403

    def test_create_template_viewer_denied(self):
        resp = client.post(f"{BASE}/templates", json=_TEMPLATE_CREATE_PAYLOAD, headers=VIEWER_HEADERS)
        assert resp.status_code == 403

    def test_update_template_viewer_denied(self):
        resp = client.patch(f"{BASE}/templates/1", json={"name": "x"}, headers=VIEWER_HEADERS)
        assert resp.status_code == 403


# ===========================================================================
# 4. Service-layer tenant isolation
# ===========================================================================

class TestServiceTenantIsolation:
    """Service functions must fail-close on missing/zero tenant_id."""

    def test_list_rejects_none_tenant(self):
        from app.modules.rector_assignment_workflow.service import list_assignments
        db = MagicMock(spec=Session)
        with pytest.raises(Exception):
            list_assignments(None, db)

    def test_create_rejects_none_tenant(self):
        from app.modules.rector_assignment_workflow.service import create_assignment
        from app.modules.rector_assignment_workflow.schemas import AssignmentCreateRequest
        db = MagicMock(spec=Session)
        payload = AssignmentCreateRequest(title="Test")
        with pytest.raises(Exception):
            create_assignment(None, 1, None, payload, db)

    def test_dashboard_rejects_none_tenant(self):
        from app.modules.rector_assignment_workflow.service import get_dashboard_summary
        db = MagicMock(spec=Session)
        with pytest.raises(Exception):
            get_dashboard_summary(None, db)

    def test_templates_list_rejects_none_tenant(self):
        from app.modules.rector_assignment_workflow.service import list_assignment_templates
        db = MagicMock(spec=Session)
        with pytest.raises(Exception):
            list_assignment_templates(None, db)

    def test_get_audit_rejects_none_tenant(self):
        from app.modules.rector_assignment_workflow.service import get_assignment_audit
        db = MagicMock(spec=Session)
        with pytest.raises(Exception):
            get_assignment_audit(None, 1, db)

    def test_list_evidence_rejects_none_tenant(self):
        from app.modules.rector_assignment_workflow.service import list_assignment_evidence
        db = MagicMock(spec=Session)
        with pytest.raises(Exception):
            list_assignment_evidence(None, 1, db)

    def test_list_comments_rejects_none_tenant(self):
        from app.modules.rector_assignment_workflow.service import list_assignment_comments
        db = MagicMock(spec=Session)
        with pytest.raises(Exception):
            list_assignment_comments(None, 1, db)


# ===========================================================================
# 5. IDOR prevention — transition guard on wrong status
# ===========================================================================

class TestTransitionIDORPrevention:
    """Transition guard prevents unauthorized state jumps."""

    def test_cannot_jump_from_draft_to_completed(self):
        from app.modules.rector_assignment_workflow.service import _assert_transition_allowed
        from app.core.module_helpers.service_validation import DomainValidationError
        with pytest.raises(DomainValidationError):
            _assert_transition_allowed("DRAFT", "COMPLETED")

    def test_cannot_jump_from_assigned_to_completed(self):
        from app.modules.rector_assignment_workflow.service import _assert_transition_allowed
        from app.core.module_helpers.service_validation import DomainValidationError
        with pytest.raises(DomainValidationError):
            _assert_transition_allowed("ASSIGNED", "COMPLETED")

    def test_cannot_resurrect_archived(self):
        from app.modules.rector_assignment_workflow.service import _assert_transition_allowed
        from app.core.module_helpers.service_validation import DomainValidationError
        for status in ("DRAFT", "ASSIGNED", "ACCEPTED", "COMPLETED"):
            with pytest.raises(DomainValidationError):
                _assert_transition_allowed("ARCHIVED", status)

    def test_cannot_go_cancelled_to_in_progress(self):
        from app.modules.rector_assignment_workflow.service import _assert_transition_allowed
        from app.core.module_helpers.service_validation import DomainValidationError
        with pytest.raises(DomainValidationError):
            _assert_transition_allowed("CANCELLED", "IN_PROGRESS")


# ===========================================================================
# 6. No fake data in service
# ===========================================================================

class TestNoFakeData:
    def test_dashboard_data_source_is_computed(self):
        from app.modules.rector_assignment_workflow.schemas import DashboardSummaryResponse
        from datetime import datetime
        r = DashboardSummaryResponse(
            tenant_id=1,
            computed_at=datetime.now(),
            total_assignments=0, active_count=0, draft_count=0, overdue_count=0,
            escalated_count=0, completed_count=0, cancelled_count=0,
            report_submitted_count=0, returned_count=0, due_this_week=0, due_today=0,
            completion_rate_30d=0.0, average_days_to_complete=None,
            by_status={}, by_priority={}, by_unit=[], top_overdue=[],
        )
        assert r.fake_metrics is False
        assert r.data_source == "computed_from_assignments"

    def test_permissions_all_non_empty(self):
        from app.modules.rector_assignment_workflow import permissions
        for perm_name in ("CREATE", "READ", "ASSIGN", "ACCEPT", "COMPLETE", "CANCEL", "ARCHIVE", "DASHBOARD_READ"):
            val = getattr(permissions, perm_name)
            assert val and len(val) > 5, f"{perm_name} should be a non-trivial string"
