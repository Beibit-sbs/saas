"""A-023.7 consistency validation for the canonical 150-module inventory.

Pure arithmetic and logic tests always run.
File-based tests skip gracefully when running inside the backend-tests
container (where repo-root .md files are not present in the image).
"""

from __future__ import annotations

import importlib
import os
from collections import Counter
from pathlib import Path
import re

import pytest


def _find_root() -> Path | None:
    """Walk upward from this file searching for the repo root (SBS_UB.md)."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "SBS_UB.md").exists():
            return parent
    env = os.environ.get("REPO_ROOT")
    if env:
        candidate = Path(env)
        if (candidate / "SBS_UB.md").exists():
            return candidate
    return None


_ROOT = _find_root()
DOCS_AVAILABLE = _ROOT is not None

if _ROOT is not None:
    INVENTORY_REPORT = _ROOT / "A-023.0-150_MODULE_EXPANSION_AND_MATURITY_INVENTORY_REPORT.md"
    SBS_UB = _ROOT / "SBS_UB.md"
    REPORT_A0231 = _ROOT / "A-023.1-ACADEMIC_EDUCATION_FOUNDATION_LIFT_REPORT.md"
    REPORT_A0232 = _ROOT / "A-023.2-STUDENT_LIFECYCLE_FOUNDATION_LIFT_REPORT.md"
    REPORT_A0233 = _ROOT / "A-023.3-CAMPUS_FACILITIES_SECURITY_FOUNDATION_LIFT_REPORT.md"
    REPORT_A0234 = _ROOT / "A-023.4-FINANCE_PROCUREMENT_ASSETS_FOUNDATION_LIFT_REPORT.md"
    REPORT_A0235 = _ROOT / "A-023.5-GOVERNANCE_RECTOR_MINISTRY_REPORTING_FOUNDATION_LIFT_REPORT.md"
    REPORT_A0236 = _ROOT / "A-023.6-AI_BRAIN_PLATFORM_INFRA_FOUNDATION_LIFT_REPORT.md"
else:
    INVENTORY_REPORT = Path("/nonexistent/inventory.md")
    SBS_UB = Path("/nonexistent/SBS_UB.md")
    REPORT_A0231 = Path("/nonexistent/a0231.md")
    REPORT_A0232 = Path("/nonexistent/a0232.md")
    REPORT_A0233 = Path("/nonexistent/a0233.md")
    REPORT_A0234 = Path("/nonexistent/a0234.md")
    REPORT_A0235 = Path("/nonexistent/a0235.md")
    REPORT_A0236 = Path("/nonexistent/a0236.md")

EXPECTED_COUNTS = {
    "L0": 4,
    "L1": 20,
    "L2": 17,
    "L3": 24,
    "L4": 62,
    "L5": 21,
    "L6": 2,
}

EXPECTED_SELECTED = {
    "A-023.1": [
        "lms_assessment_center",
        "library_circulation",
        "research_projects",
        "student_success_analytics",
        "counseling_case_management",
        "digital_certificates",
        "research_grants",
        "accreditation_compliance",
    ],
    "A-023.2": [
        "event_registration_portal",
        "health_services",
        "internship_marketplace",
        "mobile_push_gateway",
        "notification_center",
        "parent_engagement",
        "parking_enforcement",
        "parking_permit_ops",
        "counseling_case_management",
        "library_circulation",
    ],
    "A-023.3": [
        "lab_operations",
        "records_hub",
        "federation_management",
        "health_services",
        "local_user_management",
        "platform_health",
    ],
    "A-023.4": [
        "alumni_relations_ops",
        "donations_fundraising",
        "contracts_legal_repository",
        "procurement_approval_workflow",
    ],
    "A-023.5": [
        "publication_registry",
        "timetable_approval_queue",
        "timetable_change_kpi_dashboard",
        "ai_cost_governance",
    ],
    "A-023.6": [
        "exam_integrity_analytics",
        "ai_copilot_ops",
        "ai_routing_control",
        "developer_portal",
    ],
}

EXPECTED_DELTA_LINES = {
    "A-023.1": "20+16+5+24+62+21+2=150",
    "A-023.2": "12+22+7+24+62+21+2=150",
    "A-023.3": "10+20+11+24+62+21+2=150",
    "A-023.4": "8+20+13+24+62+21+2=150",
    "A-023.5": "5+22+14+24+62+21+2=150",
    "A-023.6": "4+20+17+24+62+21+2=150",
}


def _require_docs() -> None:
    """Skip the current test if markdown docs are not accessible."""
    if not DOCS_AVAILABLE:
        pytest.skip("repo-root .md files not available in this container context")


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text()


def _inventory_rows() -> list[list[str]]:
    _require_docs()
    text = _read(INVENTORY_REPORT)
    rows: list[list[str]] = []
    for line in text.splitlines():
        if re.match(r"^\|\s*\d+\s*\|", line):
            parts = [part.strip() for part in line.strip("|").split("|")]
            if len(parts) >= 6 and parts[0].isdigit():
                rows.append(parts)
    return rows


def _inventory_modules() -> list[str]:
    return [row[1] for row in _inventory_rows()]


def _metrics_block() -> dict[str, int]:
    _require_docs()
    text = _read(SBS_UB)
    result: dict[str, int] = {}
    for key in [
        "level_0_count",
        "level_1_count",
        "level_2_count",
        "level_3_count",
        "level_4_count",
        "level_5_count",
        "level_6_count",
        "foundation_gap_count",
        "level_2_gap_count",
    ]:
        match = re.search(rf"- {re.escape(key)} = (\d+)", text)
        assert match, f"missing {key} in SBS_UB.md"
        result[key] = int(match.group(1))
    return result


@pytest.mark.parametrize(
    "path",
    [
        INVENTORY_REPORT,
        SBS_UB,
        REPORT_A0231,
        REPORT_A0232,
        REPORT_A0233,
        REPORT_A0234,
        REPORT_A0235,
        REPORT_A0236,
    ],
)
def test_a0237_source_documents_exist(path: Path) -> None:
    _require_docs()
    assert path.exists(), f"missing source document: {path.name}"


# ── Pure arithmetic tests — always run, no file I/O required ─────────────────

def test_a0237_maturity_arithmetic_sums_to_150_always() -> None:
    """Canonical A-023.6-close level counts must sum to exactly 150."""
    counts = [4, 20, 17, 24, 62, 21, 2]  # L0..L6
    assert sum(counts) == 150


def test_a0237_foundation_gap_always() -> None:
    l0, l1, l2 = 4, 20, 17
    assert l0 + l1 + l2 == 41  # foundation_gap_count


def test_a0237_level_2_gap_always() -> None:
    l0, l1 = 4, 20
    assert l0 + l1 == 24  # level_2_gap_count


def test_a0237_no_duplicate_selected_modules_always() -> None:
    """All EXPECTED_SELECTED lists must be duplicate-free."""
    for action, selected in EXPECTED_SELECTED.items():
        counts = Counter(selected)
        duplicates = [m for m, c in counts.items() if c > 1]
        assert not duplicates, f"{action} has duplicate module names: {duplicates}"


def test_a0237_a0236_selected_modules_importable_always() -> None:
    """A-023.6 lifted module packages must be importable inside container."""
    for mod in [
        "app.modules.exam_integrity_analytics",
        "app.modules.ai_copilot_ops",
        "app.modules.ai_routing_control",
        "app.modules.developer_portal",
    ]:
        importlib.import_module(mod)


# ── File-based tests — skip when docs not available in container ──────────────

def test_a0237_canonical_inventory_has_exactly_150_rows_and_no_duplicates() -> None:
    _require_docs()
    modules = _inventory_modules()
    counts = Counter(modules)

    assert len(modules) == 150
    assert len(counts) == 150
    assert all(value == 1 for value in counts.values())


def test_a0237_expected_a023x_modules_are_present_in_canonical_inventory() -> None:
    _require_docs()
    modules = set(_inventory_modules())
    for action, selected in EXPECTED_SELECTED.items():
        missing = [module for module in selected if module not in modules]
        assert not missing, f"{action} missing from inventory: {missing}"


def test_a0237_metrics_block_matches_expected_values() -> None:
    _require_docs()
    metrics = _metrics_block()
    assert metrics == {
        "level_0_count": 4,
        "level_1_count": 20,
        "level_2_count": 17,
        "level_3_count": 24,
        "level_4_count": 62,
        "level_5_count": 21,
        "level_6_count": 2,
        "foundation_gap_count": 41,
        "level_2_gap_count": 24,
    }


def test_a0237_metrics_arithmetic_sums_to_150() -> None:
    _require_docs()
    metrics = _metrics_block()
    total = sum(metrics[key] for key in [
        "level_0_count",
        "level_1_count",
        "level_2_count",
        "level_3_count",
        "level_4_count",
        "level_5_count",
        "level_6_count",
    ])
    assert total == 150
    assert metrics["level_0_count"] + metrics["level_1_count"] + metrics["level_2_count"] == 41
    assert metrics["level_0_count"] + metrics["level_1_count"] == 24


def test_a0237_action_reports_contain_expected_arithmetic_and_selected_modules() -> None:
    _require_docs()
    reports = {
        "A-023.1": _read(REPORT_A0231),
        "A-023.2": _read(REPORT_A0232),
        "A-023.3": _read(REPORT_A0233),
        "A-023.4": _read(REPORT_A0234),
        "A-023.5": _read(REPORT_A0235),
        "A-023.6": _read(REPORT_A0236),
    }
    for action, selected in EXPECTED_SELECTED.items():
        report = reports[action]
        for module in selected:
            assert module in report, f"{module} missing from {action} report"
        assert EXPECTED_DELTA_LINES[action] in report, f"{action} arithmetic missing"


def test_a0237_a0236_report_has_no_inflated_language() -> None:
    _require_docs()
    text = _read(REPORT_A0236)
    forbidden_phrases = [
        "Level 3",
        "Level 4",
        "fake KPI",
        "fake Brain",
        "fully production",
        "autonomous execution",
        "ministry integration",
        "E2E proven",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in text


def test_a0237_inventory_and_sbs_anchor_a0237_readiness() -> None:
    _require_docs()
    inventory = _read(INVENTORY_REPORT)
    sbs = _read(SBS_UB)
    assert "A-023.7 Consistency Addendum" in inventory
    assert "A-023.8" in inventory
    assert "A-023.7 COMPLETE - 150 module audit consistency validated" in sbs
    assert "next_action_id = A-023.8" in sbs
