from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.interventions.playbook_models import PlaybookTriggerType
from app.modules.interventions.playbook_schemas import (
    PlaybookCreateSchema,
    PlaybookExecutionStartSchema,
    PlaybookStepCreateSchema,
)
from app.modules.interventions.playbook_service import PlaybookService


def test_create_playbook_rejects_duplicate_step_order() -> None:
    db = MagicMock()
    db.scalar.return_value = None
    service = PlaybookService(db)

    payload = PlaybookCreateSchema(
        name="Academic Guard Test",
        steps=[
            PlaybookStepCreateSchema(step_order=0, title="Step A", action_type="note"),
            PlaybookStepCreateSchema(step_order=0, title="Step B", action_type="note"),
        ],
    )

    with pytest.raises(DomainValidationError, match="duplicate step_order"):
        service.create_playbook(tenant_id=1, actor="owner@example.com", payload=payload)


def test_start_execution_rejects_student_fanout_limit() -> None:
    db = MagicMock()
    playbook = SimpleNamespace(id=10, tenant_id=1, enabled=True, steps=[])
    db.scalar.side_effect = [playbook, 3]

    service = PlaybookService(db)
    payload = PlaybookExecutionStartSchema(
        playbook_id=10,
        student_profile_id=777,
        triggered_by=PlaybookTriggerType.AUTO,
    )

    with pytest.raises(
        DomainValidationError,
        match="Too many active playbook executions for this student profile",
    ):
        service.start_execution(tenant_id=1, actor="svc:auto", payload=payload)
