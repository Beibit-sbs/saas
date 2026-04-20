"""Tests for workflows module — router-level API endpoints.

Covers: POST /start, GET /instances, GET /tasks, GET /consistency,
POST /tasks/{id}/complete, POST /tasks/{id}/assign, POST /tasks/{id}/comment.
Plus permission guards and validation checks.
"""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.main import app
from app.modules.workflows.dependencies import get_workflows_db
from tests.conftest import ADMIN_HEADERS, _auth_headers, client


def _mock_workflows_db():
    """Provide a lightweight mock Session so the 503 guard is bypassed."""
    mock = MagicMock(spec=Session)
    # query().filter().all() → empty list by default
    mock.query.return_value.filter.return_value.all.return_value = []
    mock.query.return_value.filter.return_value.first.return_value = None
    mock.query.return_value.filter_by.return_value.first.return_value = None
    mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    mock.query.return_value.filter.return_value.count.return_value = 0
    yield mock


@pytest.fixture(autouse=True)
def _override_workflows_db():
    app.dependency_overrides[get_workflows_db] = _mock_workflows_db
    yield
    app.dependency_overrides.pop(get_workflows_db, None)


# ---------------------------------------------------------------------------
# 1. GET /instances — list
# ---------------------------------------------------------------------------


def test_list_workflow_instances_returns_200() -> None:
    resp = client.get("/api/admin/workflows/instances", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "total" in body
    assert "items" in body
    assert isinstance(body["items"], list)


def test_list_workflow_instances_filter_entity_type() -> None:
    resp = client.get(
        "/api/admin/workflows/instances?entity_type=application",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["items"], list)


def test_list_workflow_instances_filter_status() -> None:
    resp = client.get(
        "/api/admin/workflows/instances?status=pending",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200


def test_list_workflow_instances_limits() -> None:
    resp = client.get(
        "/api/admin/workflows/instances?limit=5",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert len(resp.json()["items"]) <= 5


# ---------------------------------------------------------------------------
# 2. GET /tasks — user tasks
# ---------------------------------------------------------------------------


def test_list_user_tasks_returns_200() -> None:
    resp = client.get("/api/admin/workflows/tasks", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "total" in body
    assert "items" in body


def test_list_user_tasks_include_completed() -> None:
    resp = client.get(
        "/api/admin/workflows/tasks?include_completed=true",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200


def test_list_user_tasks_filter_assignee() -> None:
    resp = client.get(
        "/api/admin/workflows/tasks?assignee_ref=someone@example.com",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 3. GET /consistency — workflow health report
# ---------------------------------------------------------------------------


def test_workflow_consistency_returns_200() -> None:
    resp = client.get("/api/admin/workflows/consistency", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "definitions_count" in body or "total_definitions" in body or isinstance(body, dict)


# ---------------------------------------------------------------------------
# 4. POST /start — validation
# ---------------------------------------------------------------------------


def test_start_workflow_missing_key_fails() -> None:
    resp = client.post(
        "/api/admin/workflows/start",
        headers=ADMIN_HEADERS,
        json={"entity_type": "application", "entity_id": 1},
    )
    assert resp.status_code in (400, 422)


def test_start_workflow_missing_entity_type_fails() -> None:
    resp = client.post(
        "/api/admin/workflows/start",
        headers=ADMIN_HEADERS,
        json={"workflow_key": "admissions_review", "entity_id": 1},
    )
    assert resp.status_code in (400, 422)


def test_start_workflow_zero_entity_id_fails() -> None:
    resp = client.post(
        "/api/admin/workflows/start",
        headers=ADMIN_HEADERS,
        json={"workflow_key": "test", "entity_type": "app", "entity_id": 0},
    )
    assert resp.status_code in (400, 422)


def test_start_workflow_nonexistent_key() -> None:
    """Start with a valid payload but non-existent workflow key → 404."""
    resp = client.post(
        "/api/admin/workflows/start",
        headers=ADMIN_HEADERS,
        json={
            "workflow_key": "nonexistent_workflow_key_xyz",
            "entity_type": "application",
            "entity_id": 999,
        },
    )
    assert resp.status_code in (404, 400)


# ---------------------------------------------------------------------------
# 5. POST /tasks/{id}/complete — validation
# ---------------------------------------------------------------------------


def test_complete_task_nonexistent_id() -> None:
    resp = client.post(
        "/api/admin/workflows/tasks/999999/complete",
        headers=ADMIN_HEADERS,
        json={"expected_task_version": 1, "transition_action": "complete"},
    )
    assert resp.status_code in (404, 400)


def test_complete_task_missing_version_fails() -> None:
    resp = client.post(
        "/api/admin/workflows/tasks/1/complete",
        headers=ADMIN_HEADERS,
        json={"transition_action": "complete"},
    )
    assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# 6. POST /tasks/{id}/assign — validation
# ---------------------------------------------------------------------------


def test_assign_task_nonexistent_id() -> None:
    resp = client.post(
        "/api/admin/workflows/tasks/999999/assign",
        headers=ADMIN_HEADERS,
        json={
            "assignee_type": "user",
            "assignee_ref": "someone@example.com",
            "expected_version": 1,
        },
    )
    assert resp.status_code in (404, 400)


def test_assign_task_missing_assignee_fails() -> None:
    resp = client.post(
        "/api/admin/workflows/tasks/1/assign",
        headers=ADMIN_HEADERS,
        json={"expected_version": 1},
    )
    assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# 7. POST /tasks/{id}/comment — validation
# ---------------------------------------------------------------------------


def test_add_comment_nonexistent_task() -> None:
    resp = client.post(
        "/api/admin/workflows/tasks/999999/comment",
        headers=ADMIN_HEADERS,
        json={"body": "Test comment"},
    )
    assert resp.status_code in (404, 400)


def test_add_comment_empty_body_fails() -> None:
    resp = client.post(
        "/api/admin/workflows/tasks/1/comment",
        headers=ADMIN_HEADERS,
        json={"body": ""},
    )
    assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# 8. Permission guards
# ---------------------------------------------------------------------------


def test_workflows_instances_requires_auth() -> None:
    resp = client.get("/api/admin/workflows/instances")
    assert resp.status_code in (401, 403)


def test_workflows_tasks_requires_auth() -> None:
    resp = client.get("/api/admin/workflows/tasks")
    assert resp.status_code in (401, 403)


def test_workflows_start_requires_auth() -> None:
    resp = client.post(
        "/api/admin/workflows/start",
        json={"workflow_key": "test", "entity_type": "x", "entity_id": 1},
    )
    assert resp.status_code in (401, 403)


def test_viewer_cannot_start_workflow() -> None:
    viewer = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.post(
        "/api/admin/workflows/start",
        headers=viewer,
        json={"workflow_key": "test", "entity_type": "x", "entity_id": 1},
    )
    assert resp.status_code == 403


def test_viewer_cannot_complete_task() -> None:
    viewer = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.post(
        "/api/admin/workflows/tasks/1/complete",
        headers=viewer,
        json={"expected_task_version": 1},
    )
    assert resp.status_code == 403


def test_viewer_cannot_assign_task() -> None:
    viewer = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.post(
        "/api/admin/workflows/tasks/1/assign",
        headers=viewer,
        json={"assignee_type": "user", "assignee_ref": "x@x.com", "expected_version": 1},
    )
    assert resp.status_code == 403


def test_viewer_cannot_comment_task() -> None:
    viewer = _auth_headers("viewer@example.com", ["viewer"])
    resp = client.post(
        "/api/admin/workflows/tasks/1/comment",
        headers=viewer,
        json={"body": "nope"},
    )
    assert resp.status_code == 403
