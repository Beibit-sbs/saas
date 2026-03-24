from __future__ import annotations

from typing import Any

from app.platform.context import service as context_service
from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork


class ContextProjectionHandler:
    """
    Projects domain events into the Semantic Context Layer.

    Handles: student.created, enrollment.created, grade.submitted,
             advisor.assigned, course.created
    """

    name = "context_projection"

    def handle(self, event: OutboxEventRead, *, uow: UnitOfWork) -> dict[str, Any]:
        payload = dict(event.payload_json or {})
        tenant_id = event.tenant_id
        conn = uow.conn

        dispatch = {
            "student.created": self._on_student_created,
            "enrollment.created": self._on_enrollment_created,
            "grade.submitted": self._on_grade_submitted,
            "advisor.assigned": self._on_advisor_assigned,
            "course.created": self._on_course_created,
        }

        handler_fn = dispatch.get(event.event_type)
        if handler_fn is not None:
            handler_fn(tenant_id=tenant_id, payload=payload, conn=conn)

        return {
            "handler": self.name,
            "status": "processed",
            "event_type": event.event_type,
        }

    # ------------------------------------------------------------------ #

    def _on_student_created(
        self, *, tenant_id: int, payload: dict[str, Any], conn: object
    ) -> None:
        student_id = str(payload.get("id") or payload.get("student_id", "")).strip()
        if not student_id:
            return

        context_service.upsert_entity(
            tenant_id=tenant_id,
            entity_type="student",
            entity_id=student_id,
            data_json=payload,
            conn=conn,
        )

        program_id = str(payload.get("program_id", "")).strip()
        if program_id:
            context_service.upsert_relation(
                tenant_id=tenant_id,
                source_entity_type="student",
                source_entity_id=student_id,
                relation_type="enrolled_in",
                target_entity_type="program",
                target_entity_id=program_id,
                conn=conn,
            )

        dept_id = str(payload.get("department_id", "")).strip()
        if dept_id:
            context_service.upsert_relation(
                tenant_id=tenant_id,
                source_entity_type="department",
                source_entity_id=dept_id,
                relation_type="has_student",
                target_entity_type="student",
                target_entity_id=student_id,
                conn=conn,
            )

    def _on_enrollment_created(
        self, *, tenant_id: int, payload: dict[str, Any], conn: object
    ) -> None:
        enrollment_id = str(
            payload.get("id") or payload.get("enrollment_id", "")
        ).strip()
        if not enrollment_id:
            return

        context_service.upsert_entity(
            tenant_id=tenant_id,
            entity_type="enrollment",
            entity_id=enrollment_id,
            data_json=payload,
            conn=conn,
        )

        student_id = str(payload.get("student_id", "")).strip()
        if student_id:
            context_service.upsert_relation(
                tenant_id=tenant_id,
                source_entity_type="student",
                source_entity_id=student_id,
                relation_type="has_enrollment",
                target_entity_type="enrollment",
                target_entity_id=enrollment_id,
                conn=conn,
            )

        course_id = str(payload.get("course_id", "")).strip()
        if course_id:
            context_service.upsert_relation(
                tenant_id=tenant_id,
                source_entity_type="enrollment",
                source_entity_id=enrollment_id,
                relation_type="for_course",
                target_entity_type="course",
                target_entity_id=course_id,
                conn=conn,
            )

    def _on_grade_submitted(
        self, *, tenant_id: int, payload: dict[str, Any], conn: object
    ) -> None:
        grade_id = str(payload.get("id") or payload.get("grade_id", "")).strip()
        if not grade_id:
            return

        context_service.upsert_entity(
            tenant_id=tenant_id,
            entity_type="grade",
            entity_id=grade_id,
            data_json=payload,
            conn=conn,
        )

        student_id = str(payload.get("student_id", "")).strip()
        if student_id:
            context_service.upsert_relation(
                tenant_id=tenant_id,
                source_entity_type="student",
                source_entity_id=student_id,
                relation_type="has_grade",
                target_entity_type="grade",
                target_entity_id=grade_id,
                conn=conn,
            )

    def _on_advisor_assigned(
        self, *, tenant_id: int, payload: dict[str, Any], conn: object
    ) -> None:
        advisor_id = str(payload.get("advisor_id", "")).strip()
        student_id = str(payload.get("student_id", "")).strip()

        if advisor_id:
            context_service.upsert_entity(
                tenant_id=tenant_id,
                entity_type="advisor",
                entity_id=advisor_id,
                data_json=payload,
                conn=conn,
            )

        if student_id and advisor_id:
            context_service.upsert_relation(
                tenant_id=tenant_id,
                source_entity_type="student",
                source_entity_id=student_id,
                relation_type="advised_by",
                target_entity_type="advisor",
                target_entity_id=advisor_id,
                conn=conn,
            )

    def _on_course_created(
        self, *, tenant_id: int, payload: dict[str, Any], conn: object
    ) -> None:
        course_id = str(payload.get("id") or payload.get("course_id", "")).strip()
        if not course_id:
            return

        context_service.upsert_entity(
            tenant_id=tenant_id,
            entity_type="course",
            entity_id=course_id,
            data_json=payload,
            conn=conn,
        )

        dept_id = str(payload.get("department_id", "")).strip()
        if dept_id:
            context_service.upsert_entity(
                tenant_id=tenant_id,
                entity_type="department",
                entity_id=dept_id,
                data_json={"id": dept_id, "department_id": dept_id},
                conn=conn,
            )
