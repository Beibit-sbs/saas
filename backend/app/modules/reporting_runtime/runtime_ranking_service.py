"""Service layer for Ranking Reporting runtime endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.regulatory_reporting_integration.service import (
    get_regulatory_reporting_provider_l4_visibility_summary,
)
from app.modules.reporting_runtime.runtime_ranking_schemas import (
    RankingBenchmarkResponse,
    RankingBenchmarkSummary,
    RankingIndicatorResponse,
    RankingIndicatorSummary,
    RankingReadinessResponse,
    RankingReadinessSummary,
    RankingReportingResponse,
    RankingReportingSummary,
    RankingRiskResponse,
    RankingRiskSummary,
    RankingTrendResponse,
    RankingTrendSummary,
)
from app.modules.reporting_runtime.runtime_registry_service import ReportingRegistryRuntimeService


class RankingReportingRuntimeService:
    """Read-only aggregation service for QS/THE ranking runtime."""

    _RANKING_CATALOG = [
        ("QS", "Academic Reputation", "research_science"),
        ("QS", "Employer Reputation", "analytics"),
        ("QS", "Faculty Student Ratio", "quality_accreditation"),
        ("QS", "Citations Per Faculty", "research_science"),
        ("QS", "International Faculty", "analytics"),
        ("QS", "International Students", "analytics"),
        ("THE", "Teaching", "quality_accreditation"),
        ("THE", "Research Environment", "research_science"),
        ("THE", "Research Quality", "research_science"),
        ("THE", "International Outlook", "analytics"),
        ("THE", "Industry Engagement", "analytics"),
    ]

    _BENCHMARK_SCORES = {
        "Academic Reputation": 88,
        "Employer Reputation": 85,
        "Faculty Student Ratio": 82,
        "Citations Per Faculty": 84,
        "International Faculty": 78,
        "International Students": 76,
        "Teaching": 86,
        "Research Environment": 87,
        "Research Quality": 89,
        "International Outlook": 80,
        "Industry Engagement": 83,
    }

    _SIGNALS = [
        "ranking_readiness_low",
        "qs_indicator_decline",
        "the_indicator_decline",
        "ranking_risk_high",
        "benchmark_gap_high",
    ]

    def __init__(self) -> None:
        self._registry = ReportingRegistryRuntimeService()

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _trend_direction(self, trend_delta: int) -> str:
        if trend_delta >= 2:
            return "UP"
        if trend_delta <= -2:
            return "DOWN"
        return "STABLE"

    def _readiness_level(self, indicator_score: int, benchmark_gap: int) -> str:
        if indicator_score >= 85 and benchmark_gap <= 2:
            return "READY"
        if indicator_score >= 70 and benchmark_gap <= 8:
            return "PARTIAL"
        return "LOW"

    def _risk_level(self, readiness_level: str, trend_direction: str, benchmark_gap: int) -> str:
        if readiness_level == "LOW" or benchmark_gap >= 12:
            return "HIGH"
        if trend_direction == "DOWN" or benchmark_gap >= 8:
            return "MEDIUM"
        return "LOW"

    def _build_entries(self, tenant_id: int) -> tuple[int, datetime, list[dict[str, object]]]:
        tenant = validate_tenant_id_provided(tenant_id)
        registry = self._registry.get_registry(tenant)
        provider_visibility = get_regulatory_reporting_provider_l4_visibility_summary(tenant)

        blockers = int(provider_visibility.get("blocker_count", 0))
        warnings = int(provider_visibility.get("warning_count", 0))
        tenant_factor = (tenant % 6) + 1
        registry_shift = len(registry.entries) % 4

        entries: list[dict[str, object]] = []
        for index, (ranking_system, indicator_name, owner_module) in enumerate(self._RANKING_CATALOG):
            benchmark_score = self._BENCHMARK_SCORES[indicator_name]
            indicator_score = max(
                48,
                min(
                    98,
                    benchmark_score - 6 + tenant_factor + (index % 3) - (blockers * 2) - warnings - registry_shift,
                ),
            )
            trend_delta = ((tenant + index) % 5) - 2
            trend_direction = self._trend_direction(trend_delta)
            benchmark_gap = max(0, benchmark_score - indicator_score)
            readiness_level = self._readiness_level(indicator_score, benchmark_gap)
            risk_level = self._risk_level(readiness_level, trend_direction, benchmark_gap)

            entries.append(
                {
                    "id": f"ranking-{tenant}-{index + 1}",
                    "ranking_system": ranking_system,
                    "indicator_name": indicator_name,
                    "indicator_score": indicator_score,
                    "benchmark_score": benchmark_score,
                    "trend_direction": trend_direction,
                    "readiness_level": readiness_level,
                    "risk_level": risk_level,
                    "owner_module": owner_module,
                    "generated_at": registry.generated_at,
                    "_benchmark_gap": benchmark_gap,
                    "_trend_delta": trend_delta,
                    "_indicator_weight": max(8, 20 - (index % 6)),
                }
            )

        return tenant, registry.generated_at, entries

    def get_ranking(self, tenant_id: int) -> RankingReportingResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        reports = [
            RankingReportingSummary(**{k: v for k, v in entry.items() if not k.startswith("_")})
            for entry in entries
        ]
        return RankingReportingResponse(
            tenant_id=tenant,
            generated_at=generated_at,
            reports=reports,
            signal_inventory=list(self._SIGNALS),
        )

    def get_indicators(self, tenant_id: int) -> RankingIndicatorResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        indicators = [
            RankingIndicatorSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                indicator_weight=int(entry["_indicator_weight"]),
            )
            for entry in entries
        ]
        return RankingIndicatorResponse(tenant_id=tenant, generated_at=generated_at, indicators=indicators)

    def get_readiness(self, tenant_id: int) -> RankingReadinessResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        readiness = [
            RankingReadinessSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                readiness_score=max(0, min(100, int(entry["indicator_score"]))),
            )
            for entry in entries
        ]
        return RankingReadinessResponse(tenant_id=tenant, generated_at=generated_at, readiness=readiness)

    def get_benchmarks(self, tenant_id: int) -> RankingBenchmarkResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        benchmarks = [
            RankingBenchmarkSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                benchmark_gap=int(entry["_benchmark_gap"]),
            )
            for entry in entries
        ]
        return RankingBenchmarkResponse(tenant_id=tenant, generated_at=generated_at, benchmarks=benchmarks)

    def get_trends(self, tenant_id: int) -> RankingTrendResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        trends = [
            RankingTrendSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                trend_delta=int(entry["_trend_delta"]),
            )
            for entry in entries
        ]
        return RankingTrendResponse(tenant_id=tenant, generated_at=generated_at, trends=trends)

    def get_risks(self, tenant_id: int) -> RankingRiskResponse:
        tenant, generated_at, entries = self._build_entries(tenant_id)
        risks = [
            RankingRiskSummary(
                **{k: v for k, v in entry.items() if not k.startswith("_")},
                signal_name=self._SIGNALS[index % len(self._SIGNALS)],
            )
            for index, entry in enumerate(entries)
        ]
        return RankingRiskResponse(tenant_id=tenant, generated_at=generated_at, risks=risks)
