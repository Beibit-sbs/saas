"""A-020.3 — Scheduling Conflict Detection Enhancement Tests.

Validates SchedulingConflictEvidence contract, detect_room_requirement_conflicts(),
and build_scheduling_conflict_result() introduced in A-020.3.

Non-destructive policy:
- All helpers are evidence-only.
- No schedule/booking mutations.
- No auto-assignment, no ranking, no auto-apply.

Tenant safety:
- tenant_id must be positive and match capability.tenant_id.
- Cross-tenant spoof rejected.
"""
from __future__ import annotations

import pytest

from app.modules.scheduling.room_allocation_readiness import (
    ConflictSeverity,
    ConflictType,
    RoomAllocationRequirement,
    RoomAllocationSchedule,
    RoomCapability,
    RoomCapabilityMatchEvidence,
    SchedulingConflictCheckInput,
    SchedulingConflictEvidence,
    SchedulingConflictResult,
    build_scheduling_conflict_result,
    detect_room_requirement_conflicts,
)

# ─── Fixtures ─────────────────────────────────────────────────────────────────

TENANT = 1


def _req(**kwargs) -> RoomAllocationRequirement:
    defaults = dict(
        section_id=10,
        course_id=20,
        group_id=30,
        teacher_id="T001",
        students_count=25,
        max_capacity=30,
        required_room_type="lecture_hall",
        required_computers=None,
        equipment_required=["projector"],
        restrictions_required=None,
    )
    defaults.update(kwargs)
    return RoomAllocationRequirement(**defaults)


def _cap(**kwargs) -> RoomCapability:
    defaults = dict(
        tenant_id=TENANT,
        room_id="R001",
        room_name="Room 101",
        room_type="lecture_hall",
        capacity=40,
        computers_count=0,
        equipment_available=["projector", "whiteboard"],
        is_active=True,
        availability_status="available",
        maintenance_status=None,
        booking_status=None,
        restrictions=[],
        source_entity_id="R001",
    )
    defaults.update(kwargs)
    return RoomCapability(**defaults)


def _sched(**kwargs) -> RoomAllocationSchedule:
    defaults = dict(day_of_week="monday", time_slot_id=3)
    defaults.update(kwargs)
    return RoomAllocationSchedule(**defaults)


# ─── Test 1: Room time conflict detected ──────────────────────────────────────

def test_room_time_conflict_detected():
    """Room time conflict detected when same room booked at same day/slot."""
    req = _req()
    cap = _cap()
    sched = _sched()
    bookings = [{"room_id": "R001", "day_of_week": "monday", "time_slot_id": 3, "section_id": 99, "booking_type": "schedule"}]
    conflicts = detect_room_requirement_conflicts(
        TENANT, req, capability=cap, schedule=sched, existing_bookings=bookings
    )
    ct = [c for c in conflicts if c.conflict_type == ConflictType.ROOM_TIME_CONFLICT]
    assert ct, "Expected room_time_conflict"
    assert ct[0].severity == ConflictSeverity.CRITICAL
    assert "R001" in ct[0].reason or str(ct[0].room_id) == "R001"


# ─── Test 2: Teacher time conflict detected ───────────────────────────────────

def test_teacher_time_conflict_detected():
    """Teacher conflict detected when same teacher has another section at same slot."""
    req = _req(teacher_id="T001")
    cap = _cap()
    sched = _sched()
    teacher_schedules = [{"teacher_id": "T001", "day_of_week": "monday", "time_slot_id": 3, "section_id": 99}]
    conflicts = detect_room_requirement_conflicts(
        TENANT, req, capability=cap, schedule=sched, teacher_schedules=teacher_schedules
    )
    ct = [c for c in conflicts if c.conflict_type == ConflictType.TEACHER_TIME_CONFLICT]
    assert ct, "Expected teacher_time_conflict"
    assert ct[0].severity == ConflictSeverity.CRITICAL
    assert ct[0].teacher_id == "T001"
    assert ct[0].conflicting_entity_id == 99


# ─── Test 3: Group time conflict detected ────────────────────────────────────

def test_group_time_conflict_detected():
    """Group conflict detected when same group is already scheduled at same slot."""
    req = _req(group_id=30)
    cap = _cap()
    sched = _sched()
    group_schedules = [{"group_id": 30, "day_of_week": "monday", "time_slot_id": 3, "section_id": 88}]
    conflicts = detect_room_requirement_conflicts(
        TENANT, req, capability=cap, schedule=sched, group_schedules=group_schedules
    )
    ct = [c for c in conflicts if c.conflict_type == ConflictType.GROUP_TIME_CONFLICT]
    assert ct, "Expected group_time_conflict"
    assert ct[0].severity == ConflictSeverity.CRITICAL
    assert ct[0].group_id == 30
    assert ct[0].conflicting_entity_id == 88


# ─── Test 4: Capacity mismatch ───────────────────────────────────────────────

def test_capacity_mismatch_produces_conflict_evidence():
    """Capacity mismatch produces conflict evidence when room too small."""
    req = _req(students_count=50, equipment_required=None)
    cap = _cap(capacity=30)
    conflicts = detect_room_requirement_conflicts(TENANT, req, capability=cap)
    ct = [c for c in conflicts if c.conflict_type == ConflictType.CAPACITY_MISMATCH]
    assert ct, "Expected capacity_mismatch"
    assert ct[0].severity == ConflictSeverity.HIGH
    assert ct[0].evidence["required"] == 50


# ─── Test 5: Computer shortage ───────────────────────────────────────────────

def test_computer_shortage_produces_conflict_evidence():
    """Computer shortage conflict when room has fewer computers than required."""
    req = _req(required_computers=20, equipment_required=None)
    cap = _cap(computers_count=5)
    conflicts = detect_room_requirement_conflicts(TENANT, req, capability=cap)
    ct = [c for c in conflicts if c.conflict_type == ConflictType.COMPUTER_SHORTAGE]
    assert ct, "Expected computer_shortage"
    assert ct[0].severity == ConflictSeverity.MEDIUM
    assert ct[0].evidence["required"] == 20


# ─── Test 6: Room type mismatch ──────────────────────────────────────────────

def test_room_type_mismatch_produces_conflict_evidence():
    """Room type mismatch conflict when room type doesn't match requirement."""
    req = _req(required_room_type="computer_lab", equipment_required=None)
    cap = _cap(room_type="lecture_hall")
    conflicts = detect_room_requirement_conflicts(TENANT, req, capability=cap)
    ct = [c for c in conflicts if c.conflict_type == ConflictType.ROOM_TYPE_MISMATCH]
    assert ct, "Expected room_type_mismatch"
    assert ct[0].severity == ConflictSeverity.HIGH
    assert ct[0].evidence["required_type"] == "computer_lab"


# ─── Test 7: Equipment mismatch ──────────────────────────────────────────────

def test_equipment_mismatch_produces_conflict_evidence():
    """Equipment mismatch conflict when required equipment is missing."""
    req = _req(required_room_type=None, equipment_required=["projector", "smartboard"])
    cap = _cap(room_type="lecture_hall", equipment_available=["whiteboard"])
    conflicts = detect_room_requirement_conflicts(TENANT, req, capability=cap)
    ct = [c for c in conflicts if c.conflict_type == ConflictType.EQUIPMENT_MISMATCH]
    assert ct, "Expected equipment_mismatch"
    assert ct[0].severity == ConflictSeverity.MEDIUM
    assert "projector" in ct[0].evidence["missing_equipment"] or "smartboard" in ct[0].evidence["missing_equipment"]


# ─── Test 8: Room unavailable / maintenance ──────────────────────────────────

def test_room_unavailable_maintenance_produces_conflict_evidence():
    """Room unavailable conflict when room is under maintenance."""
    req = _req(equipment_required=None)
    cap = _cap(maintenance_status="maintenance")
    conflicts = detect_room_requirement_conflicts(TENANT, req, capability=cap)
    ct = [c for c in conflicts if c.conflict_type == ConflictType.ROOM_UNAVAILABLE]
    assert ct, "Expected room_unavailable"
    assert ct[0].severity == ConflictSeverity.HIGH
    assert "room_under_maintenance" in ct[0].evidence.get("unavailability_reasons", [])


def test_room_inactive_produces_unavailable_conflict():
    """Inactive room triggers ROOM_UNAVAILABLE conflict."""
    req = _req(equipment_required=None)
    cap = _cap(is_active=False)
    conflicts = detect_room_requirement_conflicts(TENANT, req, capability=cap)
    ct = [c for c in conflicts if c.conflict_type == ConflictType.ROOM_UNAVAILABLE]
    assert ct, "Expected room_unavailable for inactive room"


# ─── Test 9: Booking conflict ────────────────────────────────────────────────

def test_booking_conflict_produces_conflict_evidence():
    """Booking conflict detected when room already has an approved booking at slot."""
    req = _req(equipment_required=None)
    cap = _cap()
    sched = _sched()
    bookings = [{"room_id": "R001", "day_of_week": "monday", "time_slot_id": 3, "section_id": 77, "booking_type": "booking"}]
    conflicts = detect_room_requirement_conflicts(
        TENANT, req, capability=cap, schedule=sched, existing_bookings=bookings
    )
    ct = [c for c in conflicts if c.conflict_type == ConflictType.BOOKING_CONFLICT]
    assert ct, "Expected booking_conflict"
    assert ct[0].severity == ConflictSeverity.CRITICAL


# ─── Test 10: Restriction mismatch ───────────────────────────────────────────

def test_restriction_mismatch_produces_conflict_evidence():
    """Restriction mismatch conflict when required restrictions not satisfied."""
    req = _req(required_room_type=None, equipment_required=None, restrictions_required=["wheelchair_accessible"])
    cap = _cap(restrictions=[])
    conflicts = detect_room_requirement_conflicts(TENANT, req, capability=cap)
    ct = [c for c in conflicts if c.conflict_type == ConflictType.RESTRICTION_MISMATCH]
    assert ct, "Expected restriction_mismatch"
    assert ct[0].severity == ConflictSeverity.LOW


# ─── Test 11: No conflict returns empty list ─────────────────────────────────

def test_no_conflict_returns_empty_list():
    """No conflict evidence when all conditions satisfied."""
    req = _req(students_count=25, required_room_type="lecture_hall", equipment_required=["projector"])
    cap = _cap(capacity=40, room_type="lecture_hall", equipment_available=["projector"])
    conflicts = detect_room_requirement_conflicts(TENANT, req, capability=cap)
    assert conflicts == [], "Expected empty conflict list when all conditions met"


# ─── Test 12: Missing tenant_id fails closed ─────────────────────────────────

def test_missing_tenant_id_fails_closed():
    """Invalid tenant_id raises ValueError."""
    req = _req()
    with pytest.raises((ValueError, Exception)):
        detect_room_requirement_conflicts(0, req)

    with pytest.raises((ValueError, Exception)):
        detect_room_requirement_conflicts(-1, req)


# ─── Test 13: Missing optional fields do not crash ───────────────────────────

def test_missing_optional_fields_do_not_crash():
    """Minimal requirement with no optional fields does not crash."""
    req = RoomAllocationRequirement(section_id=1, course_id=2, students_count=10, max_capacity=20)
    conflicts = detect_room_requirement_conflicts(TENANT, req)
    assert isinstance(conflicts, list)


def test_no_capability_no_schedule_no_crash():
    """No capability, no schedule, no bookings — returns empty list."""
    req = _req()
    conflicts = detect_room_requirement_conflicts(TENANT, req)
    assert conflicts == []


# ─── Test 14: Cross-tenant spoof rejected ────────────────────────────────────

def test_cross_tenant_spoof_rejected():
    """Capability from different tenant is rejected."""
    req = _req()
    cap = _cap(tenant_id=999)  # different from TENANT=1
    with pytest.raises((ValueError, Exception)):
        detect_room_requirement_conflicts(TENANT, req, capability=cap)


# ─── Test 15: Conflict helper does not mutate schedule ───────────────────────

def test_conflict_helper_does_not_mutate_schedule():
    """Schedule object is not mutated by detection helper."""
    req = _req(equipment_required=None)
    cap = _cap()
    sched = _sched(day_of_week="tuesday", time_slot_id=5)
    original_day = sched.day_of_week
    original_slot = sched.time_slot_id
    detect_room_requirement_conflicts(TENANT, req, capability=cap, schedule=sched)
    assert sched.day_of_week == original_day
    assert sched.time_slot_id == original_slot


# ─── Test 16: Conflict helper does not mutate room capability ────────────────

def test_conflict_helper_does_not_mutate_room_capability():
    """Capability object is not mutated by detection helper."""
    req = _req(equipment_required=None)
    cap = _cap(capacity=10)  # triggers capacity conflict
    original_capacity = cap.capacity
    original_active = cap.is_active
    detect_room_requirement_conflicts(TENANT, req, capability=cap)
    assert cap.capacity == original_capacity
    assert cap.is_active == original_active


# ─── Test 17: No recommendation ranking produced ─────────────────────────────

def test_no_recommendation_ranking_produced():
    """Result has no ranking or recommendation fields."""
    req = _req(students_count=50, equipment_required=None)
    cap = _cap(capacity=30)
    result = build_scheduling_conflict_result(TENANT, req, capability=cap)
    result_dict = result.model_dump()
    assert "ranking" not in result_dict
    assert "recommended_room" not in result_dict
    assert "auto_assign" not in result_dict
    assert "optimization_score" not in result_dict


# ─── Test 18: No auto reassignment / auto apply ──────────────────────────────

def test_no_auto_reassignment_in_result():
    """SchedulingConflictResult carries no auto-assignment fields."""
    req = _req(equipment_required=None)
    cap = _cap()
    result = build_scheduling_conflict_result(TENANT, req, capability=cap)
    # Verify result fields only carry evidence
    assert hasattr(result, "has_conflicts")
    assert hasattr(result, "conflicts")
    assert hasattr(result, "severity_summary")
    assert not hasattr(result, "apply") or result.model_fields.get("apply") is None


# ─── Test 19: Severity summary computed correctly ────────────────────────────

def test_severity_summary_computed():
    """build_scheduling_conflict_result populates severity_summary correctly."""
    req = _req(students_count=50, required_room_type="computer_lab", required_computers=30, equipment_required=["smartboard"])
    cap = _cap(capacity=30, room_type="lecture_hall", computers_count=5, equipment_available=[], is_active=False)
    result = build_scheduling_conflict_result(TENANT, req, capability=cap)
    assert result.has_conflicts is True
    assert result.conflict_count >= 1
    assert isinstance(result.severity_summary, dict)
    total_from_summary = sum(result.severity_summary.values())
    assert total_from_summary == result.conflict_count


# ─── Test 20: A-020.1 readiness tests remain compatible ──────────────────────

def test_a020_1_schemas_still_importable():
    """A-020.1 schemas remain importable and functional after A-020.3 additions."""
    from app.modules.scheduling.room_allocation_readiness import (
        RoomAllocationReadiness,
        RoomAllocationEvidence,
        RoomAllocationAvailability,
        room_allocation_readiness_from_event_payload,
    )
    payload = {
        "section_id": 1, "course_id": 2, "enrolled_count": 10,
        "max_capacity": 20, "room_id": "R1", "room_capacity": 25,
    }
    readiness = room_allocation_readiness_from_event_payload(1, payload)
    assert readiness.tenant_id == 1
    assert readiness.requirement.section_id == 1


# ─── Test 21: A-020.2 capability tests remain compatible ─────────────────────

def test_a020_2_capability_schemas_still_importable():
    """A-020.2 schemas remain importable and functional after A-020.3 additions."""
    from app.modules.scheduling.room_allocation_readiness import (
        RoomCapability,
        RoomCapabilityMatchEvidence,
        assess_room_capability_against_requirement,
        to_room_allocation_availability,
    )
    cap = _cap()
    req = _req(equipment_required=["projector"])
    match = assess_room_capability_against_requirement(cap, req, authoritative_tenant_id=TENANT)
    assert match.capacity_ok is True
    assert match.room_allocation_required is False
    avail = to_room_allocation_availability(cap, authoritative_tenant_id=TENANT)
    assert avail.room_id == "R001"


# ─── Test 22: ConflictType enum covers all 10 categories ─────────────────────

def test_conflict_type_enum_coverage():
    """ConflictType enum has exactly the required 10 conflict categories."""
    expected = {
        "room_time_conflict", "teacher_time_conflict", "group_time_conflict",
        "capacity_mismatch", "computer_shortage", "room_type_mismatch",
        "equipment_mismatch", "room_unavailable", "booking_conflict",
        "restriction_mismatch",
    }
    actual = {ct.value for ct in ConflictType}
    assert actual == expected


# ─── Test 23: Severity enum has required levels ──────────────────────────────

def test_severity_enum_coverage():
    """ConflictSeverity has low / medium / high / critical levels."""
    expected = {"low", "medium", "high", "critical"}
    actual = {s.value for s in ConflictSeverity}
    assert actual == expected


# ─── Test 24: SchedulingConflictEvidence schema validation ───────────────────

def test_scheduling_conflict_evidence_schema():
    """SchedulingConflictEvidence validates required fields."""
    ev = SchedulingConflictEvidence(
        tenant_id=1,
        conflict_type=ConflictType.CAPACITY_MISMATCH,
        severity=ConflictSeverity.HIGH,
        reason="test",
    )
    assert ev.tenant_id == 1
    assert ev.conflict_type == ConflictType.CAPACITY_MISMATCH
    assert ev.severity == ConflictSeverity.HIGH

    with pytest.raises(Exception):
        SchedulingConflictEvidence(tenant_id=0, conflict_type=ConflictType.CAPACITY_MISMATCH, severity=ConflictSeverity.HIGH, reason="x")


# ─── Test 25: SchedulingConflictCheckInput schema ────────────────────────────

def test_scheduling_conflict_check_input_schema():
    """SchedulingConflictCheckInput accepts valid input bag."""
    req = _req(equipment_required=None)
    inp = SchedulingConflictCheckInput(tenant_id=TENANT, requirement=req)
    assert inp.tenant_id == TENANT
    assert inp.existing_bookings == []
    assert inp.teacher_schedules == []
    assert inp.group_schedules == []


# ─── Test 26: Teacher conflict not fired for same section ────────────────────

def test_teacher_conflict_not_fired_for_same_section():
    """Teacher schedule entry for same section_id does not produce conflict."""
    req = _req(teacher_id="T001")
    cap = _cap(equipment_available=["projector"])
    sched = _sched()
    # Same section_id as requirement — should not conflict
    teacher_schedules = [{"teacher_id": "T001", "day_of_week": "monday", "time_slot_id": 3, "section_id": 10}]
    conflicts = detect_room_requirement_conflicts(
        TENANT, req, capability=cap, schedule=sched, teacher_schedules=teacher_schedules
    )
    ct = [c for c in conflicts if c.conflict_type == ConflictType.TEACHER_TIME_CONFLICT]
    assert not ct, "Teacher conflict must not fire for same section_id"


# ─── Test 27: Group conflict not fired for same section ──────────────────────

def test_group_conflict_not_fired_for_same_section():
    """Group schedule entry for same section_id does not produce conflict."""
    req = _req(group_id=30)
    cap = _cap(equipment_available=["projector"])
    sched = _sched()
    group_schedules = [{"group_id": 30, "day_of_week": "monday", "time_slot_id": 3, "section_id": 10}]
    conflicts = detect_room_requirement_conflicts(
        TENANT, req, capability=cap, schedule=sched, group_schedules=group_schedules
    )
    ct = [c for c in conflicts if c.conflict_type == ConflictType.GROUP_TIME_CONFLICT]
    assert not ct, "Group conflict must not fire for same section_id"


# ─── Test 28: Slot mismatch does not produce false conflict ──────────────────

def test_different_slot_does_not_produce_room_conflict():
    """Bookings at a different time slot do not trigger room_time_conflict."""
    req = _req(equipment_required=None)
    cap = _cap()
    sched = _sched(day_of_week="monday", time_slot_id=3)
    bookings = [{"room_id": "R001", "day_of_week": "monday", "time_slot_id": 99, "section_id": 99, "booking_type": "schedule"}]
    conflicts = detect_room_requirement_conflicts(
        TENANT, req, capability=cap, schedule=sched, existing_bookings=bookings
    )
    ct = [c for c in conflicts if c.conflict_type == ConflictType.ROOM_TIME_CONFLICT]
    assert not ct, "Different slot should not trigger room_time_conflict"


# ─── Test 29: SchedulingConflictResult has_conflicts false when no conflicts ──

def test_conflict_result_no_conflicts():
    """build_scheduling_conflict_result returns has_conflicts=False when clean."""
    req = _req(students_count=20, required_room_type="lecture_hall", equipment_required=["projector"])
    cap = _cap(capacity=40, room_type="lecture_hall", equipment_available=["projector"])
    result = build_scheduling_conflict_result(TENANT, req, capability=cap)
    assert result.has_conflicts is False
    assert result.conflict_count == 0
    assert result.conflicts == []
    assert result.severity_summary == {}


# ─── Test 30: Pre-computed capability_match accepted without recomputation ────

def test_precomputed_capability_match_used():
    """detect_room_requirement_conflicts accepts pre-computed capability_match."""
    req = _req(equipment_required=None)
    cap = _cap()
    match = RoomCapabilityMatchEvidence(
        capacity_ok=False,
        mismatch_reasons=["capacity_shortage"],
    )
    # Passing pre-computed match — must not recompute internally
    conflicts = detect_room_requirement_conflicts(
        TENANT, req, capability=cap, capability_match=match
    )
    ct = [c for c in conflicts if c.conflict_type == ConflictType.CAPACITY_MISMATCH]
    assert ct, "Pre-computed match with capacity_ok=False should yield CAPACITY_MISMATCH"
