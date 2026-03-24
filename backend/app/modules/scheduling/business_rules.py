from __future__ import annotations

from datetime import time

from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError


class SchedulingRules:
    @staticmethod
    def validate_room_capacity(*, section_capacity: int, room_capacity: int) -> None:
        if int(section_capacity) > int(room_capacity):
            raise DomainValidationError(
                f"section capacity {section_capacity} exceeds classroom capacity {room_capacity}"
            )

    @staticmethod
    def validate_section_capacity(max_capacity: int) -> None:
        if int(max_capacity) < 0:
            raise DomainValidationError("max_capacity must be non-negative")

    @staticmethod
    def validate_time_slot_exists(slot: object | None, *, tenant_id: int, time_slot_id: int) -> None:
        if slot is None:
            raise TenantResourceNotFoundError(
                f"Time slot {time_slot_id} not found or does not belong to tenant {tenant_id}"
            )

    @staticmethod
    def validate_classroom_exists(classroom: object | None, *, tenant_id: int, classroom_id: int) -> None:
        if classroom is None:
            raise TenantResourceNotFoundError(
                f"Classroom {classroom_id} not found or does not belong to tenant {tenant_id}"
            )

    @staticmethod
    def validate_no_room_conflict(conflict: object | None, *, classroom_id: int, day_of_week: str) -> None:
        if conflict is not None:
            raise DomainValidationError(
                f"room conflict detected for classroom_id={classroom_id} on {day_of_week}"
            )

    @staticmethod
    def validate_no_instructor_conflict(conflicts: list[object], *, instructor_id: str, day_of_week: str) -> None:
        if conflicts:
            raise DomainValidationError(
                f"instructor conflict detected for instructor_id={instructor_id} on {day_of_week}"
            )

    @staticmethod
    def validate_time_range(*, start_time: time, end_time: time) -> None:
        if end_time <= start_time:
            raise DomainValidationError("time slot range is invalid: end_time must be greater than start_time")
