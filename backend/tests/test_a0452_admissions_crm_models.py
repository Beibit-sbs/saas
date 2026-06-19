from __future__ import annotations

import pytest

from app.modules.admissions_crm import models, permissions


def test_table_inventory_is_exact_12() -> None:
    assert len(models.TABLE_NAMES) == 12


def test_permission_inventory_is_exact_6() -> None:
    assert permissions.ADMISSIONS_CRM_PERMISSION_COUNT == 6
    assert len(permissions.ALL_PERMISSIONS) == 6


def test_module_constants_match_contract() -> None:
    assert models.MODULE_NAME == "admissions_crm"
    assert models.API_PREFIX == "/api/admin/admissions-crm"
    assert models.RUNTIME_MODE == "HUMAN_REVIEW_DECISION_SUPPORT_ONLY"
    assert models.EXPECTED_TABLE_COUNT == 12
    assert models.EXPECTED_ROUTE_COUNT == 12
    assert models.EXPECTED_PERMISSION_COUNT == 6
    assert models.TABLE_PREFIX == "acrm_"


@pytest.mark.parametrize("name", sorted(models.TABLE_NAMES))
def test_all_table_names_have_acrm_prefix(name: str) -> None:
    assert name.startswith("acrm_")


@pytest.mark.parametrize("permission", sorted(permissions.ALL_PERMISSIONS))
def test_permissions_are_namespaced(permission: str) -> None:
    assert permission.startswith("admin.admissions_crm.")


def test_safety_flags_are_fail_closed() -> None:
    assert models.FAKE_METRICS is False
    assert models.PROVIDER_LIVE_ENABLED is False
    assert models.AUTONOMOUS_DECISION_ENABLED is False
    assert models.HIDDEN_SCORE_PRESENT is False
    assert models.HUMAN_REVIEW_REQUIRED is True
