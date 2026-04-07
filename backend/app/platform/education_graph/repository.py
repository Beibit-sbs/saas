from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.platform.repository.db import _MEMORY_TX, db_available, transaction

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class EducationGraphRepository:
    def __init__(self) -> None:
        self._lock = Lock()

        self._skill_counter = 0
        self._competency_counter = 0
        self._course_skill_counter = 0
        self._student_skill_counter = 0

        self._skills: dict[int, dict[str, Any]] = {}
        self._skills_by_key: dict[tuple[int, str], int] = {}

        self._competencies: dict[int, dict[str, Any]] = {}
        self._competencies_by_key: dict[tuple[int, str], int] = {}

        self._course_skills: dict[int, dict[str, Any]] = {}
        self._course_skill_by_unique: dict[tuple[int, str, int], int] = {}

        self._student_skills: dict[int, dict[str, Any]] = {}
        self._student_skill_by_unique: dict[tuple[int, str, int], int] = {}

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _normalize_conn(self, conn: object | None) -> object | None:
        if conn is _MEMORY_TX:
            return None
        return conn

    def _needs_db_transaction(self, conn: object | None) -> bool:
        return conn is None and db_available() and psycopg is not None

    def clear_state(self) -> None:
        with self._lock:
            self._skill_counter = 0
            self._competency_counter = 0
            self._course_skill_counter = 0
            self._student_skill_counter = 0
            self._skills.clear()
            self._skills_by_key.clear()
            self._competencies.clear()
            self._competencies_by_key.clear()
            self._course_skills.clear()
            self._course_skill_by_unique.clear()
            self._student_skills.clear()
            self._student_skill_by_unique.clear()

    # ------------------------------------------------------------------
    # Skills
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
        conn: object | None = None,
    ) -> dict[str, Any]:
        tid = int(tenant_id)
        key = str(skill_key).strip().lower()
        payload = (
            tid,
            key,
            str(name).strip(),
            str(description or "").strip(),
            str(category).strip(),
            str(level).strip() if level is not None else None,
        )

        conn = self._normalize_conn(conn)

        if self._needs_db_transaction(conn):
            with transaction() as tx:
                return self.create_skill(
                    tenant_id=payload[0],
                    skill_key=payload[1],
                    name=payload[2],
                    description=payload[3],
                    category=payload[4],
                    level=payload[5],
                    conn=tx,
                )

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_graph_skills
                        (tenant_id, skill_key, name, description, category, level)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tenant_id, skill_key) DO UPDATE
                      SET name = EXCLUDED.name,
                          description = EXCLUDED.description,
                          category = EXCLUDED.category,
                          level = EXCLUDED.level,
                          updated_at = NOW()
                    RETURNING id, tenant_id, skill_key, name, description, category, level, created_at, updated_at
                    """,
                    payload,
                )
                row = cur.fetchone()
            return {
                "id": int(row[0]),
                "tenant_id": int(row[1]),
                "skill_key": str(row[2]),
                "name": str(row[3]),
                "description": str(row[4]),
                "category": str(row[5]),
                "level": str(row[6]) if row[6] is not None else None,
                "created_at": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
                "updated_at": row[8].isoformat() if hasattr(row[8], "isoformat") else str(row[8]),
            }

        with self._lock:
            uniq = (tid, key)
            existing_id = self._skills_by_key.get(uniq)
            now = self._now()
            if existing_id is not None:
                row = self._skills[existing_id]
                row["name"] = payload[2]
                row["description"] = payload[3]
                row["category"] = payload[4]
                row["level"] = payload[5]
                row["updated_at"] = now
                return dict(row)

            self._skill_counter += 1
            row = {
                "id": self._skill_counter,
                "tenant_id": tid,
                "skill_key": key,
                "name": payload[2],
                "description": payload[3],
                "category": payload[4],
                "level": payload[5],
                "created_at": now,
                "updated_at": now,
            }
            self._skills[self._skill_counter] = row
            self._skills_by_key[uniq] = self._skill_counter
            return dict(row)

    def list_skills(self, *, tenant_id: int, conn: object | None = None) -> list[dict[str, Any]]:
        tid = int(tenant_id)
        conn = self._normalize_conn(conn)
        if self._needs_db_transaction(conn):
            with transaction() as tx:
                return self.list_skills(tenant_id=tid, conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, skill_key, name, description, category, level, created_at, updated_at
                    FROM app_platform_graph_skills
                    WHERE tenant_id = %s
                    ORDER BY name ASC, id ASC
                    """,
                    (tid,),
                )
                rows = cur.fetchall()
            return [
                {
                    "id": int(r[0]),
                    "tenant_id": int(r[1]),
                    "skill_key": str(r[2]),
                    "name": str(r[3]),
                    "description": str(r[4]),
                    "category": str(r[5]),
                    "level": str(r[6]) if r[6] is not None else None,
                    "created_at": r[7].isoformat() if hasattr(r[7], "isoformat") else str(r[7]),
                    "updated_at": r[8].isoformat() if hasattr(r[8], "isoformat") else str(r[8]),
                }
                for r in rows
            ]

        with self._lock:
            rows = [dict(v) for v in self._skills.values() if int(v["tenant_id"]) == tid]
        rows.sort(key=lambda r: (str(r["name"]).lower(), int(r["id"])))
        return rows

    # ------------------------------------------------------------------
    # Competencies
    # ------------------------------------------------------------------

    def create_competency(
        self,
        *,
        tenant_id: int,
        competency_key: str,
        name: str,
        description: str,
        conn: object | None = None,
    ) -> dict[str, Any]:
        tid = int(tenant_id)
        key = str(competency_key).strip().lower()
        payload = (tid, key, str(name).strip(), str(description or "").strip())

        conn = self._normalize_conn(conn)

        if self._needs_db_transaction(conn):
            with transaction() as tx:
                return self.create_competency(
                    tenant_id=payload[0],
                    competency_key=payload[1],
                    name=payload[2],
                    description=payload[3],
                    conn=tx,
                )

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_graph_competencies
                        (tenant_id, competency_key, name, description)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (tenant_id, competency_key) DO UPDATE
                      SET name = EXCLUDED.name,
                          description = EXCLUDED.description,
                          updated_at = NOW()
                    RETURNING id, tenant_id, competency_key, name, description, created_at, updated_at
                    """,
                    payload,
                )
                row = cur.fetchone()
            return {
                "id": int(row[0]),
                "tenant_id": int(row[1]),
                "competency_key": str(row[2]),
                "name": str(row[3]),
                "description": str(row[4]),
                "created_at": row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5]),
                "updated_at": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
            }

        with self._lock:
            uniq = (tid, key)
            existing_id = self._competencies_by_key.get(uniq)
            now = self._now()
            if existing_id is not None:
                row = self._competencies[existing_id]
                row["name"] = payload[2]
                row["description"] = payload[3]
                row["updated_at"] = now
                return dict(row)
            self._competency_counter += 1
            row = {
                "id": self._competency_counter,
                "tenant_id": tid,
                "competency_key": key,
                "name": payload[2],
                "description": payload[3],
                "created_at": now,
                "updated_at": now,
            }
            self._competencies[self._competency_counter] = row
            self._competencies_by_key[uniq] = self._competency_counter
            return dict(row)

    def list_competencies(self, *, tenant_id: int, conn: object | None = None) -> list[dict[str, Any]]:
        tid = int(tenant_id)
        conn = self._normalize_conn(conn)
        if self._needs_db_transaction(conn):
            with transaction() as tx:
                return self.list_competencies(tenant_id=tid, conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, competency_key, name, description, created_at, updated_at
                    FROM app_platform_graph_competencies
                    WHERE tenant_id = %s
                    ORDER BY name ASC, id ASC
                    """,
                    (tid,),
                )
                rows = cur.fetchall()
            return [
                {
                    "id": int(r[0]),
                    "tenant_id": int(r[1]),
                    "competency_key": str(r[2]),
                    "name": str(r[3]),
                    "description": str(r[4]),
                    "created_at": r[5].isoformat() if hasattr(r[5], "isoformat") else str(r[5]),
                    "updated_at": r[6].isoformat() if hasattr(r[6], "isoformat") else str(r[6]),
                }
                for r in rows
            ]

        with self._lock:
            rows = [dict(v) for v in self._competencies.values() if int(v["tenant_id"]) == tid]
        rows.sort(key=lambda r: (str(r["name"]).lower(), int(r["id"])))
        return rows

    # ------------------------------------------------------------------
    # CourseSkill edges
    # ------------------------------------------------------------------

    def create_course_skill(
        self,
        *,
        tenant_id: int,
        course_id: str,
        skill_id: int,
        weight: float,
        conn: object | None = None,
    ) -> dict[str, Any]:
        tid = int(tenant_id)
        cid = str(course_id).strip()
        sid = int(skill_id)
        w = float(weight)

        conn = self._normalize_conn(conn)

        if self._needs_db_transaction(conn):
            with transaction() as tx:
                return self.create_course_skill(
                    tenant_id=tid,
                    course_id=cid,
                    skill_id=sid,
                    weight=w,
                    conn=tx,
                )

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_graph_course_skills
                        (tenant_id, course_id, skill_id, weight)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (tenant_id, course_id, skill_id) DO UPDATE
                      SET weight = EXCLUDED.weight,
                          updated_at = NOW()
                    RETURNING id, tenant_id, course_id, skill_id, weight, created_at, updated_at
                    """,
                    (tid, cid, sid, w),
                )
                row = cur.fetchone()
            skill = self._get_skill_by_id(tenant_id=tid, skill_id=sid, conn=conn)
            return {
                "id": int(row[0]),
                "tenant_id": int(row[1]),
                "course_id": str(row[2]),
                "skill_id": int(row[3]),
                "skill_key": str(skill["skill_key"]),
                "skill_name": str(skill["name"]),
                "weight": float(row[4]),
                "created_at": row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5]),
                "updated_at": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
            }

        with self._lock:
            skill = self._skills.get(sid)
            if skill is None or int(skill["tenant_id"]) != tid:
                raise ValueError(f"skill {sid} not found")
            uniq = (tid, cid, sid)
            existing_id = self._course_skill_by_unique.get(uniq)
            now = self._now()
            if existing_id is not None:
                row = self._course_skills[existing_id]
                row["weight"] = w
                row["updated_at"] = now
                return dict(row)
            self._course_skill_counter += 1
            row = {
                "id": self._course_skill_counter,
                "tenant_id": tid,
                "course_id": cid,
                "skill_id": sid,
                "skill_key": str(skill["skill_key"]),
                "skill_name": str(skill["name"]),
                "weight": w,
                "created_at": now,
                "updated_at": now,
            }
            self._course_skills[self._course_skill_counter] = row
            self._course_skill_by_unique[uniq] = self._course_skill_counter
            return dict(row)

    def list_course_skills(
        self,
        *,
        tenant_id: int,
        course_id: str | None = None,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        tid = int(tenant_id)
        cid = str(course_id).strip() if course_id is not None else None

        conn = self._normalize_conn(conn)

        if self._needs_db_transaction(conn):
            with transaction() as tx:
                return self.list_course_skills(tenant_id=tid, course_id=cid, conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                if cid is None:
                    cur.execute(
                        """
                        SELECT cs.id, cs.tenant_id, cs.course_id, cs.skill_id, s.skill_key, s.name,
                               cs.weight, cs.created_at, cs.updated_at
                        FROM app_platform_graph_course_skills cs
                        JOIN app_platform_graph_skills s
                          ON s.id = cs.skill_id
                         AND s.tenant_id = cs.tenant_id
                        WHERE cs.tenant_id = %s
                        ORDER BY cs.course_id ASC, s.name ASC, cs.id ASC
                        """,
                        (tid,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT cs.id, cs.tenant_id, cs.course_id, cs.skill_id, s.skill_key, s.name,
                               cs.weight, cs.created_at, cs.updated_at
                        FROM app_platform_graph_course_skills cs
                        JOIN app_platform_graph_skills s
                          ON s.id = cs.skill_id
                         AND s.tenant_id = cs.tenant_id
                        WHERE cs.tenant_id = %s
                          AND cs.course_id = %s
                        ORDER BY s.name ASC, cs.id ASC
                        """,
                        (tid, cid),
                    )
                rows = cur.fetchall()
            return [
                {
                    "id": int(r[0]),
                    "tenant_id": int(r[1]),
                    "course_id": str(r[2]),
                    "skill_id": int(r[3]),
                    "skill_key": str(r[4]),
                    "skill_name": str(r[5]),
                    "weight": float(r[6]),
                    "created_at": r[7].isoformat() if hasattr(r[7], "isoformat") else str(r[7]),
                    "updated_at": r[8].isoformat() if hasattr(r[8], "isoformat") else str(r[8]),
                }
                for r in rows
            ]

        with self._lock:
            rows = [dict(v) for v in self._course_skills.values() if int(v["tenant_id"]) == tid]
        if cid is not None:
            rows = [r for r in rows if str(r["course_id"]) == cid]
        rows.sort(key=lambda r: (str(r["course_id"]), str(r["skill_name"]).lower(), int(r["id"])))
        return rows

    # ------------------------------------------------------------------
    # StudentSkill edges
    # ------------------------------------------------------------------

    def upsert_student_skill(
        self,
        *,
        tenant_id: int,
        student_id: str,
        skill_id: int,
        proficiency_delta: float,
        source: str,
        conn: object | None = None,
    ) -> dict[str, Any]:
        tid = int(tenant_id)
        sid = str(student_id).strip()
        skill_id = int(skill_id)
        delta = float(proficiency_delta)
        src = str(source).strip().lower() or "course"

        conn = self._normalize_conn(conn)

        if self._needs_db_transaction(conn):
            with transaction() as tx:
                return self.upsert_student_skill(
                    tenant_id=tid,
                    student_id=sid,
                    skill_id=skill_id,
                    proficiency_delta=delta,
                    source=src,
                    conn=tx,
                )

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_platform_graph_student_skills
                        (tenant_id, student_id, skill_id, proficiency_level, source)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (tenant_id, student_id, skill_id) DO UPDATE
                      SET proficiency_level = app_platform_graph_student_skills.proficiency_level + EXCLUDED.proficiency_level,
                          source = EXCLUDED.source,
                          last_updated = NOW(),
                          updated_at = NOW()
                    RETURNING id, tenant_id, student_id, skill_id, proficiency_level, source, last_updated, created_at, updated_at
                    """,
                    (tid, sid, skill_id, delta, src),
                )
                row = cur.fetchone()
            skill = self._get_skill_by_id(tenant_id=tid, skill_id=skill_id, conn=conn)
            return {
                "id": int(row[0]),
                "tenant_id": int(row[1]),
                "student_id": str(row[2]),
                "skill_id": int(row[3]),
                "skill_key": str(skill["skill_key"]),
                "skill_name": str(skill["name"]),
                "proficiency_level": float(row[4]),
                "source": str(row[5]),
                "last_updated": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
                "created_at": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
                "updated_at": row[8].isoformat() if hasattr(row[8], "isoformat") else str(row[8]),
            }

        with self._lock:
            skill = self._skills.get(skill_id)
            if skill is None or int(skill["tenant_id"]) != tid:
                raise ValueError(f"skill {skill_id} not found")
            uniq = (tid, sid, skill_id)
            now = self._now()
            existing_id = self._student_skill_by_unique.get(uniq)
            if existing_id is not None:
                row = self._student_skills[existing_id]
                row["proficiency_level"] = float(row["proficiency_level"]) + delta
                row["source"] = src
                row["last_updated"] = now
                row["updated_at"] = now
                return dict(row)

            self._student_skill_counter += 1
            row = {
                "id": self._student_skill_counter,
                "tenant_id": tid,
                "student_id": sid,
                "skill_id": skill_id,
                "skill_key": str(skill["skill_key"]),
                "skill_name": str(skill["name"]),
                "proficiency_level": delta,
                "source": src,
                "last_updated": now,
                "created_at": now,
                "updated_at": now,
            }
            self._student_skills[self._student_skill_counter] = row
            self._student_skill_by_unique[uniq] = self._student_skill_counter
            return dict(row)

    def list_student_skills(
        self,
        *,
        tenant_id: int,
        student_id: str | None = None,
        conn: object | None = None,
    ) -> list[dict[str, Any]]:
        tid = int(tenant_id)
        sid = str(student_id).strip() if student_id is not None else None

        conn = self._normalize_conn(conn)

        if self._needs_db_transaction(conn):
            with transaction() as tx:
                return self.list_student_skills(tenant_id=tid, student_id=sid, conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                if sid is None:
                    cur.execute(
                        """
                        SELECT ss.id, ss.tenant_id, ss.student_id, ss.skill_id, s.skill_key, s.name,
                               ss.proficiency_level, ss.source, ss.last_updated, ss.created_at, ss.updated_at
                        FROM app_platform_graph_student_skills ss
                        JOIN app_platform_graph_skills s
                          ON s.id = ss.skill_id
                         AND s.tenant_id = ss.tenant_id
                        WHERE ss.tenant_id = %s
                        ORDER BY ss.student_id ASC, ss.proficiency_level DESC, ss.id ASC
                        """,
                        (tid,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT ss.id, ss.tenant_id, ss.student_id, ss.skill_id, s.skill_key, s.name,
                               ss.proficiency_level, ss.source, ss.last_updated, ss.created_at, ss.updated_at
                        FROM app_platform_graph_student_skills ss
                        JOIN app_platform_graph_skills s
                          ON s.id = ss.skill_id
                         AND s.tenant_id = ss.tenant_id
                        WHERE ss.tenant_id = %s
                          AND ss.student_id = %s
                        ORDER BY ss.proficiency_level DESC, ss.id ASC
                        """,
                        (tid, sid),
                    )
                rows = cur.fetchall()
            return [
                {
                    "id": int(r[0]),
                    "tenant_id": int(r[1]),
                    "student_id": str(r[2]),
                    "skill_id": int(r[3]),
                    "skill_key": str(r[4]),
                    "skill_name": str(r[5]),
                    "proficiency_level": float(r[6]),
                    "source": str(r[7]),
                    "last_updated": r[8].isoformat() if hasattr(r[8], "isoformat") else str(r[8]),
                    "created_at": r[9].isoformat() if hasattr(r[9], "isoformat") else str(r[9]),
                    "updated_at": r[10].isoformat() if hasattr(r[10], "isoformat") else str(r[10]),
                }
                for r in rows
            ]

        with self._lock:
            rows = [dict(v) for v in self._student_skills.values() if int(v["tenant_id"]) == tid]
        if sid is not None:
            rows = [r for r in rows if str(r["student_id"]) == sid]
        rows.sort(key=lambda r: (str(r["student_id"]), -float(r["proficiency_level"]), int(r["id"])))
        return rows

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def count_skills(self, *, conn: object | None = None) -> int:
        conn = self._normalize_conn(conn)
        if self._needs_db_transaction(conn):
            with transaction() as tx:
                return self.count_skills(conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM app_platform_graph_skills")
                row = cur.fetchone()
            return int(row[0]) if row else 0

        with self._lock:
            return len(self._skills)

    def count_course_skill_edges(self, *, conn: object | None = None) -> int:
        conn = self._normalize_conn(conn)
        if self._needs_db_transaction(conn):
            with transaction() as tx:
                return self.count_course_skill_edges(conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM app_platform_graph_course_skills")
                row = cur.fetchone()
            return int(row[0]) if row else 0

        with self._lock:
            return len(self._course_skills)

    def count_student_skill_edges(self, *, conn: object | None = None) -> int:
        conn = self._normalize_conn(conn)
        if self._needs_db_transaction(conn):
            with transaction() as tx:
                return self.count_student_skill_edges(conn=tx)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM app_platform_graph_student_skills")
                row = cur.fetchone()
            return int(row[0]) if row else 0

        with self._lock:
            return len(self._student_skills)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_skill_by_id(self, *, tenant_id: int, skill_id: int, conn: object | None) -> dict[str, Any]:
        tid = int(tenant_id)
        sid = int(skill_id)

        if db_available() and psycopg is not None and conn is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id, skill_key, name
                    FROM app_platform_graph_skills
                    WHERE tenant_id = %s
                      AND id = %s
                    LIMIT 1
                    """,
                    (tid, sid),
                )
                row = cur.fetchone()
            if row is None:
                raise ValueError(f"skill {sid} not found")
            return {
                "id": int(row[0]),
                "tenant_id": int(row[1]),
                "skill_key": str(row[2]),
                "name": str(row[3]),
            }

        with self._lock:
            row = self._skills.get(sid)
        if row is None or int(row["tenant_id"]) != tid:
            raise ValueError(f"skill {sid} not found")
        return dict(row)


SHARED_EDUCATION_GRAPH_REPOSITORY = EducationGraphRepository()
