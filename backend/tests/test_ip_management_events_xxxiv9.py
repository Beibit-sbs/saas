"""XXXIV.9 — ip_management: 10-step loop event hardening tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.ip_management import service as svc

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ACTIVE_CONTRACT = [{"faculty_id": "FAC-001", "status": "active"}]

_DRAFT_PAYLOAD: dict[str, object] = {
    "ip_type": "patent",
    "status": "draft",
    "commercialization_status": "none",
    "inventor_ids": None,
}

_FILED_PAYLOAD: dict[str, object] = {
    "ip_type": "patent",
    "status": "filed",
    "commercialization_status": "none",
    "inventor_ids": "FAC-001",
}

_GRANTED_PAYLOAD: dict[str, object] = {
    "ip_type": "patent",
    "status": "granted",
    "commercialization_status": "none",
    "inventor_ids": "FAC-001",
}

_LICENSED_PAYLOAD: dict[str, object] = {
    "ip_type": "patent",
    "status": "draft",
    "commercialization_status": "licensed",
    "inventor_ids": "FAC-001",
}


def _make_list(entity_type: str, tenant_id: int) -> list[dict]:
    if entity_type == "faculty_contracts":
        return _ACTIVE_CONTRACT
    return []


# ---------------------------------------------------------------------------
# 1. create_ip_asset (draft) fires asset.created
# ---------------------------------------------------------------------------

def test_create_ip_asset_draft_publishes_asset_created() -> None:
    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        return {**payload, "id": 1}

    with (
        patch("app.modules.ip_management.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.ip_management.service.list_entities_for_tenant", side_effect=_make_list),
        patch("app.modules.ip_management.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        result = svc.create_ip_asset(_DRAFT_PAYLOAD.copy(), tenant_id=1)

    assert result["id"] == 1
    event_types = [c.args[0] for c in mock_pub.publish_event.call_args_list]
    assert "ip_management.asset.created" in event_types


# ---------------------------------------------------------------------------
# 2. filed status fires asset.filed
# ---------------------------------------------------------------------------

def test_create_ip_asset_filed_fires_filed_event() -> None:
    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        return {**payload, "id": 2}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "faculty_contracts":
            return _ACTIVE_CONTRACT
        return []

    with (
        patch("app.modules.ip_management.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.ip_management.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.ip_management.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        svc.create_ip_asset(_FILED_PAYLOAD.copy(), tenant_id=1)

    event_types = [c.args[0] for c in mock_pub.publish_event.call_args_list]
    assert "ip_management.asset.filed" in event_types
    assert "ip_management.asset.created" in event_types


# ---------------------------------------------------------------------------
# 3. granted status fires asset.granted
# ---------------------------------------------------------------------------

def test_create_ip_asset_granted_fires_granted_event() -> None:
    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        return {**payload, "id": 3}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "faculty_contracts":
            return _ACTIVE_CONTRACT
        return []

    with (
        patch("app.modules.ip_management.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.ip_management.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.ip_management.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        svc.create_ip_asset(_GRANTED_PAYLOAD.copy(), tenant_id=1)

    event_types = [c.args[0] for c in mock_pub.publish_event.call_args_list]
    assert "ip_management.asset.granted" in event_types


# ---------------------------------------------------------------------------
# 4. licensed commercialization fires asset.licensed
# ---------------------------------------------------------------------------

def test_create_ip_asset_licensed_fires_licensed_event() -> None:
    created: list[str] = []

    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        created.append(entity_type)
        return {**payload, "id": 4}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "faculty_contracts":
            return _ACTIVE_CONTRACT
        return []

    with (
        patch("app.modules.ip_management.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.ip_management.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.ip_management.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        svc.create_ip_asset(_LICENSED_PAYLOAD.copy(), tenant_id=1)

    event_types = [c.args[0] for c in mock_pub.publish_event.call_args_list]
    assert "ip_management.asset.licensed" in event_types


# ---------------------------------------------------------------------------
# 5. Guard blocks inventor with no active contract for filed asset
# ---------------------------------------------------------------------------

def test_create_ip_asset_guard_blocks_no_active_contract() -> None:
    inactive = [{"faculty_id": "FAC-001", "status": "terminated"}]

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "faculty_contracts":
            return inactive
        return []

    with (
        patch("app.modules.ip_management.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.ip_management.service.create_entity_for_tenant"),
        patch("app.modules.ip_management.service.EventPublisher"),
    ):
        with pytest.raises(DomainValidationError):
            svc.create_ip_asset(_FILED_PAYLOAD.copy(), tenant_id=1)


# ---------------------------------------------------------------------------
# 6. create_ip_asset creates action log entity
# ---------------------------------------------------------------------------

def test_create_ip_asset_creates_action_log() -> None:
    created_entities: list[str] = []

    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        created_entities.append(entity_type)
        return {**payload, "id": 5}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "faculty_contracts":
            return _ACTIVE_CONTRACT
        return []

    with (
        patch("app.modules.ip_management.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.ip_management.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.ip_management.service.EventPublisher"),
    ):
        svc.create_ip_asset(_FILED_PAYLOAD.copy(), tenant_id=1)

    assert "ip_asset_action_logs" in created_entities


# ---------------------------------------------------------------------------
# 7. EventPublisher failure does not block asset creation
# ---------------------------------------------------------------------------

def test_create_ip_asset_survives_event_publisher_failure() -> None:
    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        return {**payload, "id": 99}

    with (
        patch("app.modules.ip_management.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.ip_management.service.list_entities_for_tenant", side_effect=_make_list),
        patch("app.modules.ip_management.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_pub.publish_event.side_effect = RuntimeError("broker down")
        mock_cls.return_value = mock_pub

        result = svc.create_ip_asset(_DRAFT_PAYLOAD.copy(), tenant_id=1)

    assert result["id"] == 99


# ---------------------------------------------------------------------------
# 8. draft asset with no inventors does not fire filed/granted events
# ---------------------------------------------------------------------------

def test_create_ip_asset_draft_no_status_events() -> None:
    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        return {**payload, "id": 10}

    with (
        patch("app.modules.ip_management.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.ip_management.service.list_entities_for_tenant", side_effect=_make_list),
        patch("app.modules.ip_management.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        svc.create_ip_asset(_DRAFT_PAYLOAD.copy(), tenant_id=1)

    event_types = [c.args[0] for c in mock_pub.publish_event.call_args_list]
    assert "ip_management.asset.filed" not in event_types
    assert "ip_management.asset.granted" not in event_types
    assert "ip_management.asset.licensed" not in event_types
    assert "ip_management.asset.created" in event_types
