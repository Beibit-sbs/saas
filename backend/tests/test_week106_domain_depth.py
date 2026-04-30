"""W106 — Dining: Order Menu Status Guard (cross-entity: dining_orders × dining_menus).

Business invariant: A dining order may only be placed against a menu that
exists AND has status 'active' or 'published'.

Bad outcomes if guard is missing:
  - Kitchen receives requests for unavailable / archived dishes
  - Financial transactions with no corresponding supply record
  - Brain Core Dining KPIs corrupted (phantom revenue, false utilisation)
  - Student orders unresolvable → unresolved complaint backlog

Guard location: dining/service.py :: create_dining_order() → _check_menu_is_orderable()
                BEFORE create_entity_for_tenant("dining_orders", ...)
"""
from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Module under test
# ---------------------------------------------------------------------------
SERVICE_MODULE = "app.modules.dining.service"


def _svc():
    """Return freshly imported service module."""
    return importlib.import_module(SERVICE_MODULE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_menu(menu_code: str, status: str, **extra) -> dict:
    return {"id": 1, "menu_code": menu_code, "status": status, **extra}


def _order_payload(menu_code: str = "MENU-001") -> dict:
    return {"menu_code": menu_code, "item": "burger", "quantity": 1}


TENANT = 42

# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

class TestW106Constants:
    def test_orderable_menu_statuses_constants_exist(self):
        svc = _svc()
        assert hasattr(svc, "_ORDERABLE_MENU_STATUSES")

    def test_orderable_menu_statuses_is_frozenset(self):
        svc = _svc()
        assert isinstance(svc._ORDERABLE_MENU_STATUSES, frozenset)

    def test_orderable_menu_statuses_contains_active(self):
        svc = _svc()
        assert "active" in svc._ORDERABLE_MENU_STATUSES

    def test_orderable_menu_statuses_contains_published(self):
        svc = _svc()
        assert "published" in svc._ORDERABLE_MENU_STATUSES

    def test_orderable_menu_statuses_does_not_contain_closed(self):
        svc = _svc()
        assert "closed" not in svc._ORDERABLE_MENU_STATUSES

    def test_orderable_menu_statuses_does_not_contain_archived(self):
        svc = _svc()
        assert "archived" not in svc._ORDERABLE_MENU_STATUSES


# ---------------------------------------------------------------------------
# 2. Guard unit tests (_check_menu_is_orderable)
# ---------------------------------------------------------------------------

class TestCheckMenuIsOrderable:
    def _call(self, menus: list[dict], menu_code: str = "MENU-001"):
        from app.modules.dining.service import (
            _check_menu_is_orderable,
        )
        # DomainValidationError may not be re-exported; import from canonical path

        with patch(
            "app.modules.dining.service.list_entities_for_tenant",
            return_value=menus,
        ):
            return _check_menu_is_orderable(tenant_id=TENANT, menu_code=menu_code)

    def test_passes_active_menu_exists(self):
        """Guard passes: menu exists with status 'active'."""
        self._call([_make_menu("MENU-001", "active")])

    def test_passes_published_menu_exists(self):
        """Guard passes: menu exists with status 'published'."""
        self._call([_make_menu("MENU-001", "published")])

    def test_passes_other_menu_exists_different_code(self):
        """Guard passes: another menu exists but different code — all are active."""
        self._call(
            [
                _make_menu("MENU-999", "active"),
                _make_menu("MENU-001", "active"),
            ]
        )

    def test_blocks_menu_not_found(self):
        """Guard blocks: no menu with the given code exists."""
        from app.core.module_helpers.service_validation import DomainValidationError
        with patch("app.modules.dining.service.list_entities_for_tenant", return_value=[]):
            from app.modules.dining.service import _check_menu_is_orderable
            with pytest.raises(DomainValidationError):
                _check_menu_is_orderable(tenant_id=TENANT, menu_code="MISSING-001")

    def test_blocks_closed_status(self):
        """Guard blocks: menu exists but status='closed'."""
        from app.core.module_helpers.service_validation import DomainValidationError
        with patch(
            "app.modules.dining.service.list_entities_for_tenant",
            return_value=[_make_menu("MENU-001", "closed")],
        ):
            from app.modules.dining.service import _check_menu_is_orderable
            with pytest.raises(DomainValidationError):
                _check_menu_is_orderable(tenant_id=TENANT, menu_code="MENU-001")

    def test_blocks_archived_status(self):
        """Guard blocks: menu exists but status='archived'."""
        from app.core.module_helpers.service_validation import DomainValidationError
        with patch(
            "app.modules.dining.service.list_entities_for_tenant",
            return_value=[_make_menu("MENU-001", "archived")],
        ):
            from app.modules.dining.service import _check_menu_is_orderable
            with pytest.raises(DomainValidationError):
                _check_menu_is_orderable(tenant_id=TENANT, menu_code="MENU-001")

    def test_blocks_draft_status(self):
        """Guard blocks: menu exists but status='draft'."""
        from app.core.module_helpers.service_validation import DomainValidationError
        with patch(
            "app.modules.dining.service.list_entities_for_tenant",
            return_value=[_make_menu("MENU-001", "draft")],
        ):
            from app.modules.dining.service import _check_menu_is_orderable
            with pytest.raises(DomainValidationError):
                _check_menu_is_orderable(tenant_id=TENANT, menu_code="MENU-001")

    def test_blocks_suspended_status(self):
        """Guard blocks: menu exists but status='suspended'."""
        from app.core.module_helpers.service_validation import DomainValidationError
        with patch(
            "app.modules.dining.service.list_entities_for_tenant",
            return_value=[_make_menu("MENU-001", "suspended")],
        ):
            from app.modules.dining.service import _check_menu_is_orderable
            with pytest.raises(DomainValidationError):
                _check_menu_is_orderable(tenant_id=TENANT, menu_code="MENU-001")

    def test_menu_code_match_is_case_insensitive(self):
        """Guard: menu_code matching is case-insensitive."""
        # Payload sends 'menu-001', DB has 'MENU-001' status=active → should pass
        self._call([_make_menu("MENU-001", "active")], menu_code="menu-001")

    def test_fail_closed_lookup_error_raises_domain_error(self):
        """FAIL-CLOSED: if list_entities_for_tenant raises, guard raises DomainValidationError."""
        from app.core.module_helpers.service_validation import DomainValidationError
        with patch(
            "app.modules.dining.service.list_entities_for_tenant",
            side_effect=RuntimeError("db timeout"),
        ):
            from app.modules.dining.service import _check_menu_is_orderable
            with pytest.raises(DomainValidationError):
                _check_menu_is_orderable(tenant_id=TENANT, menu_code="MENU-001")

    def test_error_message_contains_menu_code_on_not_found(self):
        """Error message must reference the menu_code for debuggability."""
        from app.core.module_helpers.service_validation import DomainValidationError
        with patch("app.modules.dining.service.list_entities_for_tenant", return_value=[]):
            from app.modules.dining.service import _check_menu_is_orderable
            with pytest.raises(DomainValidationError, match="MENU-XYZ"):
                _check_menu_is_orderable(tenant_id=TENANT, menu_code="MENU-XYZ")

    def test_error_message_contains_status_on_wrong_status(self):
        """Error message must state the actual menu status for debuggability."""
        from app.core.module_helpers.service_validation import DomainValidationError
        with patch(
            "app.modules.dining.service.list_entities_for_tenant",
            return_value=[_make_menu("MENU-001", "archived")],
        ):
            from app.modules.dining.service import _check_menu_is_orderable
            with pytest.raises(DomainValidationError, match="archived"):
                _check_menu_is_orderable(tenant_id=TENANT, menu_code="MENU-001")


# ---------------------------------------------------------------------------
# 3. Integration: create_dining_order wires the guard
# ---------------------------------------------------------------------------

class TestCreateDiningOrderGuard:
    def _run(
        self,
        menus: list[dict],
        payload: dict | None = None,
        create_return: dict | None = None,
    ) -> tuple[object, MagicMock]:
        from app.modules.dining.service import create_dining_order

        _payload = payload or _order_payload()
        _create_ret = create_return or {"id": 99, **_payload}

        mock_create = MagicMock(return_value=_create_ret)
        with (
            patch("app.modules.dining.service.list_entities_for_tenant", return_value=menus),
            patch("app.modules.dining.service.create_entity_for_tenant", mock_create),
        ):
            result = create_dining_order(_payload, TENANT)
        return result, mock_create

    def test_order_allowed_active_menu(self):
        """create_dining_order succeeds with existing active menu."""
        result, mock_create = self._run([_make_menu("MENU-001", "active")])
        mock_create.assert_called_once()

    def test_order_allowed_published_menu(self):
        """create_dining_order succeeds with existing published menu."""
        result, mock_create = self._run([_make_menu("MENU-001", "published")])
        mock_create.assert_called_once()

    def test_order_blocked_closed_menu(self):
        """create_dining_order raises for closed menu — nothing is persisted."""
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.dining.service import create_dining_order

        mock_create = MagicMock()
        with (
            patch(
                "app.modules.dining.service.list_entities_for_tenant",
                return_value=[_make_menu("MENU-001", "closed")],
            ),
            patch("app.modules.dining.service.create_entity_for_tenant", mock_create),
        ):
            with pytest.raises(DomainValidationError):
                create_dining_order(_order_payload(), TENANT)

        mock_create.assert_not_called()

    def test_order_blocked_menu_not_found(self):
        """create_dining_order raises when menu_code not found — nothing is persisted."""
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.dining.service import create_dining_order

        mock_create = MagicMock()
        with (
            patch("app.modules.dining.service.list_entities_for_tenant", return_value=[]),
            patch("app.modules.dining.service.create_entity_for_tenant", mock_create),
        ):
            with pytest.raises(DomainValidationError):
                create_dining_order(_order_payload("GHOST-MENU"), TENANT)

        mock_create.assert_not_called()

    def test_guard_fires_before_persist(self):
        """Guard is invoked BEFORE create_entity_for_tenant — persist never called on block."""
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.dining.service import create_dining_order

        call_order: list[str] = []

        def fake_list(table, tid):
            call_order.append("list")
            return [_make_menu("MENU-001", "archived")]

        def fake_create(table, payload, tid):
            call_order.append("create")
            return payload

        with (
            patch("app.modules.dining.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.dining.service.create_entity_for_tenant", side_effect=fake_create),
        ):
            with pytest.raises(DomainValidationError):
                create_dining_order(_order_payload(), TENANT)

        assert "list" in call_order
        assert "create" not in call_order

    def test_no_menu_code_in_payload_skips_guard(self):
        """If menu_code is absent from payload, guard is skipped (no breakage)."""
        from app.modules.dining.service import create_dining_order

        mock_create = MagicMock(return_value={"id": 1})
        with (
            patch("app.modules.dining.service.list_entities_for_tenant", return_value=[]),
            patch("app.modules.dining.service.create_entity_for_tenant", mock_create),
        ):
            create_dining_order({"item": "burger"}, TENANT)

        mock_create.assert_called_once()
