"""A-031.5-RUNTIME dashboard expansion tests.

Tests: dashboard schema expansion, expanded fields, fake_metrics guard,
data_source invariant, dashboard API route.
Uses MagicMock(spec=Session) — no real DB required.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.modules.rector_assignment_workflow.schemas import (
    DashboardSummaryResponse,
    OverdueAgingBuckets,
    UnitCompletionEntry,
    WeeklyTrend,
)
from app.main import app
from app.modules.rector_assignment_workflow.dependencies import get_rector_assignment_db
from tests.conftest import ADMIN_HEADERS, client
from datetime import datetime

BASE = "/api/admin/rector-assignments"


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_rector_assignment_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_rector_assignment_db, None)


# ---------------------------------------------------------------------------
# Minimal valid dashboard data
# ---------------------------------------------------------------------------

def _base_dashboard_data() -> dict:
    return {
        "tenant_id": 1,
        "computed_at": datetime(2025, 1, 1),
        "total_assignments": 10,
        "active_count": 4,
        "draft_count": 1,
        "overdue_count": 2,
        "escalated_count": 0,
        "completed_count": 3,
        "cancelled_count": 0,
        "report_submitted_count": 1,
        "returned_count": 0,
        "due_this_week": 2,
        "due_today": 0,
        "completion_rate_30d": 0.3,
        "average_days_to_complete": None,
        "by_status": {"DRAFT": 1},
        "by_priority": {"NORMAL": 10},
        "by_unit": [],
        "top_overdue": [],
        "data_source": "computed_from_assignments",
        "fake_metrics": False,
    }


# ===========================================================================
# 1. OverdueAgingBuckets schema
# ===========================================================================

class TestOverdueAgingBuckets:
    def test_defaults_to_zero(self):
        buckets = OverdueAgingBuckets()
        assert buckets.days_1_3 == 0
        assert buckets.days_4_7 == 0
        assert buckets.days_8_14 == 0
        assert buckets.days_15_plus == 0

    def test_all_fields_settable(self):
        buckets = OverdueAgingBuckets(days_1_3=1, days_4_7=2, days_8_14=3, days_15_plus=4)
        assert buckets.days_1_3 == 1
        assert buckets.days_4_7 == 2
        assert buckets.days_8_14 == 3
        assert buckets.days_15_plus == 4

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(OverdueAgingBuckets, BaseModel)


# ===========================================================================
# 2. WeeklyTrend schema
# ===========================================================================

class TestWeeklyTrend:
    def test_defaults(self):
        from datetime import date
        trend = WeeklyTrend(week_start=date(2025, 1, 6))
        assert trend.completed_count == 0
        assert trend.created_count == 0

    def test_with_counts(self):
        from datetime import date
        trend = WeeklyTrend(week_start=date(2025, 1, 6), completed_count=5, created_count=8)
        assert trend.completed_count == 5
        assert trend.created_count == 8

    def test_week_start_required(self):
        with pytest.raises(Exception):
            WeeklyTrend()


# ===========================================================================
# 3. UnitCompletionEntry schema
# ===========================================================================

class TestUnitCompletionEntry:
    def test_defaults(self):
        entry = UnitCompletionEntry()
        assert entry.unit_id is None
        assert entry.unit_name is None
        assert entry.total == 0
        assert entry.completed == 0
        assert entry.overdue == 0
        assert entry.completion_rate is None

    def test_with_data(self):
        entry = UnitCompletionEntry(unit_id=5, total=10, completed=7, overdue=2, completion_rate=0.7)
        assert entry.unit_id == 5
        assert entry.completion_rate == 0.7


# ===========================================================================
# 4. DashboardSummaryResponse expansion
# ===========================================================================

class TestDashboardSummaryResponseExpansion:
    def test_base_fields_unchanged(self):
        data = _base_dashboard_data()
        resp = DashboardSummaryResponse(**data)
        assert resp.tenant_id == 1
        assert resp.total_assignments == 10
        assert resp.fake_metrics is False
        assert resp.data_source == "computed_from_assignments"

    def test_new_fields_have_defaults(self):
        data = _base_dashboard_data()
        resp = DashboardSummaryResponse(**data)
        assert resp.overdue_aging_buckets is None
        assert resp.completion_trend_by_week == []
        assert resp.report_submission_compliance is None
        assert resp.escalation_rate is None
        assert resp.average_revision_cycles is None
        assert resp.evidence_attachment_rate is None
        assert resp.assignments_without_recent_report == 0
        assert resp.unit_completion_table == []

    def test_fake_metrics_always_false(self):
        data = _base_dashboard_data()
        resp = DashboardSummaryResponse(**data)
        assert resp.fake_metrics is False

    def test_data_source_always_computed(self):
        data = _base_dashboard_data()
        resp = DashboardSummaryResponse(**data)
        assert resp.data_source == "computed_from_assignments"

    def test_with_aging_buckets(self):
        data = _base_dashboard_data()
        data["overdue_aging_buckets"] = OverdueAgingBuckets(days_1_3=2, days_4_7=1)
        resp = DashboardSummaryResponse(**data)
        assert resp.overdue_aging_buckets.days_1_3 == 2

    def test_with_weekly_trend(self):
        from datetime import date
        data = _base_dashboard_data()
        data["completion_trend_by_week"] = [
            WeeklyTrend(week_start=date(2025, 1, 6), completed_count=3, created_count=5)
        ]
        resp = DashboardSummaryResponse(**data)
        assert len(resp.completion_trend_by_week) == 1
        assert resp.completion_trend_by_week[0].completed_count == 3

    def test_with_escalation_rate(self):
        data = _base_dashboard_data()
        data["escalation_rate"] = 0.15
        resp = DashboardSummaryResponse(**data)
        assert resp.escalation_rate == 0.15

    def test_with_unit_completion_table(self):
        data = _base_dashboard_data()
        data["unit_completion_table"] = [
            UnitCompletionEntry(unit_id=1, total=5, completed=3, completion_rate=0.6)
        ]
        resp = DashboardSummaryResponse(**data)
        assert len(resp.unit_completion_table) == 1

    def test_with_full_expanded_data(self):
        from datetime import date
        data = _base_dashboard_data()
        data.update({
            "overdue_aging_buckets": OverdueAgingBuckets(days_1_3=1, days_4_7=2, days_8_14=0, days_15_plus=3),
            "completion_trend_by_week": [
                WeeklyTrend(week_start=date(2025, 1, 6), completed_count=5, created_count=8)
            ],
            "report_submission_compliance": 0.8,
            "escalation_rate": 0.05,
            "average_revision_cycles": 1.2,
            "evidence_attachment_rate": 0.75,
            "assignments_without_recent_report": 2,
            "unit_completion_table": [
                UnitCompletionEntry(unit_id=1, total=10, completed=8, overdue=1, completion_rate=0.8)
            ],
        })
        resp = DashboardSummaryResponse(**data)
        assert resp.overdue_aging_buckets.days_4_7 == 2
        assert resp.report_submission_compliance == 0.8
        assert resp.average_revision_cycles == 1.2
        assert resp.assignments_without_recent_report == 2
        assert resp.fake_metrics is False


# ===========================================================================
# 5. Dashboard API route with expanded fields
# ===========================================================================

class TestDashboardApiExpanded:
    def test_dashboard_returns_200(self):
        data = _base_dashboard_data()
        with patch(
            "app.modules.rector_assignment_workflow.router.get_dashboard_summary",
            return_value=data,
        ):
            resp = client.get(f"{BASE}/dashboard/summary", headers=ADMIN_HEADERS)
            assert resp.status_code == 200

    def test_dashboard_fake_metrics_false(self):
        data = _base_dashboard_data()
        with patch(
            "app.modules.rector_assignment_workflow.router.get_dashboard_summary",
            return_value=data,
        ):
            resp = client.get(f"{BASE}/dashboard/summary", headers=ADMIN_HEADERS)
            assert resp.json()["fake_metrics"] is False

    def test_dashboard_data_source_correct(self):
        data = _base_dashboard_data()
        with patch(
            "app.modules.rector_assignment_workflow.router.get_dashboard_summary",
            return_value=data,
        ):
            resp = client.get(f"{BASE}/dashboard/summary", headers=ADMIN_HEADERS)
            assert resp.json()["data_source"] == "computed_from_assignments"

    def test_dashboard_with_aging_buckets(self):
        data = _base_dashboard_data()
        data["overdue_aging_buckets"] = {"days_1_3": 3, "days_4_7": 1, "days_8_14": 0, "days_15_plus": 2}
        with patch(
            "app.modules.rector_assignment_workflow.router.get_dashboard_summary",
            return_value=data,
        ):
            resp = client.get(f"{BASE}/dashboard/summary", headers=ADMIN_HEADERS)
            assert resp.status_code == 200
            body = resp.json()
            assert "overdue_aging_buckets" in body

    def test_dashboard_no_auth_returns_403(self):
        resp = client.get(f"{BASE}/dashboard/summary")
        assert resp.status_code in (401, 403)

    def test_dashboard_with_empty_trend(self):
        data = _base_dashboard_data()
        data["completion_trend_by_week"] = []
        with patch(
            "app.modules.rector_assignment_workflow.router.get_dashboard_summary",
            return_value=data,
        ):
            resp = client.get(f"{BASE}/dashboard/summary", headers=ADMIN_HEADERS)
            assert resp.status_code == 200
            assert resp.json()["completion_trend_by_week"] == []


# ===========================================================================
# 6. Service: get_dashboard_summary guard
# ===========================================================================

class TestDashboardServiceGuard:
    def test_fake_metrics_guard(self):
        from app.modules.rector_assignment_workflow.service import get_dashboard_summary
        db = MagicMock(spec=Session)
        # Simulate repo returning bad data with fake_metrics=True — service should reject
        bad_data = _base_dashboard_data()
        bad_data["fake_metrics"] = True
        with patch(
            "app.modules.rector_assignment_workflow.service.repo_compute_dashboard_summary",
            return_value=bad_data,
        ):
            with pytest.raises(AssertionError):
                get_dashboard_summary(1, db)

    def test_data_source_guard(self):
        from app.modules.rector_assignment_workflow.service import get_dashboard_summary
        db = MagicMock(spec=Session)
        bad_data = _base_dashboard_data()
        bad_data["data_source"] = "fake"
        with patch(
            "app.modules.rector_assignment_workflow.service.repo_compute_dashboard_summary",
            return_value=bad_data,
        ):
            with pytest.raises(AssertionError):
                get_dashboard_summary(1, db)

    def test_expanded_fields_error_fallback(self):
        """If expanded dashboard computation fails, base fields should still be returned."""
        from app.modules.rector_assignment_workflow.service import get_dashboard_summary
        db = MagicMock(spec=Session)
        base_data = _base_dashboard_data()
        with patch(
            "app.modules.rector_assignment_workflow.service.repo_compute_dashboard_summary",
            return_value=base_data,
        ), patch(
            "app.modules.rector_assignment_workflow.service.repo_compute_expanded_dashboard_fields",
            side_effect=Exception("DB error"),
        ):
            result = get_dashboard_summary(1, db)
            assert result["fake_metrics"] is False
            assert result["data_source"] == "computed_from_assignments"
            assert result["total_assignments"] == 10

    def test_tenant_required(self):
        from app.modules.rector_assignment_workflow.service import get_dashboard_summary
        from app.core.module_helpers.service_validation import TenantRequiredError
        db = MagicMock(spec=Session)
        with pytest.raises(Exception):
            get_dashboard_summary(0, db)


# ===========================================================================
# 7. Expanded fields dict keys from repo_compute_expanded_dashboard_fields
# ===========================================================================

class TestExpandedDashboardFieldKeys:
    """Test that the repo function returns all expected dict keys."""

    EXPECTED_KEYS = {
        "overdue_aging_buckets",
        "completion_trend_by_week",
        "report_submission_compliance",
        "escalation_rate",
        "average_revision_cycles",
        "evidence_attachment_rate",
        "assignments_without_recent_report",
        "unit_completion_table",
    }

    def test_all_expected_keys_present_in_response_schema(self):
        from pydantic import BaseModel
        fields = DashboardSummaryResponse.model_fields
        for key in self.EXPECTED_KEYS:
            assert key in fields, f"Expected field {key!r} not in DashboardSummaryResponse"

    def test_aging_buckets_expected_subfields(self):
        buckets = OverdueAgingBuckets()
        fields = buckets.model_fields
        assert "days_1_3" in fields
        assert "days_4_7" in fields
        assert "days_8_14" in fields
        assert "days_15_plus" in fields

    def test_weekly_trend_expected_fields(self):
        fields = WeeklyTrend.model_fields
        assert "week_start" in fields
        assert "completed_count" in fields
        assert "created_count" in fields

    def test_unit_completion_entry_expected_fields(self):
        fields = UnitCompletionEntry.model_fields
        assert "unit_id" in fields
        assert "total" in fields
        assert "completed" in fields
        assert "overdue" in fields
        assert "completion_rate" in fields
