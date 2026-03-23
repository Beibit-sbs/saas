from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import TenantRequiredError
from app.modules.workflows.load_templates import (
    TEMPLATE_FILES,
    _enum,
    _replace_steps_and_transitions,
    _upsert_definition,
    _upsert_version,
    load_templates,
)
from app.modules.workflows.models import (
    WorkflowDefinitionStatus,
    WorkflowStepType,
)


def _payload(definition_key: str = "admissions.workflow") -> dict:
    return {
        "definition": {
            "key": definition_key,
            "name": "Admissions Workflow",
            "description": "workflow",
            "status": "active",
            "metadata_json": {},
        },
        "version": {
            "version_no": 1,
            "status": "active",
            "is_active": True,
            "trigger_mode": "manual",
            "definition_json": {},
            "metadata_json": {},
        },
        "steps": [
            {
                "step_key": "submit",
                "name": "Submit",
                "step_type": "start",
                "task_type": None,
                "assignee_type": None,
                "assignee_ref": None,
            },
            {
                "step_key": "review_documents",
                "name": "Review",
                "step_type": "task",
                "task_type": "doc_review",
                "assignee_type": "role",
                "assignee_ref": "reviewer",
            },
            {
                "step_key": "department_approval",
                "name": "Department Approval",
                "step_type": "approval",
                "task_type": "department_approval",
                "assignee_type": "role",
                "assignee_ref": "department_chair",
            },
            {
                "step_key": "dean_approval",
                "name": "Dean Approval",
                "step_type": "approval",
                "task_type": "dean_approval",
                "assignee_type": "role",
                "assignee_ref": "dean",
            },
            {
                "step_key": "final_decision",
                "name": "Final Decision",
                "step_type": "end",
                "task_type": None,
                "assignee_type": None,
                "assignee_ref": None,
            },
        ],
        "transitions": [
            {
                "from_step_key": "submit",
                "to_step_key": "review_documents",
                "action_key": "start",
                "name": "Start",
            },
            {
                "from_step_key": "review_documents",
                "to_step_key": "department_approval",
                "action_key": "complete",
                "name": "Docs Completed",
            },
        ],
    }


@pytest.fixture
def db_session() -> MagicMock:
    db = MagicMock(name="workflow_loader_db")

    query_chain = MagicMock(name="query_chain")
    query_chain.filter.return_value = query_chain
    query_chain.update.return_value = 1
    query_chain.delete.return_value = 1
    db.query.return_value = query_chain

    def _add(instance):
        if getattr(instance, "id", None) is None:
            _add.counter += 1
            instance.id = _add.counter

    _add.counter = 100
    db.add.side_effect = _add
    return db


def _execute_result(*, scalar_one_or_none=None):
    result = MagicMock(name="execute_result")
    result.scalar_one_or_none.return_value = scalar_one_or_none
    return result


def test_json_templates_load_successfully() -> None:
    required_step_keys = {
        "submit",
        "review_documents",
        "department_approval",
        "dean_approval",
        "final_decision",
    }

    for name, path in TEMPLATE_FILES.items():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "definition" in data, f"{name}: missing definition"
        assert "version" in data, f"{name}: missing version"
        assert "steps" in data and data["steps"], f"{name}: missing steps"
        assert "transitions" in data and data["transitions"], f"{name}: missing transitions"

        step_keys = {step["step_key"] for step in data["steps"]}
        assert required_step_keys.issubset(step_keys), f"{name}: required step keys missing"


def test_upsert_definition_reuses_existing_record(db_session: MagicMock) -> None:
    payload = _payload("student.request.workflow")
    existing = SimpleNamespace(
        id=11,
        tenant_id=1,
        key="student.request.workflow",
        name="Old Name",
        description="old",
        status=WorkflowDefinitionStatus.DRAFT,
        metadata_json={},
        version=1,
        updated_by="old",
    )
    db_session.execute.return_value = _execute_result(scalar_one_or_none=existing)

    result = _upsert_definition(db_session, tenant_id=1, actor="qa@example.com", payload=payload)

    assert result is existing
    assert result.name == "Admissions Workflow"
    assert result.status == WorkflowDefinitionStatus.ACTIVE
    assert result.version == 2
    db_session.add.assert_not_called()


def test_upsert_version_second_run_updates_without_new_insert(db_session: MagicMock) -> None:
    definition = SimpleNamespace(id=10, version=1, active_version_no=None, status=WorkflowDefinitionStatus.DRAFT, updated_by="old")
    payload = _payload("admissions.workflow")

    existing_version = SimpleNamespace(
        id=21,
        tenant_id=1,
        workflow_definition_id=10,
        version_no=1,
        status="draft",
        is_active=False,
        trigger_mode="manual",
        definition_json={},
        metadata_json={},
        published_by=None,
        version=1,
        updated_by="old",
    )
    db_session.execute.return_value = _execute_result(scalar_one_or_none=existing_version)

    result = _upsert_version(db_session, tenant_id=1, actor="qa@example.com", definition=definition, payload=payload)

    assert result is existing_version
    assert result.is_active is True
    assert result.version == 2
    db_session.add.assert_not_called()
    db_session.query.assert_called()


def test_only_one_active_version_update_is_enforced(db_session: MagicMock) -> None:
    definition = SimpleNamespace(id=10, version=1, active_version_no=None, status=WorkflowDefinitionStatus.DRAFT, updated_by="old")
    payload = _payload("admissions.workflow")

    db_session.execute.return_value = _execute_result(
        scalar_one_or_none=SimpleNamespace(
            id=42,
            tenant_id=1,
            workflow_definition_id=10,
            version_no=1,
            status="active",
            is_active=True,
            trigger_mode="manual",
            definition_json={},
            metadata_json={},
            published_by=None,
            version=1,
            updated_by="old",
        )
    )

    _upsert_version(db_session, tenant_id=1, actor="qa@example.com", definition=definition, payload=payload)

    update_calls = db_session.query.return_value.update
    assert update_calls.called
    assert definition.active_version_no == 1
    assert definition.status == WorkflowDefinitionStatus.ACTIVE


def test_steps_and_transitions_recreated_for_version(db_session: MagicMock) -> None:
    payload = _payload("admissions.workflow")
    version = SimpleNamespace(id=555)

    _replace_steps_and_transitions(db_session, tenant_id=1, actor="qa@example.com", version=version, payload=payload)

    # delete transitions + delete steps + add 5 steps + add 2 transitions
    assert db_session.add.call_count == 7
    delete_calls = db_session.query.return_value.delete
    assert delete_calls.call_count == 2


def test_subset_loading_processes_only_selected_templates(monkeypatch: pytest.MonkeyPatch, db_session: MagicMock) -> None:
    calls: list[str] = []

    def fake_load_json(path: Path) -> dict:
        calls.append(path.name)
        return _payload(path.stem)

    monkeypatch.setattr("app.modules.workflows.load_templates._load_json", fake_load_json)
    monkeypatch.setattr(
        "app.modules.workflows.load_templates._upsert_definition",
        lambda db, tenant_id, actor, payload: SimpleNamespace(id=1, key=payload["definition"]["key"]),
    )
    monkeypatch.setattr(
        "app.modules.workflows.load_templates._upsert_version",
        lambda db, tenant_id, actor, definition, payload: SimpleNamespace(id=1, version_no=1),
    )
    monkeypatch.setattr(
        "app.modules.workflows.load_templates._replace_steps_and_transitions",
        lambda db, tenant_id, actor, version, payload: None,
    )

    result = load_templates(db_session, tenant_id=1, actor="qa@example.com", template_names=["admissions"])

    assert len(result) == 1
    assert result[0]["template"] == "admissions"
    assert calls == ["admissions_workflow.json"]


def test_invalid_enum_is_rejected_safely() -> None:
    with pytest.raises(ValueError, match="Unsupported value"):
        _enum(WorkflowStepType, "invalid-step-type")


def test_invalid_transition_shape_is_rejected_safely(db_session: MagicMock) -> None:
    payload = _payload("admissions.workflow")
    payload["transitions"] = [
        {
            "from_step_key": "missing",
            "to_step_key": "review_documents",
            "action_key": "start",
            "name": "Broken",
        }
    ]

    with pytest.raises(ValueError, match="Transition references missing step"):
        _replace_steps_and_transitions(
            db_session,
            tenant_id=1,
            actor="qa@example.com",
            version=SimpleNamespace(id=10),
            payload=payload,
        )


def test_tenant_id_required_fail_closed(db_session: MagicMock) -> None:
    with pytest.raises(TenantRequiredError):
        load_templates(db_session, tenant_id=None, actor="qa@example.com")


def test_loader_cli_tenant_must_be_positive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["load_templates.py", "--tenant-id", "0"])

    from app.modules.workflows.load_templates import main

    with pytest.raises(SystemExit, match="positive integer"):
        main()
