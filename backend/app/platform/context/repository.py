from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from typing import Any

from app.platform.repository.db import db_available, transaction

try:
    import psycopg  # type: ignore[import]
except ImportError:  # pragma: no cover
    psycopg = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ContextRepository:
    """
    Dual-mode repository for context entities and relations.

    When DATABASE_URL is set and psycopg is available, all operations use
    raw SQL against PostgreSQL.  Otherwise an in-memory dict store is used
    (suitable for unit tests that run without a database).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entity_counter = 0
        self._relation_counter = 0
        # key: (tenant_id, entity_type, entity_id) → record dict
        self._entities: dict[tuple[int, str, str], dict[str, Any]] = {}
        # key: (tenant_id, src_type, src_id, rel_type, tgt_type, tgt_id) → record dict
        self._relations: dict[tuple[int, str, str, str, str, str], dict[str, Any]] = {}

    # ------------------------------------------------------------------ #
    #  Row → dict helpers                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _entity_row_to_api(row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "id": int(row[0]),
            "tenant_id": int(row[1]),
            "entity_type": str(row[2]),
            "entity_id": str(row[3]),
            "data_json": dict(row[4] or {}),
            "created_at": row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5]),
            "updated_at": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
        }

    @staticmethod
    def _relation_row_to_api(row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "id": int(row[0]),
            "tenant_id": int(row[1]),
            "source_entity_type": str(row[2]),
            "source_entity_id": str(row[3]),
            "relation_type": str(row[4]),
            "target_entity_type": str(row[5]),
            "target_entity_id": str(row[6]),
            "metadata_json": dict(row[7] or {}),
            "created_at": row[8].isoformat() if hasattr(row[8], "isoformat") else str(row[8]),
        }

    def clear_state(self) -> None:
        """Reset in-memory state. For tests only."""
        with self._lock:
            self._entity_counter = 0
            self._relation_counter = 0
            self._entities.clear()
            self._relations.clear()

    # ------------------------------------------------------------------ #
    #  Entities                                                            #
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
        tid = int(tenant_id)
        etype = entity_type.strip().lower()
        eid = str(entity_id).strip()
        data = dict(data_json or {})

        if conn is None:
            with transaction() as tx:
                return self.upsert_entity(
                    tenant_id=tid,
                    entity_type=etype,
                    entity_id=eid,
                    data_json=data,
                    conn=tx,
                )

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_context_entities
                        (tenant_id, entity_type, entity_id, data_json, created_at, updated_at)
                    VALUES (%s, %s, %s, %s::jsonb, NOW(), NOW())
                    ON CONFLICT (tenant_id, entity_type, entity_id)
                    DO UPDATE SET data_json = EXCLUDED.data_json, updated_at = NOW()
                    RETURNING id, tenant_id, entity_type, entity_id,
                              data_json, created_at, updated_at
                    """,
                    (tid, etype, eid, json.dumps(data)),
                )
                row = cur.fetchone()
            return self._entity_row_to_api(row)

        # in-memory fallback
        now = _now_iso()
        key = (tid, etype, eid)
        with self._lock:
            existing = self._entities.get(key)
            if existing is not None:
                existing["data_json"] = data
                existing["updated_at"] = now
                return dict(existing)
            self._entity_counter += 1
            record: dict[str, Any] = {
                "id": self._entity_counter,
                "tenant_id": tid,
                "entity_type": etype,
                "entity_id": eid,
                "data_json": data,
                "created_at": now,
                "updated_at": now,
            }
            self._entities[key] = record
            return dict(record)

    def get_entity(
        self,
        *,
        tenant_id: int,
        entity_type: str,
        entity_id: str,
        conn: object | None = None,
    ) -> dict[str, Any] | None:
        tid = int(tenant_id)
        etype = entity_type.strip().lower()
        eid = str(entity_id).strip()

        if conn is None:
            with transaction() as tx:
                return self.get_entity(
                    tenant_id=tid, entity_type=etype, entity_id=eid, conn=tx
                )

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, entity_type, entity_id,
                           data_json, created_at, updated_at
                    FROM app_platform_context_entities
                    WHERE tenant_id = %s AND entity_type = %s AND entity_id = %s
                    """,
                    (tid, etype, eid),
                )
                row = cur.fetchone()
            return self._entity_row_to_api(row) if row is not None else None

        key = (tid, etype, eid)
        with self._lock:
            record = self._entities.get(key)
        return dict(record) if record is not None else None

    # ------------------------------------------------------------------ #
    #  Relations                                                           #
    # ------------------------------------------------------------------ #

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
        tid = int(tenant_id)
        src_type = source_entity_type.strip().lower()
        src_id = str(source_entity_id).strip()
        rel_type = relation_type.strip().lower()
        tgt_type = target_entity_type.strip().lower()
        tgt_id = str(target_entity_id).strip()
        meta = dict(metadata_json or {})

        if conn is None:
            with transaction() as tx:
                return self.upsert_relation(
                    tenant_id=tid,
                    source_entity_type=src_type,
                    source_entity_id=src_id,
                    relation_type=rel_type,
                    target_entity_type=tgt_type,
                    target_entity_id=tgt_id,
                    metadata_json=meta,
                    conn=tx,
                )

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_context_relations (
                        tenant_id,
                        source_entity_type, source_entity_id,
                        relation_type,
                        target_entity_type, target_entity_id,
                        metadata_json, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, NOW())
                    ON CONFLICT (tenant_id,
                                 source_entity_type, source_entity_id,
                                 relation_type,
                                 target_entity_type, target_entity_id)
                    DO UPDATE SET metadata_json = EXCLUDED.metadata_json
                    RETURNING id, tenant_id,
                              source_entity_type, source_entity_id,
                              relation_type,
                              target_entity_type, target_entity_id,
                              metadata_json, created_at
                    """,
                    (tid, src_type, src_id, rel_type, tgt_type, tgt_id, json.dumps(meta)),
                )
                row = cur.fetchone()
            return self._relation_row_to_api(row)

        # in-memory fallback
        now = _now_iso()
        key = (tid, src_type, src_id, rel_type, tgt_type, tgt_id)
        with self._lock:
            existing = self._relations.get(key)
            if existing is not None:
                existing["metadata_json"] = meta
                return dict(existing)
            self._relation_counter += 1
            record: dict[str, Any] = {
                "id": self._relation_counter,
                "tenant_id": tid,
                "source_entity_type": src_type,
                "source_entity_id": src_id,
                "relation_type": rel_type,
                "target_entity_type": tgt_type,
                "target_entity_id": tgt_id,
                "metadata_json": meta,
                "created_at": now,
            }
            self._relations[key] = record
            return dict(record)

    def get_relations_by_source(
        self,
        *,
        tenant_id: int,
        source_entity_type: str,
        source_entity_id: str,
        relation_type: str | None = None,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        tid = int(tenant_id)
        src_type = source_entity_type.strip().lower()
        src_id = str(source_entity_id).strip()
        rel_type = relation_type.strip().lower() if relation_type else None

        if conn is None:
            with transaction() as tx:
                return self.get_relations_by_source(
                    tenant_id=tid,
                    source_entity_type=src_type,
                    source_entity_id=src_id,
                    relation_type=rel_type,
                    conn=tx,
                )

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                if rel_type:
                    cur.execute(
                        """
                        SELECT id, tenant_id,
                               source_entity_type, source_entity_id,
                               relation_type,
                               target_entity_type, target_entity_id,
                               metadata_json, created_at
                        FROM app_platform_context_relations
                        WHERE tenant_id = %s
                          AND source_entity_type = %s
                          AND source_entity_id = %s
                          AND relation_type = %s
                        ORDER BY id
                        """,
                        (tid, src_type, src_id, rel_type),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, tenant_id,
                               source_entity_type, source_entity_id,
                               relation_type,
                               target_entity_type, target_entity_id,
                               metadata_json, created_at
                        FROM app_platform_context_relations
                        WHERE tenant_id = %s
                          AND source_entity_type = %s
                          AND source_entity_id = %s
                        ORDER BY id
                        """,
                        (tid, src_type, src_id),
                    )
                rows = cur.fetchall()
            return [self._relation_row_to_api(r) for r in rows]

        with self._lock:
            result = [
                dict(v)
                for k, v in self._relations.items()
                if k[0] == tid
                and k[1] == src_type
                and k[2] == src_id
                and (rel_type is None or k[3] == rel_type)
            ]
        return result

    def get_relations_by_target(
        self,
        *,
        tenant_id: int,
        target_entity_type: str,
        target_entity_id: str,
        relation_type: str | None = None,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        tid = int(tenant_id)
        tgt_type = target_entity_type.strip().lower()
        tgt_id = str(target_entity_id).strip()
        rel_type = relation_type.strip().lower() if relation_type else None

        if conn is None:
            with transaction() as tx:
                return self.get_relations_by_target(
                    tenant_id=tid,
                    target_entity_type=tgt_type,
                    target_entity_id=tgt_id,
                    relation_type=rel_type,
                    conn=tx,
                )

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                if rel_type:
                    cur.execute(
                        """
                        SELECT id, tenant_id,
                               source_entity_type, source_entity_id,
                               relation_type,
                               target_entity_type, target_entity_id,
                               metadata_json, created_at
                        FROM app_platform_context_relations
                        WHERE tenant_id = %s
                          AND target_entity_type = %s
                          AND target_entity_id = %s
                          AND relation_type = %s
                        ORDER BY id
                        """,
                        (tid, tgt_type, tgt_id, rel_type),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, tenant_id,
                               source_entity_type, source_entity_id,
                               relation_type,
                               target_entity_type, target_entity_id,
                               metadata_json, created_at
                        FROM app_platform_context_relations
                        WHERE tenant_id = %s
                          AND target_entity_type = %s
                          AND target_entity_id = %s
                        ORDER BY id
                        """,
                        (tid, tgt_type, tgt_id),
                    )
                rows = cur.fetchall()
            return [self._relation_row_to_api(r) for r in rows]

        with self._lock:
            result = [
                dict(v)
                for k, v in self._relations.items()
                if k[0] == tid
                and k[4] == tgt_type
                and k[5] == tgt_id
                and (rel_type is None or k[3] == rel_type)
            ]
        return result

    # ------------------------------------------------------------------ #
    #  High-level context queries                                          #
    # ------------------------------------------------------------------ #

    def get_student_context(
        self,
        *,
        tenant_id: int,
        student_id: str,
        conn: object | None = None,
    ) -> dict[str, Any] | None:
        return self.get_entity(
            tenant_id=tenant_id,
            entity_type="student",
            entity_id=str(student_id),
            conn=conn,
        )

    def get_program_students(
        self,
        *,
        tenant_id: int,
        program_id: str,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        rels = self.get_relations_by_target(
            tenant_id=tenant_id,
            target_entity_type="program",
            target_entity_id=str(program_id),
            relation_type="enrolled_in",
            conn=conn,
        )
        students = []
        for rel in rels:
            entity = self.get_entity(
                tenant_id=tenant_id,
                entity_type="student",
                entity_id=rel["source_entity_id"],
                conn=conn,
            )
            if entity is not None:
                students.append(entity)
        return students

    def get_student_courses(
        self,
        *,
        tenant_id: int,
        student_id: str,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        enrollment_rels = self.get_relations_by_source(
            tenant_id=tenant_id,
            source_entity_type="student",
            source_entity_id=str(student_id),
            relation_type="has_enrollment",
            conn=conn,
        )
        courses: list[dict[str, Any]] = []
        for enroll_rel in enrollment_rels:
            course_rels = self.get_relations_by_source(
                tenant_id=tenant_id,
                source_entity_type=enroll_rel["target_entity_type"],
                source_entity_id=enroll_rel["target_entity_id"],
                relation_type="for_course",
                conn=conn,
            )
            for course_rel in course_rels:
                entity = self.get_entity(
                    tenant_id=tenant_id,
                    entity_type=course_rel["target_entity_type"],
                    entity_id=course_rel["target_entity_id"],
                    conn=conn,
                )
                if entity is not None:
                    courses.append(entity)
        return courses

    def get_student_grades(
        self,
        *,
        tenant_id: int,
        student_id: str,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        rels = self.get_relations_by_source(
            tenant_id=tenant_id,
            source_entity_type="student",
            source_entity_id=str(student_id),
            relation_type="has_grade",
            conn=conn,
        )
        grades: list[dict[str, Any]] = []
        for rel in rels:
            entity = self.get_entity(
                tenant_id=tenant_id,
                entity_type=rel["target_entity_type"],
                entity_id=rel["target_entity_id"],
                conn=conn,
            )
            if entity is not None:
                grades.append(entity)
        return grades

    def get_student_advisor(
        self,
        *,
        tenant_id: int,
        student_id: str,
        conn: object | None = None,
    ) -> dict[str, Any] | None:
        rels = self.get_relations_by_source(
            tenant_id=tenant_id,
            source_entity_type="student",
            source_entity_id=str(student_id),
            relation_type="advised_by",
            conn=conn,
        )
        if not rels:
            return None
        return self.get_entity(
            tenant_id=tenant_id,
            entity_type=rels[0]["target_entity_type"],
            entity_id=rels[0]["target_entity_id"],
            conn=conn,
        )

    def get_department_students(
        self,
        *,
        tenant_id: int,
        department_id: str,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        rels = self.get_relations_by_source(
            tenant_id=tenant_id,
            source_entity_type="department",
            source_entity_id=str(department_id),
            relation_type="has_student",
            conn=conn,
        )
        students: list[dict[str, Any]] = []
        for rel in rels:
            entity = self.get_entity(
                tenant_id=tenant_id,
                entity_type=rel["target_entity_type"],
                entity_id=rel["target_entity_id"],
                conn=conn,
            )
            if entity is not None:
                students.append(entity)
        return students
