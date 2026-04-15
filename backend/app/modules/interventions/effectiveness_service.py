from __future__ import annotations

from datetime import UTC, datetime

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


def _utc_now() -> datetime:
    return datetime.now(UTC)


class InterventionEffectivenessService:
    """F3 design-only service skeleton for intervention effectiveness cohorts."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def finalize_cohort(
        self,
        *,
        tenant_id: int,
        actor: str,
        payload: CohortFinalizeRequestSchema,
    ) -> InterventionCohortModel:
        validate_tenant_id_provided(tenant_id)
        raise DomainValidationError(
            "F3 finalize_cohort is frozen until F3.3 delivery is officially unfrozen."
        )

    def get_outcomes(
        self,
        *,
        tenant_id: int,
        cohort_id: int,
    ) -> list[InterventionCohortOutcomeModel]:
        validate_tenant_id_provided(tenant_id)

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

    def get_latest_by_playbook(
        self,
        *,
        tenant_id: int,
        playbook_id: int,
    ) -> InterventionCohortModel:
        validate_tenant_id_provided(tenant_id)

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

    def analyze_cohort(
        self,
        *,
        tenant_id: int,
        cohort_id: int,
        actor: str,
        payload: CohortAnalyzeRequestSchema,
    ) -> dict[str, object]:
        validate_tenant_id_provided(tenant_id)

        cohort = self._db.scalar(
            select(InterventionCohortModel).where(InterventionCohortModel.id == cohort_id)
        )
        if cohort is None:
            raise TenantResourceNotFoundError(f"Cohort {cohort_id} not found.")
        assert_resource_belongs_to_tenant(cohort, tenant_id)

        raise DomainValidationError(
            "F3 analyze_cohort is frozen until F3.3 delivery is officially unfrozen."
        )
