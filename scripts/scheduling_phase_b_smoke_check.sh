#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

# Load JWT secret from infra env if not provided by shell.
if [[ -z "${JWT_SECRET:-}" && -f "${ROOT_DIR}/infra/.env" ]]; then
  source <(grep '^JWT_SECRET=' "${ROOT_DIR}/infra/.env")
fi

: "${JWT_SECRET:?JWT_SECRET not found. Set JWT_SECRET in environment or ${ROOT_DIR}/infra/.env}"

export ROOT_DIR
export BACKEND_DIR="${ROOT_DIR}/backend"
export JWT_SECRET
export API_BASE_URL="${API_BASE_URL:-http://backend:8000}"

pushd "${ROOT_DIR}/infra" >/dev/null
"${COMPOSE[@]}" up -d --build db redis backend >/dev/null

"${COMPOSE[@]}" exec -T backend sh -c "ROOT_DIR='${ROOT_DIR}' BACKEND_DIR='${BACKEND_DIR}' API_BASE_URL='${API_BASE_URL}' python -" <<'PY'
from __future__ import annotations

import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

ROOT_DIR = Path(os.environ["ROOT_DIR"])
BACKEND_DIR = Path(os.environ["BACKEND_DIR"])

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient

from app.core.db import build_engine, make_session_factory
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.enrollments.models import AcademicTermModel
from app.modules.profiles.models import PersonModel
from app.modules.students.models import StudentAdmissionSource, StudentProfileModel, StudentStatus
from app.platform.tenant import service as tenant_service

results: list[tuple[str, bool, str]] = []


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def record(name: str, ok: bool, detail: str) -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")
    results.append((name, ok, detail))


def run_check(name: str, callback) -> None:
    try:
        detail = str(callback())
    except Exception as exc:
        record(name, False, str(exc))
        return
    record(name, True, detail)


suffix = uuid.uuid4().hex[:8]
tenant = tenant_service.create_tenant(f"sched-pilot-{suffix}", f"Scheduling Pilot {suffix}")
tenant_id = int(tenant["tenant_id"])


def admin_headers() -> dict[str, str]:
    token = create_access_token(
        user_id="pilot.ops@example.com",
        roles=["institution_admin"],
        auth_source="smoke",
        tenant_id=tenant_id,
        permissions=["scheduling.read", "scheduling.write"],
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }


session_factory = make_session_factory(build_engine())

with session_factory() as db:
    term = AcademicTermModel(
        tenant_id=tenant_id,
        term_code=f"SMOKE-{suffix}",
        term_name=f"Smoke Term {suffix}",
        status="active",
        metadata_json={},
    )
    db.add(term)
    db.flush()

    section_id = int(
        db.execute(
            text(
                """
                INSERT INTO app_scheduling_course_sections
                (tenant_id, course_id, term_id, section_code, instructor_id, max_capacity, status, version)
                VALUES
                (:tenant_id, :course_id, :term_id, :section_code, :instructor_id, :max_capacity, 'scheduled', 1)
                RETURNING id
                """
            ),
            {
                "tenant_id": tenant_id,
                "course_id": 900001,
                "term_id": int(term.id),
                "section_code": f"S-{suffix[:4]}",
                "instructor_id": "inst@example.com",
                "max_capacity": 30,
            },
        ).scalar_one()
    )

    person = PersonModel(
        tenant_id=tenant_id,
        email=f"sched-student-{suffix}@example.edu",
        first_name="Pilot",
        last_name="Student",
        status="active",
        metadata_json={},
        version=1,
        created_by="smoke",
    )
    db.add(person)
    db.flush()

    student = StudentProfileModel(
        tenant_id=tenant_id,
        person_id=person.id,
        student_number=f"SN-{suffix.upper()}",
        cohort_year=datetime.now(UTC).year,
        current_status=StudentStatus.ACTIVE,
        admission_source=StudentAdmissionSource.MANUAL,
        metadata_json={},
        version=1,
        created_by="smoke",
        updated_by="smoke",
    )
    db.add(student)
    db.flush()
    student_id = int(student.id)
    db.commit()

client = TestClient(app, base_url=os.environ["API_BASE_URL"], raise_server_exceptions=False)
client.__enter__()
headers = admin_headers()

state: dict[str, int] = {}


def create_lesson() -> str:
    response = client.post(
        f"/api/admin/scheduling/sections/{section_id}/lessons",
        headers=headers,
        json={
            "scheduled_date": datetime.now(UTC).date().isoformat(),
            "topic_title": "Pilot Smoke Topic",
            "notes": "phase-b smoke",
            "metadata_json": {"source": "pilot-smoke"},
        },
    )
    ensure(response.status_code == 201, f"create lesson returned {response.status_code}: {response.text}")
    payload = response.json()
    state["lesson_id"] = int(payload["id"])
    ensure(payload["section_id"] == section_id, "lesson section mismatch")
    return f"lesson_id={payload['id']}"


def list_lessons() -> str:
    response = client.get(
        f"/api/admin/scheduling/sections/{section_id}/lessons?page=1&page_size=20",
        headers=headers,
    )
    ensure(response.status_code == 200, f"list lessons returned {response.status_code}: {response.text}")
    payload = response.json()
    ensure(payload["total"] >= 1, "no lessons returned")
    ensure(any(int(item["id"]) == state["lesson_id"] for item in payload["items"]), "created lesson missing")
    return f"total={payload['total']}"


def upsert_attendance() -> str:
    response = client.put(
        f"/api/admin/scheduling/lessons/{state['lesson_id']}/attendance",
        headers=headers,
        json={"student_profile_id": student_id, "attendance_status": "present"},
    )
    ensure(response.status_code == 200, f"upsert attendance returned {response.status_code}: {response.text}")
    payload = response.json()
    ensure(int(payload["student_profile_id"]) == student_id, "attendance student mismatch")
    ensure(payload["attendance_status"] == "present", "attendance status mismatch")
    return f"attendance_id={payload['id']}"


def list_attendance() -> str:
    response = client.get(
        f"/api/admin/scheduling/lessons/{state['lesson_id']}/attendance",
        headers=headers,
    )
    ensure(response.status_code == 200, f"list attendance returned {response.status_code}: {response.text}")
    payload = response.json()
    ensure(payload["total"] >= 1, "no attendance rows returned")
    ensure(
        any(int(item["student_profile_id"]) == student_id for item in payload["items"]),
        "expected student attendance row missing",
    )
    return f"total={payload['total']}"


run_check("Phase B Lesson Create", create_lesson)
run_check("Phase B Lesson List", list_lessons)
run_check("Phase B Attendance Upsert", upsert_attendance)
run_check("Phase B Attendance List", list_attendance)

failed = [name for name, ok, _detail in results if not ok]
print(f"[SUMMARY] passed={len(results) - len(failed)} failed={len(failed)}")
client.__exit__(None, None, None)
if failed:
    raise SystemExit(1)
PY

popd >/dev/null
