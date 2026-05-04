"""Phase CIV — faculty service hardening tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.faculty import service as faculty_service


def _make_entity(id_val: int = 1, **kwargs) -> dict:
    return {"id": id_val, **kwargs}


# ---------------------------------------------------------------------------
# 1. create_faculty_member — records outcome + metric
# ---------------------------------------------------------------------------
def test_create_faculty_member_records_outcome_and_metric() -> None:
    payload = {"faculty_id": "F001", "status": "active", "department": "CS"}
    created = _make_entity(id_val=101, faculty_id="F001", status="active", department="CS")

    with (
        patch("app.modules.faculty.service.create_entity_for_tenant", return_value=created) as mock_create,
        patch("app.modules.faculty.service.record_usage_event") as mock_metric,
        patch("app.modules.faculty.service._record_outcome") as mock_outcome,
    ):
        result = faculty_service.create_faculty_member(payload, tenant_id=7)

    assert result == created
    mock_create.assert_called_once_with("faculty", payload, 7)
    mock_outcome.assert_called_once_with(101, "faculty_member_created", "system")
    mock_metric.assert_called_once_with(tenant_id=7, metric="faculty_members_created", value=1)


# ---------------------------------------------------------------------------
# 2. create_faculty_contract — records outcome + metric (positional tenant API)
# ---------------------------------------------------------------------------
def test_create_faculty_contract_records_outcome_and_metric() -> None:
    payload = {"faculty_id": "F002", "status": "active"}
    created = _make_entity(id_val=201, faculty_id="F002", status="active")

    faculty_row = {"faculty_id": "F002", "status": "active"}

    def fake_list(entity_name: str, tenant_id: int):
        if entity_name == "faculty":
            return [faculty_row]
        return []

    with (
        patch("app.modules.faculty.service.list_entities_for_tenant", side_effect=fake_list),
        patch("app.modules.faculty.service.create_entity_for_tenant", return_value=created),
        patch("app.modules.faculty.service.record_usage_event") as mock_metric,
        patch("app.modules.faculty.service._record_outcome") as mock_outcome,
    ):
        result = faculty_service.create_faculty_contract(payload, tenant_id=7)

    assert result == created
    mock_outcome.assert_called_once_with(201, "faculty_contract_created", "system")
    mock_metric.assert_called_once_with(tenant_id=7, metric="faculty_contracts_created", value=1)


# ---------------------------------------------------------------------------
# 3. _record_outcome — fail-safe: brain_core down must not propagate
# ---------------------------------------------------------------------------
def test_record_outcome_fail_safe() -> None:
    brain_core_mock = MagicMock()
    brain_core_mock.record_dispatch_outcome.side_effect = RuntimeError("brain_core down")

    with patch.dict("sys.modules", {"app.modules.brain_core": MagicMock(service=brain_core_mock)}):
        # Must not raise
        faculty_service._record_outcome(999, "faculty_member_created", "admin@uni.edu")


# ---------------------------------------------------------------------------
# 4. create_faculty_contract guard — faculty not found raises ValueError
# ---------------------------------------------------------------------------
def test_create_faculty_contract_guard_faculty_not_found() -> None:
    payload = {"faculty_id": "GHOST", "status": "active"}

    with patch("app.modules.faculty.service.list_entities_for_tenant", return_value=[]):
        with pytest.raises(ValueError, match="faculty not found"):
            faculty_service.create_faculty_contract(payload, tenant_id=5)
