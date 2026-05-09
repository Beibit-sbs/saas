"""A-024.5 targeted tests for university_core L3->L4 readiness visibility."""

from __future__ import annotations

import importlib
import inspect

import pytest

import app.main as main_module
from app.modules.university_core import service as university_core_service
from tests.conftest import ADMIN_HEADERS, client


@pytest.mark.parametrize("module_name", ["app.modules.university_core.service"])
def test_a0245_module_imports_successfully(module_name: str) -> None:
    importlib.import_module(module_name)


@pytest.mark.parametrize("tenant_id", [0, -1])
def test_a0245_tenant_id_required_and_positive(tenant_id: int) -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        university_core_service.build_university_core_readiness_summary(
            tenant_id=tenant_id,
            active_migrated_tables=[],
            planned_not_active_tables=[],
            test_only_or_stub_tables=[],
            fallback_classified_tables=[],
            unknown_tables=[],
            known_conditions=[],
            source_entity_type="university_core_table_validation",
            source_entity_id="validate_entity_tables_impl",
        )


def test_a0245_empty_classification_input_safe_unknown_summary() -> None:
    summary = university_core_service.build_university_core_readiness_summary(
        tenant_id=1,
        active_migrated_tables=[],
        planned_not_active_tables=[],
        test_only_or_stub_tables=[],
        fallback_classified_tables=[],
        unknown_tables=[],
        known_conditions=[],
        source_entity_type="university_core_table_validation",
        source_entity_id="validate_entity_tables_impl",
    )
    assert summary["readiness_status"] == "unknown"
    assert summary["data_quality_note"] is not None


def test_a0245_active_migrated_tables_count_as_active_coverage() -> None:
    summary = university_core_service.build_university_core_readiness_summary(
        tenant_id=1,
        active_migrated_tables=["university_students", "university_courses"],
        planned_not_active_tables=[],
        test_only_or_stub_tables=[],
        fallback_classified_tables=[],
        unknown_tables=[],
        known_conditions=[],
        source_entity_type="university_core_table_validation",
        source_entity_id="validate_entity_tables_impl",
    )
    assert summary["active_migrated_count"] == 2


def test_a0245_planned_tables_do_not_count_as_active() -> None:
    summary = university_core_service.build_university_core_readiness_summary(
        tenant_id=1,
        active_migrated_tables=["university_students"],
        planned_not_active_tables=["future_table"],
        test_only_or_stub_tables=[],
        fallback_classified_tables=[],
        unknown_tables=[],
        known_conditions=["planned_not_active table pending migration"],
        source_entity_type="university_core_table_validation",
        source_entity_id="validate_entity_tables_impl",
    )
    assert summary["active_migrated_count"] == 1
    assert summary["planned_not_active_count"] == 1


def test_a0245_test_only_tables_do_not_count_as_active() -> None:
    summary = university_core_service.build_university_core_readiness_summary(
        tenant_id=1,
        active_migrated_tables=["university_students"],
        planned_not_active_tables=[],
        test_only_or_stub_tables=["admissions_scorings"],
        fallback_classified_tables=[],
        unknown_tables=[],
        known_conditions=["test-only table absent in production db"],
        source_entity_type="university_core_table_validation",
        source_entity_id="validate_entity_tables_impl",
    )
    assert summary["active_migrated_count"] == 1
    assert summary["test_only_or_stub_count"] == 1


def test_a0245_fallback_classified_tables_do_not_count_as_active() -> None:
    summary = university_core_service.build_university_core_readiness_summary(
        tenant_id=1,
        active_migrated_tables=["university_students"],
        planned_not_active_tables=[],
        test_only_or_stub_tables=[],
        fallback_classified_tables=["legacy_fallback_table"],
        unknown_tables=[],
        known_conditions=["fallback table classification retained"],
        source_entity_type="university_core_table_validation",
        source_entity_id="validate_entity_tables_impl",
    )
    assert summary["active_migrated_count"] == 1
    assert summary["fallback_classified_count"] == 1


def test_a0245_unknown_tables_increase_risk_and_review_required() -> None:
    summary = university_core_service.build_university_core_readiness_summary(
        tenant_id=1,
        active_migrated_tables=["university_students"],
        planned_not_active_tables=[],
        test_only_or_stub_tables=[],
        fallback_classified_tables=[],
        unknown_tables=["required_but_missing_table"],
        known_conditions=["required table missing"],
        source_entity_type="university_core_table_validation",
        source_entity_id="validate_entity_tables_impl",
    )
    assert summary["risk_level"] in {"high", "critical"}
    assert summary["review_required"] is True


def test_a0245_known_conditions_preserved_in_summary() -> None:
    summary = university_core_service.build_university_core_readiness_summary(
        tenant_id=1,
        active_migrated_tables=["university_students"],
        planned_not_active_tables=["planned_table"],
        test_only_or_stub_tables=[],
        fallback_classified_tables=[],
        unknown_tables=[],
        known_conditions=["known condition: fallback profile"],
        source_entity_type="university_core_table_validation",
        source_entity_id="validate_entity_tables_impl",
    )
    assert "known condition: fallback profile" in summary["known_conditions"]


def test_a0245_readiness_status_is_deterministic() -> None:
    payload = dict(
        tenant_id=1,
        active_migrated_tables=["university_students"],
        planned_not_active_tables=["planned_table"],
        test_only_or_stub_tables=["admissions_scorings"],
        fallback_classified_tables=["legacy_fallback_table"],
        unknown_tables=[],
        known_conditions=["known condition"],
        source_entity_type="university_core_table_validation",
        source_entity_id="validate_entity_tables_impl",
    )
    assert university_core_service.build_university_core_readiness_summary(**payload) == (
        university_core_service.build_university_core_readiness_summary(**payload)
    )


def test_a0245_evidence_lineage_is_deterministic() -> None:
    one = university_core_service.build_university_core_evidence_item(
        classification="active_migrated",
        table_name="university_students",
        source_entity_type="validation",
        source_entity_id="validate_entity_tables_impl",
        source_report="A-022.9",
    )
    two = university_core_service.build_university_core_evidence_item(
        classification="active_migrated",
        table_name="university_students",
        source_entity_type="validation",
        source_entity_id="validate_entity_tables_impl",
        source_report="A-022.9",
    )
    assert one == two


def test_a0245_no_fake_table_creation_flag_exists() -> None:
    summary = university_core_service.build_university_core_readiness_summary(
        tenant_id=1,
        active_migrated_tables=[],
        planned_not_active_tables=[],
        test_only_or_stub_tables=[],
        fallback_classified_tables=[],
        unknown_tables=[],
        known_conditions=[],
        source_entity_type="university_core_table_validation",
        source_entity_id="validate_entity_tables_impl",
    )
    assert summary["no_fake_table_creation"] is True


def test_a0245_no_fake_migration_flag_exists() -> None:
    summary = university_core_service.build_university_core_readiness_summary(
        tenant_id=1,
        active_migrated_tables=[],
        planned_not_active_tables=[],
        test_only_or_stub_tables=[],
        fallback_classified_tables=[],
        unknown_tables=[],
        known_conditions=[],
        source_entity_type="university_core_table_validation",
        source_entity_id="validate_entity_tables_impl",
    )
    assert summary["no_fake_migration"] is True


def test_a0245_no_fake_smoke_pass_flag_exists() -> None:
    summary = university_core_service.build_university_core_readiness_summary(
        tenant_id=1,
        active_migrated_tables=[],
        planned_not_active_tables=[],
        test_only_or_stub_tables=[],
        fallback_classified_tables=[],
        unknown_tables=[],
        known_conditions=[],
        source_entity_type="university_core_table_validation",
        source_entity_id="validate_entity_tables_impl",
    )
    assert summary["no_fake_smoke_pass"] is True


def test_a0245_no_level5_or_level6_claim_exists() -> None:
    summary = university_core_service.build_university_core_readiness_summary(
        tenant_id=1,
        active_migrated_tables=["university_students"],
        planned_not_active_tables=[],
        test_only_or_stub_tables=[],
        fallback_classified_tables=[],
        unknown_tables=[],
        known_conditions=[],
        source_entity_type="university_core_table_validation",
        source_entity_id="validate_entity_tables_impl",
    )
    text = str(summary).lower()
    assert "level 5" not in text
    assert "level 6" not in text


def test_a0245_no_fake_production_readiness_claim_exists() -> None:
    summary = university_core_service.build_university_core_readiness_summary(
        tenant_id=1,
        active_migrated_tables=[],
        planned_not_active_tables=["planned_table"],
        test_only_or_stub_tables=[],
        fallback_classified_tables=[],
        unknown_tables=[],
        known_conditions=["known condition"],
        source_entity_type="university_core_table_validation",
        source_entity_id="validate_entity_tables_impl",
    )
    text = str(summary).lower()
    assert "production complete" not in text
    assert "fully production" not in text


def test_a0245_visible_surface_exists_if_l4_is_claimed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "validate_entity_tables_impl",
        lambda: {
            "missing": [],
            "present": ["university_students"],
            "missing_fallback": ["planned_table"],
            "present_fallback": [],
        },
    )
    response = client.get("/api/admin/university-core/readiness", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["visible_surface"] == "/api/admin/university-core/readiness"


def test_a0245_readiness_api_route_returns_deterministic_tenant_safe_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "validate_entity_tables_impl",
        lambda: {
            "missing": ["required_table"],
            "present": ["university_students"],
            "missing_fallback": ["planned_table", "admissions_scorings"],
            "present_fallback": ["legacy_table"],
        },
    )
    response = client.get("/api/admin/university-core/readiness", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["tenant_id"] == 1
    assert payload["active_migrated_count"] == 1
    assert payload["unknown_count"] == 1
    assert payload["planned_not_active_count"] >= 1


def test_a0245_missing_tenant_context_fails_closed() -> None:
    with pytest.raises(ValueError, match="tenant_id must be a positive integer"):
        university_core_service.validate_university_core_tenant(0)


def test_a0245_api_payload_includes_classification_counts_and_known_conditions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "validate_entity_tables_impl",
        lambda: {
            "missing": ["required_table"],
            "present": ["university_students", "university_courses"],
            "missing_fallback": ["planned_table", "admissions_scorings"],
            "present_fallback": ["legacy_table"],
        },
    )
    response = client.get("/api/admin/university-core/readiness", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total_classified_count"] == (
        payload["active_migrated_count"]
        + payload["planned_not_active_count"]
        + payload["test_only_or_stub_count"]
        + payload["fallback_classified_count"]
        + payload["unknown_count"]
    )
    assert isinstance(payload["known_conditions"], list)


def test_a0245_no_module_count_expansion() -> None:
    assert not hasattr(university_core_service, "MODULE_COUNT")


def test_a0245_no_unrelated_module_mutation_from_contract() -> None:
    source = inspect.getsource(university_core_service).lower()
    for forbidden in ["create table", "alembic upgrade", "smoke gate pass"]:
        assert forbidden not in source
