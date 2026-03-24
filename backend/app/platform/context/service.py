from __future__ import annotations

import logging
from typing import Any

from app.platform.context.repository import ContextRepository

logger = logging.getLogger("app.platform.context")

# Module-level shared repository instance (mirrors the uow.py pattern).
_SHARED_CONTEXT_REPOSITORY = ContextRepository()


class ContextService:
    def __init__(self, repository: ContextRepository | None = None) -> None:
        self._repository = repository or _SHARED_CONTEXT_REPOSITORY

    # ------------------------------------------------------------------ #
    #  Write operations (called from event projection handler)             #
    # ------------------------------------------------------------------ #

    def upsert_entity(
        self,
        *,
        tenant_id: int,
        entity_type: str,
        entity_id: str,
        data_json: dict[str, Any] | None = None,
        conn: object | None = None,
    ) -> dict[str, Any]:
        return self._repository.upsert_entity(
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            data_json=data_json,
            conn=conn,
        )

    def upsert_relation(
        self,
        *,
        tenant_id: int,
        source_entity_type: str,
        source_entity_id: str,
        relation_type: str,
        target_entity_type: str,
        target_entity_id: str,
        metadata_json: dict[str, Any] | None = None,
        conn: object | None = None,
    ) -> dict[str, Any]:
        return self._repository.upsert_relation(
            tenant_id=tenant_id,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            relation_type=relation_type,
            target_entity_type=target_entity_type,
            target_entity_id=target_entity_id,
            metadata_json=metadata_json,
            conn=conn,
        )

    # ------------------------------------------------------------------ #
    #  Profile builder — base object for AI reasoning                      #
    # ------------------------------------------------------------------ #

    def build_student_profile(
        self,
        *,
        student_id: str,
        tenant_id: int,
        conn: object | None = None,
    ) -> dict[str, Any]:
        sid = str(student_id).strip()
        tid = int(tenant_id)

        student = self._repository.get_student_context(
            tenant_id=tid, student_id=sid, conn=conn
        )

        # Relations originating from student
        program_rels = self._repository.get_relations_by_source(
            tenant_id=tid,
            source_entity_type="student",
            source_entity_id=sid,
            relation_type="enrolled_in",
            conn=conn,
        )
        enrollment_rels = self._repository.get_relations_by_source(
            tenant_id=tid,
            source_entity_type="student",
            source_entity_id=sid,
            relation_type="has_enrollment",
            conn=conn,
        )
        grade_rels = self._repository.get_relations_by_source(
            tenant_id=tid,
            source_entity_type="student",
            source_entity_id=sid,
            relation_type="has_grade",
            conn=conn,
        )
        advisor_rels = self._repository.get_relations_by_source(
            tenant_id=tid,
            source_entity_type="student",
            source_entity_id=sid,
            relation_type="advised_by",
            conn=conn,
        )
        # Relations targeting student (department → student)
        dept_rels = self._repository.get_relations_by_target(
            tenant_id=tid,
            target_entity_type="student",
            target_entity_id=sid,
            relation_type="has_student",
            conn=conn,
        )

        # Resolve entities
        program: dict[str, Any] | None = None
        if program_rels:
            program = self._repository.get_entity(
                tenant_id=tid,
                entity_type=program_rels[0]["target_entity_type"],
                entity_id=program_rels[0]["target_entity_id"],
                conn=conn,
            )

        advisor: dict[str, Any] | None = None
        if advisor_rels:
            advisor = self._repository.get_entity(
                tenant_id=tid,
                entity_type=advisor_rels[0]["target_entity_type"],
                entity_id=advisor_rels[0]["target_entity_id"],
                conn=conn,
            )

        enrollments: list[dict[str, Any]] = []
        for rel in enrollment_rels:
            entity = self._repository.get_entity(
                tenant_id=tid,
                entity_type=rel["target_entity_type"],
                entity_id=rel["target_entity_id"],
                conn=conn,
            )
            if entity is not None:
                enrollments.append(entity)

        grades: list[dict[str, Any]] = []
        for rel in grade_rels:
            entity = self._repository.get_entity(
                tenant_id=tid,
                entity_type=rel["target_entity_type"],
                entity_id=rel["target_entity_id"],
                conn=conn,
            )
            if entity is not None:
                grades.append(entity)

        department: dict[str, Any] | None = None
        if dept_rels:
            department = self._repository.get_entity(
                tenant_id=tid,
                entity_type=dept_rels[0]["source_entity_type"],
                entity_id=dept_rels[0]["source_entity_id"],
                conn=conn,
            )

        return {
            "student": student,
            "program": program,
            "advisor": advisor,
            "enrollments": enrollments,
            "grades": grades,
            "department": department,
            "automation_flags": {},
        }

    # ------------------------------------------------------------------ #
    #  Scheduler rebuild stub                                              #
    # ------------------------------------------------------------------ #

    def rebuild_context_for_tenant(self, *, tenant_id: int) -> dict[str, int]:
        """
        No-op rebuild placeholder.
        Context is maintained incrementally via event projection.
        A full rebuild would replay all domain events from the outbox.
        """
        return {"tenant_id": int(tenant_id), "rebuilt": 0}

    def clear_context_state(self) -> None:
        """Reset in-memory state. For tests only."""
        self._repository.clear_state()


context_service = ContextService()


def clear_context_state() -> None:
    """Reset in-memory state. For tests only."""
    context_service.clear_context_state()


# ------------------------------------------------------------------ #
#  Module-level convenience functions (mirrors automation service API) #
# ------------------------------------------------------------------ #

def upsert_entity(
    *,
    tenant_id: int,
    entity_type: str,
    entity_id: str,
    data_json: dict[str, Any] | None = None,
    conn: object | None = None,
) -> dict[str, Any]:
    return context_service.upsert_entity(
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        data_json=data_json,
        conn=conn,
    )


def upsert_relation(
    *,
    tenant_id: int,
    source_entity_type: str,
    source_entity_id: str,
    relation_type: str,
    target_entity_type: str,
    target_entity_id: str,
    metadata_json: dict[str, Any] | None = None,
    conn: object | None = None,
) -> dict[str, Any]:
    return context_service.upsert_relation(
        tenant_id=tenant_id,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        relation_type=relation_type,
        target_entity_type=target_entity_type,
        target_entity_id=target_entity_id,
        metadata_json=metadata_json,
        conn=conn,
    )


def build_student_profile(
    *,
    student_id: str,
    tenant_id: int,
    conn: object | None = None,
) -> dict[str, Any]:
    return context_service.build_student_profile(
        student_id=student_id,
        tenant_id=tenant_id,
        conn=conn,
    )
