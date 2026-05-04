"""Phase CV — programs service hardening tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.programs import service as programs_service


def _make_entity(id_val: int = 1, **kwargs) -> dict:
    return {"id": id_val, **kwargs}


# ---------------------------------------------------------------------------
# 1. create_program — records outcome + metric
# ---------------------------------------------------------------------------
def test_create_program_records_outcome_and_metric() -> None:
    payload = {"program_code": "CS-BSC", "degree_type": "bachelor", "status": "draft"}
    created = _make_entity(id_val=301, program_code="CS-BSC", degree_type="bachelor", status="draft")

    def fake_list(entity_name: str, tenant_id: int):
        return []

    with (
        patch("app.modules.programs.service.list_entities_for_tenant", side_effect=fake_list),
        patch("app.modules.programs.service.create_entity_for_tenant", return_value=created),
        patch("app.modules.programs.service.record_usage_event") as mock_metric,
        patch("app.modules.programs.service._record_outcome") as mock_outcome,
    ):
        result = programs_service.create_program(payload, tenant_id=9)

    assert result == created
    mock_outcome.assert_called_once_with(301, "program_created", "system")
    mock_metric.assert_called_once_with(tenant_id=9, metric="programs_created", value=1)


# ---------------------------------------------------------------------------
# 2. update_program — records outcome + metric (non-activation status)
# ---------------------------------------------------------------------------
def test_update_program_records_outcome_and_metric() -> None:
    payload = {"status": "draft", "program_code": "CS-BSC", "degree_type": "bachelor"}
    updated = _make_entity(id_val=401, **payload)

    with (
        patch("app.modules.programs.service.update_entity_for_tenant", return_value=updated),
        patch("app.modules.programs.service.record_usage_event") as mock_metric,
        patch("app.modules.programs.service._record_outcome") as mock_outcome,
    ):
        result = programs_service.update_program(401, payload, tenant_id=9)

    assert result == updated
    mock_outcome.assert_called_once_with(401, "program_updated", "system")
    mock_metric.assert_called_once_with(tenant_id=9, metric="programs_updated", value=1)


# ---------------------------------------------------------------------------
# 3. _record_outcome — fail-safe: brain_core down must not propagate
# ---------------------------------------------------------------------------
def test_record_outcome_fail_safe() -> None:
    brain_core_mock = MagicMock()
    brain_core_mock.record_dispatch_outcome.side_effect = RuntimeError("brain_core down")

    with patch.dict("sys.modules", {"app.modules.brain_core": MagicMock(service=brain_core_mock)}):
        # Must not raise
        programs_service._record_outcome(999, "program_created", "admin@uni.edu")


# ---------------------------------------------------------------------------
# 4. create_program guard — degree_type cap reached raises ValueError
# ---------------------------------------------------------------------------
def test_create_program_cap_guard_raises() -> None:
    # Fill up to cap (50 active bachelor programs)
    active_programs = [
        {"status": "active", "degree_type": "bachelor"} for _ in range(50)
    ]
    payload = {"program_code": "NEW-BSC", "degree_type": "bachelor", "status": "active"}

    with patch("app.modules.programs.service.list_entities_for_tenant", return_value=active_programs):
        with pytest.raises(ValueError, match="cap"):
            programs_service.create_program(payload, tenant_id=5)
