"""Read-only accreditation evidence runtime service for Quality / Accreditation."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.modules.quality_accreditation import models, repository
from app.modules.quality_accreditation.dependencies import validate_tenant_id
from app.modules.quality_accreditation.quality_accreditation_evidence_schemas import (
    AccreditationEvidenceItem,
    AccreditationEvidenceRuntimeResponse,
    EvidenceCategorySummary,
    EvidenceCoverageSummary,
    EvidenceReadinessSummary,
    EvidenceRiskSummary,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _coerce_datetime(value: object | None, fallback: datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return fallback


def _as_int(value: object | None, fallback: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return fallback


def _safe_text(value: object | None, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _evidence_category(item: Any) -> str:
    metadata = getattr(item, "metadata_json", None)
    if isinstance(metadata, dict):
        raw = metadata.get("evidence_category")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return _safe_text(getattr(item, "criterion_ref", None), "GENERAL")


def _owner_unit(item: Any) -> str:
    return _safe_text(getattr(item, "source_family_id", None), _safe_text(getattr(item, "source_capability_id", None), "quality_accreditation"))


def _review_score(status: str) -> int:
    status_upper = status.upper()
    if status_upper == models.EvidenceReviewStatus.ACCEPTED_METADATA_ONLY:
        return 100
    if status_upper == models.EvidenceReviewStatus.REVIEWED_METADATA_ONLY:
        return 85
    if status_upper == models.EvidenceReviewStatus.SUBMITTED_FOR_REVIEW:
        return 70
    if status_upper == models.EvidenceReviewStatus.LIMITATION_RECORDED:
        return 45
    if status_upper in {models.EvidenceReviewStatus.MISSING, models.EvidenceReviewStatus.EXPIRED}:
        return 20
    return 55


def _base_score(status: str) -> int:
    status_upper = status.upper()
    if status_upper in {
        models.EvidenceReviewStatus.REVIEWED_METADATA_ONLY,
        models.EvidenceReviewStatus.ACCEPTED_METADATA_ONLY,
    }:
        return 85
    if status_upper == models.EvidenceReviewStatus.SUBMITTED_FOR_REVIEW:
        return 70
    if status_upper in {models.EvidenceReviewStatus.DRAFT, models.EvidenceReviewStatus.LIMITATION_RECORDED}:
        return 50
    if status_upper in {models.EvidenceReviewStatus.MISSING, models.EvidenceReviewStatus.EXPIRED}:
        return 20
    return 55


def _completeness_score(item: Any, review_scores: list[int], limitation_penalty: int) -> int:
    status = _safe_text(getattr(item, "status", None), models.EvidenceReviewStatus.DRAFT)
    score = _base_score(status)
    if review_scores:
        score = max(score, int(sum(review_scores) / len(review_scores)))
    score -= limitation_penalty
    return max(0, min(100, score))


def _risk_level(item: Any, completeness_score: int, has_limitation: bool) -> str:
    status = _safe_text(getattr(item, "status", None), "UNKNOWN").upper()
    if has_limitation or status in {models.EvidenceReviewStatus.MISSING, models.EvidenceReviewStatus.EXPIRED}:
        return "HIGH"
    if completeness_score >= 85:
        return "LOW"
    if completeness_score >= 60:
        return "MEDIUM"
    return "HIGH"


def _readiness_band(completeness_score: int) -> str:
    if completeness_score >= 85:
        return "READY"
    if completeness_score >= 60:
        return "IN_PROGRESS"
    return "NEEDS_ATTENTION"


def _coverage_scope(item: AccreditationEvidenceItem) -> str:
    return item.accreditation_standard if item.accreditation_standard != "UNSPECIFIED" else item.evidence_category


def _summarize_categories(items: list[AccreditationEvidenceItem]) -> list[EvidenceCategorySummary]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for item in items:
        grouped[item.evidence_category].append(item.completeness_score)

    return [
        EvidenceCategorySummary(
            evidence_category=category,
            evidence_count=len(scores),
            average_completeness_score=sum(scores) / len(scores),
        )
        for category, scores in sorted(grouped.items())
    ]


def _summarize_readiness(items: list[AccreditationEvidenceItem]) -> list[EvidenceReadinessSummary]:
    grouped: dict[str, int] = defaultdict(int)
    for item in items:
        grouped[_readiness_band(item.completeness_score)] += 1

    return [EvidenceReadinessSummary(readiness_band=band, evidence_count=count) for band, count in sorted(grouped.items())]


def _summarize_coverage(items: list[AccreditationEvidenceItem]) -> list[EvidenceCoverageSummary]:
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"evidence_count": 0, "covered_count": 0})

    for item in items:
        scope = _coverage_scope(item)
        grouped[scope]["evidence_count"] += 1
        if item.completeness_score >= 60:
            grouped[scope]["covered_count"] += 1

    output: list[EvidenceCoverageSummary] = []
    for scope, values in sorted(grouped.items()):
        evidence_count = values["evidence_count"]
        covered_count = values["covered_count"]
        coverage_percent = (covered_count / evidence_count * 100.0) if evidence_count else 0.0
        output.append(
            EvidenceCoverageSummary(
                coverage_scope=scope,
                evidence_count=evidence_count,
                covered_count=covered_count,
                coverage_percent=coverage_percent,
            )
        )

    return output


def _summarize_risk(items: list[AccreditationEvidenceItem]) -> list[EvidenceRiskSummary]:
    grouped: dict[str, int] = defaultdict(int)
    for item in items:
        grouped[item.risk_level] += 1

    return [EvidenceRiskSummary(risk_level=risk_level, evidence_count=count) for risk_level, count in sorted(grouped.items())]


class AccreditationEvidenceRuntimeService:
    """Read-only aggregation service for accreditation evidence runtime."""

    def get_accreditation_evidence_runtime(self, db: Session, tenant_id: int) -> AccreditationEvidenceRuntimeResponse:
        tenant = validate_tenant_id(tenant_id)
        generated_at = _now()

        evidence_rows = repository.list_resources(db, models.QualityEvidenceRegistry, tenant)
        review_rows = repository.list_resources(db, models.EvidenceReview, tenant)
        limitation_rows = repository.list_resources(db, models.EvidenceLimitation, tenant)

        review_scores_by_evidence: dict[str, list[int]] = defaultdict(list)
        for row in review_rows:
            evidence_ref = getattr(row, "evidence_ref", None)
            if evidence_ref:
                review_scores_by_evidence[str(evidence_ref)].append(_review_score(_safe_text(getattr(row, "status", None), models.EvidenceReviewStatus.DRAFT)))

        limitation_count_by_evidence: dict[str, int] = defaultdict(int)
        for row in limitation_rows:
            evidence_ref = getattr(row, "evidence_ref", None)
            if evidence_ref:
                limitation_count_by_evidence[str(evidence_ref)] += 1

        inventory: list[AccreditationEvidenceItem] = []
        for row in evidence_rows:
            evidence_ref = _safe_text(getattr(row, "evidence_ref", None), f"EVID-{_as_int(getattr(row, 'id', None), 0)}")
            review_scores = review_scores_by_evidence.get(evidence_ref, [])
            limitation_count = limitation_count_by_evidence.get(evidence_ref, 0)
            limitation_penalty = min(20, limitation_count * 10)
            completeness_score = _completeness_score(row, review_scores, limitation_penalty)
            risk_level = _risk_level(row, completeness_score, limitation_count > 0)

            inventory.append(
                AccreditationEvidenceItem(
                    evidence_id=evidence_ref,
                    evidence_name=_safe_text(getattr(row, "title", None), evidence_ref),
                    evidence_category=_evidence_category(row),
                    accreditation_standard=_safe_text(getattr(row, "standard_ref", None), "UNSPECIFIED"),
                    accreditation_section=_safe_text(getattr(row, "criterion_ref", None), "UNSPECIFIED"),
                    owner_unit=_owner_unit(row),
                    evidence_status=_safe_text(getattr(row, "status", None), "UNKNOWN"),
                    completeness_score=completeness_score,
                    last_updated=_coerce_datetime(getattr(row, "updated_at", None), generated_at),
                    risk_level=risk_level,
                )
            )

        return AccreditationEvidenceRuntimeResponse(
            tenant_id=tenant,
            generated_at=generated_at,
            evidence_inventory=inventory,
            evidence_categories=_summarize_categories(inventory),
            evidence_readiness=_summarize_readiness(inventory),
            evidence_coverage=_summarize_coverage(inventory),
            evidence_risk=_summarize_risk(inventory),
        )


accreditation_evidence_runtime_service = AccreditationEvidenceRuntimeService()
