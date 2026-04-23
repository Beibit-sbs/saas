"""I5 — Ministry KPI Contract v1 hardening tests.

Covers:
  I5.1  Contract constants are present and correct types/values.
  I5.2  Whitelist contains the expected aggregate metric keys.
  I5.3  No PII field keys appear in the whitelist.
  I5.4  Non-whitelisted KPIs are excluded from the result.
  I5.5  Values strictly below suppression threshold yield the suppressed sentinel.
  I5.6  Values at or above the threshold are passed through unchanged.
  I5.7  An audit entry is appended on every call (including empty input).
  I5.8  Audit entries carry tenant_id, contract_version, and keys_requested.
  I5.9  Multiple calls produce independent audit entries.
  I5.10 Mixed input (whitelisted + non-whitelisted, suppressed + above threshold).
  I5.11 All-whitelisted, all-above-threshold input round-trips correctly.
"""
from __future__ import annotations

import pytest

from app.platform.kpi.ministry_kpi import (
    MINISTRY_KPI_AUDIT_ACTION,
    MINISTRY_KPI_CONTRACT_VERSION,
    MINISTRY_KPI_REQUIRED_ROLE,
    MINISTRY_KPI_SUPPRESSED_SENTINEL,
    MINISTRY_KPI_SUPPRESSION_THRESHOLD,
    MINISTRY_KPI_WHITELIST,
    apply_ministry_kpi_contract,
)

# ---------------------------------------------------------------------------
# I5.1  Contract constants — type and value checks
# ---------------------------------------------------------------------------


def test_contract_version_is_v1() -> None:
    assert MINISTRY_KPI_CONTRACT_VERSION == "v1"


def test_suppression_threshold_is_positive_int() -> None:
    assert isinstance(MINISTRY_KPI_SUPPRESSION_THRESHOLD, int)
    assert MINISTRY_KPI_SUPPRESSION_THRESHOLD > 0


def test_suppressed_sentinel_value() -> None:
    assert MINISTRY_KPI_SUPPRESSED_SENTINEL == "suppressed"


def test_required_role_is_ministry_kpi_read() -> None:
    assert MINISTRY_KPI_REQUIRED_ROLE == "ministry.kpi.read"


def test_audit_action_constant() -> None:
    assert MINISTRY_KPI_AUDIT_ACTION == "ministry.kpi.read"


# ---------------------------------------------------------------------------
# I5.2  Whitelist contains expected aggregate KPI keys
# ---------------------------------------------------------------------------


def test_whitelist_contains_total_students() -> None:
    assert "total_students" in MINISTRY_KPI_WHITELIST


def test_whitelist_contains_total_enrollments() -> None:
    assert "total_enrollments" in MINISTRY_KPI_WHITELIST


def test_whitelist_contains_total_grades_submitted() -> None:
    assert "total_grades_submitted" in MINISTRY_KPI_WHITELIST


def test_whitelist_is_non_empty_frozenset() -> None:
    assert isinstance(MINISTRY_KPI_WHITELIST, frozenset)
    assert len(MINISTRY_KPI_WHITELIST) > 0


# ---------------------------------------------------------------------------
# I5.3  No PII field keys in whitelist
# ---------------------------------------------------------------------------

_PII_FIELDS: frozenset[str] = frozenset(
    {
        "student_name",
        "email",
        "phone",
        "address",
        "student_id",
        "national_id",
        "passport_number",
        "date_of_birth",
        "gender",
        "ethnicity",
        "full_name",
        "first_name",
        "last_name",
    }
)


def test_whitelist_contains_no_pii_fields() -> None:
    overlap = MINISTRY_KPI_WHITELIST & _PII_FIELDS
    assert overlap == frozenset(), f"PII fields found in whitelist: {overlap}"


# ---------------------------------------------------------------------------
# I5.4  Non-whitelisted KPIs are excluded from the result
# ---------------------------------------------------------------------------


def test_non_whitelisted_key_excluded() -> None:
    audit_log: list = []
    result = apply_ministry_kpi_contract(
        kpis={"total_students": 100, "total_active_subscriptions": 50},
        tenant_id=1,
        audit_log=audit_log,
    )
    assert "total_active_subscriptions" not in result


def test_platform_internal_key_excluded() -> None:
    audit_log: list = []
    result = apply_ministry_kpi_contract(
        kpis={"total_failed_jobs": 3, "analytics_kpi_reads_total": 999},
        tenant_id=1,
        audit_log=audit_log,
    )
    assert "total_failed_jobs" not in result
    assert "analytics_kpi_reads_total" not in result


def test_result_keys_are_subset_of_whitelist() -> None:
    audit_log: list = []
    result = apply_ministry_kpi_contract(
        kpis={
            "total_students": 100,
            "total_enrollments": 200,
            "total_failed_jobs": 3,
            "some_random_metric": 999,
            "analytics_reads_total": 42,
        },
        tenant_id=1,
        audit_log=audit_log,
    )
    for key in result:
        assert key in MINISTRY_KPI_WHITELIST, f"Non-whitelisted key in result: {key}"


# ---------------------------------------------------------------------------
# I5.5  Suppression threshold — values below threshold yield sentinel
# ---------------------------------------------------------------------------


def test_zero_value_is_suppressed() -> None:
    audit_log: list = []
    result = apply_ministry_kpi_contract(
        kpis={"total_students": 0},
        tenant_id=1,
        audit_log=audit_log,
    )
    assert result["total_students"] == MINISTRY_KPI_SUPPRESSED_SENTINEL


def test_value_one_below_threshold_is_suppressed() -> None:
    audit_log: list = []
    below = MINISTRY_KPI_SUPPRESSION_THRESHOLD - 1
    result = apply_ministry_kpi_contract(
        kpis={"total_students": below},
        tenant_id=1,
        audit_log=audit_log,
    )
    assert result["total_students"] == MINISTRY_KPI_SUPPRESSED_SENTINEL


def test_value_one_is_suppressed_when_threshold_gt_one() -> None:
    if MINISTRY_KPI_SUPPRESSION_THRESHOLD > 1:
        audit_log: list = []
        result = apply_ministry_kpi_contract(
            kpis={"total_enrollments": 1},
            tenant_id=1,
            audit_log=audit_log,
        )
        assert result["total_enrollments"] == MINISTRY_KPI_SUPPRESSED_SENTINEL


# ---------------------------------------------------------------------------
# I5.6  Values at/above threshold pass through unchanged
# ---------------------------------------------------------------------------


def test_value_at_threshold_passes_through() -> None:
    audit_log: list = []
    at_threshold = MINISTRY_KPI_SUPPRESSION_THRESHOLD
    result = apply_ministry_kpi_contract(
        kpis={"total_students": at_threshold},
        tenant_id=1,
        audit_log=audit_log,
    )
    assert result["total_students"] == at_threshold


def test_value_well_above_threshold_passes_through() -> None:
    audit_log: list = []
    result = apply_ministry_kpi_contract(
        kpis={"total_students": 10_000},
        tenant_id=1,
        audit_log=audit_log,
    )
    assert result["total_students"] == 10_000


# ---------------------------------------------------------------------------
# I5.7  Audit entry always appended (including empty input)
# ---------------------------------------------------------------------------


def test_audit_entry_appended_on_every_call() -> None:
    audit_log: list = []
    apply_ministry_kpi_contract(kpis={"total_students": 100}, tenant_id=42, audit_log=audit_log)
    assert len(audit_log) == 1


def test_audit_entry_appended_for_empty_input() -> None:
    audit_log: list = []
    result = apply_ministry_kpi_contract(kpis={}, tenant_id=99, audit_log=audit_log)
    assert result == {}
    assert len(audit_log) == 1


# ---------------------------------------------------------------------------
# I5.8  Audit entries carry required fields
# ---------------------------------------------------------------------------


def test_audit_entry_action_field() -> None:
    audit_log: list = []
    apply_ministry_kpi_contract(kpis={"total_students": 100}, tenant_id=42, audit_log=audit_log)
    assert audit_log[0]["action"] == MINISTRY_KPI_AUDIT_ACTION


def test_audit_entry_tenant_id_field() -> None:
    audit_log: list = []
    apply_ministry_kpi_contract(kpis={"total_students": 100}, tenant_id=42, audit_log=audit_log)
    assert audit_log[0]["tenant_id"] == 42


def test_audit_entry_contract_version_field() -> None:
    audit_log: list = []
    apply_ministry_kpi_contract(kpis={"total_students": 100}, tenant_id=1, audit_log=audit_log)
    assert audit_log[0]["contract_version"] == MINISTRY_KPI_CONTRACT_VERSION


def test_audit_entry_keys_requested_field() -> None:
    audit_log: list = []
    apply_ministry_kpi_contract(
        kpis={"total_students": 100, "total_enrollments": 50},
        tenant_id=1,
        audit_log=audit_log,
    )
    assert set(audit_log[0]["keys_requested"]) == {"total_students", "total_enrollments"}


# ---------------------------------------------------------------------------
# I5.9  Multiple calls produce independent audit entries
# ---------------------------------------------------------------------------


def test_two_calls_produce_two_audit_entries() -> None:
    audit_log: list = []
    apply_ministry_kpi_contract(kpis={"total_students": 100}, tenant_id=1, audit_log=audit_log)
    apply_ministry_kpi_contract(kpis={"total_enrollments": 200}, tenant_id=2, audit_log=audit_log)
    assert len(audit_log) == 2
    assert audit_log[0]["tenant_id"] == 1
    assert audit_log[1]["tenant_id"] == 2


def test_three_calls_produce_three_audit_entries() -> None:
    audit_log: list = []
    for i in range(3):
        apply_ministry_kpi_contract(kpis={"total_students": 10 + i}, tenant_id=i, audit_log=audit_log)
    assert len(audit_log) == 3


# ---------------------------------------------------------------------------
# I5.10  Mixed input (whitelisted + non-whitelisted, suppressed + above threshold)
# ---------------------------------------------------------------------------


def test_mixed_input_correct_filtering_and_suppression() -> None:
    audit_log: list = []
    result = apply_ministry_kpi_contract(
        kpis={
            "total_students": 1000,  # whitelisted, above threshold → pass
            "total_enrollments": 2,  # whitelisted, below threshold → suppressed
            "total_active_subscriptions": 999,  # non-whitelisted → excluded
        },
        tenant_id=5,
        audit_log=audit_log,
    )
    assert result["total_students"] == 1000
    assert result["total_enrollments"] == MINISTRY_KPI_SUPPRESSED_SENTINEL
    assert "total_active_subscriptions" not in result
    assert len(audit_log) == 1


# ---------------------------------------------------------------------------
# I5.11  All-whitelisted, all-above-threshold round-trip
# ---------------------------------------------------------------------------


def test_all_whitelisted_above_threshold_roundtrip() -> None:
    audit_log: list = []
    input_kpis = {
        "total_students": 500,
        "total_enrollments": 1000,
        "total_grades_submitted": 3000,
    }
    result = apply_ministry_kpi_contract(
        kpis=input_kpis,
        tenant_id=3,
        audit_log=audit_log,
    )
    assert result == input_kpis
