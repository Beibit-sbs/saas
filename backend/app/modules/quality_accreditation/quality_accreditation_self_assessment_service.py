"""Read-only self-assessment runtime service for Quality / Accreditation."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.modules.quality_accreditation import models, repository
from app.modules.quality_accreditation.dependencies import validate_tenant_id
from app.modules.quality_accreditation.quality_accreditation_self_assessment_schemas import (
    SelfAssessmentCoverageSummary,
    SelfAssessmentReadinessSummary,
    SelfAssessmentRiskSummary,
    SelfAssessmentRuntimeResponse,
    SelfAssessmentScorecard,
    SelfAssessmentStandard,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _safe_text(value: object | None, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _as_int(value: object | None, fallback: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return fallback


def _coerce_datetime(value: object | None, fallback: datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return fallback


def _owner_unit(item: Any) -> str:
    return _safe_text(getattr(item, "source_family_id", None), _safe_text(getattr(item, "source_capability_id", None), "quality_accreditation"))


def _readiness_band(score: int) -> str:
    if score >= 85:
        return "READY"
    if score >= 60:
        return "IN_PROGRESS"
    return "NEEDS_ATTENTION"


def _risk_level(score: int, gap_count: int) -> str:
    if gap_count >= 3 or score < 50:
        return "HIGH"
    if gap_count >= 1 or score < 75:
        return "MEDIUM"
    return "LOW"


def _summarize_readiness(standards: list[SelfAssessmentStandard]) -> list[SelfAssessmentReadinessSummary]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for item in standards:
        grouped[_readiness_band(item.readiness_score)].append(item.readiness_score)

    output: list[SelfAssessmentReadinessSummary] = []
    for band, scores in sorted(grouped.items()):
        output.append(
            SelfAssessmentReadinessSummary(
                readiness_band=band,
                standard_count=len(scores),
                average_readiness_score=sum(scores) / len(scores),
            )
        )
    return output


def _summarize_coverage(standards: list[SelfAssessmentStandard]) -> list[SelfAssessmentCoverageSummary]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for item in standards:
        grouped[item.accreditation_framework].append(item.evidence_coverage)

    output: list[SelfAssessmentCoverageSummary] = []
    for scope, coverages in sorted(grouped.items()):
        output.append(
            SelfAssessmentCoverageSummary(
                coverage_scope=scope,
                standard_count=len(coverages),
                average_evidence_coverage=sum(coverages) / len(coverages),
            )
        )
    return output


def _summarize_risk(standards: list[SelfAssessmentStandard]) -> list[SelfAssessmentRiskSummary]:
    grouped: dict[str, int] = defaultdict(int)
    for item in standards:
        grouped[item.risk_level] += 1

    return [SelfAssessmentRiskSummary(risk_level=level, standard_count=count) for level, count in sorted(grouped.items())]


def _build_scorecard(standards: list[SelfAssessmentStandard]) -> SelfAssessmentScorecard:
    if not standards:
        return SelfAssessmentScorecard()

    standards_total = len(standards)
    ready_standards = len([item for item in standards if item.readiness_score >= 85])
    high_risk_standards = len([item for item in standards if item.risk_level == "HIGH"])
    gap_total = sum(item.gap_count for item in standards)

    return SelfAssessmentScorecard(
        standards_total=standards_total,
        ready_standards=ready_standards,
        average_readiness_score=sum(item.readiness_score for item in standards) / standards_total,
        average_completion_percentage=sum(item.completion_percentage for item in standards) / standards_total,
        average_evidence_coverage=sum(item.evidence_coverage for item in standards) / standards_total,
        high_risk_standards=high_risk_standards,
        gap_total=gap_total,
    )


class SelfAssessmentRuntimeService:
    """Read-only aggregation service for self-assessment runtime."""

    def get_self_assessment_runtime(self, db: Session, tenant_id: int) -> SelfAssessmentRuntimeResponse:
        tenant = validate_tenant_id(tenant_id)
        generated_at = _now()

        standard_rows = repository.list_resources(db, models.AccreditationStandard, tenant)
        evidence_rows = repository.list_resources(db, models.QualityEvidenceRegistry, tenant)
        limitation_rows = repository.list_resources(db, models.EvidenceLimitation, tenant)
        program_readiness_rows = repository.list_resources(db, models.ProgramAccreditationReadiness, tenant)
        institutional_readiness_rows = repository.list_resources(db, models.InstitutionalAccreditationReadiness, tenant)

        evidence_count_by_standard: dict[str, int] = defaultdict(int)
        for row in evidence_rows:
            key = _safe_text(getattr(row, "standard_ref", None), "UNSPECIFIED")
            evidence_count_by_standard[key] += 1

        limitation_count_by_standard: dict[str, int] = defaultdict(int)
        for row in limitation_rows:
            key = _safe_text(getattr(row, "standard_ref", None), "UNSPECIFIED")
            limitation_count_by_standard[key] += 1

        completion_values = [
            _as_int(getattr(row, "completion_percent", None), 0)
            for row in [*program_readiness_rows, *institutional_readiness_rows]
        ]
        baseline_completion = int(sum(completion_values) / len(completion_values)) if completion_values else 0

        standards: list[SelfAssessmentStandard] = []
        for row in standard_rows:
            standard_ref = _safe_text(getattr(row, "standard_ref", None), "UNSPECIFIED")
            evidence_count = evidence_count_by_standard.get(standard_ref, 0)
            limitation_count = limitation_count_by_standard.get(standard_ref, 0)
            evidence_coverage = min(100, evidence_count * 20)
            gap_count = limitation_count + (1 if evidence_count == 0 else 0)
            completion_percentage = max(0, min(100, baseline_completion + min(20, evidence_count * 5) - min(20, limitation_count * 5)))
            readiness_score = max(0, min(100, int((completion_percentage * 0.6) + (evidence_coverage * 0.4) - (gap_count * 4))))
            risk_level = _risk_level(readiness_score, gap_count)

            standards.append(
                SelfAssessmentStandard(
                    standard_id=standard_ref,
                    standard_name=_safe_text(getattr(row, "title", None), standard_ref),
                    accreditation_framework=_safe_text(getattr(row, "framework_ref", None), "QUALITY_FRAMEWORK"),
                    readiness_score=readiness_score,
                    completion_percentage=completion_percentage,
                    evidence_coverage=evidence_coverage,
                    gap_count=gap_count,
                    risk_level=risk_level,
                    owner_unit=_owner_unit(row),
                    last_updated=_coerce_datetime(getattr(row, "updated_at", None), generated_at),
                )
            )

        return SelfAssessmentRuntimeResponse(
            tenant_id=tenant,
            generated_at=generated_at,
            standards=standards,
            scorecard=_build_scorecard(standards),
            readiness_summary=_summarize_readiness(standards),
            coverage_summary=_summarize_coverage(standards),
            risk_summary=_summarize_risk(standards),
        )


self_assessment_runtime_service = SelfAssessmentRuntimeService()
