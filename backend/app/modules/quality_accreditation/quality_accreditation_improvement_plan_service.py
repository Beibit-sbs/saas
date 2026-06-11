"""Read-only deterministic improvement plan runtime service for Quality / Accreditation."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.quality_accreditation.dependencies import validate_tenant_id
from app.modules.quality_accreditation.quality_accreditation_improvement_plan_schemas import (
    ImprovementForecastDTO,
    ImprovementInitiativeDTO,
    ImprovementKpiTargetDTO,
    ImprovementMilestoneDTO,
    ImprovementPlanRuntimeDTO,
    ImprovementPlanRuntimeResponseDTO,
    ImprovementRoadmapDTO,
)


def _now() -> datetime:
    return datetime.now(UTC)


class ImprovementPlanRuntimeService:
    """Provides read-only deterministic runtime payload for improvement plans."""

    def get_improvement_plan_runtime(self, db: Session, tenant_id: int) -> ImprovementPlanRuntimeResponseDTO:
        del db
        tenant = validate_tenant_id(tenant_id)
        generated_at = _now()

        roadmap = ImprovementRoadmapDTO(
            roadmap_id="ROADMAP-QUALITY-2026",
            roadmap_title="Accreditation Improvement Roadmap 2026",
            accreditation_cycle="2026-2027",
            phase="EXECUTION",
            initiatives_total=3,
            initiatives_completed=1,
            completion_percentage=46,
        )

        milestones_primary = [
            ImprovementMilestoneDTO(
                milestone_id="MS-QUALITY-01",
                milestone_title="Finalize curriculum mapping remediation",
                due_date=datetime(2026, 7, 15, tzinfo=UTC),
                completion_percentage=80,
                status="IN_PROGRESS",
            ),
            ImprovementMilestoneDTO(
                milestone_id="MS-QUALITY-02",
                milestone_title="Complete faculty evidence normalization",
                due_date=datetime(2026, 8, 20, tzinfo=UTC),
                completion_percentage=55,
                status="IN_PROGRESS",
            ),
        ]

        milestones_secondary = [
            ImprovementMilestoneDTO(
                milestone_id="MS-QUALITY-03",
                milestone_title="Close assessment documentation gaps",
                due_date=datetime(2026, 9, 5, tzinfo=UTC),
                completion_percentage=40,
                status="IN_PROGRESS",
            ),
        ]

        kpi_targets_primary = [
            ImprovementKpiTargetDTO(
                kpi_target_id="KPI-QUALITY-01",
                kpi_name="Evidence completeness ratio",
                baseline_value=62.0,
                target_value=90.0,
                current_value=78.0,
                unit="percent",
            ),
            ImprovementKpiTargetDTO(
                kpi_target_id="KPI-QUALITY-02",
                kpi_name="Corrective action closure rate",
                baseline_value=45.0,
                target_value=85.0,
                current_value=68.0,
                unit="percent",
            ),
        ]

        kpi_targets_secondary = [
            ImprovementKpiTargetDTO(
                kpi_target_id="KPI-QUALITY-03",
                kpi_name="Milestone on-time completion",
                baseline_value=50.0,
                target_value=88.0,
                current_value=64.0,
                unit="percent",
            )
        ]

        initiatives = [
            ImprovementInitiativeDTO(
                initiative_id="INIT-QUALITY-01",
                initiative_title="Curriculum and standards remediation",
                strategic_theme="ACADEMIC_QUALITY",
                owner_unit="academic_operations",
                status="IN_PROGRESS",
                completion_percentage=67,
                milestones=milestones_primary,
                kpi_targets=kpi_targets_primary,
            ),
            ImprovementInitiativeDTO(
                initiative_id="INIT-QUALITY-02",
                initiative_title="Assessment and documentation closure",
                strategic_theme="COMPLIANCE_READINESS",
                owner_unit="quality_accreditation",
                status="IN_PROGRESS",
                completion_percentage=40,
                milestones=milestones_secondary,
                kpi_targets=kpi_targets_secondary,
            ),
        ]

        forecasts = [
            ImprovementForecastDTO(
                forecast_id="FC-QUALITY-01",
                forecast_type="COMPLETION_FORECAST",
                confidence_level="MEDIUM",
                projected_completion_date=datetime(2026, 11, 30, tzinfo=UTC),
                readiness_forecast_score=79,
                risk_level="MEDIUM",
            ),
            ImprovementForecastDTO(
                forecast_id="FC-QUALITY-02",
                forecast_type="ACCREDITATION_READINESS_FORECAST",
                confidence_level="MEDIUM",
                projected_completion_date=datetime(2026, 12, 20, tzinfo=UTC),
                readiness_forecast_score=82,
                risk_level="MEDIUM",
            ),
        ]

        runtime = ImprovementPlanRuntimeDTO(
            plan_id="PLAN-QUALITY-2026",
            plan_title="Quality Accreditation Improvement Plan",
            accreditation_standard="INSTITUTIONAL_QUALITY_STANDARD_SET",
            owner_unit="quality_accreditation",
            progress_tracking_status="TRACKED",
            completion_percentage=52,
            initiatives=initiatives,
            roadmaps=[roadmap],
            forecasts=forecasts,
            last_updated=generated_at,
        )

        return ImprovementPlanRuntimeResponseDTO(
            tenant_id=tenant,
            generated_at=generated_at,
            improvement_plans=[runtime],
        )


improvement_plan_runtime_service = ImprovementPlanRuntimeService()
