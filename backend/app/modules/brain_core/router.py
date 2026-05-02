from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
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


class ReprocessSignalRequest(BaseModel):
    dry_run: bool = False
    idempotency_key: str | None = Field(default=None, min_length=1)
    replay_reason: str | None = None
    expected_tenant_id: int | None = Field(default=None, gt=0)


class ReplayApprovalRequest(BaseModel):
    actor: str = Field(default="operator@brain")
    reason: str | None = None
    idempotency_key: str | None = Field(default=None, min_length=1)
    expected_tenant_id: int | None = Field(default=None, gt=0)


class ReplayRejectRequest(BaseModel):
    actor: str = Field(default="operator@brain")
    reason: str | None = None
    expected_tenant_id: int | None = Field(default=None, gt=0)


class ReplayCancelRequest(BaseModel):
    actor: str = Field(default="operator@brain")
    reason: str | None = None
    expected_tenant_id: int | None = Field(default=None, gt=0)


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


class LearningApplyRequest(BaseModel):
    tenant_id: int = Field(..., gt=0)
    actor: str = Field(default="ops@brain")
    dry_run: bool = False
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class PolicyDriftAlert(BaseModel):
    """XVIII3 — Policy drift alert model."""
    alert_id: str | None = None
    tenant_id: int
    type: str = "policy_drift"
    status: str  # "active", "resolved", "no_drift"
    severity: str | None = None  # "high", "medium"
    reason: str
    threshold: dict | None = None
    current_metrics: dict
    created_at: str | None = None
    resolved_at: str | None = None


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


@router.get("/replay-audit")
def get_replay_audit(
    signal_id: str | None = None,
    event_type: str | None = None,
    limit: int = 100,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXVIII3 — Replay audit trail. Returns log of replay_requested/executed/rejected events."""
    records = brain_core_service.get_replay_audit(
        signal_id=signal_id,
        event_type=event_type,
        limit=limit,
    )
    return {"total": len(records), "records": records}


@router.post("/reprocess/{signal_id}")
def reprocess_signal(
    signal_id: str,
    payload: ReprocessSignalRequest = Body(default_factory=ReprocessSignalRequest),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    result = brain_core_service.reprocess_signal(
        signal_id,
        actor="operator@brain",
        dry_run=payload.dry_run,
        idempotency_key=payload.idempotency_key,
        replay_reason=payload.replay_reason,
        expected_tenant_id=payload.expected_tenant_id,
    )
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="signal_not_found")
    if result.get("status") == "tenant_mismatch":
        raise HTTPException(status_code=403, detail="tenant_mismatch")
    if result.get("status") == "safety_gate_blocked":
        raise HTTPException(status_code=403, detail=result.get("reason", "safety_gate_blocked"))
    return result


@router.post("/reprocess/{signal_id}/approve")
def approve_reprocess_signal(
    signal_id: str,
    payload: ReplayApprovalRequest = Body(default_factory=ReplayApprovalRequest),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    result = brain_core_service.approve_signal_reprocess(
        signal_id,
        actor=payload.actor,
        reason=payload.reason,
        idempotency_key=payload.idempotency_key,
        expected_tenant_id=payload.expected_tenant_id,
    )
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="signal_not_found")
    if result.get("status") == "tenant_mismatch":
        raise HTTPException(status_code=403, detail="tenant_mismatch")
    if result.get("status") == "safety_gate_blocked":
        raise HTTPException(status_code=403, detail=result.get("reason", "safety_gate_blocked"))
    return result


@router.post("/reprocess/{signal_id}/reject")
def reject_reprocess_signal(
    signal_id: str,
    payload: ReplayRejectRequest = Body(default_factory=ReplayRejectRequest),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    result = brain_core_service.reject_signal_reprocess(
        signal_id,
        actor=payload.actor,
        reason=payload.reason,
        expected_tenant_id=payload.expected_tenant_id,
    )
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="signal_not_found")
    if result.get("status") == "tenant_mismatch":
        raise HTTPException(status_code=403, detail="tenant_mismatch")
    return result


@router.post("/reprocess/{signal_id}/cancel")
def cancel_reprocess_signal(
    signal_id: str,
    payload: ReplayCancelRequest = Body(default_factory=ReplayCancelRequest),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    result = brain_core_service.cancel_signal_reprocess(
        signal_id,
        actor=payload.actor,
        reason=payload.reason,
        expected_tenant_id=payload.expected_tenant_id,
    )
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="signal_not_found")
    if result.get("status") == "tenant_mismatch":
        raise HTTPException(status_code=403, detail="tenant_mismatch")
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


@router.post("/learning/apply")
def apply_learning(
    payload: LearningApplyRequest,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XVIII1 — Apply adaptive learning suggestions (supports dry-run + idempotency)."""
    return brain_core_service.apply_learning(
        tenant_id=payload.tenant_id,
        actor=payload.actor,
        dry_run=payload.dry_run,
        idempotency_key=payload.idempotency_key,
    )


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


@router.get("/policy-drift/{tenant_id}")
def get_policy_drift_alerts(
    tenant_id: Annotated[int, Path(gt=0)],
    status: str | None = None,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XVIII3 — Retrieve policy drift alerts for a tenant."""
    alerts = brain_core_service.get_policy_drift_alerts(tenant_id, status=status)
    return {"tenant_id": tenant_id, "total": len(alerts), "alerts": alerts}


@router.post("/policy-drift/{tenant_id}/detect")
def detect_policy_drift(
    tenant_id: Annotated[int, Path(gt=0)],
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XVIII3 — Trigger policy drift detection."""
    alert = brain_core_service.detect_policy_drift(tenant_id)
    return alert


@router.get("/reasoning/policy/{tenant_id}")
def reason_about_policy(
    tenant_id: Annotated[int, Path(gt=0)],
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XIX1 — Use LLM to reason about current policy effectiveness and suggest improvements."""
    result = brain_core_service.reason_about_policy(tenant_id)
    return result


@router.get("/cross-tenant-recommendations/{tenant_id}")
def get_cross_tenant_recommendations(
    tenant_id: Annotated[int, Path(gt=0)],
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XIX3 — Privacy-safe peer learning recommendations."""
    return brain_core_service.get_cross_tenant_recommendations(tenant_id)


@router.get("/policy-optimization/{tenant_id}")
def get_predictive_policy_optimization(
    tenant_id: Annotated[int, Path(gt=0)],
    horizon_days: int = 14,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XIX4 — Predictive policy optimization for the near-term horizon."""
    return brain_core_service.predict_policy_optimization(tenant_id, horizon_days=horizon_days)


@router.get("/policy-rollout-plan/{tenant_id}")
def get_policy_rollout_plan(
    tenant_id: Annotated[int, Path(gt=0)],
    horizon_days: int = 14,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XX1 — Build a staged rollout plan for safe policy profile transitions."""
    return brain_core_service.generate_policy_rollout_plan(tenant_id, horizon_days=horizon_days)



@router.post("/policy-rollout-phase/{tenant_id}/execute")
def execute_policy_rollout_phase(
    tenant_id: Annotated[int, Path(gt=0)],
    plan_id: str = Query(...),
    phase: str = Query(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XX2 — Execute a single phase of a policy rollout plan with idempotency guarantee."""
    return brain_core_service.execute_policy_rollout_phase(
        tenant_id=tenant_id,
        plan_id=plan_id,
        phase=phase,
    )


@router.post("/policy-rollout-phase/{tenant_id}/rollback")
def rollback_policy_rollout(
    tenant_id: Annotated[int, Path(gt=0)],
    plan_id: str = Query(...),
    trigger: str = Query(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XX3 — Detect rollback trigger and execute safe rollback to prior policy profile."""
    return brain_core_service.rollback_policy_rollout(
        tenant_id=tenant_id,
        plan_id=plan_id,
        trigger=trigger,
    )


@router.post("/policy-rollout-coordination")
def coordinate_cross_tenant_rollout(
    plan_id: str = Query(...),
    phase: str = Query(...),
    tenant_ids: list[int] = Query(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XX4 — Fan-out rollout plan to multiple tenants with phase coordination."""
    return brain_core_service.coordinate_cross_tenant_rollout(
        plan_id=plan_id,
        tenant_ids=tenant_ids,
        phase=phase,
    )


# ---------------------------------------------------------------------------
# XXI — Autonomous Agent Workflows & Self-Governance
# ---------------------------------------------------------------------------

@router.post("/agent/tasks")
def create_agent_task(
    tenant_id: int = Query(..., gt=0),
    workflow_type: str = Query(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXI1 — Create a multi-step agent task graph for the given workflow type."""
    return brain_core_service.create_agent_task(
        tenant_id=tenant_id,
        workflow_type=workflow_type,
        context={},
    )


@router.post("/agent/tasks/{task_id}/steps/{step_id}/execute")
def execute_agent_step(
    task_id: str = Path(...),
    step_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXI2 — Execute a single step of an agent task (state machine transition)."""
    return brain_core_service.execute_agent_step(task_id=task_id, step_id=step_id)


@router.get("/agent/tasks/{task_id}/status")
def get_agent_task_status(
    task_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXI3 — Get agent task status; apply self-correction if blocked steps detected."""
    return brain_core_service.get_agent_task_status(task_id=task_id)


@router.get("/agent/policy/{tenant_id}")
def get_tenant_agent_policy(
    tenant_id: Annotated[int, Path(gt=0)],
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXI4 — Get tenant-scoped agent policy configuration."""
    return brain_core_service.get_tenant_agent_policy(tenant_id=tenant_id)


@router.post("/agent/policy/{tenant_id}")
def update_tenant_agent_policy(
    tenant_id: Annotated[int, Path(gt=0)],
    approval_gate_required: bool = Query(False),
    step_budget: int = Query(10, gt=0),
    workflow_types: list[str] = Query(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXI4 — Update tenant-scoped agent policy configuration."""
    return brain_core_service.update_tenant_agent_policy(
        tenant_id=tenant_id,
        allowed_workflow_types=workflow_types,
        approval_gate_required=approval_gate_required,
        step_budget=step_budget,
    )


# ---------------------------------------------------------------------------
# XXII — Agent Execution Governance
# ---------------------------------------------------------------------------

@router.post("/agent/tasks/claim")
def claim_next_agent_step(
    tenant_id: int = Query(..., gt=0),
    worker_id: str = Query(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXII1 — Claim next executable step from tenant queue."""
    return brain_core_service.claim_next_agent_step(tenant_id=tenant_id, worker_id=worker_id)


@router.post("/agent/tasks/{task_id}/steps/{step_id}/complete")
def complete_agent_step(
    task_id: str = Path(...),
    step_id: str = Path(...),
    worker_id: str = Query(...),
    success: bool = Query(...),
    error_code: str | None = Query(None),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXII2 — Complete/Fail running step with retry policy."""
    return brain_core_service.complete_agent_step(
        task_id=task_id,
        step_id=step_id,
        worker_id=worker_id,
        success=success,
        error_code=error_code,
    )


@router.get("/agent/sla/{tenant_id}")
def get_agent_sla_report(
    tenant_id: Annotated[int, Path(gt=0)],
    sla_seconds: int = Query(300, gt=0),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXII3 — Get SLA breaches report for tenant agent tasks."""
    return brain_core_service.get_agent_sla_report(tenant_id=tenant_id, sla_seconds=sla_seconds)


@router.get("/agent/queue/{tenant_id}")
def get_agent_queue_metrics(
    tenant_id: Annotated[int, Path(gt=0)],
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXII4 — Get queue metrics for tenant agent tasks."""
    return brain_core_service.get_agent_queue_metrics(tenant_id=tenant_id)


# ---------------------------------------------------------------------------
# Phase XXIII — Agent Observability & Telemetry
# ---------------------------------------------------------------------------

class _StepEventBody(BaseModel):
    event_type: str = Field(..., description="One of: started, progress, checkpoint, warning, retry, cancelled, custom")
    payload: dict = Field(default_factory=dict)


@router.post("/agent/tasks/{task_id}/steps/{step_id}/log")
def log_agent_step_event(
    task_id: str = Path(...),
    step_id: str = Path(...),
    body: _StepEventBody = None,
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXIII1 — Append an observability event to a step's execution log."""
    try:
        return brain_core_service.log_agent_step_event(
            task_id=task_id,
            step_id=step_id,
            event_type=body.event_type if body else "custom",
            payload=body.payload if body else {},
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/agent/tasks/{task_id}/steps/{step_id}/log")
def get_agent_step_log(
    task_id: str = Path(...),
    step_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXIII1 — Retrieve chronological event log for a step."""
    return brain_core_service.get_agent_step_log(task_id=task_id, step_id=step_id)


@router.get("/agent/tasks/{task_id}/audit")
def get_agent_task_audit(
    task_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXIII2 — Return full audit trail for a task."""
    return brain_core_service.get_agent_task_audit(task_id=task_id)


@router.get("/agent/performance/{tenant_id}")
def get_agent_performance_report(
    tenant_id: Annotated[int, Path(gt=0)],
    window_hours: int = Query(24, gt=0),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXIII3 — Tenant-scoped agent step performance report."""
    return brain_core_service.get_agent_performance_report(
        tenant_id=tenant_id, window_hours=window_hours
    )


# ---------------------------------------------------------------------------
# Phase XXIV — Agent Dependency & Resource Control
# ---------------------------------------------------------------------------

class _StepDepsBody(BaseModel):
    depends_on: list[str] = []


class _ResourceBudgetBody(BaseModel):
    token_limit: int
    cost_limit_usd: float


class _OutcomeFeedbackBody(BaseModel):
    quality_score: float
    notes: str = ""


@router.post("/agent/tasks/{task_id}/steps/{step_id}/dependencies")
def set_step_dependencies(
    task_id: str = Path(...),
    step_id: str = Path(...),
    body: _StepDepsBody = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXIV1 — Set dependency list for a step (must complete before this step runs)."""
    try:
        return brain_core_service.set_step_dependencies(
            task_id=task_id, step_id=step_id, depends_on=body.depends_on
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/agent/tasks/{task_id}/ready-queue")
def get_step_ready_queue(
    task_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXIV1 — Steps whose dependencies are all done (ready to execute)."""
    try:
        return brain_core_service.get_step_ready_queue(task_id=task_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/agent/tasks/{task_id}/resources")
def set_task_resource_budget(
    task_id: str = Path(...),
    body: _ResourceBudgetBody = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXIV2 — Set token and cost budget for a task."""
    try:
        return brain_core_service.set_task_resource_budget(
            task_id=task_id, token_limit=body.token_limit, cost_limit_usd=body.cost_limit_usd
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/agent/tasks/{task_id}/resources")
def get_task_resource_usage(
    task_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXIV2 — Current resource usage vs. budget for a task."""
    try:
        return brain_core_service.get_task_resource_usage(task_id=task_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/agent/tasks/{task_id}/feedback")
def record_task_outcome_feedback(
    task_id: str = Path(...),
    body: _OutcomeFeedbackBody = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXIV3 — Record quality feedback for a completed task."""
    try:
        return brain_core_service.record_task_outcome_feedback(
            task_id=task_id, quality_score=body.quality_score, notes=body.notes
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/agent/outcomes/{tenant_id}")
def get_task_outcome_summary(
    tenant_id: Annotated[int, Path(gt=0)],
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXIV3 — Aggregate outcome feedback summary for a tenant."""
    return brain_core_service.get_task_outcome_summary(tenant_id=tenant_id)


# ---------------------------------------------------------------------------
# Phase XXV — Agent Multi-Agent Collaboration & Handoff
# ---------------------------------------------------------------------------

class _HandoffBody(BaseModel):
    to_agent_id: str
    context_snapshot: dict = Field(default_factory=dict)


class _TaskSplitBody(BaseModel):
    split_strategy: str
    subtask_configs: list[dict]


class _MergeBody(BaseModel):
    subtask_ids: list[str]


@router.post("/agent/handoff/{from_task_id}")
def initiate_agent_handoff(
    from_task_id: str = Path(...),
    body: _HandoffBody = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXV1 — Initiate handoff of task context to another agent."""
    try:
        return brain_core_service.initiate_agent_handoff(
            from_task_id=from_task_id,
            to_agent_id=body.to_agent_id,
            context_snapshot=body.context_snapshot,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/agent/handoff/{handoff_id}")
def get_handoff_status(
    handoff_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXV1 — Current state of an agent handoff."""
    try:
        return brain_core_service.get_handoff_status(handoff_id=handoff_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/agent/handoff/{handoff_id}/accept")
def accept_agent_handoff(
    handoff_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXV1 — Mark handoff accepted by receiving agent."""
    try:
        return brain_core_service.accept_agent_handoff(handoff_id=handoff_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/agent/tasks/{task_id}/split")
def split_agent_task(
    task_id: str = Path(...),
    body: _TaskSplitBody = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXV2 — Decompose task into parallel subtasks for multiple agents."""
    try:
        return brain_core_service.split_agent_task(
            task_id=task_id,
            split_strategy=body.split_strategy,
            subtask_configs=body.subtask_configs,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/agent/tasks/{task_id}/merge")
def merge_agent_results(
    task_id: str = Path(...),
    body: _MergeBody = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXV3 — Merge parallel subtask results into unified outcome."""
    try:
        return brain_core_service.merge_agent_results(
            task_id=task_id,
            subtask_ids=body.subtask_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/agent/tasks/{task_id}/merge-status")
def get_merge_status(
    task_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXV3 — Return the merge record for a task."""
    try:
        return brain_core_service.get_merge_status(task_id=task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Phase XXVI — Agent Adaptive Learning & Self-Optimization
# ---------------------------------------------------------------------------


@router.post("/agent/tasks/{task_id}/learning")
def record_agent_learning_signal(
    task_id: str = Path(...),
    body: dict = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXVI1 — Record a learning signal from a task outcome for an agent."""
    try:
        return brain_core_service.record_agent_learning_signal(
            task_id=task_id,
            agent_id=body["agent_id"],
            signal_type=body["signal_type"],
            value=float(body["value"]),
            context=body.get("context"),
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/agent/learning/{agent_id}")
def get_agent_learning_summary(
    agent_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXVI1 — Return aggregated learning summary for an agent."""
    return brain_core_service.get_agent_learning_summary(agent_id=agent_id)


@router.post("/agent/tasks/{task_id}/optimize")
def optimize_agent_workflow(
    task_id: str = Path(...),
    body: dict = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXVI2 — Apply self-optimization to an agent workflow."""
    try:
        return brain_core_service.optimize_agent_workflow(
            task_id=task_id,
            optimization_target=body["optimization_target"],
            strategy=body.get("strategy", "auto"),
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/agent/tasks/{task_id}/optimize-history")
def get_optimization_history(
    task_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXVI2 — Return optimization history for a task."""
    try:
        return brain_core_service.get_optimization_history(task_id=task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/agent/benchmark")
def benchmark_agent_performance(
    body: dict = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXVI3 — Record a performance benchmark for an agent vs. baseline."""
    try:
        return brain_core_service.benchmark_agent_performance(
            agent_id=body["agent_id"],
            metric=body["metric"],
            observed_value=float(body["observed_value"]),
            baseline_value=float(body["baseline_value"]),
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/agent/benchmark/{agent_id}")
def get_agent_benchmark(
    agent_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXVI3 — Return all benchmarks for an agent."""
    return brain_core_service.get_agent_benchmark(agent_id=agent_id)


# Phase XXVII — Agent Knowledge Graph & Cross-Agent Memory

@router.post("/agent/knowledge")
def store_agent_knowledge(
    body: dict = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXVII1 — Store a knowledge entry for an agent."""
    try:
        return brain_core_service.store_agent_knowledge(
            agent_id=body["agent_id"],
            key=body["key"],
            value=body["value"],
            confidence=float(body["confidence"]),
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/agent/knowledge/share")
def share_knowledge(
    body: dict = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXVII2 — Share a knowledge entry between agents (conflict guard)."""
    try:
        return brain_core_service.share_knowledge(
            from_agent_id=body["from_agent_id"],
            to_agent_id=body["to_agent_id"],
            key=body["key"],
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/agent/knowledge/{agent_id}/shared")
def get_shared_knowledge(
    agent_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXVII2 — Return all knowledge shared TO this agent."""
    return brain_core_service.get_shared_knowledge(agent_id=agent_id)


@router.post("/agent/knowledge/{agent_id}/expire")
def expire_stale_knowledge(
    agent_id: str = Path(...),
    body: dict = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXVII3 — Expire knowledge entries older than max_age_hours."""
    try:
        return brain_core_service.expire_stale_knowledge(
            agent_id=agent_id,
            max_age_hours=float(body["max_age_hours"]),
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/agent/knowledge/{agent_id}/health")
def get_knowledge_health(
    agent_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXVII3 — Return knowledge health metrics for an agent."""
    return brain_core_service.get_knowledge_health(agent_id=agent_id)


@router.get("/agent/knowledge/{agent_id}/{key}")
def retrieve_agent_knowledge(
    agent_id: str = Path(...),
    key: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXVII1 — Retrieve a knowledge entry for an agent."""
    try:
        return brain_core_service.retrieve_agent_knowledge(agent_id=agent_id, key=key)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# ── XXX1 — Replay Analytics ───────────────────────────────────────────────
@router.get("/reprocess/analytics/{tenant_id}")
def get_replay_analytics(
    tenant_id: int = Path(...),
    window_days: int = Query(30, ge=1, le=365),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXX1 — Replay analytics: approve/reject/cancel counts, avg resolution time, top actors."""
    return brain_core_service.get_replay_analytics(tenant_id=tenant_id, window_days=window_days)


# ── XXX2 — Replay Trend Alerts ────────────────────────────────────────────
@router.get("/reprocess/alerts/{tenant_id}")
def get_replay_trend_alerts(
    tenant_id: int = Path(...),
    reject_rate_threshold: float = Query(0.5, ge=0.0, le=1.0),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> list:
    """XXX2 — Return active replay trend alerts for tenant."""
    return brain_core_service.get_replay_trend_alerts(
        tenant_id=tenant_id,
        reject_rate_threshold=reject_rate_threshold,
    )


# ── XXX3 — Replay Operator Summary ───────────────────────────────────────
@router.get("/reprocess/operator-summary/{actor}")
def get_replay_operator_summary(
    actor: str = Path(...),
    window_days: int = Query(30, ge=1, le=365),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXX3 — Per-actor replay action summary."""
    return brain_core_service.get_replay_operator_summary(actor=actor, window_days=window_days)


# ── XXXI1 — Replay Policy Config ──────────────────────────────────────────
class ReplayPolicyRequest(BaseModel):
    actor: str = Field(..., min_length=1)
    max_window_days: int = Field(90, ge=1, le=365)
    allowed_actors: list[str] | None = Field(None)
    auto_reject_threshold: float | None = Field(None, ge=0.0, le=1.0)
    require_dual_approval: bool = Field(False)
    max_replays_per_signal: int = Field(5, ge=1, le=100)


@router.get("/reprocess/policy/{tenant_id}")
def get_replay_policy(
    tenant_id: int = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXXI1 — Return tenant-scoped replay governance policy."""
    return brain_core_service.get_replay_policy(tenant_id=tenant_id)


@router.put("/reprocess/policy/{tenant_id}")
def set_replay_policy(
    tenant_id: int = Path(...),
    body: ReplayPolicyRequest = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXXI1 — Update tenant-scoped replay governance policy."""
    try:
        return brain_core_service.set_replay_policy(
            tenant_id,
            actor=body.actor,
            max_window_days=body.max_window_days,
            allowed_actors=body.allowed_actors,
            auto_reject_threshold=body.auto_reject_threshold,
            require_dual_approval=body.require_dual_approval,
            max_replays_per_signal=body.max_replays_per_signal,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# ── XXXI2 — Replay Policy Enforcement Check ───────────────────────────────
@router.get("/reprocess/policy/{tenant_id}/check")
def check_replay_policy(
    tenant_id: int = Path(...),
    actor: str = Query(...),
    signal_id: str = Query(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXXI2 — Check whether a replay action is permitted under current policy."""
    return brain_core_service.check_replay_policy(tenant_id, actor=actor, signal_id=signal_id)


# ── XXXI3 — Replay Policy History ─────────────────────────────────────────
@router.get("/reprocess/policy/{tenant_id}/history")
def get_replay_policy_history(
    tenant_id: int = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> list:
    """XXXI3 — Return chronological history of replay policy changes for tenant."""
    return brain_core_service.get_replay_policy_history(tenant_id=tenant_id)


# ── XIX1 — Policy Reasoning Engine ────────────────────────────────────────
@router.get("/reasoning/policy/{tenant_id}")
def get_policy_reasoning(
    tenant_id: int = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XIX1 — Analyze and reason about tenant's policy effectiveness."""
    return brain_core_service.reason_about_policy(tenant_id=tenant_id)


# ── XIX4 — Predictive Policy Optimization ────────────────────────────────
@router.get("/policy-optimization/{tenant_id}")
def predict_policy_optimization(
    tenant_id: int = Path(...),
    horizon_days: int = Query(30),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XIX4 — Predict outcomes of policy optimization."""
    return brain_core_service.predict_policy_optimization(tenant_id=tenant_id, horizon_days=horizon_days)


# ── XX1 — Policy Rollout Plan ─────────────────────────────────────────────
@router.get("/policy-rollout-plan/{tenant_id}")
def generate_policy_rollout_plan(
    tenant_id: int = Path(...),
    horizon_days: int = Query(30),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XX1 — Generate staged policy rollout plan."""
    return brain_core_service.generate_policy_rollout_plan(tenant_id=tenant_id, horizon_days=horizon_days)


# ── XXXII1 — Replay Request Queue ─────────────────────────────────────────
class ReplayRequestCreate(BaseModel):
    signal_id: str = Field(..., min_length=1)
    decision_id: str = Field(..., min_length=1)
    requested_by: str = Field(..., min_length=1)
    priority: str = Field("normal", pattern="^(low|normal|high|urgent)$")
    escalation_level: int = Field(0, ge=0)


@router.post("/reprocess/request")
def create_replay_request(
    tenant_id: int = Query(...),
    body: ReplayRequestCreate = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXXII1 — Create a new replay request and add it to the queue."""
    try:
        return brain_core_service.create_replay_request(
            tenant_id,
            signal_id=body.signal_id,
            decision_id=body.decision_id,
            requested_by=body.requested_by,
            priority=body.priority,
            escalation_level=body.escalation_level,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/reprocess/request-queue")
def get_replay_request_queue(
    tenant_id: int = Query(...),
    status: str | None = Query(None, pattern="^(pending|resolved)$"),
    priority: str | None = Query(None, pattern="^(low|normal|high|urgent)$"),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXXII1 — Get filtered list of replay requests for a tenant."""
    queue = brain_core_service.get_replay_request_queue(
        tenant_id,
        status=status,
        priority=priority,
    )
    return {"total": len(queue), "requests": queue}


# ── XXXII2 — Replay Request Escalation ────────────────────────────────────
class ReplayEscalation(BaseModel):
    reason: str = Field(..., min_length=1)
    target_level: int = Field(..., ge=1)


@router.post("/reprocess/request/{request_id}/escalate")
def escalate_replay_request(
    request_id: str = Path(...),
    body: ReplayEscalation = Body(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.write"))] = None,
) -> dict:
    """XXXII2 — Escalate a replay request to a higher level."""
    try:
        return brain_core_service.escalate_replay_request(
            request_id,
            reason=body.reason,
            target_level=body.target_level,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/reprocess/request/{request_id}/escalations")
def get_escalation_history(
    request_id: str = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXXII2 — Return escalation history for a replay request."""
    escalations = brain_core_service.get_escalation_history(request_id)
    return {"request_id": request_id, "escalations": escalations}


# ── XXXII3 — Replay SLA & Queue Metrics ────────────────────────────────────
@router.get("/reprocess/queue-metrics/{tenant_id}")
def get_replay_queue_metrics(
    tenant_id: int = Path(...),
    __: Annotated[None, Depends(permission_dependency("admin.dashboard.read"))] = None,
) -> dict:
    """XXXII3 — Get SLA and queue metrics for a tenant."""
    return brain_core_service.get_replay_queue_metrics(tenant_id)
