from __future__ import annotations

from datetime import UTC, datetime
import time

from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantResourceNotFoundError,
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
)
from app.modules.interventions.effectiveness_models import (
    InterventionCohortModel,
    InterventionCohortOutcomeModel,
)
from app.modules.interventions.effectiveness_schemas import (
    CohortAnalyzeRequestSchema,
    CohortFinalizeRequestSchema,
)
from app.modules.observability.metrics import (
    observe_f3_analysis_queue_enqueued,
    observe_f3_cohort_operation,
    observe_f3_guardrail_evaluation,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class InterventionEffectivenessService:
    """F3 intervention effectiveness cohort service."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def _validate_tenant_guardrail(self, *, tenant_id: int) -> None:
        try:
            validate_tenant_id_provided(tenant_id)
        except Exception:
            observe_f3_guardrail_evaluation(
                tenant_id=tenant_id,
                guardrail="tenant_id_provided",
                result="fail",
            )
            raise
        observe_f3_guardrail_evaluation(
            tenant_id=tenant_id,
            guardrail="tenant_id_provided",
            result="pass",
        )

    def finalize_cohort(
        self,
        *,
        tenant_id: int,
        actor: str,
        payload: CohortFinalizeRequestSchema,
    ) -> InterventionCohortModel:
        started = time.perf_counter()
        status = "success"
        try:
            self._validate_tenant_guardrail(tenant_id=tenant_id)
            cohort = InterventionCohortModel(
                tenant_id=tenant_id,
                playbook_id=payload.playbook_id,
                cohort_name=payload.cohort_name,
                analysis_window_start=payload.analysis_window_start,
                analysis_window_end=payload.analysis_window_end,
                student_count=0,
                created_by=actor,
                created_at=_utc_now(),
            )
            self._db.add(cohort)
            self._db.flush()
            return cohort
        except Exception:
            status = "error"
            raise
        finally:
            observe_f3_cohort_operation(
                tenant_id=tenant_id,
                operation="finalize",
                status=status,
                duration_seconds=time.perf_counter() - started,
            )

    def get_outcomes(
        self,
        *,
        tenant_id: int,
        cohort_id: int,
    ) -> list[InterventionCohortOutcomeModel]:
        started = time.perf_counter()
        status = "success"
        try:
            self._validate_tenant_guardrail(tenant_id=tenant_id)

            cohort = self._db.scalar(
                select(InterventionCohortModel).where(InterventionCohortModel.id == cohort_id)
            )
            if cohort is None:
                raise TenantResourceNotFoundError(f"Cohort {cohort_id} not found.")
            assert_resource_belongs_to_tenant(cohort, tenant_id)

            return list(
                self._db.scalars(
                    select(InterventionCohortOutcomeModel)
                    .where(InterventionCohortOutcomeModel.cohort_id == cohort_id)
                    .order_by(
                        InterventionCohortOutcomeModel.outcome_type,
                        InterventionCohortOutcomeModel.segment_name,
                    )
                )
            )
        except Exception:
            status = "error"
            raise
        finally:
            observe_f3_cohort_operation(
                tenant_id=tenant_id,
                operation="fetch_outcomes",
                status=status,
                duration_seconds=time.perf_counter() - started,
            )

    def list_cohorts(
        self,
        *,
        tenant_id: int,
    ) -> list[InterventionCohortModel]:
        started = time.perf_counter()
        status = "success"
        try:
            self._validate_tenant_guardrail(tenant_id=tenant_id)
            return list(
                self._db.scalars(
                    select(InterventionCohortModel)
                    .where(InterventionCohortModel.tenant_id == tenant_id)
                    .order_by(desc(InterventionCohortModel.created_at), desc(InterventionCohortModel.id))
                )
            )
        except Exception:
            status = "error"
            raise
        finally:
            observe_f3_cohort_operation(
                tenant_id=tenant_id,
                operation="fetch_list",
                status=status,
                duration_seconds=time.perf_counter() - started,
            )

    def get_cohort(
        self,
        *,
        tenant_id: int,
        cohort_id: int,
    ) -> InterventionCohortModel:
        started = time.perf_counter()
        status = "success"
        try:
            self._validate_tenant_guardrail(tenant_id=tenant_id)
            cohort = self._db.scalar(
                select(InterventionCohortModel).where(InterventionCohortModel.id == cohort_id)
            )
            if cohort is None:
                raise TenantResourceNotFoundError(f"Cohort {cohort_id} not found.")
            assert_resource_belongs_to_tenant(cohort, tenant_id)
            return cohort
        except Exception:
            status = "error"
            raise
        finally:
            observe_f3_cohort_operation(
                tenant_id=tenant_id,
                operation="fetch_detail",
                status=status,
                duration_seconds=time.perf_counter() - started,
            )

    def get_latest_by_playbook(
        self,
        *,
        tenant_id: int,
        playbook_id: int,
    ) -> InterventionCohortModel:
        started = time.perf_counter()
        status = "success"
        try:
            self._validate_tenant_guardrail(tenant_id=tenant_id)

            cohort = self._db.scalar(
                select(InterventionCohortModel)
                .where(
                    and_(
                        InterventionCohortModel.tenant_id == tenant_id,
                        InterventionCohortModel.playbook_id == playbook_id,
                    )
                )
                .order_by(desc(InterventionCohortModel.analysis_window_end), desc(InterventionCohortModel.id))
                .limit(1)
            )
            if cohort is None:
                raise TenantResourceNotFoundError(
                    f"No cohort found for playbook {playbook_id}."
                )
            return cohort
        except Exception:
            status = "error"
            raise
        finally:
            observe_f3_cohort_operation(
                tenant_id=tenant_id,
                operation="fetch_latest_by_playbook",
                status=status,
                duration_seconds=time.perf_counter() - started,
            )

    def finalize_existing_cohort(
        self,
        *,
        tenant_id: int,
        cohort_id: int,
    ) -> InterventionCohortModel:
        started = time.perf_counter()
        status = "success"
        try:
            self._validate_tenant_guardrail(tenant_id=tenant_id)
            cohort = self._db.scalar(
                select(InterventionCohortModel).where(InterventionCohortModel.id == cohort_id)
            )
            if cohort is None:
                raise TenantResourceNotFoundError(f"Cohort {cohort_id} not found.")
            assert_resource_belongs_to_tenant(cohort, tenant_id)

            if cohort.student_count <= 0:
                cohort.student_count = 1

            self._db.flush()
            return cohort
        except Exception:
            status = "error"
            raise
        finally:
            observe_f3_cohort_operation(
                tenant_id=tenant_id,
                operation="finalize_existing",
                status=status,
                duration_seconds=time.perf_counter() - started,
            )

    def analyze_cohort(
        self,
        *,
        tenant_id: int,
        cohort_id: int,
        actor: str,
        payload: CohortAnalyzeRequestSchema,
    ) -> dict[str, object]:
        started = time.perf_counter()
        status = "success"
        try:
            self._validate_tenant_guardrail(tenant_id=tenant_id)

            cohort = self._db.scalar(
                select(InterventionCohortModel).where(InterventionCohortModel.id == cohort_id)
            )
            if cohort is None:
                raise TenantResourceNotFoundError(f"Cohort {cohort_id} not found.")
            assert_resource_belongs_to_tenant(cohort, tenant_id)

            if cohort.student_count <= 0 and cohort.data_completeness_pct is None:
                raise DomainValidationError("Cohort must be finalized before analysis.")

            observe_f3_analysis_queue_enqueued(tenant_id=tenant_id)

            return {
                "cohort_id": cohort.id,
                "status": "analysis_queued",
                "detail": f"Effectiveness analysis queued for cohort {cohort_id}.",
                "requested_at": _utc_now(),
            }
        except Exception:
            status = "error"
            raise
        finally:
            observe_f3_cohort_operation(
                tenant_id=tenant_id,
                operation="analyze",
                status=status,
                duration_seconds=time.perf_counter() - started,
            )
