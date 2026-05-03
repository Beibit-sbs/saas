"""Phase XXXIV.4 — syllabus_governance lifecycle workflow/event tests (10-step loop hardening)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.syllabus_governance.schemas import SyllabusCreateSchema, SyllabusUpdateSchema
from app.modules.syllabus_governance import service as svc


@pytest.fixture()
def _no_audit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "log_admin_action", lambda **kwargs: None)


def _seed_syllabus(status: str = "draft") -> dict[str, object]:
    return {
        "id": 1,
        "course_code": "CS-201",
        "course_title": "Algorithms",
        "department_id": "cs",
        "faculty_id": "FAC-1",
        "term_id": "2026-fall",
        "status": status,
        "tenant_id": "1",
    }


def _base_payload(status: str = "draft") -> SyllabusCreateSchema:
    return SyllabusCreateSchema(
        course_code="CS-201",
        course_title="Algorithms",
        department_id="cs",
        faculty_id="FAC-1",
        term_id="2026-fall",
        status=status,
    )


def test_create_publishes_syllabus_created(_no_audit, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "_check_faculty_has_active_contract_for_syllabus", lambda **kwargs: None)
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda entity, tid: [])
    monkeypatch.setattr(
        svc,
        "create_entity_for_tenant",
        lambda entity, payload, tid: {"id": 11, **payload, "tenant_id": str(tid)},
    )

    with patch("app.modules.syllabus_governance.service.EventPublisher") as mock_cls:
        publisher = MagicMock()
        mock_cls.return_value = publisher

        row = svc.create_syllabus(tenant_id=1, payload=_base_payload("draft"), actor="owner@example.com")

    assert row.id == 11
    event_types = [c.kwargs["event_type"] for c in publisher.publish_event.call_args_list]
    assert "syllabus.created" in event_types


def test_under_review_transition_creates_workflow_and_brain_signal(_no_audit, monkeypatch: pytest.MonkeyPatch) -> None:
    syllabus = _seed_syllabus("draft")
    created: list[tuple[str, dict[str, object]]] = []

    def fake_list(entity: str, tid: int) -> list[dict[str, object]]:
        if entity == "syllabi":
            return [syllabus]
        return []

    def fake_create(entity: str, payload: dict[str, object], tid: int) -> dict[str, object]:
        rec = {"id": 100 + len(created), **payload, "tenant_id": tid}
        created.append((entity, rec))
        return rec

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)
    monkeypatch.setattr(svc, "update_entity_for_tenant", lambda e, sid, payload, tid: {**payload, "id": sid, "tenant_id": str(tid)})

    with patch("app.modules.syllabus_governance.service.EventPublisher") as mock_cls:
        publisher = MagicMock()
        mock_cls.return_value = publisher

        updated = svc.update_syllabus(
            tenant_id=1,
            syllabus_id=1,
            payload=SyllabusUpdateSchema(status="under_review"),
            actor="owner@example.com",
        )

    assert updated.status == "under_review"
    created_names = [n for n, _ in created]
    assert "syllabus_approval_workflows" in created_names
    assert "syllabus_approval_actions" in created_names
    assert "syllabus_review_backlogs" in created_names
    event_types = [c.kwargs["event_type"] for c in publisher.publish_event.call_args_list]
    assert "syllabus.review_requested" in event_types
    assert "campus.syllabus_governance.review_backlog_detected" in event_types


def test_invalid_transition_rejected(_no_audit, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda entity, tid: [_seed_syllabus("draft")])

    with pytest.raises(ValueError, match="Invalid syllabus transition"):
        svc.update_syllabus(
            tenant_id=1,
            syllabus_id=1,
            payload=SyllabusUpdateSchema(status="published"),
            actor="owner@example.com",
        )


def test_approval_guard_blocks_when_program_not_active(_no_audit, monkeypatch: pytest.MonkeyPatch) -> None:
    syllabus = _seed_syllabus("under_review")

    def fake_list(entity: str, tid: int) -> list[dict[str, object]]:
        if entity == "syllabi":
            return [syllabus]
        if entity == "courses":
            return [{"course_code": "CS-201", "program_id": "P-1"}]
        if entity == "programs":
            return [{"id": "P-1", "status": "inactive"}]
        return []

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)

    with pytest.raises(DomainValidationError, match="approval blocked"):
        svc.update_syllabus(
            tenant_id=1,
            syllabus_id=1,
            payload=SyllabusUpdateSchema(status="approved"),
            actor="owner@example.com",
        )


def test_approved_transition_records_outcome_and_event(_no_audit, monkeypatch: pytest.MonkeyPatch) -> None:
    syllabus = _seed_syllabus("under_review")
    created: list[tuple[str, dict[str, object]]] = []

    def fake_list(entity: str, tid: int) -> list[dict[str, object]]:
        if entity == "syllabi":
            return [syllabus]
        if entity == "courses":
            return [{"course_code": "CS-201", "program_id": "P-1"}]
        if entity == "programs":
            return [{"id": "P-1", "status": "active"}]
        return []

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", lambda e, p, tid: ({"id": 501, **p}, created.append((e, p)))[0])
    monkeypatch.setattr(svc, "update_entity_for_tenant", lambda e, sid, payload, tid: {**payload, "id": sid})

    with patch("app.modules.syllabus_governance.service.EventPublisher") as mock_cls:
        publisher = MagicMock()
        mock_cls.return_value = publisher
        updated = svc.update_syllabus(1, 1, SyllabusUpdateSchema(status="approved"), "owner@example.com")

    assert updated.status == "approved"
    assert any(name == "syllabus_approval_outcomes" for name, _ in created)
    event_types = [c.kwargs["event_type"] for c in publisher.publish_event.call_args_list]
    assert "syllabus.approved" in event_types
    assert "syllabus.outcome_recorded" in event_types


def test_published_transition_records_outcome_and_event(_no_audit, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda entity, tid: [_seed_syllabus("approved")])
    monkeypatch.setattr(svc, "create_entity_for_tenant", lambda e, p, tid: {"id": 600, **p})
    monkeypatch.setattr(svc, "update_entity_for_tenant", lambda e, sid, payload, tid: {**payload, "id": sid})

    with patch("app.modules.syllabus_governance.service.EventPublisher") as mock_cls:
        publisher = MagicMock()
        mock_cls.return_value = publisher
        updated = svc.update_syllabus(1, 1, SyllabusUpdateSchema(status="published"), "owner@example.com")

    assert updated.status == "published"
    event_types = [c.kwargs["event_type"] for c in publisher.publish_event.call_args_list]
    assert "syllabus.published" in event_types
    assert "syllabus.outcome_recorded" in event_types


def test_archived_transition_records_outcome_and_event(_no_audit, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda entity, tid: [_seed_syllabus("published")])
    monkeypatch.setattr(svc, "create_entity_for_tenant", lambda e, p, tid: {"id": 700, **p})
    monkeypatch.setattr(svc, "update_entity_for_tenant", lambda e, sid, payload, tid: {**payload, "id": sid})

    with patch("app.modules.syllabus_governance.service.EventPublisher") as mock_cls:
        publisher = MagicMock()
        mock_cls.return_value = publisher
        updated = svc.update_syllabus(1, 1, SyllabusUpdateSchema(status="archived"), "owner@example.com")

    assert updated.status == "archived"
    event_types = [c.kwargs["event_type"] for c in publisher.publish_event.call_args_list]
    assert "syllabus.archived" in event_types
    assert "syllabus.outcome_recorded" in event_types


def test_under_review_transition_fail_closed_on_workflow_action_error(_no_audit, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda entity, tid: [_seed_syllabus("draft")])

    def fail_create(entity: str, payload: dict[str, object], tid: int) -> dict[str, object]:
        if entity == "syllabus_approval_actions":
            raise RuntimeError("write failed")
        return {"id": 10, **payload}

    monkeypatch.setattr(svc, "create_entity_for_tenant", fail_create)

    called_update = {"value": False}

    def fake_update(entity: str, sid: int, payload: dict[str, object], tid: int) -> dict[str, object]:
        called_update["value"] = True
        return {**payload, "id": sid}

    monkeypatch.setattr(svc, "update_entity_for_tenant", fake_update)

    with pytest.raises(DomainValidationError, match="failed to persist approval workflow/action path"):
        svc.update_syllabus(1, 1, SyllabusUpdateSchema(status="under_review"), "owner@example.com")

    assert called_update["value"] is False


def test_get_approval_workflow_uses_persisted_records(_no_audit, monkeypatch: pytest.MonkeyPatch) -> None:
    syllabus = _seed_syllabus("under_review")

    def fake_list(entity: str, tid: int) -> list[dict[str, object]]:
        if entity == "syllabi":
            return [syllabus]
        if entity == "syllabus_approval_workflows":
            return [{"id": 41, "syllabus_id": 1, "workflow_status": "in_progress", "current_step": 2, "total_steps": 4}]
        if entity == "syllabus_approval_actions":
            return [{"id": 501, "workflow_id": 41, "syllabus_id": 1, "step_order": 2, "step_type": "academic_dean", "assigned_to": "dean@example.com", "action_status": "pending"}]
        return []

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)

    wf = svc.get_approval_workflow(tenant_id=1, syllabus_id=1)
    assert wf["workflow_id"] == "41"
    assert wf["status"] == "in_progress"
    assert len(wf["approval_steps"]) == 1
    assert wf["approval_steps"][0]["step_type"] == "academic_dean"


def test_create_under_review_emits_review_requested_and_brain_signal(_no_audit, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "_check_faculty_has_active_contract_for_syllabus", lambda **kwargs: None)

    def fake_list(entity: str, tid: int) -> list[dict[str, object]]:
        return []

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)

    seq = {"id": 1}

    def fake_create(entity: str, payload: dict[str, object], tid: int) -> dict[str, object]:
        seq["id"] += 1
        return {"id": seq["id"], **payload, "tenant_id": tid}

    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

    with patch("app.modules.syllabus_governance.service.EventPublisher") as mock_cls:
        publisher = MagicMock()
        mock_cls.return_value = publisher

        row = svc.create_syllabus(1, _base_payload("under_review"), "owner@example.com")

    assert row.status == "under_review"
    event_types = [c.kwargs["event_type"] for c in publisher.publish_event.call_args_list]
    assert "syllabus.review_requested" in event_types
    assert "campus.syllabus_governance.review_backlog_detected" in event_types
