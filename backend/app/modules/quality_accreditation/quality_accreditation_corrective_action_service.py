"""Read-only corrective action runtime service for Quality / Accreditation."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.modules.quality_accreditation import models, repository
from app.modules.quality_accreditation.dependencies import validate_tenant_id
from app.modules.quality_accreditation.quality_accreditation_corrective_action_schemas import (
    CorrectiveActionItem,
    CorrectiveActionOverdueSummary,
    CorrectiveActionReadinessSummary,
    CorrectiveActionRiskSummary,
    CorrectiveActionRuntimeResponse,
    CorrectiveActionSummary,
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
    return _safe_text(getattr(item, "owner_ref", None), _safe_text(getattr(item, "source_family_id", None), "quality_accreditation"))


def _completion_percentage(status: str, evidence_count: int, gap_count: int) -> int:
    status_upper = status.upper()
    if "COMPLETED" in status_upper:
        return 100
    if "DELAYED" in status_upper:
        return max(10, 45 - (gap_count * 10))
    if "ACTIVE" in status_upper:
        return min(95, 55 + (evidence_count * 10) - (gap_count * 5))
    return max(5, 35 + (evidence_count * 8) - (gap_count * 8))


def _readiness_score(completion_percentage: int, gap_count: int, overdue: bool) -> int:
    score = completion_percentage - (gap_count * 5) - (15 if overdue else 0)
    return max(0, min(100, score))


def _risk_level(readiness_score: int, overdue: bool, gap_count: int) -> str:
    if overdue or readiness_score < 50 or gap_count >= 3:
        return "HIGH"
    if readiness_score < 75 or gap_count >= 1:
        return "MEDIUM"
    return "LOW"


def _readiness_band(score: int) -> str:
    if score >= 85:
        return "READY"
    if score >= 60:
        return "IN_PROGRESS"
    return "NEEDS_ATTENTION"


def _build_action_summary(items: list[CorrectiveActionItem]) -> CorrectiveActionSummary:
    if not items:
        return CorrectiveActionSummary()

    completed = len([item for item in items if item.completion_percentage >= 100])
    in_progress = len([item for item in items if 0 < item.completion_percentage < 100])
    overdue = len([item for item in items if item.overdue_flag])

    return CorrectiveActionSummary(
        total_actions=len(items),
        completed_actions=completed,
        in_progress_actions=in_progress,
        overdue_actions=overdue,
        average_completion_percentage=sum(item.completion_percentage for item in items) / len(items),
    )


def _summarize_readiness(items: list[CorrectiveActionItem]) -> list[CorrectiveActionReadinessSummary]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for item in items:
        grouped[_readiness_band(item.readiness_score)].append(item.readiness_score)

    output: list[CorrectiveActionReadinessSummary] = []
    for band, scores in sorted(grouped.items()):
        output.append(
            CorrectiveActionReadinessSummary(
                readiness_band=band,
                action_count=len(scores),
                average_readiness_score=sum(scores) / len(scores),
            )
        )
    return output


def _summarize_risk(items: list[CorrectiveActionItem]) -> list[CorrectiveActionRiskSummary]:
    grouped: dict[str, int] = defaultdict(int)
    for item in items:
        grouped[item.risk_level] += 1

    return [CorrectiveActionRiskSummary(risk_level=risk, action_count=count) for risk, count in sorted(grouped.items())]


def _summarize_overdue(items: list[CorrectiveActionItem]) -> list[CorrectiveActionOverdueSummary]:
    overdue = len([item for item in items if item.overdue_flag])
    not_overdue = len(items) - overdue
    return [
        CorrectiveActionOverdueSummary(overdue_state="NOT_OVERDUE", action_count=not_overdue),
        CorrectiveActionOverdueSummary(overdue_state="OVERDUE", action_count=overdue),
    ]


class CorrectiveActionRuntimeService:
    """Read-only aggregation service for corrective action runtime."""

    def get_corrective_action_runtime(self, db: Session, tenant_id: int) -> CorrectiveActionRuntimeResponse:
        tenant = validate_tenant_id(tenant_id)
        generated_at = _now()

        action_rows = repository.list_resources(db, models.QualityImprovementAction, tenant)
        evidence_rows = repository.list_resources(db, models.QualityEvidenceRegistry, tenant)
        finding_rows = repository.list_resources(db, models.QualityAuditFinding, tenant)

        evidence_by_standard: dict[str, int] = defaultdict(int)
        for row in evidence_rows:
            standard_ref = _safe_text(getattr(row, "standard_ref", None), "UNSPECIFIED")
            evidence_by_standard[standard_ref] += 1

        findings_by_action: dict[str, str] = {}
        for row in finding_rows:
            action_ref = _safe_text(getattr(row, "action_ref", None), "")
            if action_ref:
                findings_by_action[action_ref] = _safe_text(getattr(row, "finding_ref", None), "UNSPECIFIED")

        corrective_actions: list[CorrectiveActionItem] = []
        for row in action_rows:
            action_ref = _safe_text(getattr(row, "action_ref", None), f"ACT-{_as_int(getattr(row, 'id', None), 0)}")
            standard_ref = _safe_text(getattr(row, "standard_ref", None), "UNSPECIFIED")
            evidence_count = evidence_by_standard.get(standard_ref, 0)
            gap_count = max(0, 2 - min(2, evidence_count))
            base_updated_at = _coerce_datetime(getattr(row, "updated_at", None), generated_at)
            due_date = _coerce_datetime(getattr(row, "archived_at", None), base_updated_at + timedelta(days=30))
            status = _safe_text(getattr(row, "status", None), "DRAFT")
            completion = max(0, min(100, _completion_percentage(status, evidence_count, gap_count)))
            overdue_flag = due_date < generated_at and completion < 100
            readiness_score = _readiness_score(completion, gap_count, overdue_flag)
            risk_level = _risk_level(readiness_score, overdue_flag, gap_count)

            corrective_actions.append(
                CorrectiveActionItem(
                    action_id=action_ref,
                    action_title=_safe_text(getattr(row, "title", None), action_ref),
                    accreditation_standard=standard_ref,
                    finding_reference=findings_by_action.get(action_ref, _safe_text(getattr(row, "plan_ref", None), "UNSPECIFIED")),
                    owner_unit=_owner_unit(row),
                    due_date=due_date,
                    completion_percentage=completion,
                    status=status,
                    readiness_score=readiness_score,
                    risk_level=risk_level,
                    overdue_flag=overdue_flag,
                    last_updated=base_updated_at,
                )
            )

        return CorrectiveActionRuntimeResponse(
            tenant_id=tenant,
            generated_at=generated_at,
            corrective_actions=corrective_actions,
            action_summary=_build_action_summary(corrective_actions),
            readiness_summary=_summarize_readiness(corrective_actions),
            risk_summary=_summarize_risk(corrective_actions),
            overdue_summary=_summarize_overdue(corrective_actions),
        )


corrective_action_runtime_service = CorrectiveActionRuntimeService()
