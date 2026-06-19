from __future__ import annotations

from app.modules.student_services_support import models, permissions


def test_table_inventory_is_exact_12() -> None:
    assert len(models.TABLE_NAMES) == 12


def test_permission_inventory_is_exact_6() -> None:
    assert permissions.STUDENT_SERVICES_SUPPORT_PERMISSION_COUNT == 6
    assert len(permissions.ALL_PERMISSIONS) == 6


def test_module_constants_match_contract() -> None:
    assert models.MODULE_NAME == "student_services_support"
    assert models.API_PREFIX == "/api/admin/student-services"
    assert models.RUNTIME_MODE == "METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY"
    assert models.EXPECTED_TABLE_COUNT == 12
    assert models.EXPECTED_ROUTE_COUNT == 21
    assert models.EXPECTED_PERMISSION_COUNT == 6
    assert models.TABLE_PREFIX == "sss_"


def test_all_table_names_have_sss_prefix() -> None:
    assert all(name.startswith("sss_") for name in models.TABLE_NAMES)


def test_safety_flags_are_fail_closed() -> None:
    assert models.FAKE_METRICS is False
    assert models.PROVIDER_LIVE_ENABLED is False
    assert models.AUTONOMOUS_DECISION_ENABLED is False
    assert models.HIDDEN_SCORE_PRESENT is False
    assert models.HUMAN_REVIEW_REQUIRED is True
