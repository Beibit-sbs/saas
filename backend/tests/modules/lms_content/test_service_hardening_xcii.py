"""
XCII — LMS Content Service Hardening Tests.

Verifies:
  1. complete_lesson persists progress BEFORE firing event (persist-first).
  2. submit_assignment survives publisher failure (fire-and-forget).
  3. grade_submission uses canonical tenant API signatures and outcome path is fail-safe.
  4. check_falling_behind persists risk first — no rollback when event publish fails.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

MODULE = "app.modules.lms_content.service"


def test_complete_lesson_persists_before_event() -> None:
    call_order: list[str] = []

    def fake_create(entity_name, payload, tenant_id):
        call_order.append("persist")
        return {"id": "prog-1", **payload}

    def fake_publish(self, **kwargs):
        call_order.append("event")

    with (
        patch(f"{MODULE}.create_entity_for_tenant", side_effect=fake_create),
        patch(f"{MODULE}.EventPublisher.publish_event", fake_publish),
        patch(f"{MODULE}.log_admin_action"),
        patch(f"{MODULE}.record_usage_event"),
    ):
        from app.modules.lms_content import service as svc

        result = svc.complete_lesson(1, lesson_id="lesson-1", student_id="stu-1")

    assert result["status"] == "COMPLETED"
    assert call_order == ["persist", "event"]


def test_submit_assignment_survives_publish_failure() -> None:
    fake_submission = {
        "id": "sub-1",
        "assignment_id": "asg-1",
        "student_id": "stu-1",
        "status": "SUBMITTED",
        "tenant_id": 1,
    }

    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=fake_submission),
        patch(f"{MODULE}.EventPublisher.publish_event", side_effect=RuntimeError("broker down")),
        patch(f"{MODULE}.log_admin_action") as mock_audit,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
    ):
        from app.modules.lms_content import service as svc

        result = svc.submit_assignment(
            1,
            assignment_id="asg-1",
            student_id="stu-1",
            content="answer",
        )

    assert result["submission_id"] == "sub-1"
    assert result["status"] == "SUBMITTED"
    mock_audit.assert_called_once()
    mock_metric.assert_called_once()


def test_grade_submission_uses_canonical_tenant_api_and_fail_safe_outcome() -> None:
    submission = {
        "id": "sub-1",
        "assignment_id": "asg-1",
        "student_id": "stu-1",
        "status": "SUBMITTED",
        "tenant_id": 1,
    }

    mock_list = MagicMock(return_value=[submission])
    mock_create = MagicMock(return_value={"id": "grade-1"})
    mock_update = MagicMock(return_value={"id": "sub-1", "status": "GRADED"})

    with (
        patch(f"{MODULE}.list_entities_for_tenant", mock_list),
        patch(f"{MODULE}.create_entity_for_tenant", mock_create),
        patch(f"{MODULE}.update_entity_for_tenant", mock_update),
        patch(f"{MODULE}.EventPublisher.publish_event", return_value=None),
        patch("app.modules.brain_core.service.brain_core_service") as mock_brain,
        patch(f"{MODULE}.log_admin_action") as mock_audit,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
    ):
        from app.modules.lms_content import service as svc

        mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")
        result = svc.grade_submission(1, submission_id="sub-1", grade=90)

    list_args, list_kwargs = mock_list.call_args
    assert len(list_args) == 2
    assert list_args[0] == "lms_submissions"
    assert list_args[1] == 1
    assert "tenant_id" not in list_kwargs

    create_args, create_kwargs = mock_create.call_args
    assert len(create_args) == 3
    assert create_args[0] == "lms_grades"
    assert "tenant_id" not in create_kwargs

    update_args, update_kwargs = mock_update.call_args
    assert len(update_args) == 4
    assert update_args[0] == "lms_submissions"
    assert update_args[1] == "sub-1"
    assert "tenant_id" not in update_kwargs

    assert result["status"] == "GRADED"
    mock_audit.assert_called_once()
    mock_metric.assert_called_once()


def test_check_falling_behind_persist_before_event_no_rollback() -> None:
    lessons = [
        {"id": "l1", "course_id": "c-1"},
        {"id": "l2", "course_id": "c-1"},
        {"id": "l3", "course_id": "c-1"},
    ]
    progress = [{"id": "p1", "lesson_id": "l1", "student_id": "stu-1", "status": "COMPLETED"}]

    mock_list = MagicMock(
        side_effect=lambda entity, tenant_id: (
            lessons if entity == "lms_lessons" else progress if entity == "lms_lesson_progress" else []
        )
    )
    mock_create = MagicMock(return_value={"id": "risk-1"})

    with (
        patch(f"{MODULE}.list_entities_for_tenant", mock_list),
        patch(f"{MODULE}.create_entity_for_tenant", mock_create),
        patch(f"{MODULE}.EventPublisher.publish_event", side_effect=Exception("broker unavailable")),
        patch(f"{MODULE}.log_admin_action") as mock_audit,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
    ):
        from app.modules.lms_content import service as svc

        result = svc.check_falling_behind(1, course_id="c-1", student_id="stu-1")

    assert result["event_fired"] is True
    assert result["risk_record_id"] == "risk-1"
    assert mock_create.called
    mock_audit.assert_called_once()
    mock_metric.assert_called_once()
