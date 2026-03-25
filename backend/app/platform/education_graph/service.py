from __future__ import annotations

from typing import Any

from app.platform.education_graph.repository import SHARED_EDUCATION_GRAPH_REPOSITORY, EducationGraphRepository
from app.platform.events.schemas import OutboxEventRead

_SHARED_EDU_GRAPH_REPOSITORY = SHARED_EDUCATION_GRAPH_REPOSITORY


class EducationGraphService:
    def __init__(self, repository: EducationGraphRepository | None = None) -> None:
        self._repository = repository or _SHARED_EDU_GRAPH_REPOSITORY

    def clear_state(self) -> None:
        self._repository.clear_state()

    # ------------------------------------------------------------------
    # CRUD / mappings
    # ------------------------------------------------------------------

    def create_skill(
        self,
        *,
        tenant_id: int,
        skill_key: str,
        name: str,
        description: str,
        category: str,
        level: str | None,
        uow: Any,
    ) -> dict[str, Any]:
        return uow.education_graph_repository.create_skill(
            tenant_id=tenant_id,
            skill_key=skill_key,
            name=name,
            description=description,
            category=category,
            level=level,
            conn=uow.conn,
        )

    def list_skills(self, *, tenant_id: int, uow: Any) -> list[dict[str, Any]]:
        return uow.education_graph_repository.list_skills(tenant_id=tenant_id, conn=uow.conn)

    def create_competency(
        self,
        *,
        tenant_id: int,
        competency_key: str,
        name: str,
        description: str,
        uow: Any,
    ) -> dict[str, Any]:
        return uow.education_graph_repository.create_competency(
            tenant_id=tenant_id,
            competency_key=competency_key,
            name=name,
            description=description,
            conn=uow.conn,
        )

    def list_competencies(self, *, tenant_id: int, uow: Any) -> list[dict[str, Any]]:
        return uow.education_graph_repository.list_competencies(tenant_id=tenant_id, conn=uow.conn)

    def map_course_skill(
        self,
        *,
        tenant_id: int,
        course_id: str,
        skill_id: int,
        weight: float,
        uow: Any,
    ) -> dict[str, Any]:
        return uow.education_graph_repository.create_course_skill(
            tenant_id=tenant_id,
            course_id=course_id,
            skill_id=skill_id,
            weight=weight,
            conn=uow.conn,
        )

    def list_course_skills(
        self,
        *,
        tenant_id: int,
        course_id: str | None,
        uow: Any,
    ) -> list[dict[str, Any]]:
        return uow.education_graph_repository.list_course_skills(
            tenant_id=tenant_id,
            course_id=course_id,
            conn=uow.conn,
        )

    def list_student_skills(
        self,
        *,
        tenant_id: int,
        student_id: str | None,
        uow: Any,
    ) -> list[dict[str, Any]]:
        return uow.education_graph_repository.list_student_skills(
            tenant_id=tenant_id,
            student_id=student_id,
            conn=uow.conn,
        )

    def seed_taxonomy(
        self,
        *,
        tenant_id: int,
        skills: list[dict[str, Any]],
        uow: Any,
    ) -> list[dict[str, Any]]:
        seeded: list[dict[str, Any]] = []
        for item in skills:
            seeded.append(
                self.create_skill(
                    tenant_id=tenant_id,
                    skill_key=str(item.get("skill_key", "")),
                    name=str(item.get("name", "")),
                    description=str(item.get("description", "")),
                    category=str(item.get("category", "General")),
                    level=(str(item.get("level")) if item.get("level") is not None else None),
                    uow=uow,
                )
            )
        return seeded

    # ------------------------------------------------------------------
    # Event-driven inference
    # ------------------------------------------------------------------

    def infer_from_event(self, event: OutboxEventRead, *, uow: Any) -> dict[str, Any]:
        if event.event_type not in {"grade.submitted", "course.completed"}:
            return {
                "status": "ignored",
                "event_type": event.event_type,
                "updated_edges": 0,
            }

        payload = dict(event.payload_json or {})
        tenant_id = int(event.tenant_id)

        student_id = self._resolve_student_id(payload)
        if not student_id:
            return {
                "status": "skipped_missing_student",
                "event_type": event.event_type,
                "updated_edges": 0,
            }

        course_id = self._resolve_course_id(payload, tenant_id=tenant_id, uow=uow)
        if not course_id:
            return {
                "status": "skipped_missing_course",
                "event_type": event.event_type,
                "updated_edges": 0,
            }

        if event.event_type == "grade.submitted":
            grade = self._extract_grade(payload)
            if grade is None:
                return {
                    "status": "skipped_missing_grade",
                    "event_type": event.event_type,
                    "updated_edges": 0,
                }
            if grade < 60.0:
                return {
                    "status": "skipped_non_passing_grade",
                    "event_type": event.event_type,
                    "updated_edges": 0,
                }
            source = "exam"
        else:
            source = "course"

        mappings = self.list_course_skills(tenant_id=tenant_id, course_id=course_id, uow=uow)
        if not mappings:
            return {
                "status": "skipped_no_course_skill_mappings",
                "event_type": event.event_type,
                "updated_edges": 0,
            }

        updates = 0
        for mapping in mappings:
            delta = float(mapping.get("weight", 1.0) or 0.0)
            if delta <= 0:
                continue
            uow.education_graph_repository.upsert_student_skill(
                tenant_id=tenant_id,
                student_id=student_id,
                skill_id=int(mapping["skill_id"]),
                proficiency_delta=delta,
                source=source,
                conn=uow.conn,
            )
            updates += 1

        return {
            "status": "inferred",
            "event_type": event.event_type,
            "updated_edges": updates,
            "student_id": student_id,
            "course_id": course_id,
        }

    @staticmethod
    def _resolve_student_id(payload: dict[str, Any]) -> str | None:
        for key in ("student_id", "student_profile_id"):
            raw = payload.get(key)
            if raw is not None and str(raw).strip():
                return str(raw).strip()
        return None

    @staticmethod
    def _extract_grade(payload: dict[str, Any]) -> float | None:
        for key in ("grade_value", "grade_points"):
            raw = payload.get(key)
            if raw is None:
                continue
            try:
                return float(raw)
            except (TypeError, ValueError):
                continue
        return None

    @staticmethod
    def _resolve_course_id(payload: dict[str, Any], *, tenant_id: int, uow: Any) -> str | None:
        course_id = payload.get("course_id")
        if course_id is not None and str(course_id).strip():
            return str(course_id).strip()

        enrollment_id = payload.get("enrollment_id")
        if enrollment_id is None:
            return None

        enrollment = uow.context_repository.get_entity(
            tenant_id=tenant_id,
            entity_type="enrollment",
            entity_id=str(enrollment_id),
            conn=uow.conn,
        )
        if enrollment is None:
            return None
        data = dict(enrollment.get("data_json") or {})
        raw = data.get("course_id")
        if raw is None or not str(raw).strip():
            return None
        return str(raw).strip()


education_graph_service = EducationGraphService()


def clear_state() -> None:
    education_graph_service.clear_state()


def create_skill(
    *,
    tenant_id: int,
    skill_key: str,
    name: str,
    description: str,
    category: str,
    level: str | None,
    uow: Any,
) -> dict[str, Any]:
    return education_graph_service.create_skill(
        tenant_id=tenant_id,
        skill_key=skill_key,
        name=name,
        description=description,
        category=category,
        level=level,
        uow=uow,
    )


def list_skills(*, tenant_id: int, uow: Any) -> list[dict[str, Any]]:
    return education_graph_service.list_skills(tenant_id=tenant_id, uow=uow)


def map_course_skill(
    *,
    tenant_id: int,
    course_id: str,
    skill_id: int,
    weight: float,
    uow: Any,
) -> dict[str, Any]:
    return education_graph_service.map_course_skill(
        tenant_id=tenant_id,
        course_id=course_id,
        skill_id=skill_id,
        weight=weight,
        uow=uow,
    )


def list_course_skills(*, tenant_id: int, course_id: str | None, uow: Any) -> list[dict[str, Any]]:
    return education_graph_service.list_course_skills(tenant_id=tenant_id, course_id=course_id, uow=uow)


def list_student_skills(*, tenant_id: int, student_id: str | None, uow: Any) -> list[dict[str, Any]]:
    return education_graph_service.list_student_skills(tenant_id=tenant_id, student_id=student_id, uow=uow)


def infer_from_event(event: OutboxEventRead, *, uow: Any) -> dict[str, Any]:
    return education_graph_service.infer_from_event(event, uow=uow)
