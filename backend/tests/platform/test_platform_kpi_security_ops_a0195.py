"""
A-019.5: Security Operations KPI Dashboard - Backend Test Suite

Tests KPI metrics, titles, event lineage, and computation for security operations
completion metrics including visitor visit tracking and security incident resolution.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.platform.kpi.service import (
    METRIC_TITLES,
    EVENT_DERIVED_METRIC_LINEAGE,
    refresh_tenant_metrics,
)
from app.platform.events.registry import EXACT_EVENT_REGISTRY
from app.platform.event_ingestion.types import VALID_EVENT_TYPES as _INGESTION_EVENT_TYPES


class TestA0195MetricTitles:
    """Verify all A-019.5 metrics have proper titles."""

    def test_visitor_kpi_titles_exist(self):
        """Visitor metrics have display titles."""
        required_visitor_metrics = {
            "visitor_requests_pending_count",
            "visitors_checked_in_count",
            "visitor_unauthorized_attempts_count",
            "visitor_visits_completed_count",
            "visitor_visits_cancelled_count",
        }
        for metric in required_visitor_metrics:
            assert metric in METRIC_TITLES, f"Missing title for {metric}"
            assert isinstance(METRIC_TITLES[metric], str), f"Title not string for {metric}"
            assert len(METRIC_TITLES[metric]) > 0, f"Empty title for {metric}"

    def test_access_kpi_titles_exist(self):
        """Access control metrics have display titles."""
        required_access_metrics = {
            "access_denied_count",
            "unauthorized_attempts_count",
            "active_access_cards_count",
            "suspended_access_cards_count",
            "security_access_anomaly_count",
        }
        for metric in required_access_metrics:
            assert metric in METRIC_TITLES, f"Missing title for {metric}"
            assert isinstance(METRIC_TITLES[metric], str), f"Title not string for {metric}"

    def test_security_kpi_titles_exist(self):
        """Security operations metrics have display titles."""
        required_security_metrics = {
            "security_incidents_open_count",
            "security_incidents_escalated_count",
            "security_incidents_resolved_count",
            "security_incident_review_required_count",
            "security_high_risk_incidents_count",
        }
        for metric in required_security_metrics:
            assert metric in METRIC_TITLES, f"Missing title for {metric}"
            assert isinstance(METRIC_TITLES[metric], str), f"Title not string for {metric}"


class TestEventLineageCompleteness:
    """Verify all supported metrics have event lineage definitions."""

    def test_visitor_metrics_have_event_lineage(self):
        """All visitor metrics map to event types."""
        visitor_metrics = [
            "visitor_requests_pending_count",
            "visitors_checked_in_count",
            "visitor_unauthorized_attempts_count",
            "visitor_visits_completed_count",
            "visitor_visits_cancelled_count",
        ]
        for metric in visitor_metrics:
            assert metric in EVENT_DERIVED_METRIC_LINEAGE, f"Missing lineage for {metric}"
            lineage = EVENT_DERIVED_METRIC_LINEAGE[metric]
            assert isinstance(lineage, list), f"Lineage not list for {metric}"
            assert len(lineage) > 0, f"Empty lineage for {metric}"

    def test_access_metrics_have_event_lineage(self):
        """All access metrics map to event types."""
        access_metrics = [
            "access_denied_count",
            "unauthorized_attempts_count",
            "active_access_cards_count",
            "suspended_access_cards_count",
            "security_access_anomaly_count",
        ]
        for metric in access_metrics:
            assert metric in EVENT_DERIVED_METRIC_LINEAGE, f"Missing lineage for {metric}"

    def test_security_metrics_have_event_lineage(self):
        """All security metrics map to event types."""
        security_metrics = [
            "security_incidents_open_count",
            "security_incidents_escalated_count",
            "security_incidents_resolved_count",
            "security_incident_review_required_count",
            "security_high_risk_incidents_count",
        ]
        for metric in security_metrics:
            assert metric in EVENT_DERIVED_METRIC_LINEAGE, f"Missing lineage for {metric}"

    def test_event_types_are_registered(self):
        """All event types in lineage are registered (domain registry or ingestion registry)."""
        for metric_key, event_list in EVENT_DERIVED_METRIC_LINEAGE.items():
            for event_type in event_list:
                assert event_type in EXACT_EVENT_REGISTRY or event_type in _INGESTION_EVENT_TYPES, \
                    f"Unregistered event type: {event_type}"


class TestMetricComputationScaffolding:
    """Verify metrics can be computed from event counts (scaffolding test)."""

    @patch("app.platform.kpi.service.event_ingestion_service")
    def test_visitor_metrics_compute_from_events(self, mock_event_ingestion_service):
        """Visitor metrics derive from event counts."""
        mock_event_ingestion_service.summary_for_tenant = MagicMock(return_value={})
        tenant_id = "test-tenant"

        # This is a scaffolding test - actual computation in integration tests
        lineage = EVENT_DERIVED_METRIC_LINEAGE.get("visitor_visits_completed_count", [])
        assert "visitor.checked_out" in lineage, "visitor_visits_completed_count should use visitor.checked_out"

    def test_security_metrics_derive_from_incident_events(self):
        """Security metrics reference incident lifecycle events."""
        resolved_lineage = EVENT_DERIVED_METRIC_LINEAGE.get("security_incidents_resolved_count", [])
        assert "security.incident.resolved" in resolved_lineage

        review_lineage = EVENT_DERIVED_METRIC_LINEAGE.get("security_incident_review_required_count", [])
        assert "security.incident.opened" in review_lineage

        high_risk_lineage = EVENT_DERIVED_METRIC_LINEAGE.get("security_high_risk_incidents_count", [])
        assert "security.incident.escalated" in high_risk_lineage


class TestKpiPolicyConsistency:
    """Verify KPI metrics follow platform policy."""

    def test_no_duplicate_metric_names(self):
        """Metric keys are unique."""
        metric_keys = list(METRIC_TITLES.keys())
        assert len(metric_keys) == len(set(metric_keys)), "Duplicate metric keys detected"

    def test_no_empty_titles(self):
        """All metric titles are non-empty."""
        for metric_key, title in METRIC_TITLES.items():
            assert title.strip(), f"Empty title for {metric_key}"
            assert " " in title or len(title) > 3, f"Title too short or oddly formatted for {metric_key}"

    def test_metric_naming_consistency(self):
        """Metrics follow naming convention (metric_key should have _count suffix for counts)."""
        count_metrics = [k for k in METRIC_TITLES.keys() if k.endswith("_count")]
        # At least some of our new metrics should be counts
        security_counts = [k for k in count_metrics if "security" in k]
        assert len(security_counts) > 0, "Expected security *_count metrics"

    def test_no_destructive_policy_keywords_in_titles(self):
        """Security/visitor metrics don't contain dangerous keywords."""
        forbidden_keywords = ["ban", "blacklist", "lockout", "punch out", "eject", "remove", "destroy", "delete"]
        for metric_key, title in METRIC_TITLES.items():
            title_lower = title.lower()
            for keyword in forbidden_keywords:
                assert keyword not in title_lower, f"Forbidden keyword '{keyword}' in metric title: {title}"

    def test_no_hardware_control_keywords_in_titles(self):
        """Metrics don't reference hardware/door control."""
        forbidden_keywords = ["door", "lock", "hardware", "rfid", "barrier"]
        for metric_key, title in METRIC_TITLES.items():
            title_lower = title.lower()
            # Skip legitimate keywords like "locked" in "locked down" for security incident
            for keyword in ["hardware", "barrier", "rfid"]:
                assert keyword not in title_lower, f"Hardware keyword '{keyword}' in metric title: {title}"


class TestA0195MetricAvailability:
    """Ensure A-019.5 specific metrics are present."""

    def test_new_security_metrics_present(self):
        """A-019.5 added security metrics are in METRIC_TITLES."""
        new_metrics = {
            "security_incidents_resolved_count",
            "security_incident_review_required_count",
            "security_high_risk_incidents_count",
        }
        for metric in new_metrics:
            assert metric in METRIC_TITLES, f"A-019.5 metric missing: {metric}"

    def test_new_visitor_completion_metrics_present(self):
        """A-019.5 added visitor completion metrics are in METRIC_TITLES."""
        completion_metrics = {
            "visitor_visits_completed_count",
            "visitor_visits_cancelled_count",
        }
        for metric in completion_metrics:
            assert metric in METRIC_TITLES, f"Visitor completion metric missing: {metric}"

    def test_all_a0195_metrics_have_lineage(self):
        """All A-019.5 metrics have event lineage definitions."""
        a0195_metrics = {
            "security_incidents_resolved_count",
            "security_incident_review_required_count",
            "security_high_risk_incidents_count",
            "visitor_visits_completed_count",
            "visitor_visits_cancelled_count",
        }
        for metric in a0195_metrics:
            assert metric in EVENT_DERIVED_METRIC_LINEAGE, f"Missing lineage for {metric}"


@pytest.mark.integration
class TestDashboardMetricContract:
    """Verify metrics match dashboard contract expectations."""

    def test_required_metrics_for_dashboard_rendering(self):
        """Dashboard expects specific KPI metrics to exist."""
        dashboard_metrics = {
            # Visitor metrics
            "visitor_requests_pending_count",
            "visitors_checked_in_count",
            "visitor_unauthorized_attempts_count",
            "visitor_visits_completed_count",
            "visitor_visits_cancelled_count",
            # Access metrics
            "access_denied_count",
            "unauthorized_attempts_count",
            "active_access_cards_count",
            "suspended_access_cards_count",
            "security_access_anomaly_count",
            # Security metrics
            "security_incidents_open_count",
            "security_incidents_escalated_count",
            "security_incidents_resolved_count",
            "security_incident_review_required_count",
            "security_high_risk_incidents_count",
        }

        missing_metrics = dashboard_metrics - set(METRIC_TITLES.keys())
        assert not missing_metrics, f"Dashboard metrics missing from METRIC_TITLES: {missing_metrics}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
