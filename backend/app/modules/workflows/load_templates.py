from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.db import build_engine, make_session_factory
from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.workflows.models import (
    WorkflowAssigneeType,
    WorkflowDefinitionModel,
    WorkflowDefinitionStatus,
    WorkflowDefinitionVersionModel,
    WorkflowDefinitionVersionStatus,
    WorkflowStepType,
    WorkflowStepModel,
    WorkflowTransitionModel,
    WorkflowTriggerMode,
)


TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
TEMPLATE_FILES = {
    "admissions": TEMPLATE_DIR / "admissions_workflow.json",
    "student-request": TEMPLATE_DIR / "student_request_workflow.json",
    "faculty-hiring": TEMPLATE_DIR / "faculty_hiring_workflow.json",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _enum(enum_cls, value: str):
    try:
        return enum_cls(value)
    except ValueError as exc:
        raise ValueError(f"Unsupported value '{value}' for {enum_cls.__name__}") from exc


def _upsert_definition(db: Session, tenant_id: int, actor: str, payload: dict) -> WorkflowDefinitionModel:
    definition_data = payload["definition"]

    definition = db.execute(
        select(WorkflowDefinitionModel).where(
            and_(
                WorkflowDefinitionModel.tenant_id == tenant_id,
                WorkflowDefinitionModel.key == definition_data["key"],
            )
        )
    ).scalar_one_or_none()

    status = _enum(WorkflowDefinitionStatus, definition_data.get("status", "active"))

    if definition is None:
        definition = WorkflowDefinitionModel(
            tenant_id=tenant_id,
            key=definition_data["key"],
            name=definition_data["name"],
            description=definition_data.get("description"),
            status=status,
            metadata_json=definition_data.get("metadata_json", {}),
            version=1,
            created_by=actor,
            updated_by=actor,
        )
        db.add(definition)
        db.flush()
        db.refresh(definition)
        return definition

    definition.name = definition_data["name"]
    definition.description = definition_data.get("description")
    definition.status = status
    definition.metadata_json = definition_data.get("metadata_json", {})
    definition.version += 1
    definition.updated_by = actor
    db.flush()
    db.refresh(definition)
    return definition


def _upsert_version(
    db: Session,
    tenant_id: int,
    actor: str,
    definition: WorkflowDefinitionModel,
    payload: dict,
) -> WorkflowDefinitionVersionModel:
    version_data = payload["version"]
    version_no = int(version_data["version_no"])

    version = db.execute(
        select(WorkflowDefinitionVersionModel).where(
            and_(
                WorkflowDefinitionVersionModel.tenant_id == tenant_id,
                WorkflowDefinitionVersionModel.workflow_definition_id == definition.id,
                WorkflowDefinitionVersionModel.version_no == version_no,
            )
        )
    ).scalar_one_or_none()

    version_status = _enum(WorkflowDefinitionVersionStatus, version_data.get("status", "active"))
    trigger_mode = _enum(WorkflowTriggerMode, version_data.get("trigger_mode", "manual"))
    is_active = bool(version_data.get("is_active", True))

    if version is None:
        version = WorkflowDefinitionVersionModel(
            tenant_id=tenant_id,
            workflow_definition_id=definition.id,
            version_no=version_no,
            status=version_status,
            is_active=is_active,
            trigger_mode=trigger_mode,
            definition_json=version_data.get("definition_json", {}),
            metadata_json=version_data.get("metadata_json", {}),
            published_by=actor if is_active else None,
            version=1,
            created_by=actor,
            updated_by=actor,
        )
        db.add(version)
        db.flush()
        db.refresh(version)
    else:
        version.status = version_status
        version.is_active = is_active
        version.trigger_mode = trigger_mode
        version.definition_json = version_data.get("definition_json", {})
        version.metadata_json = version_data.get("metadata_json", {})
        version.published_by = actor if is_active else version.published_by
        version.version += 1
        version.updated_by = actor
        db.flush()
        db.refresh(version)

    if is_active:
        db.query(WorkflowDefinitionVersionModel).filter(
            WorkflowDefinitionVersionModel.tenant_id == tenant_id,
            WorkflowDefinitionVersionModel.workflow_definition_id == definition.id,
            WorkflowDefinitionVersionModel.id != version.id,
        ).update({"is_active": False}, synchronize_session=False)

        definition.active_version_no = version.version_no
        definition.status = WorkflowDefinitionStatus.ACTIVE
        definition.updated_by = actor
        definition.version += 1

    db.flush()
    db.refresh(version)
    return version


def _replace_steps_and_transitions(
    db: Session,
    tenant_id: int,
    actor: str,
    version: WorkflowDefinitionVersionModel,
    payload: dict,
) -> None:
    db.query(WorkflowTransitionModel).filter(
        WorkflowTransitionModel.tenant_id == tenant_id,
        WorkflowTransitionModel.workflow_definition_version_id == version.id,
    ).delete(synchronize_session=False)

    db.query(WorkflowStepModel).filter(
        WorkflowStepModel.tenant_id == tenant_id,
        WorkflowStepModel.workflow_definition_version_id == version.id,
    ).delete(synchronize_session=False)

    step_id_by_key: dict[str, int] = {}
    for step in payload["steps"]:
        step_row = WorkflowStepModel(
            tenant_id=tenant_id,
            workflow_definition_version_id=version.id,
            step_key=step["step_key"],
            name=step["name"],
            step_type=_enum(WorkflowStepType, step["step_type"]),
            task_type=step.get("task_type"),
            assignee_type=(
                _enum(WorkflowAssigneeType, step["assignee_type"]) if step.get("assignee_type") else None
            ),
            assignee_ref=step.get("assignee_ref"),
            sla_minutes=step.get("sla_minutes"),
            is_blocking=bool(step.get("is_blocking", True)),
            sequence_hint=step.get("sequence_hint"),
            config_json=step.get("config_json", {}),
            metadata_json=step.get("metadata_json", {}),
            version=1,
            created_by=actor,
            updated_by=actor,
        )
        db.add(step_row)
        db.flush()
        step_id_by_key[step_row.step_key] = step_row.id

    for transition in payload["transitions"]:
        from_key = transition["from_step_key"]
        to_key = transition["to_step_key"]
        if from_key not in step_id_by_key or to_key not in step_id_by_key:
            raise ValueError(f"Transition references missing step: {from_key} -> {to_key}")

        transition_row = WorkflowTransitionModel(
            tenant_id=tenant_id,
            workflow_definition_version_id=version.id,
            from_step_id=step_id_by_key[from_key],
            to_step_id=step_id_by_key[to_key],
            action_key=transition["action_key"],
            name=transition["name"],
            condition_json=transition.get("condition_json", {}),
            is_default=bool(transition.get("is_default", False)),
            metadata_json=transition.get("metadata_json", {}),
            version=1,
            created_by=actor,
            updated_by=actor,
        )
        db.add(transition_row)

    db.flush()


def load_templates(
    db: Session,
    tenant_id: int,
    actor: str,
    *,
    template_names: list[str] | None = None,
) -> list[dict]:
    tenant_id = validate_tenant_id_provided(tenant_id)
    selected = template_names or list(TEMPLATE_FILES.keys())
    results: list[dict] = []

    for template_name in selected:
        path = TEMPLATE_FILES.get(template_name)
        if path is None:
            raise ValueError(f"Unknown template name: {template_name}")

        payload = _load_json(path)
        definition = _upsert_definition(db, tenant_id, actor, payload)
        version = _upsert_version(db, tenant_id, actor, definition, payload)
        _replace_steps_and_transitions(db, tenant_id, actor, version, payload)

        results.append(
            {
                "template": template_name,
                "definition_key": definition.key,
                "definition_id": definition.id,
                "version_no": version.version_no,
                "version_id": version.id,
            }
        )

    db.commit()
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Load workflow templates into app_workflows tables")
    parser.add_argument("--tenant-id", type=int, required=True, help="Tenant id for seeded templates")
    parser.add_argument("--actor", type=str, default="system@workflow-loader", help="Audit actor id")
    parser.add_argument(
        "--templates",
        nargs="*",
        choices=sorted(TEMPLATE_FILES.keys()),
        help="Optional subset of templates to load",
    )
    args = parser.parse_args()

    if args.tenant_id <= 0:
        raise SystemExit("--tenant-id must be a positive integer")

    engine = build_engine()
    session_factory = make_session_factory(engine)
    session = session_factory()
    try:
        result = load_templates(
            session,
            tenant_id=args.tenant_id,
            actor=args.actor,
            template_names=args.templates,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        session.close()
        engine.dispose()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
