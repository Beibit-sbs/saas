"""A-022.6 Cross-feature timetable workflow E2E / consolidation tests.

Validation-only suite proving the timetable workflow stays non-destructive while
connecting the contract chain end-to-end:

Room Allocation Recommendation
→ Timetable Change Proposal
→ Simulation / Preview
→ Approval Queue
→ Human Decision Record
→ KPI / Dashboard
→ Audit evidence

Non-destructive guarantees:
- no schedule mutation
- no room reservation
- no booking override
- no apply / commit semantics
- no fake KPI values
- no cross-tenant leakage
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.modules.scheduling.room_allocation_readiness import (
    CapacityRiskLevel,
    RoomAllocationRecommendationStatus,
    RoomAllocationRequirement,
    RoomCapability,
    build_room_allocation_recommendation_result,
)
from app.modules.scheduling.timetable_approval_queue import (
    TimetableApprovalDecision,
    TimetableApprovalDecisionStatus,
    TimetableApprovalQueueInput,
    build_timetable_approval_queue_item,
    record_timetable_approval_decision,
)
from app.modules.scheduling.timetable_change_proposal import (
    TimetableChangeCurrentSnapshot,
    TimetableChangeProposalRiskLevel,
    TimetableChangeProposalSourceType,
)
from app.modules.scheduling.timetable_change_simulation import (
    TimetableChangeSimulationInput,
    build_timetable_change_simulation,
)
from app.modules.scheduling.timetable_recommendation_bridge import (
    RoomRecommendationToProposalBridgeInput,
    build_proposal_from_room_allocation_recommendation,
)
from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork


def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(tenant["id"])


def _requirement(**overrides: object) -> RoomAllocationRequirement:
    payload: dict[str, object] = {
        "section_id": 8201,
        "course_id": 8301,
        "group_id": 8401,
        "teacher_id": "teacher-8201",
        "students_count": 36,
        "max_capacity": 40,
        "required_room_type": "computer_lab",
        "required_computers": 18,
        "equipment_required": ["projector", "whiteboard"],
        "restrictions_required": ["exam_enabled"],
    }
    payload.update(overrides)
    return RoomAllocationRequirement(**payload)


def _capability(tenant_id: int, room_id: str, **overrides: object) -> RoomCapability:
    payload: dict[str, object] = {
        "tenant_id": tenant_id,
        "room_id": room_id,
        "room_code": room_id,
        "room_name": room_id,
        "room_type": "computer_lab",
        "capacity": 40,
        "computers_count": 24,
        "equipment_available": ["projector", "whiteboard"],
        "supported_lesson_types": ["lecture", "lab"],
        "restrictions": ["exam_enabled"],
        "availability_status": "available",
        "booking_status": "released",
        "maintenance_status": "ok",
        "is_active": True,
        "source_entity_type": "campus_room",
        "source_entity_id": f"entity-{room_id}",
    }
    payload.update(overrides)
    return RoomCapability(**payload)


def _snapshot(room_id: str = "ROOM-A") -> TimetableChangeCurrentSnapshot:
    return TimetableChangeCurrentSnapshot(
        section_id=8201,
        course_id=8301,
        group_id=8401,
        teacher_id="teacher-8201",
        room_id=room_id,
        day_of_week="monday",
        time_slot_id=2,
        start_time="09:00:00",
        end_time="10:30:00",
        room_capacity=40,
        students_count=36,
        source_entity_type="section",
        source_entity_id=8201,
    )


def _recommendation_result(
    tenant_id: int,
    *,
    viable: bool = True,
    selected_room: str = "ROOM-B",
    capacity: int = 44,
    computers_count: int = 24,
    maintenance_status: str = "ok",
    availability_status: str = "available",
) -> object:
    requirement = _requirement()
    capability = _capability(
        tenant_id,
        selected_room,
        capacity=capacity,
        computers_count=computers_count,
        maintenance_status=maintenance_status,
        availability_status=availability_status,
    )
    recommendation = build_room_allocation_recommendation_result(tenant_id, requirement, [capability])

    if not viable:
        recommendation = recommendation.model_copy(
            update={
                "has_viable_candidate": False,
                "best_candidate_id": None,
                "recommendation_status": RoomAllocationRecommendationStatus.NO_VIABLE_CANDIDATE,
            }
        )

    return recommendation


def _bridge_input(
    tenant_id: int,
    recommendation_result: object,
    *,
    source_entity_id: str,
    allow_review_only_no_viable: bool = False,
    explicit_review_reason: str | None = None,
    selected_candidate_id: str | int | None = None,
) -> RoomRecommendationToProposalBridgeInput:
    return RoomRecommendationToProposalBridgeInput(
        tenant_id=tenant_id,
        recommendation_result=recommendation_result,
        current_snapshot=_snapshot(),
        selected_candidate_id=selected_candidate_id,
        created_by="reviewer-1",
        reason="Bridge from room allocation recommendation",
        explicit_review_reason=explicit_review_reason,
        allow_review_only_no_viable=allow_review_only_no_viable,
        source_entity_type="room_allocation_recommendation",
        source_entity_id=source_entity_id,
    )


def _workflow_flow(
    tenant_id: int,
    *,
    recommendation_result: object | None = None,
    source_entity_id: str = "reco-a0226-001",
    allow_review_only_no_viable: bool = False,
    explicit_review_reason: str | None = None,
    selected_candidate_id: str | int | None = None,
) -> tuple[object, object, object, object]:
    recommendation = recommendation_result or _recommendation_result(tenant_id)
    bridge_result = build_proposal_from_room_allocation_recommendation(
        _bridge_input(
            tenant_id,
            recommendation,
            source_entity_id=source_entity_id,
            allow_review_only_no_viable=allow_review_only_no_viable,
            explicit_review_reason=explicit_review_reason,
            selected_candidate_id=selected_candidate_id,
        )
    )
    simulation = build_timetable_change_simulation(bridge_result.simulation_input)
    queue_item = build_timetable_approval_queue_item(
        TimetableApprovalQueueInput(
            proposal=bridge_result.proposal,
            simulation=simulation,
            created_by="reviewer-1",
            assigned_to="reviewer-queue",
            authoritative_tenant_id=tenant_id,
        )
    )
    decision = TimetableApprovalDecision(
        tenant_id=tenant_id,
        queue_item_id=queue_item.queue_item_id,
        proposal_id=queue_item.proposal_id,
        decision_status=TimetableApprovalDecisionStatus.APPROVED,
        reviewer_id="reviewer-2",
        reviewer_note="reviewed and recorded",
        decision_reason="decision-record-only",
    )
    decision_result = record_timetable_approval_decision(
        queue_item=queue_item,
        decision=decision,
        proposal=bridge_result.proposal,
        apply_proposal_fsm=False,
    )
    return bridge_result, simulation, queue_item, decision_result


def test_recommendation_to_proposal_to_simulation_flow(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0226-flow1")
    bridge_result, simulation, queue_item, decision_result = _workflow_flow(
        tenant_id,
        source_entity_id="reco-a0226-flow1",
    )

    proposal = bridge_result.proposal

    assert proposal.source_type == TimetableChangeProposalSourceType.ROOM_ALLOCATION_RECOMMENDATION
    assert proposal.source_recommendation_id == "reco-a0226-flow1"
    assert proposal.tenant_id == tenant_id
    assert proposal.current_snapshot.section_id == 8201
    assert proposal.proposed_change.proposed_room_id == bridge_result.selected_candidate_id
    assert proposal.status.value == "draft"

    assert simulation.proposal_id == proposal.proposal_id
    assert simulation.tenant_id == tenant_id
    assert simulation.review_required is True
    assert simulation.before_after_snapshot.changed_fields == ["room_id"]
    assert simulation.conflict_delta.conflicts_created == 0
    assert simulation.risk_delta.review_required is True

    assert queue_item.tenant_id == tenant_id
    assert queue_item.proposal_id == proposal.proposal_id
    assert queue_item.simulation_id == simulation.simulation_id
    assert queue_item.review_required is True
    assert queue_item.priority.value in {"low", "medium", "high", "critical"}

    assert decision_result.decision_recorded is True
    assert decision_result.queue_item.review_status.value == "decision_recorded"
    assert decision_result.queue_item.decision_status.value == "approved"
    assert bridge_result.proposal.status.value == "draft"


def test_proposal_simulation_to_approval_queue_flow(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0226-flow2")
    bridge_result, simulation, queue_item, _ = _workflow_flow(
        tenant_id,
        source_entity_id="reco-a0226-flow2",
    )

    assert bridge_result.data_quality_note is None
    assert bridge_result.proposal.evidence.source_recommendation_id == "reco-a0226-flow2"
    assert simulation.data_quality_note is not None
    assert "draft" in simulation.data_quality_note.lower()
    assert queue_item.evidence_summary.startswith(f"proposal_id={bridge_result.proposal.proposal_id}")
    assert "simulation_id=" in queue_item.evidence_summary
    assert "review_required=True" in queue_item.evidence_summary
    assert queue_item.data_quality_note is not None
    assert "draft" in queue_item.data_quality_note.lower()


def test_approved_decision_record_does_not_apply_schedule(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0226-flow3")
    bridge_result, simulation, queue_item, decision_result = _workflow_flow(
        tenant_id,
        source_entity_id="reco-a0226-flow3",
    )

    assert decision_result.proposal is not None
    assert decision_result.proposal.status.value == "draft"
    assert decision_result.queue_item.decision_status == TimetableApprovalDecisionStatus.APPROVED
    assert decision_result.queue_item.review_status.value == "decision_recorded"
    assert simulation.proposal_id == bridge_result.proposal.proposal_id
    assert queue_item.review_status.value == "queued"


def test_rejected_decision_record_does_not_mutate_schedule(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0226-flow4")
    bridge_result, simulation, queue_item, _ = _workflow_flow(
        tenant_id,
        source_entity_id="reco-a0226-flow4",
    )

    rejected = TimetableApprovalDecision(
        tenant_id=tenant_id,
        queue_item_id=queue_item.queue_item_id,
        proposal_id=queue_item.proposal_id,
        decision_status=TimetableApprovalDecisionStatus.REJECTED,
        reviewer_id="reviewer-2",
        reviewer_note="reviewed and declined",
        decision_reason="decision-record-only",
    )
    result = record_timetable_approval_decision(
        queue_item=queue_item,
        decision=rejected,
        proposal=bridge_result.proposal,
        apply_proposal_fsm=False,
    )

    assert result.queue_item.decision_status == TimetableApprovalDecisionStatus.REJECTED
    assert result.queue_item.review_status.value == "decision_recorded"
    assert bridge_result.proposal.status.value == "draft"
    assert simulation.status.value == "computed"


def test_revision_requested_keeps_workflow_non_destructive(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0226-flow5")
    bridge_result, _, queue_item, _ = _workflow_flow(
        tenant_id,
        source_entity_id="reco-a0226-flow5",
    )

    revision = TimetableApprovalDecision(
        tenant_id=tenant_id,
        queue_item_id=queue_item.queue_item_id,
        proposal_id=queue_item.proposal_id,
        decision_status=TimetableApprovalDecisionStatus.REVISION_REQUESTED,
        reviewer_id="reviewer-2",
        reviewer_note="needs a narrower room change",
        decision_reason="review requested",
    )
    result = record_timetable_approval_decision(
        queue_item=queue_item,
        decision=revision,
        proposal=bridge_result.proposal,
        apply_proposal_fsm=False,
    )

    assert result.queue_item.review_status.value == "revision_requested"
    assert result.queue_item.decision_status == TimetableApprovalDecisionStatus.REVISION_REQUESTED
    assert bridge_result.proposal.status.value == "draft"


def test_workflow_preserves_source_recommendation_and_audit_evidence(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0226-flow6")
    bridge_result, simulation, queue_item, decision_result = _workflow_flow(
        tenant_id,
        source_entity_id="reco-a0226-flow6",
    )

    proposal_actions = [entry.action for entry in bridge_result.proposal.audit_evidence]
    queue_actions = [entry.action for entry in queue_item.audit_evidence]
    decision_actions = [entry.action for entry in decision_result.queue_item.audit_evidence]
    simulation_actions = [entry.action for entry in simulation.audit_evidence]

    assert bridge_result.proposal.source_recommendation_id == "reco-a0226-flow6"
    assert bridge_result.proposal.source_entity_id == "reco-a0226-flow6"
    assert "bridge_from_room_recommendation" in proposal_actions
    assert "simulation_computed" in simulation_actions
    assert "approval_queue_item_created" in queue_actions
    assert "approval_decision_recorded" in decision_actions
    assert bridge_result.bridge_evidence


def test_high_risk_simulation_requires_human_review(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0226-flow7")
    recommendation = _recommendation_result(
        tenant_id,
        viable=False,
        selected_room="ROOM-HIGH-RISK",
        maintenance_status="maintenance",
        availability_status="unavailable",
    )

    bridge_result = build_proposal_from_room_allocation_recommendation(
        _bridge_input(
            tenant_id,
            recommendation,
            source_entity_id="reco-a0226-flow7",
            allow_review_only_no_viable=True,
            explicit_review_reason="No viable room candidate; human review required",
        )
    )
    simulation = build_timetable_change_simulation(bridge_result.simulation_input)

    assert bridge_result.proposal.risk_level == TimetableChangeProposalRiskLevel.HIGH
    assert recommendation.recommendation_status == RoomAllocationRecommendationStatus.NO_VIABLE_CANDIDATE
    assert simulation.review_required is True
    assert simulation.risk_delta.risk_after == TimetableChangeProposalRiskLevel.HIGH
    assert simulation.risk_delta.review_required is True
    assert simulation.data_quality_note is not None


def test_cross_tenant_workflow_rejected(reset_shared_state) -> None:
    tenant_a = _create_tenant("a0226-flow8-a")
    tenant_b = _create_tenant("a0226-flow8-b")
    recommendation = _recommendation_result(tenant_b)

    with pytest.raises(ValueError, match="Cross-tenant bridge rejected"):
        build_proposal_from_room_allocation_recommendation(
            _bridge_input(
                tenant_a,
                recommendation,
                source_entity_id="reco-cross-tenant",
            )
        )

    bridge_result, simulation, queue_item, _ = _workflow_flow(
        tenant_a,
        source_entity_id="reco-a0226-flow8",
    )

    with pytest.raises(ValueError, match="Cross-tenant queue rejected"):
        build_timetable_approval_queue_item(
            TimetableApprovalQueueInput(
                proposal=bridge_result.proposal,
                simulation=simulation,
                created_by="reviewer-1",
                authoritative_tenant_id=tenant_a + 1,
            )
        )

    with pytest.raises(ValueError, match="Cross-tenant decision"):
        record_timetable_approval_decision(
            queue_item=queue_item,
            decision=TimetableApprovalDecision(
                tenant_id=tenant_a + 1,
                queue_item_id=queue_item.queue_item_id,
                proposal_id=queue_item.proposal_id,
                decision_status=TimetableApprovalDecisionStatus.APPROVED,
                reviewer_id="reviewer-2",
                reviewer_note="cross-tenant",
                decision_reason="cross-tenant",
            ),
        )


def test_no_apply_no_reservation_no_booking_override_fields_exist(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0226-flow9")
    bridge_result, simulation, queue_item, decision_result = _workflow_flow(
        tenant_id,
        source_entity_id="reco-a0226-flow9",
    )

    forbidden_keys = {
        "apply",
        "apply_flag",
        "commit",
        "auto_apply",
        "execute",
        "mutation",
        "mutate",
        "schedule_applied",
        "reservation",
        "reservation_flag",
        "reserve_room",
        "booking_override",
        "override_booking",
        "force_booking",
        "fake_optimization",
    }

    payloads = [
        bridge_result.proposal.model_dump(),
        simulation.model_dump(),
        queue_item.model_dump(),
        decision_result.queue_item.model_dump(),
    ]
    combined_text = " ".join(str(payload).lower() for payload in payloads)

    for payload in payloads:
        for key in forbidden_keys:
            assert key not in payload

    for phrase in {
        "apply now",
        "auto-apply",
        "approved and applied",
        "schedule changed automatically",
        "room reserved automatically",
        "booking overridden",
        "committed change",
        "executed",
    }:
        assert phrase not in combined_text


def test_workflow_kpi_event_contract_consistency_if_supported(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0226-flow10")

    workflow_events = [
        ("scheduling.timetable_proposal.created", 1001),
        ("scheduling.timetable_proposal.submitted", 1002),
        ("scheduling.timetable_proposal.approved", 1003),
        ("scheduling.timetable_proposal.rejected", 1004),
        ("scheduling.timetable_proposal.revision_requested", 1005),
        ("scheduling.timetable_simulation.computed", 1010),
        ("scheduling.timetable_simulation.review_required", 1011),
        ("scheduling.timetable_simulation.conflicts_created", 1012),
        ("scheduling.timetable_simulation.conflicts_resolved", 1013),
        ("scheduling.timetable_approval.queued", 1020),
        ("scheduling.timetable_approval.in_review", 1021),
        ("scheduling.timetable_approval.approved", 1022),
        ("scheduling.timetable_approval.rejected", 1023),
        ("scheduling.timetable_approval.revision_requested", 1024),
        ("scheduling.timetable_approval.high_risk", 1025),
    ]
    for event_type, event_id in workflow_events:
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type=event_type,
            payload={"id": event_id, "source": "a0226-e2e"},
        )

    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

    values = {str(item["metric_key"]): int(item["metric_value"]) for item in rows}

    assert values["timetable_change_proposals_count"] == 1
    assert values["timetable_change_pending_review_count"] == 1
    assert values["timetable_change_approved_count"] == 1
    assert values["timetable_change_rejected_count"] == 1
    assert values["timetable_change_revision_requested_count"] == 1
    assert values["timetable_simulations_count"] == 1
    assert values["timetable_simulations_review_required_count"] == 1
    assert values["timetable_simulation_conflicts_created_count"] == 1
    assert values["timetable_simulation_conflicts_resolved_count"] == 1
    assert values["timetable_approval_queue_count"] == 1
    assert values["timetable_approval_pending_count"] == 2
    assert values["timetable_approval_approved_count"] == 1
    assert values["timetable_approval_rejected_count"] == 1
    assert values["timetable_approval_revision_requested_count"] == 1
    assert values["timetable_approval_high_risk_count"] == 1