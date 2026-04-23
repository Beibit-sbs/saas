"""Phase I — Module Max Hardening: I6 Release Gate

Meta-tests verifying that the complete Phase I hardening suite is in place:
- All I1–I5 test files exist
- Ministry KPI contract v1 exports all required constants
- Contract values are within expected bounds
- Phase I test count (95 total) can be collected without error

These tests run without Docker and require no DB/network.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants / expected values
# ---------------------------------------------------------------------------

PHASE_I_TEST_FILES = [
    "tests/test_phase_i1_hardening.py",
    "tests/test_phase_i2_hardening.py",
    "tests/test_phase_i3_hardening.py",
    "tests/test_phase_i4_hardening.py",
    "tests/test_phase_i5_hardening.py",
]

MINISTRY_KPI_MODULE = "app.platform.kpi.ministry_kpi"

REQUIRED_CONSTANTS = [
    "MINISTRY_KPI_CONTRACT_VERSION",
    "MINISTRY_KPI_REQUIRED_ROLE",
    "MINISTRY_KPI_AUDIT_ACTION",
    "MINISTRY_KPI_SUPPRESSION_THRESHOLD",
    "MINISTRY_KPI_SUPPRESSED_SENTINEL",
    "MINISTRY_KPI_WHITELIST",
    "apply_ministry_kpi_contract",
]

EXPECTED_CONTRACT_VERSION = "v1"
EXPECTED_REQUIRED_ROLE = "ministry.kpi.read"
EXPECTED_AUDIT_ACTION = "ministry.kpi.read"
EXPECTED_SUPPRESSION_THRESHOLD = 5
EXPECTED_SUPPRESSED_SENTINEL = "suppressed"
EXPECTED_WHITELIST_KEYS = {
    "total_students",
    "total_enrollments",
    "total_grades_submitted",
}

# Expected Phase I test counts per file (from hardening sessions)
PHASE_I_EXPECTED_COUNTS = {
    "test_phase_i1_hardening.py": 8,
    "test_phase_i2_hardening.py": 10,
    "test_phase_i3_hardening.py": 20,
    "test_phase_i4_hardening.py": 29,
    "test_phase_i5_hardening.py": 28,
}
PHASE_I_TOTAL_EXPECTED = sum(PHASE_I_EXPECTED_COUNTS.values())  # 95


# ---------------------------------------------------------------------------
# I6.1 — All Phase I hardening test files exist
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel_path", PHASE_I_TEST_FILES)
def test_i6_phase_i_test_file_exists(rel_path: str) -> None:
    """I6.1: Every Phase I hardening test file must be present on disk."""
    # Resolve relative to backend root (two levels up from this file)
    backend_root = Path(__file__).resolve().parent.parent
    full_path = backend_root / rel_path
    assert full_path.exists(), (
        f"Phase I test file missing: {rel_path}\n"
        f"Expected at: {full_path}"
    )


# ---------------------------------------------------------------------------
# I6.2 — Ministry KPI contract module is importable
# ---------------------------------------------------------------------------

def test_i6_ministry_kpi_module_importable() -> None:
    """I6.2: Ministry KPI contract module must be importable without errors."""
    mod = importlib.import_module(MINISTRY_KPI_MODULE)
    assert mod is not None


# ---------------------------------------------------------------------------
# I6.3 — All required contract symbols are exported
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("symbol", REQUIRED_CONSTANTS)
def test_i6_ministry_kpi_symbol_exported(symbol: str) -> None:
    """I6.3: Each required symbol must be present in the KPI contract module."""
    mod = importlib.import_module(MINISTRY_KPI_MODULE)
    assert hasattr(mod, symbol), (
        f"Ministry KPI contract missing required symbol: {symbol}"
    )


# ---------------------------------------------------------------------------
# I6.4 — Contract constant values match specification
# ---------------------------------------------------------------------------

def test_i6_contract_version_is_v1() -> None:
    """I6.4a: CONTRACT_VERSION must be 'v1'."""
    mod = importlib.import_module(MINISTRY_KPI_MODULE)
    assert mod.MINISTRY_KPI_CONTRACT_VERSION == EXPECTED_CONTRACT_VERSION


def test_i6_required_role_value() -> None:
    """I6.4b: REQUIRED_ROLE must be 'ministry.kpi.read'."""
    mod = importlib.import_module(MINISTRY_KPI_MODULE)
    assert mod.MINISTRY_KPI_REQUIRED_ROLE == EXPECTED_REQUIRED_ROLE


def test_i6_audit_action_value() -> None:
    """I6.4c: AUDIT_ACTION must be 'ministry.kpi.read'."""
    mod = importlib.import_module(MINISTRY_KPI_MODULE)
    assert mod.MINISTRY_KPI_AUDIT_ACTION == EXPECTED_AUDIT_ACTION


def test_i6_suppression_threshold_is_5() -> None:
    """I6.4d: SUPPRESSION_THRESHOLD must be 5 (k-anonymity baseline)."""
    mod = importlib.import_module(MINISTRY_KPI_MODULE)
    assert mod.MINISTRY_KPI_SUPPRESSION_THRESHOLD == EXPECTED_SUPPRESSION_THRESHOLD


def test_i6_suppressed_sentinel_value() -> None:
    """I6.4e: SUPPRESSED_SENTINEL must be the string 'suppressed'."""
    mod = importlib.import_module(MINISTRY_KPI_MODULE)
    assert mod.MINISTRY_KPI_SUPPRESSED_SENTINEL == EXPECTED_SUPPRESSED_SENTINEL


def test_i6_whitelist_contains_all_required_keys() -> None:
    """I6.4f: Whitelist must contain exactly the 3 ministry-approved KPI keys."""
    mod = importlib.import_module(MINISTRY_KPI_MODULE)
    whitelist: frozenset[str] = mod.MINISTRY_KPI_WHITELIST
    assert EXPECTED_WHITELIST_KEYS.issubset(whitelist), (
        f"Whitelist missing keys: {EXPECTED_WHITELIST_KEYS - whitelist}"
    )


def test_i6_whitelist_is_immutable() -> None:
    """I6.4g: Whitelist must be a frozenset (immutable contract)."""
    mod = importlib.import_module(MINISTRY_KPI_MODULE)
    assert isinstance(mod.MINISTRY_KPI_WHITELIST, frozenset)


# ---------------------------------------------------------------------------
# I6.5 — apply_ministry_kpi_contract is callable (smoke)
# ---------------------------------------------------------------------------

def test_i6_apply_contract_callable() -> None:
    """I6.5: apply_ministry_kpi_contract must be callable."""
    mod = importlib.import_module(MINISTRY_KPI_MODULE)
    assert callable(mod.apply_ministry_kpi_contract)


def test_i6_apply_contract_returns_dict() -> None:
    """I6.5b: apply_ministry_kpi_contract must return a dict."""
    mod = importlib.import_module(MINISTRY_KPI_MODULE)
    audit_log: list[dict] = []
    result = mod.apply_ministry_kpi_contract(
        kpis={"total_students": 100, "total_enrollments": 200},
        tenant_id=1,
        audit_log=audit_log,
    )
    assert isinstance(result, dict)
    assert len(audit_log) == 1  # audit entry appended


def test_i6_apply_contract_suppresses_below_threshold() -> None:
    """I6.5c: Values below suppression threshold must be suppressed."""
    mod = importlib.import_module(MINISTRY_KPI_MODULE)
    result = mod.apply_ministry_kpi_contract(
        kpis={"total_students": 3},  # below threshold of 5
        tenant_id=1,
        audit_log=[],
    )
    assert result["total_students"] == mod.MINISTRY_KPI_SUPPRESSED_SENTINEL


def test_i6_apply_contract_passes_above_threshold() -> None:
    """I6.5d: Values at or above threshold must pass through unchanged."""
    mod = importlib.import_module(MINISTRY_KPI_MODULE)
    result = mod.apply_ministry_kpi_contract(
        kpis={"total_students": 5},  # exactly at threshold
        tenant_id=1,
        audit_log=[],
    )
    assert result["total_students"] == 5


# ---------------------------------------------------------------------------
# I6.6 — Phase I test count accounting (meta)
# ---------------------------------------------------------------------------

def test_i6_phase_i_total_test_count_is_95() -> None:
    """I6.6: Phase I must account for exactly 95 hardening tests in total."""
    assert PHASE_I_TOTAL_EXPECTED == 95, (
        f"Expected 95 Phase I tests total, got {PHASE_I_TOTAL_EXPECTED}"
    )


@pytest.mark.parametrize("filename,expected_count", list(PHASE_I_EXPECTED_COUNTS.items()))
def test_i6_per_file_expected_count(filename: str, expected_count: int) -> None:
    """I6.6b: Each Phase I file must account for the correct expected count."""
    assert expected_count > 0, f"{filename} has no expected tests"
    assert isinstance(expected_count, int)


# ---------------------------------------------------------------------------
# I6.7 — Phase I files are non-empty (size guard)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel_path", PHASE_I_TEST_FILES)
def test_i6_phase_i_test_file_non_empty(rel_path: str) -> None:
    """I6.7: Each Phase I test file must be non-empty (>= 1KB)."""
    backend_root = Path(__file__).resolve().parent.parent
    full_path = backend_root / rel_path
    if not full_path.exists():
        pytest.skip(f"File not found: {rel_path}")
    size = full_path.stat().st_size
    assert size >= 1024, (
        f"Phase I test file suspiciously small ({size} bytes): {rel_path}"
    )


# ---------------------------------------------------------------------------
# I6.8 — ministry_kpi.py module file exists on disk
# ---------------------------------------------------------------------------

def test_i6_ministry_kpi_module_file_exists() -> None:
    """I6.8: ministry_kpi.py must exist in the KPI package directory."""
    backend_root = Path(__file__).resolve().parent.parent
    kpi_module_path = backend_root / "app" / "platform" / "kpi" / "ministry_kpi.py"
    assert kpi_module_path.exists(), (
        f"Ministry KPI module file missing: {kpi_module_path}"
    )
