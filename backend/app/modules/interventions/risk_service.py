from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import asyncio
from time import perf_counter

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantResourceNotFoundError,
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
)
from app.modules.audit.service import log_admin_action
from app.modules.interventions.models import (
    InterventionActionModel,
    InterventionActionType,
    InterventionAssigneeType,
    InterventionCaseModel,
    InterventionCaseSeverity,
    InterventionCaseStatus,
    InterventionCaseType,
    OutcomeTrackingModel,
    RiskMetric,
    RiskSignalModel,
    RiskThresholdComparison,
    RiskThresholdModel,
)
from app.modules.observability.metrics import (
    observe_risk_recommendation_ack,
    observe_risk_scoring_duration,
    observe_risk_scoring_job,
    set_risk_high_band_students_total,
    set_risk_latest_snapshot_age_seconds,
)
from app.modules.interventions.schemas import (
    OutcomeTrackingUpsertSchema,
    RiskThresholdCreateSchema,
    RiskThresholdUpdateSchema,
)
from app.modules.scheduling.models import (
    AttendanceStatus,
    LessonAttendanceModel,
    LessonInstanceModel,
    LessonStatus,
    StudentTopicProgressModel,
)
from app.modules.students.models import StudentProfileModel


@dataclass(slots=True)
class RiskDetectionResult:
    tenant_id: int
    thresholds_evaluated: int
    signals_created: int
    cases_created: int


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _audit(*, actor: str, action: str, entity: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path="risk_service",
        client_ip="service",
        entity=entity,
        metadata=metadata,
        tenant_id=tenant_id,
    )


def _compare_metric(*, value: float, comparison: RiskThresholdComparison, threshold: float) -> bool:
    if comparison == RiskThresholdComparison.LTE:
        return value <= threshold
    if comparison == RiskThresholdComparison.GTE:
        return value >= threshold
    return value == threshold


def _default_assignment_for_severity(
    severity: InterventionCaseSeverity,
) -> tuple[InterventionAssigneeType, str]:
    if severity == InterventionCaseSeverity.HIGH:
        return InterventionAssigneeType.GROUP, "dean_office"
    if severity == InterventionCaseSeverity.MEDIUM:
        return InterventionAssigneeType.GROUP, "faculty_advisor"
    return InterventionAssigneeType.GROUP, "student_support"


def _default_due_at(severity: InterventionCaseSeverity) -> datetime:
    days = {
        InterventionCaseSeverity.HIGH: 3,
        InterventionCaseSeverity.MEDIUM: 5,
        InterventionCaseSeverity.LOW: 7,
    }[severity]
    return _utc_now() + timedelta(days=days)


class InterventionRiskService:
    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_threshold(
        self,
        *,
        tenant_id: int,
        request: RiskThresholdCreateSchema,
    ) -> RiskThresholdModel:
        tenant_id = validate_tenant_id_provided(tenant_id)
        threshold = RiskThresholdModel(
            tenant_id=tenant_id,
            risk_category=request.risk_category,
            rule_name=request.rule_name,
            metric=request.metric,
            threshold_value=request.threshold_value,
            comparison=request.comparison,
            severity_level=request.severity_level,
            signal_type=request.signal_type,
            enabled=request.enabled,
            auto_create_case=request.auto_create_case,
            window_days=request.window_days,
            escalate_to_refs_json=request.escalate_to_refs_json,
        )
        self.db.add(threshold)

        try:
            self.db.flush()
            self.db.refresh(threshold)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to create risk threshold due to constraint violation") from exc

        return threshold

    async def list_thresholds(self, *, tenant_id: int) -> list[RiskThresholdModel]:
        tenant_id = validate_tenant_id_provided(tenant_id)
        return self.db.execute(
            select(RiskThresholdModel)
            .where(RiskThresholdModel.tenant_id == tenant_id)
            .order_by(RiskThresholdModel.rule_name.asc())
        ).scalars().all()

    async def update_threshold(
        self,
        *,
        tenant_id: int,
        threshold_id: int,
        request: RiskThresholdUpdateSchema,
    ) -> RiskThresholdModel:
        threshold = await self.get_threshold(tenant_id=tenant_id, threshold_id=threshold_id)

        payload = request.model_dump(exclude_unset=True)
        for field, value in payload.items():
            setattr(threshold, field, value)

        try:
            self.db.flush()
            self.db.refresh(threshold)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to update risk threshold due to constraint violation") from exc

        return threshold

    async def get_threshold(self, *, tenant_id: int, threshold_id: int) -> RiskThresholdModel:
        tenant_id = validate_tenant_id_provided(tenant_id)
        threshold = self.db.execute(
            select(RiskThresholdModel).where(
                and_(
                    RiskThresholdModel.id == threshold_id,
                    RiskThresholdModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            threshold,
            tenant_id,
            resource_name="Risk threshold",
            resource_id=threshold_id,
        )
        return threshold

    async def list_signals(
        self,
        *,
        tenant_id: int,
        page: int,
        page_size: int,
    ) -> tuple[int, list[RiskSignalModel]]:
        tenant_id = validate_tenant_id_provided(tenant_id)

        filters = [RiskSignalModel.tenant_id == tenant_id]
        total = self.db.execute(
            select(func.count()).select_from(RiskSignalModel).where(and_(*filters))
        ).scalar_one()

        rows = self.db.execute(
            select(RiskSignalModel)
            .where(and_(*filters))
            .order_by(RiskSignalModel.detected_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        return int(total), rows

    async def get_student_latest_signal(
        self, *, tenant_id: int, student_profile_id: int
    ) -> RiskSignalModel:
        tenant_id = validate_tenant_id_provided(tenant_id)
        row = self.db.execute(
            select(RiskSignalModel)
            .where(
                and_(
                    RiskSignalModel.tenant_id == tenant_id,
                    RiskSignalModel.student_profile_id == student_profile_id,
                )
            )
            .order_by(RiskSignalModel.detected_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            row,
            tenant_id,
            resource_name="Risk signal",
            resource_id=student_profile_id,
        )
        return row

    async def list_student_signal_history(
        self,
        *,
        tenant_id: int,
        student_profile_id: int,
        page: int,
        page_size: int,
    ) -> tuple[int, list[RiskSignalModel]]:
        tenant_id = validate_tenant_id_provided(tenant_id)
        filters = and_(
            RiskSignalModel.tenant_id == tenant_id,
            RiskSignalModel.student_profile_id == student_profile_id,
        )
        total = int(
            self.db.execute(
                select(func.count()).select_from(RiskSignalModel).where(filters)
            ).scalar_one()
            or 0
        )
        rows = self.db.execute(
            select(RiskSignalModel)
            .where(filters)
            .order_by(RiskSignalModel.detected_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()
        return total, rows

    async def acknowledge_recommendation(
        self,
        *,
        tenant_id: int,
        recommendation_id: int,
        actor: str,
        note: str | None = None,
    ) -> InterventionActionModel:
        tenant_id = validate_tenant_id_provided(tenant_id)
        case = self.db.execute(
            select(InterventionCaseModel).where(
                and_(
                    InterventionCaseModel.id == recommendation_id,
                    InterventionCaseModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if case is None:
            observe_risk_recommendation_ack(tenant_id=tenant_id, status="error")
            raise TenantResourceNotFoundError("Recommendation", recommendation_id)

        action = InterventionActionModel(
            tenant_id=tenant_id,
            case_id=case.id,
            action_type=InterventionActionType.NOTE,
            description="Risk recommendation acknowledged",
            outcome_note=note,
            performed_by=actor,
            metadata_json={
                "source": "risk_recommendation_ack",
                "recommendation_id": recommendation_id,
            },
        )
        self.db.add(action)
        self.db.flush()
        self.db.refresh(action)
        self.db.commit()
        observe_risk_recommendation_ack(tenant_id=tenant_id, status="success")
        _audit(
            actor=actor,
            action="risk_recommendation.ack",
            entity=f"case:{case.id}",
            metadata={"recommendation_id": recommendation_id},
            tenant_id=tenant_id,
        )
        return action

    async def upsert_outcome(
        self,
        *,
        tenant_id: int,
        case_id: int,
        request: OutcomeTrackingUpsertSchema,
    ) -> OutcomeTrackingModel:
        tenant_id = validate_tenant_id_provided(tenant_id)

        case = self.db.execute(
            select(InterventionCaseModel).where(
                and_(
                    InterventionCaseModel.id == case_id,
                    InterventionCaseModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if case is None:
            raise TenantResourceNotFoundError("Intervention case", case_id)

        row = self.db.execute(
            select(OutcomeTrackingModel).where(
                and_(
                    OutcomeTrackingModel.case_id == case_id,
                    OutcomeTrackingModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        payload = request.model_dump()
        if row is None:
            row = OutcomeTrackingModel(tenant_id=tenant_id, case_id=case_id, **payload)
            self.db.add(row)
        else:
            for field, value in payload.items():
                setattr(row, field, value)

        self.db.flush()
        self.db.refresh(row)
        self.db.commit()
        return row

    async def get_outcome(self, *, tenant_id: int, case_id: int) -> OutcomeTrackingModel:
        tenant_id = validate_tenant_id_provided(tenant_id)
        row = self.db.execute(
            select(OutcomeTrackingModel).where(
                and_(
                    OutcomeTrackingModel.case_id == case_id,
                    OutcomeTrackingModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            row,
            tenant_id,
            resource_name="Outcome tracking",
            resource_id=case_id,
        )
        return row

    async def run_daily_detection(self, *, tenant_id: int, actor: str) -> RiskDetectionResult:
        tenant_id = validate_tenant_id_provided(tenant_id)
        thresholds = self.db.execute(
            select(RiskThresholdModel).where(
                and_(RiskThresholdModel.tenant_id == tenant_id, RiskThresholdModel.enabled.is_(True))
            )
        ).scalars().all()

        signals_created = 0
        cases_created = 0

        for threshold in thresholds:
            violations = self._load_violations(tenant_id=tenant_id, threshold=threshold)
            for student_profile_id, current_value, signal_data in violations:
                detected_on = _utc_now().date()

                already_exists = self.db.execute(
                    select(func.count())
                    .select_from(RiskSignalModel)
                    .where(
                        and_(
                            RiskSignalModel.tenant_id == tenant_id,
                            RiskSignalModel.student_profile_id == student_profile_id,
                            RiskSignalModel.threshold_id == threshold.id,
                            RiskSignalModel.detected_on == detected_on,
                        )
                    )
                ).scalar_one()
                if int(already_exists or 0) > 0:
                    continue

                associated_case_id: int | None = None
                if threshold.auto_create_case:
                    associated_case_id = self._ensure_open_case(
                        tenant_id=tenant_id,
                        student_profile_id=student_profile_id,
                        threshold=threshold,
                        actor=actor,
                        signal_data=signal_data,
                    )
                    if associated_case_id is not None:
                        cases_created += 1

                signal = RiskSignalModel(
                    tenant_id=tenant_id,
                    student_profile_id=student_profile_id,
                    threshold_id=threshold.id,
                    signal_type=threshold.signal_type,
                    detected_on=detected_on,
                    current_value=current_value,
                    threshold_value=threshold.threshold_value,
                    severity=threshold.severity_level,
                    signal_data_json=signal_data,
                    associated_case_id=associated_case_id,
                )
                self.db.add(signal)
                signals_created += 1

        self.db.flush()
        self.db.commit()

        _audit(
            actor=actor,
            action="risk_detection.run",
            entity="risk_detection",
            metadata={
                "thresholds_evaluated": len(thresholds),
                "signals_created": signals_created,
                "cases_created": cases_created,
            },
            tenant_id=tenant_id,
        )

        return RiskDetectionResult(
            tenant_id=tenant_id,
            thresholds_evaluated=len(thresholds),
            signals_created=signals_created,
            cases_created=cases_created,
        )

    async def _refresh_observability_snapshot(self, *, tenant_id: int) -> None:
        tenant_id = validate_tenant_id_provided(tenant_id)
        high_band_total = int(
            self.db.execute(
                select(func.count(func.distinct(RiskSignalModel.student_profile_id))).where(
                    and_(
                        RiskSignalModel.tenant_id == tenant_id,
                        RiskSignalModel.severity == InterventionCaseSeverity.HIGH,
                    )
                )
            ).scalar_one()
            or 0
        )
        latest_detected_at = self.db.execute(
            select(func.max(RiskSignalModel.detected_at)).where(
                RiskSignalModel.tenant_id == tenant_id
            )
        ).scalar_one_or_none()
        age_seconds = 0.0
        if latest_detected_at is not None:
            age_seconds = max(0.0, (_utc_now() - latest_detected_at).total_seconds())

        set_risk_high_band_students_total(tenant_id=tenant_id, total=high_band_total)
        set_risk_latest_snapshot_age_seconds(tenant_id=tenant_id, age_seconds=age_seconds)

    async def recompute_scores(self, *, tenant_id: int, actor: str) -> RiskDetectionResult:
        tenant_id = validate_tenant_id_provided(tenant_id)
        started_at = perf_counter()
        try:
            result = await self.run_daily_detection(tenant_id=tenant_id, actor=actor)
            await self._refresh_observability_snapshot(tenant_id=tenant_id)
        except Exception:
            duration_seconds = perf_counter() - started_at
            observe_risk_scoring_job(tenant_id=tenant_id, status="error")
            observe_risk_scoring_duration(
                tenant_id=tenant_id,
                status="error",
                duration_seconds=duration_seconds,
            )
            raise

        duration_seconds = perf_counter() - started_at
        observe_risk_scoring_job(tenant_id=tenant_id, status="success")
        observe_risk_scoring_duration(
            tenant_id=tenant_id,
            status="success",
            duration_seconds=duration_seconds,
        )
        return result

    async def get_kpi_summary(self, *, tenant_id: int) -> dict[str, object]:
        tenant_id = validate_tenant_id_provided(tenant_id)
        since = _utc_now() - timedelta(hours=24)

        open_cases_total = int(
            self.db.execute(
                select(func.count())
                .select_from(InterventionCaseModel)
                .where(
                    and_(
                        InterventionCaseModel.tenant_id == tenant_id,
                        InterventionCaseModel.status.in_(
                            (InterventionCaseStatus.OPEN, InterventionCaseStatus.IN_PROGRESS)
                        ),
                    )
                )
            ).scalar_one()
            or 0
        )

        signals_last_24h = int(
            self.db.execute(
                select(func.count())
                .select_from(RiskSignalModel)
                .where(
                    and_(
                        RiskSignalModel.tenant_id == tenant_id,
                        RiskSignalModel.detected_at >= since,
                    )
                )
            ).scalar_one()
            or 0
        )

        auto_created_cases_last_24h = int(
            self.db.execute(
                select(func.count())
                .select_from(InterventionCaseModel)
                .where(
                    and_(
                        InterventionCaseModel.tenant_id == tenant_id,
                        InterventionCaseModel.created_at >= since,
                        InterventionCaseModel.created_by == "risk-engine",
                    )
                )
            ).scalar_one()
            or 0
        )

        severity_rows = self.db.execute(
            select(RiskSignalModel.severity, func.count())
            .where(
                and_(
                    RiskSignalModel.tenant_id == tenant_id,
                    RiskSignalModel.detected_at >= since,
                )
            )
            .group_by(RiskSignalModel.severity)
        ).all()

        severity_breakdown: dict[str, int] = {}
        for row in severity_rows:
            if isinstance(row, tuple) and len(row) >= 2:
                level, count = row[0], row[1]
            else:
                level = getattr(row, "severity", None)
                count = getattr(row, "count", 0)
            key = str(getattr(level, "value", level))
            severity_breakdown[key] = int(count or 0)

        return {
            "tenant_id": tenant_id,
            "open_cases_total": open_cases_total,
            "signals_last_24h": signals_last_24h,
            "auto_created_cases_last_24h": auto_created_cases_last_24h,
            "severity_breakdown": severity_breakdown,
        }

    def _load_violations(
        self,
        *,
        tenant_id: int,
        threshold: RiskThresholdModel,
    ) -> list[tuple[int, float, dict]]:
        now = _utc_now()
        try:
            window_days = int(getattr(threshold, "window_days", 30))
        except (TypeError, ValueError):
            window_days = 30
        if window_days <= 0:
            window_days = 30
        since = now - timedelta(days=window_days)

        if threshold.metric == RiskMetric.ABSENCE_COUNT:
            rows = self.db.execute(
                select(
                    LessonAttendanceModel.student_profile_id,
                    func.count(LessonAttendanceModel.id).label("absence_count"),
                )
                .join(
                    LessonInstanceModel,
                    and_(
                        LessonInstanceModel.tenant_id == LessonAttendanceModel.tenant_id,
                        LessonInstanceModel.id == LessonAttendanceModel.lesson_instance_id,
                    ),
                )
                .where(
                    and_(
                        LessonAttendanceModel.tenant_id == tenant_id,
                        LessonAttendanceModel.attendance_status == AttendanceStatus.ABSENT,
                        LessonInstanceModel.status == LessonStatus.COMPLETED,
                        LessonAttendanceModel.marked_at >= since,
                    )
                )
                .group_by(LessonAttendanceModel.student_profile_id)
            ).all()

            return [
                (
                    int(student_id),
                    float(absence_count),
                    {
                        "metric": RiskMetric.ABSENCE_COUNT.value,
                        "window_days": window_days,
                        "absence_count": int(absence_count),
                    },
                )
                for student_id, absence_count in rows
                if _compare_metric(
                    value=float(absence_count),
                    comparison=threshold.comparison,
                    threshold=float(threshold.threshold_value),
                )
            ]

        if threshold.metric == RiskMetric.QUIZ_BEST_SCORE:
            rows = self.db.execute(
                select(
                    StudentTopicProgressModel.student_profile_id,
                    func.min(StudentTopicProgressModel.quiz_best_score).label("best_score"),
                )
                .where(
                    and_(
                        StudentTopicProgressModel.tenant_id == tenant_id,
                        StudentTopicProgressModel.quiz_best_score.is_not(None),
                        StudentTopicProgressModel.updated_at >= since,
                    )
                )
                .group_by(StudentTopicProgressModel.student_profile_id)
            ).all()

            return [
                (
                    int(student_id),
                    float(best_score),
                    {
                        "metric": RiskMetric.QUIZ_BEST_SCORE.value,
                        "window_days": window_days,
                        "quiz_best_score": float(best_score),
                    },
                )
                for student_id, best_score in rows
                if best_score is not None
                and _compare_metric(
                    value=float(best_score),
                    comparison=threshold.comparison,
                    threshold=float(threshold.threshold_value),
                )
            ]

        return []

    def _ensure_open_case(
        self,
        *,
        tenant_id: int,
        student_profile_id: int,
        threshold: RiskThresholdModel,
        actor: str,
        signal_data: dict,
    ) -> int | None:
        student = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.tenant_id == tenant_id,
                    StudentProfileModel.id == student_profile_id,
                )
            )
        ).scalar_one_or_none()
        if student is None:
            return None

        existing = self.db.execute(
            select(InterventionCaseModel.id)
            .where(
                and_(
                    InterventionCaseModel.tenant_id == tenant_id,
                    InterventionCaseModel.student_profile_id == student_profile_id,
                    InterventionCaseModel.case_type == InterventionCaseType.ACADEMIC_RISK,
                    InterventionCaseModel.status.in_(
                        (InterventionCaseStatus.OPEN, InterventionCaseStatus.IN_PROGRESS)
                    ),
                )
            )
            .order_by(InterventionCaseModel.id.desc())
            .limit(1)
        ).scalar_one_or_none()
        if existing is not None:
            return int(existing)

        assignee_type, assignee_ref = _default_assignment_for_severity(threshold.severity_level)
        if threshold.escalate_to_refs_json:
            assignee_ref = str(threshold.escalate_to_refs_json[0])

        case = InterventionCaseModel(
            tenant_id=tenant_id,
            case_type=InterventionCaseType.ACADEMIC_RISK,
            student_profile_id=student_profile_id,
            severity=threshold.severity_level,
            status=InterventionCaseStatus.OPEN,
            title=f"Auto risk: {threshold.rule_name}",
            description=(
                f"Auto-detected risk for student={student_profile_id} by rule '{threshold.rule_name}'"
            ),
            risk_snapshot_json={
                "rule_name": threshold.rule_name,
                "metric": threshold.metric.value,
                "threshold_value": threshold.threshold_value,
                "comparison": threshold.comparison.value,
                "signal_data": signal_data,
            },
            assignee_type=assignee_type,
            assignee_ref=assignee_ref,
            due_at=_default_due_at(threshold.severity_level),
            metadata_json={"source": "ai_risk_engine"},
            created_by=actor,
            updated_by=actor,
        )
        self.db.add(case)
        self.db.flush()

        self.db.add(
            InterventionActionModel(
                tenant_id=tenant_id,
                case_id=case.id,
                action_type=InterventionActionType.ASSIGNMENT,
                description=f"Auto-assigned by risk engine to {assignee_type.value}:{assignee_ref}",
                outcome_note=None,
                performed_by=actor,
                metadata_json={"auto_assignment": True, "source": "ai_risk_engine"},
            )
        )

        return int(case.id)


def run_daily_detection_for_all_tenants(*, db_session: Session, actor: str = "risk-engine") -> dict[str, int]:
    tenant_rows = db_session.execute(select(RiskThresholdModel.tenant_id).distinct()).scalars().all()
    service = InterventionRiskService(db_session)

    processed = 0
    created_signals = 0
    created_cases = 0

    for tenant_id in tenant_rows:
        item = asyncio.run(service.run_daily_detection(tenant_id=int(tenant_id), actor=actor))
        processed += 1
        created_signals += item.signals_created
        created_cases += item.cases_created

    return {
        "tenants_processed": processed,
        "signals_created": created_signals,
        "cases_created": created_cases,
    }
