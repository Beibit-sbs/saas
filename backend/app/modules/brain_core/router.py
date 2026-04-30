from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.modules.rbac.security import permission_dependency
from app.modules.brain_core.service import brain_core_service


router = APIRouter(
    prefix="/api/admin/brain",
    tags=["brain_core"],
    dependencies=[Depends(permission_dependency("admin.dashboard.read"))],
)


@router.get("/health")
def get_brain_health() -> dict:
    return {"status": "ok", "module": "brain_core", "phase": "skeleton"}


@router.get("/signals")
def list_signals() -> dict:
    items = brain_core_service.list_signals()
    return {"total": len(items), "items": items}


@router.get("/decisions")
def list_decisions() -> dict:
    items = brain_core_service.list_decisions()
    return {"total": len(items), "items": items}


@router.get("/decisions/{decision_id}")
def get_decision(decision_id: str) -> dict:
    decision = brain_core_service.get_decision(decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="decision_not_found")
    return decision


@router.get("/explanations/{decision_id}")
def get_explanation(decision_id: str) -> dict:
    explanation = brain_core_service.get_explanation(decision_id)
    if explanation is None:
        raise HTTPException(status_code=404, detail="explanation_not_found")
    return explanation


@router.get("/dispatch/snapshot")
def get_dispatch_snapshot() -> dict:
    return brain_core_service.dispatch_snapshot()


class StudentRiskSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    student_id: str = Field(..., min_length=1)
    course_id: str | None = None
    section_id: str | None = None
    attendance_rate: float = Field(..., ge=0, le=1)
    grade_trend: str = Field(default="declining")
    advisor_id: str | None = None
    faculty_id: str | None = None


class ThesisDelaySignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    student_id: str = Field(..., min_length=1)
    thesis_id: str = Field(..., min_length=1)
    advisor_id: str | None = None
    faculty_id: str | None = None
    days_since_last_milestone: int = Field(..., ge=0)
    old_status: str | None = None
    new_status: str = Field(default="stagnant")


class FacultyOverloadSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    faculty_id: str = Field(..., min_length=1)
    workload_ratio: float = Field(..., ge=0)


class PaymentOverdueSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    student_id: str = Field(..., min_length=1)
    delinquency_days: int = Field(..., ge=0)
    balance_due: float = Field(..., ge=0)


class PredictRiskRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    event_type: str = Field(..., min_length=3)
    entity_id: str = Field(..., min_length=1)
    history: list[dict] = Field(default_factory=list)
    horizon_days: int = Field(default=7, ge=1, le=30)


class BrainOptimizeDomainSignal(BaseModel):
    domain: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)
    value: float
    threshold: float = 0.0


class BrainOptimizeRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    domain_signals: list[BrainOptimizeDomainSignal] = Field(default_factory=list)


class DetectAnomaliesRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    metric_name: str = Field(..., min_length=2)
    values: list[float] = Field(..., min_length=1)
    entity_ids: list[str] | None = None
    z_threshold: float = Field(default=2.0, ge=1.0, le=5.0)


class BudgetVarianceSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    budget_code: str = Field(..., min_length=1)
    variance_amount: float = Field(..., ge=0)
    variance_ratio: float = Field(..., ge=0)
    vendor_code: str | None = None
    contract_code: str | None = None
    asset_code: str | None = None


class VendorSLADegradedSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    vendor_code: str = Field(..., min_length=1)
    sla_breach_rate: float = Field(..., ge=0, le=1)
    on_time_delivery_rate: float = Field(..., ge=0, le=1)


class ContractRiskHighSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    contract_code: str = Field(..., min_length=1)
    vendor_code: str | None = None
    risk_score: float = Field(..., ge=0, le=1)
    sla_target_met: bool = True


class SupplyLowSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    stock_item_id: str = Field(..., min_length=1)
    stock_level: float = Field(..., ge=0)
    threshold: float = Field(..., ge=0)
    projected_daily_usage: float | None = Field(default=None, ge=0)
    lead_time_days: int | None = Field(default=None, ge=0)
    auto_reorder: bool = False


class FacilityIssueSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    facility_code: str = Field(..., min_length=1)
    issue_type: str = Field(..., min_length=1)
    severity: str = Field(default="medium", min_length=1)


class CleaningServiceMissedSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    room_code: str = Field(..., min_length=1)
    building_code: str | None = None
    missed_count: int = Field(..., ge=1)


class MaintenancePredictedDueSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    asset_code: str = Field(..., min_length=1)
    facility_code: str = Field(..., min_length=1)
    asset_type: str = Field(..., min_length=1)
    days_since_maintenance: int = Field(..., ge=0)
    expected_service_interval_days: int = Field(..., ge=1)
    health_score: float = Field(..., ge=0, le=100)


class UtilitiesSpikeSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    meter_code: str = Field(..., min_length=1)
    building_code: str = Field(..., min_length=1)
    utility_type: str = Field(..., min_length=1)
    usage_value: float = Field(..., ge=0)
    baseline_value: float = Field(..., ge=0)
    spike_ratio: float = Field(..., ge=1)
    affected_buildings: int = Field(default=1, ge=1)


class StudentLifeWellbeingSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    student_id: str = Field(..., min_length=1)
    wellbeing_score: int = Field(..., ge=0, le=100)
    concern_type: str = Field(default="wellbeing", min_length=1)


class StudentLifeDisciplinarySignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    student_id: str = Field(..., min_length=1)
    incident_type: str = Field(..., min_length=1)
    incident_severity: str = Field(default="medium", min_length=1)
    incident_count_30d: int = Field(default=1, ge=1)


class ResearchGrantDeadlineSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    grant_id: str = Field(..., min_length=1)
    research_project_id: str | None = None
    days_to_deadline: int = Field(..., ge=0)


class ResearchPublicationStagnantSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    publication_id: str = Field(..., min_length=1)
    research_project_id: str | None = None
    days_without_progress: int = Field(..., ge=0)


class ResearchGrantPipelineRiskSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    grant_id: str = Field(..., min_length=1)
    research_project_id: str | None = None
    pipeline_risk_score: float = Field(..., ge=0, le=1)
    delayed_milestones: int = Field(default=0, ge=0)


class ResearchLabUtilizationLowSignalRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    lab_code: str = Field(..., min_length=1)
    research_project_id: str | None = None
    utilization_rate: float = Field(..., ge=0, le=1)
    idle_days: int = Field(..., ge=0)


class DecisionActionRequest(BaseModel):
    actor: str = Field(default="admin@brain")
    reason: str | None = None


class OutcomeRecordRequest(BaseModel):
    actor: str = Field(default="ops@brain")
    outcome_type: str = Field(default="completed")
    effectiveness: str = Field(default="neutral")
    notes: str | None = None


class PolicyTuningApplyRequest(BaseModel):
    actor: str = Field(default="ops@brain")


class PolicyConfigUpdateRequest(BaseModel):
    autonomy_level: int = Field(..., ge=0, le=4)
    require_approval_for_critical: bool
    default_approval_role: str = Field(..., min_length=1, max_length=64)
    enable_ai_reasoning: bool = Field(default=False)
    actor: str = Field(default="admin@brain")


class WhatIfPolicyOverrideRequest(BaseModel):
    autonomy_level: int = Field(default=2, ge=0, le=4)
    require_approval_for_critical: bool = True
    default_approval_role: str = Field(default="dean_office", min_length=1, max_length=64)
    enable_ai_reasoning: bool = False


class WhatIfSimulationRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    event_type: str = Field(..., min_length=3)
    subject: dict = Field(default_factory=dict)
    payload: dict = Field(default_factory=dict)
    forecast_horizon_days: int = Field(default=30, ge=1, le=365)
    simulation_label: str | None = Field(default=None, max_length=120)
    policy_override: WhatIfPolicyOverrideRequest | None = None


@router.put("/policy/{tenant_id}")
def update_policy_profile(
    tenant_id: int,
    payload: PolicyConfigUpdateRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    return brain_core_service.update_policy_profile(
        tenant_id=tenant_id,
        autonomy_level=payload.autonomy_level,
        require_approval_for_critical=payload.require_approval_for_critical,
        default_approval_role=payload.default_approval_role,
        enable_ai_reasoning=payload.enable_ai_reasoning,
        actor=payload.actor,
    )


@router.post("/simulate/student-risk")
def simulate_student_risk(
    payload: StudentRiskSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    correlation_id = str(uuid4())
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": correlation_id,
        "event_type": "academic.attendance_risk.detected",
        "subject": {
            "student_id": payload.student_id,
            "course_id": payload.course_id,
            "section_id": payload.section_id,
            "faculty_id": payload.faculty_id,
        },
        "payload": {
            "student_id": payload.student_id,
            "course_id": payload.course_id,
            "section_id": payload.section_id,
            "attendance_rate": payload.attendance_rate,
            "grade_trend": payload.grade_trend,
            "advisor_id": payload.advisor_id,
            "faculty_id": payload.faculty_id,
            "source_entity_type": "section_attendance",
            "source_entity_id": payload.section_id or "unknown",
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/what-if")
def simulate_what_if(
    payload: WhatIfSimulationRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": payload.event_type,
        "subject": dict(payload.subject),
        "payload": dict(payload.payload),
        "metadata": {"source": "brain_api_simulation", "mode": "what_if"},
    }
    return brain_core_service.simulate_what_if(
        signal=signal,
        forecast_horizon_days=payload.forecast_horizon_days,
        simulation_label=payload.simulation_label,
        policy_override=payload.policy_override.model_dump() if payload.policy_override else None,
    )


@router.post("/predict")
def predict_risk(
    payload: PredictRiskRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    return brain_core_service.predict_risk(
        event_type=payload.event_type,
        tenant_id=payload.tenant_id,
        entity_id=payload.entity_id,
        history=payload.history,
        horizon_days=payload.horizon_days,
    )


@router.post("/anomalies")
def detect_anomalies(
    payload: DetectAnomaliesRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    return brain_core_service.detect_anomalies(
        tenant_id=payload.tenant_id,
        metric_name=payload.metric_name,
        values=payload.values,
        entity_ids=payload.entity_ids,
        z_threshold=payload.z_threshold,
    )


@router.get("/recommendations/{tenant_id}")
def get_proactive_recommendations(tenant_id: int) -> dict:
    return brain_core_service.proactive_recommendations(tenant_id)


@router.get("/executive-kpi/{tenant_id}")
def get_executive_kpi_dashboard(tenant_id: int) -> dict:
    return brain_core_service.get_kpi_dashboard(tenant_id)


@router.post("/simulate/thesis-delay")
def simulate_thesis_delay(
    payload: ThesisDelaySignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    correlation_id = str(uuid4())
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": correlation_id,
        "event_type": "thesis.status_changed",
        "subject": {
            "student_id": payload.student_id,
            "faculty_id": payload.faculty_id,
        },
        "payload": {
            "student_id": payload.student_id,
            "thesis_id": payload.thesis_id,
            "advisor_id": payload.advisor_id,
            "faculty_id": payload.faculty_id,
            "old_status": payload.old_status,
            "new_status": payload.new_status,
            "days_since_last_milestone": payload.days_since_last_milestone,
            "source_entity_type": "thesis",
            "source_entity_id": payload.thesis_id,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/faculty-overload")
def simulate_faculty_overload(
    payload: FacultyOverloadSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "faculty.workload_overload.detected",
        "subject": {"faculty_id": payload.faculty_id},
        "payload": {
            "faculty_id": payload.faculty_id,
            "workload_ratio": payload.workload_ratio,
            "source_entity_type": "faculty_workload",
            "source_entity_id": payload.faculty_id,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/budget-variance")
def simulate_budget_variance(
    payload: BudgetVarianceSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "finance.budget_variance.threshold_reached",
        "subject": {},
        "payload": {
            "budget_code": payload.budget_code,
            "variance_amount": payload.variance_amount,
            "variance_ratio": payload.variance_ratio,
            "vendor_code": payload.vendor_code,
            "contract_code": payload.contract_code,
            "asset_code": payload.asset_code,
            "source_entity_type": "budget_variance",
            "source_entity_id": payload.budget_code,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/vendor-sla-degraded")
def simulate_vendor_sla_degraded(
    payload: VendorSLADegradedSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "procurement.vendor_sla.degraded",
        "subject": {},
        "payload": {
            "vendor_code": payload.vendor_code,
            "sla_breach_rate": payload.sla_breach_rate,
            "on_time_delivery_rate": payload.on_time_delivery_rate,
            "source_entity_type": "vendor_sla_profile",
            "source_entity_id": payload.vendor_code,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/contract-risk-high")
def simulate_contract_risk_high(
    payload: ContractRiskHighSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "procurement.contract_risk.high",
        "subject": {},
        "payload": {
            "contract_code": payload.contract_code,
            "vendor_code": payload.vendor_code,
            "risk_score": payload.risk_score,
            "sla_target_met": payload.sla_target_met,
            "source_entity_type": "contract_risk_profile",
            "source_entity_id": payload.contract_code,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/supply-low")
def simulate_supply_low(
    payload: SupplyLowSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "operations.consumable_stock.low",
        "subject": {},
        "payload": {
            "stock_item_id": payload.stock_item_id,
            "stock_level": payload.stock_level,
            "threshold": payload.threshold,
            "projected_daily_usage": payload.projected_daily_usage,
            "lead_time_days": payload.lead_time_days,
            "auto_reorder": payload.auto_reorder,
            "source_entity_type": "inventory_item",
            "source_entity_id": payload.stock_item_id,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/payment-overdue")
def simulate_payment_overdue(
    payload: PaymentOverdueSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "finance.payment_overdue.detected",
        "subject": {"student_id": payload.student_id},
        "payload": {
            "student_id": payload.student_id,
            "delinquency_days": payload.delinquency_days,
            "balance_due": payload.balance_due,
            "source_entity_type": "billing_account",
            "source_entity_id": payload.student_id,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/supply-low")
def simulate_supply_low(
    payload: SupplyLowSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "operations.consumable_stock.low",
        "subject": {},
        "payload": {
            "stock_item_id": payload.stock_item_id,
            "stock_level": payload.stock_level,
            "threshold": payload.threshold,
            "source_entity_type": "inventory_item",
            "source_entity_id": payload.stock_item_id,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/facility-issue")
def simulate_facility_issue(
    payload: FacilityIssueSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "operations.facility_issue.reported",
        "subject": {},
        "payload": {
            "facility_code": payload.facility_code,
            "issue_type": payload.issue_type,
            "severity": payload.severity,
            "source_entity_type": "facility_issue",
            "source_entity_id": payload.facility_code,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/cleaning-service-missed")
def simulate_cleaning_service_missed(
    payload: CleaningServiceMissedSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "operations.cleaning_service.missed",
        "subject": {},
        "payload": {
            "room_code": payload.room_code,
            "building_code": payload.building_code,
            "missed_count": payload.missed_count,
            "source_entity_type": "cleaning_check",
            "source_entity_id": payload.room_code,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/maintenance-predicted-due")
def simulate_maintenance_predicted_due(
    payload: MaintenancePredictedDueSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "operations.maintenance.predicted_due",
        "subject": {},
        "payload": {
            "asset_code": payload.asset_code,
            "facility_code": payload.facility_code,
            "asset_type": payload.asset_type,
            "days_since_maintenance": payload.days_since_maintenance,
            "expected_service_interval_days": payload.expected_service_interval_days,
            "health_score": payload.health_score,
            "source_entity_type": "maintenance_asset",
            "source_entity_id": payload.asset_code,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/utilities-spike")
def simulate_utilities_spike(
    payload: UtilitiesSpikeSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "operations.utilities.spike_detected",
        "subject": {},
        "payload": {
            "meter_code": payload.meter_code,
            "building_code": payload.building_code,
            "utility_type": payload.utility_type,
            "usage_value": payload.usage_value,
            "baseline_value": payload.baseline_value,
            "spike_ratio": payload.spike_ratio,
            "affected_buildings": payload.affected_buildings,
            "source_entity_type": "utility_reading",
            "source_entity_id": payload.meter_code,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/student-life-wellbeing")
def simulate_student_life_wellbeing(
    payload: StudentLifeWellbeingSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "student_life.wellbeing.at_risk",
        "subject": {"student_id": payload.student_id},
        "payload": {
            "student_id": payload.student_id,
            "wellbeing_score": payload.wellbeing_score,
            "concern_type": payload.concern_type,
            "source_entity_type": "wellbeing_checkin",
            "source_entity_id": payload.student_id,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/student-life-disciplinary")
def simulate_student_life_disciplinary(
    payload: StudentLifeDisciplinarySignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "student_life.disciplinary.incident_reported",
        "subject": {"student_id": payload.student_id},
        "payload": {
            "student_id": payload.student_id,
            "incident_type": payload.incident_type,
            "incident_severity": payload.incident_severity,
            "incident_count_30d": payload.incident_count_30d,
            "source_entity_type": "disciplinary_incident",
            "source_entity_id": payload.student_id,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/research-grant-deadline")
def simulate_research_grant_deadline(
    payload: ResearchGrantDeadlineSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "research.grant_deadline.approaching",
        "subject": {},
        "payload": {
            "grant_id": payload.grant_id,
            "research_project_id": payload.research_project_id,
            "days_to_deadline": payload.days_to_deadline,
            "source_entity_type": "grant_record",
            "source_entity_id": payload.grant_id,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/research-publication-stagnant")
def simulate_research_publication_stagnant(
    payload: ResearchPublicationStagnantSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "research.publication_stagnant",
        "subject": {},
        "payload": {
            "publication_id": payload.publication_id,
            "research_project_id": payload.research_project_id,
            "days_without_progress": payload.days_without_progress,
            "source_entity_type": "publication_record",
            "source_entity_id": payload.publication_id,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/research-grant-pipeline-risk")
def simulate_research_grant_pipeline_risk(
    payload: ResearchGrantPipelineRiskSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "research.grant_pipeline.at_risk",
        "subject": {},
        "payload": {
            "grant_id": payload.grant_id,
            "research_project_id": payload.research_project_id,
            "pipeline_risk_score": payload.pipeline_risk_score,
            "delayed_milestones": payload.delayed_milestones,
            "source_entity_type": "grant_pipeline",
            "source_entity_id": payload.grant_id,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/simulate/research-lab-utilization-low")
def simulate_research_lab_utilization_low(
    payload: ResearchLabUtilizationLowSignalRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    signal = {
        "signal_id": str(uuid4()),
        "tenant_id": payload.tenant_id,
        "correlation_id": str(uuid4()),
        "event_type": "research.lab_utilization.low",
        "subject": {},
        "payload": {
            "lab_code": payload.lab_code,
            "research_project_id": payload.research_project_id,
            "utilization_rate": payload.utilization_rate,
            "idle_days": payload.idle_days,
            "source_entity_type": "research_lab",
            "source_entity_id": payload.lab_code,
        },
        "metadata": {"source": "brain_api_simulation"},
    }
    return brain_core_service.process_signal(signal)


@router.post("/reprocess/{signal_id}")
def reprocess_signal(
    signal_id: str,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    result = brain_core_service.reprocess_signal(signal_id, actor="operator@brain")
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="signal_not_found")
    return result


@router.post("/decisions/{decision_id}/approve")
def approve_decision(
    decision_id: str,
    payload: DecisionActionRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    result = brain_core_service.approve_decision(decision_id, actor=payload.actor)
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="decision_not_found")
    return result


@router.post("/decisions/{decision_id}/cancel")
def cancel_decision(
    decision_id: str,
    payload: DecisionActionRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    result = brain_core_service.cancel_decision(
        decision_id,
        actor=payload.actor,
        reason=payload.reason or "cancelled_by_operator",
    )
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="decision_not_found")
    return result


@router.post("/decisions/{decision_id}/outcome")
def record_outcome(
    decision_id: str,
    payload: OutcomeRecordRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    result = brain_core_service.record_outcome(
        decision_id,
        actor=payload.actor,
        payload={
            "outcome_type": payload.outcome_type,
            "effectiveness": payload.effectiveness,
            "notes": payload.notes,
        },
    )
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="decision_not_found")
    return result


@router.post("/dispatch/workflow-cases/{case_id}/outcome")
def record_dispatch_outcome(
    case_id: str,
    payload: OutcomeRecordRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    result = brain_core_service.record_dispatch_outcome(
        case_id,
        actor=payload.actor,
        payload={
            "outcome_type": payload.outcome_type,
            "effectiveness": payload.effectiveness,
            "notes": payload.notes,
        },
    )
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="dispatch_case_not_found")
    if result.get("status") == "invalid_dispatch_item":
        raise HTTPException(status_code=409, detail=result.get("reason") or "invalid_dispatch_item")
    return result


@router.get("/outcomes")
def list_outcomes() -> dict:
    items = brain_core_service.list_outcomes()
    return {"total": len(items), "items": items}


@router.get("/learning/metrics")
def get_learning_metrics() -> dict:
    return brain_core_service.learning_metrics()


@router.get("/policy/{tenant_id}")
def get_policy_profile(tenant_id: int) -> dict:
    return brain_core_service.policy_profile(tenant_id)


@router.get("/learning/policy-tuning/{tenant_id}")
def get_policy_tuning(tenant_id: int) -> dict:
    return brain_core_service.policy_tuning_suggestion(tenant_id)


@router.post("/learning/policy-tuning/{tenant_id}/apply")
def apply_policy_tuning(
    tenant_id: int,
    payload: PolicyTuningApplyRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    return brain_core_service.apply_policy_tuning(tenant_id, actor=payload.actor)


@router.get("/metrics")
def get_brain_metrics() -> dict:
    return brain_core_service.observability_metrics()


@router.get("/traces")
def get_brain_traces(limit: int = 100) -> dict:
    items = brain_core_service.observability_traces(limit=limit)
    return {"total": len(items), "items": items}


# ------------------------------------------------------------------
# Phase XVII — Adaptive Learning & Optimization
# ------------------------------------------------------------------

@router.get("/learning/evaluate/{tenant_id}")
def evaluate_learning(tenant_id: int) -> dict:
    """XVII3 — Detailed learning state evaluation for a tenant."""
    return brain_core_service.evaluate_learning(tenant_id)


@router.post("/optimize")
def optimize_resources(
    payload: BrainOptimizeRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XVII4 — Brain Optimization Engine: resource allocation recommendations."""
    return brain_core_service.optimize(
        tenant_id=payload.tenant_id,
        domain_signals=[s.model_dump() for s in payload.domain_signals],
    )
