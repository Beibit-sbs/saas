"""
ERP-QA-84 – Playbook router endpoint tests.

Covers 11 endpoints under /api/admin/interventions/playbooks:
  POST    /                                         (interventions:manage_playbooks)
  GET     /                                         (interventions:view)
  GET     /{id}                                     (interventions:view)
  PATCH   /{id}                                     (interventions:manage_playbooks)
  DELETE  /{id}                                     (interventions:manage_playbooks)
  POST    /executions                               (interventions:execute_playbook)
  GET     /executions                               (interventions:view)
  GET     /executions/{id}                          (interventions:view)
  POST    /executions/{id}/abandon                  (interventions:execute_playbook)
  POST    /executions/{id}/steps/{sid}/complete      (interventions:execute_playbook)
  POST    /executions/{id}/steps/{sid}/skip          (interventions:execute_playbook)
"""

from __future__ import annotations

from datetime import datetime, UTC
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from tests.conftest import _auth_headers, client
from app.main import app
from app.modules.interventions.dependencies import get_interventions_db
from app.modules.interventions import playbook_router
from app.modules.rbac import service as rbac_service
from app.modules.auth.token_service import create_access_token

BASE = "/api/admin/interventions/playbooks"


def _make_headers_with_permissions(user_id: str, roles: list[str], tenant_id: int, extra_perms: set[str]) -> dict[str, str]:
    """Create auth headers with extra permissions baked into the JWT."""
    base_perms = set(rbac_service.resolve_permissions_for_tenant(roles, tenant_id=tenant_id))
    all_perms = sorted(base_perms | extra_perms)
    token = create_access_token(user_id=user_id, roles=roles, auth_source="test", tenant_id=tenant_id, permissions=all_perms)
    return {"Authorization": f"Bearer {token}"}


_EXTRA_PERMS = {"interventions:view", "interventions:manage_playbooks", "interventions:execute_playbook"}
ADMIN_HEADERS = _make_headers_with_permissions("owner@example.com", ["admin"], 1, _EXTRA_PERMS)
VIEWER_HEADERS = _auth_headers("viewer@example.com", ["viewer"], tenant_id=1)


@pytest.fixture(autouse=True)
def _enable_playbook_flag(monkeypatch: pytest.MonkeyPatch):
    """Enable the playbook feature flag for all tests in this module."""
    monkeypatch.setattr(playbook_router, "is_flag_enabled", lambda *args, **kwargs: True)


@pytest.fixture(autouse=True)
def _override_interventions_db():
    session = MagicMock(spec=Session)
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.refresh = MagicMock()
    app.dependency_overrides[get_interventions_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_interventions_db, None)


# ---------------------------------------------------------------------------
# helpers — mock return objects
# ---------------------------------------------------------------------------

_now = datetime(2026, 4, 20, 10, 0, 0, tzinfo=UTC)


def _mock_step(step_id=1):
    s = MagicMock()
    s.id = step_id
    s.playbook_id = 1
    s.step_order = 0
    s.title = "Step A"
    s.action_type = "notification_sent"
    s.rationale = "Notify student"
    s.is_mandatory = True
    s.due_days_offset = 3
    s.assignee_role = "advisor"
    s.metadata_json = {}
    return s


def _mock_playbook(pb_id=1, enabled=True):
    p = MagicMock()
    p.id = pb_id
    p.tenant_id = 1
    p.name = "Risk Playbook"
    p.description = "Standard risk response"
    p.trigger_threshold_id = None
    p.enabled = enabled
    p.version = 1
    p.metadata_json = {}
    p.created_by = "owner@example.com"
    p.updated_by = "owner@example.com"
    p.created_at = _now
    p.updated_at = _now
    p.steps = [_mock_step()]
    return p


def _mock_step_execution(se_id=1):
    se = MagicMock()
    se.id = se_id
    se.execution_id = 1
    se.step_id = 1
    se.status = "pending"
    se.performed_by = None
    se.performed_at = None
    se.outcome_note = None
    se.metadata_json = {}
    return se


def _mock_execution(exec_id=1):
    e = MagicMock()
    e.id = exec_id
    e.tenant_id = 1
    e.playbook_id = 1
    e.case_id = None
    e.student_profile_id = None
    e.triggered_by = "manual"
    e.status = "in_progress"
    e.started_at = _now
    e.completed_at = None
    e.abandoned_at = None
    e.abandon_reason = None
    e.outcome_delta_score = None
    e.metadata_json = {}
    e.created_by = "owner@example.com"
    e.created_at = _now
    e.updated_at = _now
    e.step_executions = [_mock_step_execution()]
    return e


# flag always enabled unless a test overrides
_FLAG_PATCH = "app.modules.interventions.playbook_router.is_flag_enabled"
SVC = "app.modules.interventions.playbook_router.PlaybookService"


def _flag_enabled(*a, **kw):
    return True


def _flag_disabled(*a, **kw):
    return False


# ---------------------------------------------------------------------------
# POST / – create playbook
# ---------------------------------------------------------------------------


class TestCreatePlaybook:
    _payload = {
        "name": "Risk Playbook",
        "description": "Standard risk response",
        "enabled": True,
        "steps": [
            {
                "step_order": 0,
                "title": "Notify student",
                "action_type": "notification_sent",
            }
        ],
    }

    def test_create_happy(self):
        svc = MagicMock()
        svc.create_playbook.return_value = _mock_playbook()
        with patch(_FLAG_PATCH, side_effect=_flag_enabled), \
             patch(SVC, return_value=svc):
            r = client.post(f"{BASE}", json=self._payload, headers=ADMIN_HEADERS)
        assert r.status_code == 201

    def test_create_feature_disabled(self):
        with patch(_FLAG_PATCH, side_effect=_flag_disabled):
            r = client.post(f"{BASE}", json=self._payload, headers=ADMIN_HEADERS)
        assert r.status_code == 403

    def test_create_viewer_forbidden(self):
        r = client.post(f"{BASE}", json=self._payload, headers=VIEWER_HEADERS)
        assert r.status_code == 403

    def test_create_no_auth(self):
        r = client.post(f"{BASE}", json=self._payload)
        assert r.status_code in (401, 403)

    def test_create_invalid_empty_name(self):
        payload = {**self._payload, "name": ""}
        with patch(_FLAG_PATCH, side_effect=_flag_enabled):
            r = client.post(f"{BASE}", json=payload, headers=ADMIN_HEADERS)
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# GET / – list playbooks
# ---------------------------------------------------------------------------


class TestListPlaybooks:
    def test_list_happy(self):
        svc = MagicMock()
        svc.list_playbooks.return_value = ([_mock_playbook()], 1)
        with patch(SVC, return_value=svc):
            r = client.get(f"{BASE}", headers=ADMIN_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1

    def test_list_with_filters(self):
        svc = MagicMock()
        svc.list_playbooks.return_value = ([], 0)
        with patch(SVC, return_value=svc):
            r = client.get(f"{BASE}?enabled_only=true&offset=0&limit=10", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_list_viewer_forbidden(self):
        r = client.get(f"{BASE}", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /{id} – get playbook
# ---------------------------------------------------------------------------


class TestGetPlaybook:
    def test_get_happy(self):
        svc = MagicMock()
        svc.get_playbook.return_value = _mock_playbook()
        with patch(SVC, return_value=svc):
            r = client.get(f"{BASE}/1", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_get_not_found(self):
        from app.core.module_helpers.service_validation import TenantResourceNotFoundError
        svc = MagicMock()
        svc.get_playbook.side_effect = TenantResourceNotFoundError("not found")
        with patch(SVC, return_value=svc):
            r = client.get(f"{BASE}/999", headers=ADMIN_HEADERS)
        assert r.status_code == 404

    def test_get_viewer_forbidden(self):
        r = client.get(f"{BASE}/1", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /{id} – update playbook
# ---------------------------------------------------------------------------


class TestUpdatePlaybook:
    _payload = {"expected_version": 1, "name": "Updated Playbook"}

    def test_update_happy(self):
        svc = MagicMock()
        svc.update_playbook.return_value = _mock_playbook()
        with patch(_FLAG_PATCH, side_effect=_flag_enabled), \
             patch(SVC, return_value=svc):
            r = client.patch(f"{BASE}/1", json=self._payload, headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_update_feature_disabled(self):
        with patch(_FLAG_PATCH, side_effect=_flag_disabled):
            r = client.patch(f"{BASE}/1", json=self._payload, headers=ADMIN_HEADERS)
        assert r.status_code == 403

    def test_update_viewer_forbidden(self):
        r = client.patch(f"{BASE}/1", json=self._payload, headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /{id} – delete playbook
# ---------------------------------------------------------------------------


class TestDeletePlaybook:
    def test_delete_happy(self):
        svc = MagicMock()
        svc.delete_playbook.return_value = None
        with patch(_FLAG_PATCH, side_effect=_flag_enabled), \
             patch(SVC, return_value=svc):
            r = client.delete(f"{BASE}/1", headers=ADMIN_HEADERS)
        assert r.status_code == 204

    def test_delete_feature_disabled(self):
        with patch(_FLAG_PATCH, side_effect=_flag_disabled):
            r = client.delete(f"{BASE}/1", headers=ADMIN_HEADERS)
        assert r.status_code == 403

    def test_delete_viewer_forbidden(self):
        r = client.delete(f"{BASE}/1", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /executions – start execution
# ---------------------------------------------------------------------------


class TestStartExecution:
    _payload = {"playbook_id": 1, "triggered_by": "manual"}

    def test_start_happy(self):
        svc = MagicMock()
        svc.start_execution.return_value = _mock_execution()
        with patch(_FLAG_PATCH, side_effect=_flag_enabled), \
             patch(SVC, return_value=svc):
            r = client.post(f"{BASE}/executions", json=self._payload, headers=ADMIN_HEADERS)
        assert r.status_code == 201

    def test_start_feature_disabled(self):
        with patch(_FLAG_PATCH, side_effect=_flag_disabled):
            r = client.post(f"{BASE}/executions", json=self._payload, headers=ADMIN_HEADERS)
        assert r.status_code == 403

    def test_start_viewer_forbidden(self):
        r = client.post(f"{BASE}/executions", json=self._payload, headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /executions – list executions
# ---------------------------------------------------------------------------


class TestListExecutions:
    def test_list_happy(self):
        svc = MagicMock()
        svc.list_executions.return_value = ([_mock_execution()], 1)
        with patch(SVC, return_value=svc):
            r = client.get(f"{BASE}/executions", headers=ADMIN_HEADERS)
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_with_filters(self):
        svc = MagicMock()
        svc.list_executions.return_value = ([], 0)
        with patch(SVC, return_value=svc):
            r = client.get(
                f"{BASE}/executions?playbook_id=1&status=in_progress&offset=0&limit=10",
                headers=ADMIN_HEADERS,
            )
        assert r.status_code == 200

    def test_list_viewer_forbidden(self):
        r = client.get(f"{BASE}/executions", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /executions/{id} – get execution
# ---------------------------------------------------------------------------


class TestGetExecution:
    def test_get_happy(self):
        svc = MagicMock()
        svc.get_execution.return_value = _mock_execution()
        with patch(SVC, return_value=svc):
            r = client.get(f"{BASE}/executions/1", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_get_not_found(self):
        from app.core.module_helpers.service_validation import TenantResourceNotFoundError
        svc = MagicMock()
        svc.get_execution.side_effect = TenantResourceNotFoundError("not found")
        with patch(SVC, return_value=svc):
            r = client.get(f"{BASE}/executions/999", headers=ADMIN_HEADERS)
        assert r.status_code == 404

    def test_get_viewer_forbidden(self):
        r = client.get(f"{BASE}/executions/1", headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /executions/{id}/abandon
# ---------------------------------------------------------------------------


class TestAbandonExecution:
    _payload = {"abandon_reason": "Changed approach"}

    def test_abandon_happy(self):
        svc = MagicMock()
        exec_obj = _mock_execution()
        exec_obj.status = "abandoned"
        svc.abandon_execution.return_value = exec_obj
        with patch(_FLAG_PATCH, side_effect=_flag_enabled), \
             patch(SVC, return_value=svc):
            r = client.post(f"{BASE}/executions/1/abandon", json=self._payload, headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_abandon_feature_disabled(self):
        with patch(_FLAG_PATCH, side_effect=_flag_disabled):
            r = client.post(f"{BASE}/executions/1/abandon", json=self._payload, headers=ADMIN_HEADERS)
        assert r.status_code == 403

    def test_abandon_reason_too_short(self):
        with patch(_FLAG_PATCH, side_effect=_flag_enabled):
            r = client.post(f"{BASE}/executions/1/abandon", json={"abandon_reason": "ab"}, headers=ADMIN_HEADERS)
        assert r.status_code == 400

    def test_abandon_viewer_forbidden(self):
        r = client.post(f"{BASE}/executions/1/abandon", json=self._payload, headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /executions/{id}/steps/{sid}/complete
# ---------------------------------------------------------------------------


class TestCompleteStep:
    _payload = {"outcome_note": "Done"}

    def test_complete_happy(self):
        svc = MagicMock()
        se = _mock_step_execution()
        se.status = "completed"
        svc.complete_step.return_value = se
        with patch(_FLAG_PATCH, side_effect=_flag_enabled), \
             patch(SVC, return_value=svc):
            r = client.post(f"{BASE}/executions/1/steps/1/complete", json=self._payload, headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_complete_feature_disabled(self):
        with patch(_FLAG_PATCH, side_effect=_flag_disabled):
            r = client.post(f"{BASE}/executions/1/steps/1/complete", json=self._payload, headers=ADMIN_HEADERS)
        assert r.status_code == 403

    def test_complete_viewer_forbidden(self):
        r = client.post(f"{BASE}/executions/1/steps/1/complete", json=self._payload, headers=VIEWER_HEADERS)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /executions/{id}/steps/{sid}/skip
# ---------------------------------------------------------------------------


class TestSkipStep:
    _payload = {"outcome_note": "Not applicable"}

    def test_skip_happy(self):
        svc = MagicMock()
        se = _mock_step_execution()
        se.status = "skipped"
        svc.skip_step.return_value = se
        with patch(_FLAG_PATCH, side_effect=_flag_enabled), \
             patch(SVC, return_value=svc):
            r = client.post(f"{BASE}/executions/1/steps/1/skip", json=self._payload, headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_skip_feature_disabled(self):
        with patch(_FLAG_PATCH, side_effect=_flag_disabled):
            r = client.post(f"{BASE}/executions/1/steps/1/skip", json=self._payload, headers=ADMIN_HEADERS)
        assert r.status_code == 403

    def test_skip_viewer_forbidden(self):
        r = client.post(f"{BASE}/executions/1/steps/1/skip", json=self._payload, headers=VIEWER_HEADERS)
        assert r.status_code == 403
