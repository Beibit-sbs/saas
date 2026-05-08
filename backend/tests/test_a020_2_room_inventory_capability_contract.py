"""A-020.2 — Room Inventory / Room Capability Contract tests."""
from __future__ import annotations

import pytest

from app.modules.scheduling.room_allocation_readiness import (
    RoomAllocationRequirement,
    RoomCapability,
    STANDARD_LESSON_TYPES,
    STANDARD_ROOM_TYPES,
    assess_room_capability_against_requirement,
    build_room_capability_evidence,
    to_room_allocation_availability,
)


def _base_requirement(**overrides):
    data = {
        "section_id": 10,
        "course_id": 20,
        "students_count": 30,
        "max_capacity": 35,
        "required_room_type": "computer_lab",
        "required_computers": 20,
        "equipment_required": ["projector", "whiteboard"],
        "restrictions_required": ["exam_enabled"],
    }
    data.update(overrides)
    return RoomAllocationRequirement(**data)


def _base_capability(**overrides):
    data = {
        "tenant_id": 1,
        "room_id": "LAB-101",
        "room_code": "LAB-101",
        "room_name": "Computer Lab 101",
        "room_type": "computer_lab",
        "capacity": 40,
        "computers_count": 25,
        "equipment_available": ["projector", "whiteboard", "audio"],
        "supported_lesson_types": ["lecture", "lab", "exam"],
        "accessibility_features": ["wheelchair_access"],
        "campus": "North",
        "building": "A",
        "floor": "1",
        "availability_status": "available",
        "booking_status": "released",
        "maintenance_status": "ok",
        "restrictions": ["exam_enabled", "quiet_zone"],
        "is_active": True,
        "evidence": {"source": "room_registry"},
        "source_entity_type": "campus_room",
        "source_entity_id": "room-101",
    }
    data.update(overrides)
    return RoomCapability(**data)


class TestRoomCapabilitySchema:
    def test_room_capability_requires_tenant_and_room_id(self):
        with pytest.raises(Exception):
            RoomCapability(tenant_id=1, source_entity_id="x")

        with pytest.raises(Exception):
            RoomCapability(room_id="R1", source_entity_id="x")

    def test_negative_capacity_rejected(self):
        with pytest.raises(Exception):
            _base_capability(capacity=-1)

    def test_negative_computers_count_rejected(self):
        with pytest.raises(Exception):
            _base_capability(computers_count=-1)

    def test_missing_optional_equipment_does_not_crash(self):
        capability = _base_capability(equipment_available=[])
        assert capability.equipment_available == []

    def test_standard_types_constants_defined(self):
        assert "computer_lab" in STANDARD_ROOM_TYPES
        assert "lab" in STANDARD_LESSON_TYPES


class TestAvailabilityEvidence:
    def test_inactive_room_represented_unavailable(self):
        capability = _base_capability(is_active=False)
        availability = to_room_allocation_availability(capability, authoritative_tenant_id=1)
        assert availability.is_available is False

    def test_maintenance_room_represented_unavailable(self):
        capability = _base_capability(maintenance_status="maintenance")
        availability = to_room_allocation_availability(capability, authoritative_tenant_id=1)
        assert availability.is_available is False


class TestCapabilityMatching:
    def test_capacity_sufficient_true(self):
        capability = _base_capability(capacity=50)
        requirement = _base_requirement(students_count=30)
        evidence = assess_room_capability_against_requirement(capability, requirement, authoritative_tenant_id=1)
        assert evidence.capacity_ok is True

    def test_capacity_mismatch_false_with_reason(self):
        capability = _base_capability(capacity=20)
        requirement = _base_requirement(students_count=30)
        evidence = assess_room_capability_against_requirement(capability, requirement, authoritative_tenant_id=1)
        assert evidence.capacity_ok is False
        assert "capacity_shortage" in evidence.mismatch_reasons

    def test_computers_sufficient_true(self):
        capability = _base_capability(computers_count=25)
        requirement = _base_requirement(required_computers=20)
        evidence = assess_room_capability_against_requirement(capability, requirement, authoritative_tenant_id=1)
        assert evidence.computers_ok is True

    def test_computer_shortage_false_with_reason(self):
        capability = _base_capability(computers_count=10)
        requirement = _base_requirement(required_computers=20)
        evidence = assess_room_capability_against_requirement(capability, requirement, authoritative_tenant_id=1)
        assert evidence.computers_ok is False
        assert "computers_shortage" in evidence.mismatch_reasons

    def test_equipment_match_lists_missing_equipment(self):
        capability = _base_capability(equipment_available=["projector"])
        requirement = _base_requirement(equipment_required=["projector", "whiteboard"])
        evidence = assess_room_capability_against_requirement(capability, requirement, authoritative_tenant_id=1)
        assert evidence.equipment_ok is False
        assert evidence.missing_equipment == ["whiteboard"]

    def test_room_type_match(self):
        capability = _base_capability(room_type="computer_lab")
        requirement = _base_requirement(required_room_type="computer_lab")
        evidence = assess_room_capability_against_requirement(capability, requirement, authoritative_tenant_id=1)
        assert evidence.room_type_ok is True

    def test_room_type_mismatch(self):
        capability = _base_capability(room_type="lecture_hall")
        requirement = _base_requirement(required_room_type="computer_lab")
        evidence = assess_room_capability_against_requirement(capability, requirement, authoritative_tenant_id=1)
        assert evidence.room_type_ok is False
        assert "room_type_mismatch" in evidence.mismatch_reasons

    def test_restrictions_mismatch(self):
        capability = _base_capability(restrictions=["quiet_zone"])
        requirement = _base_requirement(restrictions_required=["exam_enabled"])
        evidence = assess_room_capability_against_requirement(capability, requirement, authoritative_tenant_id=1)
        assert evidence.restrictions_ok is False
        assert "restrictions_mismatch" in evidence.mismatch_reasons

    def test_conversion_to_room_allocation_availability(self):
        capability = _base_capability(campus="Main", building="B", floor="2")
        availability = to_room_allocation_availability(capability, authoritative_tenant_id=1)
        assert availability.room_id == "LAB-101"
        assert availability.room_capacity == 40
        assert availability.location == "Main, B, 2"

    def test_tenant_spoof_cannot_override_authoritative_tenant(self):
        capability = _base_capability(tenant_id=2)
        requirement = _base_requirement()
        with pytest.raises(ValueError, match="authoritative tenant_id mismatch"):
            assess_room_capability_against_requirement(capability, requirement, authoritative_tenant_id=1)

    def test_no_schedule_mutation_occurs(self):
        capability = _base_capability()
        requirement = _base_requirement()
        before = (capability.model_dump(), requirement.model_dump())
        _ = assess_room_capability_against_requirement(capability, requirement, authoritative_tenant_id=1)
        after = (capability.model_dump(), requirement.model_dump())
        assert before == after

    def test_no_room_booking_mutation_occurs(self):
        capability = _base_capability(booking_status="approved")
        requirement = _base_requirement()
        _ = assess_room_capability_against_requirement(capability, requirement, authoritative_tenant_id=1)
        assert capability.booking_status == "approved"

    def test_no_recommendation_ranking_produced(self):
        capability = _base_capability()
        requirement = _base_requirement()
        evidence = build_room_capability_evidence(capability, requirement, authoritative_tenant_id=1)
        assert "ranking" not in evidence
        assert "score_rank" not in evidence

    def test_compatibility_evidence_can_trigger_allocation_required(self):
        capability = _base_capability(capacity=10, computers_count=5, equipment_available=[])
        requirement = _base_requirement(students_count=30, required_computers=20, equipment_required=["projector"])
        evidence = assess_room_capability_against_requirement(capability, requirement, authoritative_tenant_id=1)
        assert evidence.room_allocation_required is True


class TestA0201RegressionCompatibility:
    def test_a020_1_readiness_import_still_works(self):
        requirement = _base_requirement()
        assert requirement.required_room_type == "computer_lab"
