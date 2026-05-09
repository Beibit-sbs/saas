"""A-022.4 Human Approval Queue / Decision Contract.

Non-destructive contract for recording human review decisions for timetable
change proposals. This module never applies schedule changes.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.scheduling.timetable_change_proposal import (
    TimetableChangeAuditEvidence,
    TimetableChangeProposal,
    TimetableChangeProposalRiskLevel,
    TimetableChangeProposalStatus,
    transition_timetable_change_proposal,
)
from app.modules.scheduling.timetable_change_simulation import (
    TimetableChangeSimulationResult,
)


class TimetableApprovalReviewStatus(str, Enum):
    QUEUED = "queued"
    IN_REVIEW = "in_review"
    DECISION_RECORDED = "decision_recorded"
    REVISION_REQUESTED = "revision_requested"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TimetableApprovalDecisionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TimetableApprovalPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TimetableApprovalAuditEvidence(BaseModel):
    action: str
    previous_status: Optional[str] = None
    new_status: str
    actor_id: Optional[str | int] = None
    reason: Optional[str] = None
    timestamp: Optional[str] = None
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[str | int] = None


class TimetableApprovalQueueItem(BaseModel):
    queue_item_id: str
    tenant_id: int = Field(gt=0)

    proposal_id: str
    simulation_id: Optional[str] = None

    domain: str = "scheduling"
    title: str = "Timetable change review"

    review_status: TimetableApprovalReviewStatus = TimetableApprovalReviewStatus.QUEUED
    decision_status: TimetableApprovalDecisionStatus = TimetableApprovalDecisionStatus.PENDING

    priority: TimetableApprovalPriority = TimetableApprovalPriority.MEDIUM
    risk_level: TimetableChangeProposalRiskLevel = TimetableChangeProposalRiskLevel.MEDIUM
    review_required: bool = True

    created_by: Optional[str | int] = None
    assigned_to: Optional[str | int] = None
    reviewer_id: Optional[str | int] = None
    reviewer_note: Optional[str] = None
    decision_reason: Optional[str] = None

    evidence_summary: str = ""
    data_quality_note: Optional[str] = None

    source_entity_type: Optional[str] = "scheduling_section"
    source_entity_id: Optional[str | int] = None

    audit_evidence: list[TimetableApprovalAuditEvidence] = Field(default_factory=list)


class TimetableApprovalDecision(BaseModel):
    tenant_id: int = Field(gt=0)
    queue_item_id: str
    proposal_id: str

    decision_status: TimetableApprovalDecisionStatus

    reviewer_id: Optional[str | int] = None
    reviewer_note: Optional[str] = None
    decision_reason: Optional[str] = None
    decided_at: Optional[str] = None

    source_entity_type: Optional[str] = "timetable_approval_queue"
    source_entity_id: Optional[str | int] = None


class TimetableApprovalQueueInput(BaseModel):
    proposal: TimetableChangeProposal
    simulation: Optional[TimetableChangeSimulationResult] = None

    created_by: Optional[str | int] = None
    assigned_to: Optional[str | int] = None
    priority: Optional[TimetableApprovalPriority] = None
    authoritative_tenant_id: Optional[int] = None

    domain: str = "scheduling"


class TimetableApprovalQueueResult(BaseModel):
    queue_item: TimetableApprovalQueueItem
    decision: Optional[TimetableApprovalDecision] = None
    proposal: Optional[TimetableChangeProposal] = None
    decision_recorded: bool = False
    data_quality_note: Optional[str] = None


_QUEUE_COUNTER = 0

_TERMINAL_REVIEW_STATUSES: frozenset[TimetableApprovalReviewStatus] = frozenset(
    {
        TimetableApprovalReviewStatus.DECISION_RECORDED,
        TimetableApprovalReviewStatus.CANCELLED,
        TimetableApprovalReviewStatus.EXPIRED,
    }
)


def _generate_queue_item_id() -> str:
    global _QUEUE_COUNTER
    _QUEUE_COUNTER += 1
    return f"approval_{_QUEUE_COUNTER:06d}"


def _derive_priority(risk_level: TimetableChangeProposalRiskLevel) -> TimetableApprovalPriority:
    mapping = {
        TimetableChangeProposalRiskLevel.LOW: TimetableApprovalPriority.LOW,
        TimetableChangeProposalRiskLevel.MEDIUM: TimetableApprovalPriority.MEDIUM,
        TimetableChangeProposalRiskLevel.HIGH: TimetableApprovalPriority.HIGH,
        TimetableChangeProposalRiskLevel.CRITICAL: TimetableApprovalPriority.CRITICAL,
    }
    return mapping[risk_level]


def _build_evidence_summary(
    proposal: TimetableChangeProposal,
    simulation: Optional[TimetableChangeSimulationResult],
) -> str:
    parts: list[str] = [
        f"proposal_id={proposal.proposal_id}",
        f"proposal_status={proposal.status.value}",
        f"risk={proposal.risk_level.value}",
    ]
    if proposal.evidence.risk_summary:
        parts.append(proposal.evidence.risk_summary)
    if simulation is not None:
        parts.append(f"simulation_id={simulation.simulation_id}")
        parts.append(f"simulation_status={simulation.status.value}")
        parts.append(f"review_required={simulation.review_required}")
    return "; ".join(parts)


def build_timetable_approval_audit_evidence(
    *,
    action: str,
    previous_status: Optional[str],
    new_status: str,
    actor_id: Optional[str | int] = None,
    reason: Optional[str] = None,
    source_entity_type: Optional[str] = None,
    source_entity_id: Optional[str | int] = None,
) -> TimetableApprovalAuditEvidence:
    return TimetableApprovalAuditEvidence(
        action=action,
        previous_status=previous_status,
        new_status=new_status,
        actor_id=actor_id,
        reason=reason,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
    )


def build_timetable_approval_queue_item(
    inp: TimetableApprovalQueueInput,
) -> TimetableApprovalQueueItem:
    proposal = inp.proposal
    simulation = inp.simulation

    if proposal.tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")

    if not proposal.proposal_id:
        raise ValueError("proposal_id is required")

    if inp.authoritative_tenant_id is not None and inp.authoritative_tenant_id != proposal.tenant_id:
        raise ValueError(
            "Cross-tenant queue rejected: proposal tenant does not match authoritative tenant"
        )

    if simulation is not None:
        if simulation.tenant_id != proposal.tenant_id:
            raise ValueError(
                "Cross-tenant queue rejected: simulation tenant does not match proposal tenant"
            )
        if simulation.proposal_id != proposal.proposal_id:
            raise ValueError(
                "simulation.proposal_id must match proposal.proposal_id"
            )

    risk_level = simulation.risk_delta.risk_after if simulation is not None else proposal.risk_level
    priority = inp.priority or _derive_priority(risk_level)

    audit_entry = build_timetable_approval_audit_evidence(
        action="approval_queue_item_created",
        previous_status=None,
        new_status=TimetableApprovalReviewStatus.QUEUED.value,
        actor_id=inp.created_by,
        reason="Human approval queue item created",
        source_entity_type=proposal.source_entity_type,
        source_entity_id=proposal.source_entity_id,
    )

    data_quality_note = (
        simulation.data_quality_note if simulation is not None else proposal.evidence.data_quality_note
    )

    return TimetableApprovalQueueItem(
        queue_item_id=_generate_queue_item_id(),
        tenant_id=proposal.tenant_id,
        proposal_id=proposal.proposal_id,
        simulation_id=simulation.simulation_id if simulation is not None else None,
        domain=inp.domain,
        title=f"Timetable change proposal {proposal.proposal_id}",
        review_status=TimetableApprovalReviewStatus.QUEUED,
        decision_status=TimetableApprovalDecisionStatus.PENDING,
        priority=priority,
        risk_level=risk_level,
        review_required=True,
        created_by=inp.created_by,
        assigned_to=inp.assigned_to,
        evidence_summary=_build_evidence_summary(proposal, simulation),
        data_quality_note=data_quality_note,
        source_entity_type=proposal.source_entity_type,
        source_entity_id=proposal.source_entity_id,
        audit_evidence=[audit_entry],
    )


def validate_timetable_approval_decision(
    queue_item: TimetableApprovalQueueItem,
    decision: TimetableApprovalDecision,
) -> None:
    if decision.tenant_id != queue_item.tenant_id:
        raise ValueError("Cross-tenant decision rejected")

    if decision.queue_item_id != queue_item.queue_item_id:
        raise ValueError("decision.queue_item_id does not match queue item")

    if decision.proposal_id != queue_item.proposal_id:
        raise ValueError("decision.proposal_id does not match queue item")

    if queue_item.review_status in _TERMINAL_REVIEW_STATUSES:
        raise ValueError("Terminal queue item cannot be decided again")

    if decision.decision_status == TimetableApprovalDecisionStatus.PENDING:
        raise ValueError("Invalid decision status: pending")

    if decision.decision_status in {
        TimetableApprovalDecisionStatus.APPROVED,
        TimetableApprovalDecisionStatus.REJECTED,
        TimetableApprovalDecisionStatus.REVISION_REQUESTED,
    } and decision.reviewer_id is None:
        raise ValueError("reviewer_id is required for this decision")

    if decision.decision_status in {
        TimetableApprovalDecisionStatus.REJECTED,
        TimetableApprovalDecisionStatus.REVISION_REQUESTED,
    } and not decision.reviewer_note:
        raise ValueError("reviewer_note is required for rejected/revision_requested")

    if queue_item.risk_level in {
        TimetableChangeProposalRiskLevel.HIGH,
        TimetableChangeProposalRiskLevel.CRITICAL,
    } and decision.decision_status in {
        TimetableApprovalDecisionStatus.APPROVED,
        TimetableApprovalDecisionStatus.REJECTED,
        TimetableApprovalDecisionStatus.REVISION_REQUESTED,
    } and not decision.reviewer_note:
        raise ValueError("high/critical decisions require explicit reviewer_note")


def _review_status_from_decision(
    decision_status: TimetableApprovalDecisionStatus,
) -> TimetableApprovalReviewStatus:
    if decision_status == TimetableApprovalDecisionStatus.REVISION_REQUESTED:
        return TimetableApprovalReviewStatus.REVISION_REQUESTED
    if decision_status == TimetableApprovalDecisionStatus.CANCELLED:
        return TimetableApprovalReviewStatus.CANCELLED
    if decision_status == TimetableApprovalDecisionStatus.EXPIRED:
        return TimetableApprovalReviewStatus.EXPIRED
    return TimetableApprovalReviewStatus.DECISION_RECORDED


def _proposal_status_from_decision(
    decision_status: TimetableApprovalDecisionStatus,
) -> TimetableChangeProposalStatus:
    mapping = {
        TimetableApprovalDecisionStatus.APPROVED: TimetableChangeProposalStatus.APPROVED,
        TimetableApprovalDecisionStatus.REJECTED: TimetableChangeProposalStatus.REJECTED,
        TimetableApprovalDecisionStatus.REVISION_REQUESTED: TimetableChangeProposalStatus.REVISION_REQUESTED,
        TimetableApprovalDecisionStatus.CANCELLED: TimetableChangeProposalStatus.CANCELLED,
        TimetableApprovalDecisionStatus.EXPIRED: TimetableChangeProposalStatus.EXPIRED,
    }
    return mapping[decision_status]


def record_timetable_approval_decision(
    *,
    queue_item: TimetableApprovalQueueItem,
    decision: TimetableApprovalDecision,
    proposal: Optional[TimetableChangeProposal] = None,
    apply_proposal_fsm: bool = False,
) -> TimetableApprovalQueueResult:
    validate_timetable_approval_decision(queue_item, decision)

    next_review_status = _review_status_from_decision(decision.decision_status)

    audit_entry = build_timetable_approval_audit_evidence(
        action="approval_decision_recorded",
        previous_status=queue_item.review_status.value,
        new_status=next_review_status.value,
        actor_id=decision.reviewer_id,
        reason=decision.decision_reason or decision.reviewer_note,
        source_entity_type=decision.source_entity_type,
        source_entity_id=decision.source_entity_id or queue_item.queue_item_id,
    )

    updated_queue_item = queue_item.model_copy(
        update={
            "review_status": next_review_status,
            "decision_status": decision.decision_status,
            "reviewer_id": decision.reviewer_id,
            "reviewer_note": decision.reviewer_note,
            "decision_reason": decision.decision_reason,
            "audit_evidence": queue_item.audit_evidence + [audit_entry],
        }
    )

    updated_proposal = proposal
    if apply_proposal_fsm:
        if proposal is None:
            raise ValueError("proposal is required when apply_proposal_fsm=True")
        if proposal.tenant_id != queue_item.tenant_id or proposal.proposal_id != queue_item.proposal_id:
            raise ValueError("proposal must match queue item tenant/proposal")

        updated_proposal = transition_timetable_change_proposal(
            proposal,
            _proposal_status_from_decision(decision.decision_status),
            actor_id=decision.reviewer_id,
            reviewer_id=decision.reviewer_id,
            reviewer_note=decision.reviewer_note,
            reason=decision.decision_reason,
            requesting_tenant_id=decision.tenant_id,
        )

    return TimetableApprovalQueueResult(
        queue_item=updated_queue_item,
        decision=decision,
        proposal=updated_proposal,
        decision_recorded=True,
        data_quality_note=updated_queue_item.data_quality_note,
    )
