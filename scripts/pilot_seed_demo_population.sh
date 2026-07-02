#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="${ROOT_DIR}/infra"

STUDENT_COUNT="${STUDENT_COUNT:-100}"
TEACHER_COUNT="${TEACHER_COUNT:-10}"
DEAN_COUNT="${DEAN_COUNT:-1}"
TENANT_ID="${TENANT_ID:-1}"
DEMO_PASSWORD="${DEMO_PASSWORD:-password123}"
SKIP_LDAP="${SKIP_LDAP:-0}"

if [ "${1:-}" = "--skip-ldap" ]; then
  SKIP_LDAP="1"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[pilot-seed-demo] FAIL: docker is not installed"
  exit 1
fi

compose() {
  (cd "${INFRA_DIR}" && docker compose --env-file .env "$@")
}

echo "[pilot-seed-demo] ensuring required services are running..."
if [ "${SKIP_LDAP}" = "1" ]; then
  compose up -d db redis backend worker scheduler >/dev/null
else
  compose up -d ldap db redis backend worker scheduler >/dev/null
fi

echo "[pilot-seed-demo] waiting for LDAP readiness..."
LDAP_READY=0
if [ "${SKIP_LDAP}" != "1" ]; then
  for _ in $(seq 1 30); do
    if compose exec -T ldap ldapwhoami -H ldap://localhost -D "cn=admin,dc=example,dc=local" -w admin >/dev/null 2>&1; then
      LDAP_READY=1
      break
    fi
    sleep 2
  done
fi

if [ "${SKIP_LDAP}" = "1" ]; then
  echo "[pilot-seed-demo] SKIP_LDAP=1 set, LDAP user provisioning is disabled"
elif [ "${LDAP_READY}" -ne 1 ]; then
  echo "[pilot-seed-demo] WARN: LDAP is unavailable (container unhealthy or restarting), LDAP user provisioning will be skipped"
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

USERS_LDIF="${TMP_DIR}/demo_users.ldif"
GROUPS_LDIF="${TMP_DIR}/demo_groups.ldif"
MEMBERS_LDIF="${TMP_DIR}/demo_group_members.ldif"

{
  for i in $(seq 1 "${DEAN_COUNT}"); do
    cn="dean_$(printf "%02d" "${i}")"
    cat <<EOF

dn: cn=${cn},ou=Users,dc=example,dc=local
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
cn: ${cn}
sn: Dean
givenName: Dean
displayName: Demo Dean ${i}
mail: ${cn}@example.local
userPassword: ${DEMO_PASSWORD}
EOF
  done

  for i in $(seq 1 "${TEACHER_COUNT}"); do
    cn="teacher_$(printf "%03d" "${i}")"
    cat <<EOF

dn: cn=${cn},ou=Users,dc=example,dc=local
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
cn: ${cn}
sn: Teacher
givenName: Teacher
displayName: Demo Teacher ${i}
mail: ${cn}@example.local
userPassword: ${DEMO_PASSWORD}
EOF
  done

  for i in $(seq 1 "${STUDENT_COUNT}"); do
    cn="student_$(printf "%03d" "${i}")"
    cat <<EOF

dn: cn=${cn},ou=Users,dc=example,dc=local
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
cn: ${cn}
sn: Student
givenName: Student
displayName: Demo Student ${i}
mail: ${cn}@example.local
userPassword: ${DEMO_PASSWORD}
EOF
  done
} >"${USERS_LDIF}"

cat >"${GROUPS_LDIF}" <<EOF

dn: cn=dean,ou=Groups,dc=example,dc=local
objectClass: groupOfNames
cn: dean
description: Demo dean users
member: cn=dean_01,ou=Users,dc=example,dc=local

dn: cn=teacher,ou=Groups,dc=example,dc=local
objectClass: groupOfNames
cn: teacher
description: Demo teacher users
member: cn=teacher_001,ou=Users,dc=example,dc=local

dn: cn=student,ou=Groups,dc=example,dc=local
objectClass: groupOfNames
cn: student
description: Demo student users
member: cn=student_001,ou=Users,dc=example,dc=local
EOF

{
  printf 'dn: cn=dean,ou=Groups,dc=example,dc=local\nchangetype: modify\nreplace: member\n'
  for i in $(seq 1 "${DEAN_COUNT}"); do
    printf 'member: cn=dean_%02d,ou=Users,dc=example,dc=local\n' "${i}"
  done
  printf '\n'

  printf 'dn: cn=teacher,ou=Groups,dc=example,dc=local\nchangetype: modify\nreplace: member\n'
  for i in $(seq 1 "${TEACHER_COUNT}"); do
    printf 'member: cn=teacher_%03d,ou=Users,dc=example,dc=local\n' "${i}"
  done
  printf '\n'

  printf 'dn: cn=student,ou=Groups,dc=example,dc=local\nchangetype: modify\nreplace: member\n'
  for i in $(seq 1 "${STUDENT_COUNT}"); do
    printf 'member: cn=student_%03d,ou=Users,dc=example,dc=local\n' "${i}"
  done
  printf '\n'
} >"${MEMBERS_LDIF}"

if [ "${SKIP_LDAP}" != "1" ] && [ "${LDAP_READY}" -eq 1 ]; then
  echo "[pilot-seed-demo] applying base LDAP structure from infra/ldap-init.ldif (idempotent)..."
  cat "${INFRA_DIR}/ldap-init.ldif" | compose exec -T ldap ldapadd -c -x -D "cn=admin,dc=example,dc=local" -w admin || true

  echo "[pilot-seed-demo] creating LDAP users (idempotent)..."
  cat "${USERS_LDIF}" | compose exec -T ldap ldapadd -c -x -D "cn=admin,dc=example,dc=local" -w admin || true

  echo "[pilot-seed-demo] creating LDAP groups (idempotent)..."
  cat "${GROUPS_LDIF}" | compose exec -T ldap ldapadd -c -x -D "cn=admin,dc=example,dc=local" -w admin || true

  echo "[pilot-seed-demo] attaching users to LDAP groups (idempotent)..."
  cat "${MEMBERS_LDIF}" | compose exec -T ldap ldapmodify -c -x -D "cn=admin,dc=example,dc=local" -w admin || true
fi

echo "[pilot-seed-demo] seeding demo academic dataset..."
compose exec -T \
  -e TENANT_ID="${TENANT_ID}" \
  -e STUDENT_COUNT="${STUDENT_COUNT}" \
  -e TEACHER_COUNT="${TEACHER_COUNT}" \
  -e DEAN_COUNT="${DEAN_COUNT}" \
  backend python - <<'PY'
from __future__ import annotations

import json
import os
import random
from datetime import date, datetime, timezone

import psycopg

TENANT_ID = int(os.environ.get("TENANT_ID", "1"))
STUDENT_COUNT = int(os.environ.get("STUDENT_COUNT", "100"))
TEACHER_COUNT = int(os.environ.get("TEACHER_COUNT", "10"))
DEAN_COUNT = int(os.environ.get("DEAN_COUNT", "1"))

random.seed(42)

conn = psycopg.connect(os.environ["DATABASE_URL"])
conn.autocommit = False



def q1(cur, sql, params=()):
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0] if row else None


with conn.cursor() as cur:
    tenant_exists = q1(cur, "SELECT id FROM app_tenants WHERE id = %s", (TENANT_ID,))
    if not tenant_exists:
        cur.execute(
            """
            INSERT INTO app_tenants (id, slug, name, status, plan_id, created_at, updated_at)
            VALUES (%s, %s, %s, 'active', 1, NOW(), NOW())
            """,
            (TENANT_ID, f"demo-tenant-{TENANT_ID}", "Demo University"),
        )

    cur.execute(
        """
        INSERT INTO university_programs (program_code, title, degree_type, faculty, status, tenant_id)
        VALUES (%s, %s, %s, %s, 'active', %s)
        ON CONFLICT (program_code) DO UPDATE SET
          title = EXCLUDED.title,
          degree_type = EXCLUDED.degree_type,
          faculty = EXCLUDED.faculty,
          status = EXCLUDED.status
        RETURNING id
        """,
        ("DEMO-BSC-CS", "Computer Science", "bachelor", "School of Engineering", str(TENANT_ID)),
    )
    uni_program_id = cur.fetchone()[0]

    dept_code = "DEMO-CS"
    cur.execute(
        """
        INSERT INTO app_profiles_departments
          (tenant_id, code, name, unit_type, status, metadata_json, version, created_by, created_at, updated_at)
        VALUES
          (%s, %s, %s, 'department', 'active', '{}'::jsonb, 1, 'demo.seed', NOW(), NOW())
        ON CONFLICT (tenant_id, code) DO UPDATE SET
          name = EXCLUDED.name,
          status = EXCLUDED.status,
          updated_at = NOW()
        RETURNING id
        """,
        (TENANT_ID, dept_code, "Department of Computer Science"),
    )
    profile_dept_id = cur.fetchone()[0]

    cur.execute(
        """
        INSERT INTO app_profiles_programs
          (tenant_id, department_id, code, title, degree_type, status, metadata_json, version, created_by, created_at, updated_at)
        VALUES
          (%s, %s, %s, %s, %s, 'active', '{}'::jsonb, 1, 'demo.seed', NOW(), NOW())
        ON CONFLICT (tenant_id, code) DO UPDATE SET
          department_id = EXCLUDED.department_id,
          title = EXCLUDED.title,
          degree_type = EXCLUDED.degree_type,
          status = EXCLUDED.status,
          updated_at = NOW()
        RETURNING id
        """,
        (TENANT_ID, profile_dept_id, "DEMO-PROFILE-CS", "Computer Science", "bachelor"),
    )
    profile_program_id = cur.fetchone()[0]

    term_code = "2026-SPRING"
    cur.execute(
        """
        INSERT INTO app_enrollments_terms
          (tenant_id, term_code, term_name, start_date, end_date, status, metadata_json, created_at, updated_at)
        VALUES
          (%s, %s, %s, NOW(), NOW() + interval '120 day', 'active', '{}'::jsonb, NOW(), NOW())
        ON CONFLICT (tenant_id, term_code) DO UPDATE SET
          term_name = EXCLUDED.term_name,
          status = EXCLUDED.status,
          updated_at = NOW()
        RETURNING id
        """,
        (TENANT_ID, term_code, "Spring 2026"),
    )
    term_id = cur.fetchone()[0]

    course_ids: list[int] = []
    for idx, title in enumerate(
        [
            "Calculus I",
            "Linear Algebra",
            "Physics I",
            "Programming Fundamentals",
            "Data Structures",
            "Discrete Math",
            "Database Systems",
            "Computer Networks",
        ],
        start=1,
    ):
        code = f"DEMO-CS-{idx:03d}"
        cur.execute(
            """
            INSERT INTO university_courses (course_code, title, credits, program_id, status, tenant_id)
            VALUES (%s, %s, %s, %s, 'active', %s)
            ON CONFLICT (course_code) DO UPDATE SET
              title = EXCLUDED.title,
              credits = EXCLUDED.credits,
              program_id = EXCLUDED.program_id,
              status = EXCLUDED.status,
              tenant_id = EXCLUDED.tenant_id
            RETURNING id
            """,
            (code, title, 5, uni_program_id, str(TENANT_ID)),
        )
        course_ids.append(cur.fetchone()[0])

    cur.execute(
        """
        INSERT INTO app_grades_scales (tenant_id, name, description, is_active)
        VALUES (%s, %s, %s, true)
        ON CONFLICT (tenant_id, name) DO UPDATE SET
          description = EXCLUDED.description,
          is_active = true
        RETURNING id
        """,
        (TENANT_ID, "DEMO_A_F", "Demo A-F scale"),
    )
    scale_id = cur.fetchone()[0]

    scale_rows = [
        ("A", 4.00, 90.00, 100.00),
        ("B", 3.00, 80.00, 89.99),
        ("C", 2.00, 70.00, 79.99),
        ("D", 1.00, 60.00, 69.99),
        ("F", 0.00, 0.00, 59.99),
    ]
    for grade_code, grade_points, pmin, pmax in scale_rows:
        cur.execute(
            """
            INSERT INTO app_grades_scale_items
              (tenant_id, scale_id, grade_code, grade_points, min_percentage, max_percentage)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id, scale_id, grade_code) DO UPDATE SET
              grade_points = EXCLUDED.grade_points,
              min_percentage = EXCLUDED.min_percentage,
              max_percentage = EXCLUDED.max_percentage
            """,
            (TENANT_ID, scale_id, grade_code, grade_points, pmin, pmax),
        )

    dean_user_ids: list[str] = []
    for i in range(1, DEAN_COUNT + 1):
        dean_user_ids.append(f"dean_{i:02d}")

    teacher_user_ids: list[str] = []
    for i in range(1, TEACHER_COUNT + 1):
        teacher_user_ids.append(f"teacher_{i:03d}")

    student_user_ids: list[str] = []
    for i in range(1, STUDENT_COUNT + 1):
        student_user_ids.append(f"student_{i:03d}")

    section_ids_by_course: dict[int, int] = {}
    for idx, course_id in enumerate(course_ids, start=1):
        section_code = f"DEMO-SEC-{idx:03d}"
        instructor_id = teacher_user_ids[(idx - 1) % len(teacher_user_ids)] if teacher_user_ids else None
        cur.execute(
            """
            INSERT INTO app_scheduling_course_sections
              (tenant_id, course_id, term_id, section_code, instructor_id, max_capacity, status, created_at, updated_at, version)
            VALUES
              (%s, %s, %s, %s, %s, %s, 'scheduled', NOW(), NOW(), 1)
            ON CONFLICT (tenant_id, course_id, term_id, section_code) DO UPDATE SET
              instructor_id = EXCLUDED.instructor_id,
              max_capacity = EXCLUDED.max_capacity,
              status = EXCLUDED.status,
              updated_at = NOW()
            RETURNING id
            """,
            (TENANT_ID, course_id, term_id, section_code, instructor_id, STUDENT_COUNT),
        )
        section_ids_by_course[course_id] = cur.fetchone()[0]

    def upsert_person(user_id: str, first_name: str, last_name: str) -> int:
        email = f"{user_id}@example.local"
        cur.execute(
            """
            INSERT INTO app_profiles_people
              (tenant_id, email, first_name, last_name, status, metadata_json, version, created_by, created_at, updated_at)
            VALUES
              (%s, %s, %s, %s, 'active', '{}'::jsonb, 1, 'demo.seed', NOW(), NOW())
            ON CONFLICT (tenant_id, email) DO UPDATE SET
              first_name = EXCLUDED.first_name,
              last_name = EXCLUDED.last_name,
              status = EXCLUDED.status,
              updated_at = NOW()
            RETURNING id
            """,
            (TENANT_ID, email, first_name, last_name),
        )
        return cur.fetchone()[0]

    for user_id in dean_user_ids:
        person_id = upsert_person(user_id, "Demo", "Dean")
        cur.execute(
            """
            INSERT INTO app_profiles_faculty
              (tenant_id, person_id, department_id, faculty_number, academic_title, status, metadata_json, version, created_by, created_at, updated_at)
            VALUES
              (%s, %s, %s, %s, %s, 'active', '{}'::jsonb, 1, 'demo.seed', NOW(), NOW())
            ON CONFLICT (tenant_id, person_id) DO UPDATE SET
              department_id = EXCLUDED.department_id,
              faculty_number = EXCLUDED.faculty_number,
              academic_title = EXCLUDED.academic_title,
              status = EXCLUDED.status,
              updated_at = NOW()
            """,
            (TENANT_ID, person_id, profile_dept_id, f"DEAN-{user_id}", "Dean"),
        )

    for idx, user_id in enumerate(teacher_user_ids, start=1):
        person_id = upsert_person(user_id, "Demo", f"Teacher{idx}")
        cur.execute(
            """
            INSERT INTO app_profiles_faculty
              (tenant_id, person_id, department_id, faculty_number, academic_title, status, metadata_json, version, created_by, created_at, updated_at)
            VALUES
              (%s, %s, %s, %s, %s, 'active', '{}'::jsonb, 1, 'demo.seed', NOW(), NOW())
            ON CONFLICT (tenant_id, person_id) DO UPDATE SET
              department_id = EXCLUDED.department_id,
              faculty_number = EXCLUDED.faculty_number,
              academic_title = EXCLUDED.academic_title,
              status = EXCLUDED.status,
              updated_at = NOW()
            """,
            (TENANT_ID, person_id, profile_dept_id, f"TCH-{idx:03d}", "Senior Lecturer"),
        )

    enrollment_count = 0
    grade_submission_count = 0
    severe_count = 0
    at_risk_count = 0
    case_count = 0

    severe_students: list[tuple[int, str, float]] = []
    at_risk_students: list[tuple[int, str, float]] = []

    for idx, user_id in enumerate(student_user_ids, start=1):
        person_id = upsert_person(user_id, "Demo", f"Student{idx}")
        student_number = f"DEMO-S-{idx:04d}"
        cur.execute(
            """
            INSERT INTO app_students_profiles
              (tenant_id, person_id, student_number, cohort_year, academic_level, current_status, admission_source, metadata_json, version, created_by, updated_by, created_at, updated_at)
            VALUES
              (%s, %s, %s, 2026, 'undergraduate', 'active', 'manual', '{}'::jsonb, 1, 'demo.seed', 'demo.seed', NOW(), NOW())
            ON CONFLICT (tenant_id, person_id) DO UPDATE SET
              student_number = EXCLUDED.student_number,
              cohort_year = EXCLUDED.cohort_year,
              academic_level = EXCLUDED.academic_level,
              current_status = EXCLUDED.current_status,
              updated_by = EXCLUDED.updated_by,
              updated_at = NOW()
            RETURNING id
            """,
            (TENANT_ID, person_id, student_number),
        )
        student_profile_id = cur.fetchone()[0]

        chosen_courses = random.sample(course_ids, k=3)
        student_best_grade = 100.0
        for course_id in chosen_courses:
            cur.execute(
                """
                SELECT id
                FROM app_enrollments_enrollments
                WHERE tenant_id = %s
                  AND student_profile_id = %s
                  AND course_id = %s
                  AND term_id = %s
                  AND enrollment_status IN ('pending', 'enrolled', 'waitlist', 'suspended')
                LIMIT 1
                """,
                (TENANT_ID, student_profile_id, course_id, term_id),
            )
            existing = cur.fetchone()
            if existing:
                enrollment_id = existing[0]
            else:
                cur.execute(
                    """
                    INSERT INTO app_enrollments_enrollments
                      (tenant_id, student_profile_id, course_id, term_id, section_id, enrollment_status, enrollment_type, metadata_json, version, created_by, updated_by, created_at, updated_at)
                    VALUES
                      (%s, %s, %s, %s, %s, 'enrolled', 'regular', '{}'::jsonb, 1, 'demo.seed', 'demo.seed', NOW(), NOW())
                    RETURNING id
                    """,
                    (TENANT_ID, student_profile_id, course_id, term_id, section_ids_by_course[course_id]),
                )
                enrollment_id = cur.fetchone()[0]
                enrollment_count += 1

            if idx <= 12:
                numeric_grade = random.uniform(35, 48)
            elif idx <= 35:
                numeric_grade = random.uniform(50, 59)
            elif idx <= 65:
                numeric_grade = random.uniform(60, 72)
            else:
                numeric_grade = random.uniform(73, 96)

            student_best_grade = min(student_best_grade, numeric_grade)

            if numeric_grade >= 90:
                grade_code, grade_points = "A", 4.0
            elif numeric_grade >= 80:
                grade_code, grade_points = "B", 3.0
            elif numeric_grade >= 70:
                grade_code, grade_points = "C", 2.0
            elif numeric_grade >= 60:
                grade_code, grade_points = "D", 1.0
            else:
                grade_code, grade_points = "F", 0.0

            cur.execute(
                """
                INSERT INTO app_grades_submissions
                  (tenant_id, enrollment_id, grade_code, grade_points, grading_scale_id, submitted_by, submitted_at, version, metadata_json)
                VALUES
                  (%s, %s, %s, %s, %s, %s, NOW(), 1, '{}'::jsonb)
                ON CONFLICT (tenant_id, enrollment_id) DO UPDATE SET
                  grade_code = EXCLUDED.grade_code,
                  grade_points = EXCLUDED.grade_points,
                  grading_scale_id = EXCLUDED.grading_scale_id,
                  submitted_by = EXCLUDED.submitted_by,
                  submitted_at = NOW()
                """,
                (TENANT_ID, enrollment_id, grade_code, grade_points, scale_id, teacher_user_ids[(idx - 1) % len(teacher_user_ids)]),
            )
            grade_submission_count += 1

            cur.execute(
                """
                UPDATE app_enrollments_enrollments
                SET grade_code = %s,
                    grade_points = %s,
                    updated_by = 'demo.seed',
                    updated_at = NOW()
                WHERE tenant_id = %s AND id = %s
                """,
                (grade_code, grade_points, TENANT_ID, enrollment_id),
            )

        cur.execute(
            """
            INSERT INTO app_platform_context_entities
              (tenant_id, entity_type, entity_id, data_json, created_at, updated_at)
            VALUES
              (%s, 'student', %s, %s::jsonb, NOW(), NOW())
            ON CONFLICT (tenant_id, entity_type, entity_id) DO UPDATE SET
              data_json = EXCLUDED.data_json,
              updated_at = NOW()
            """,
            (
                TENANT_ID,
                student_number,
                json.dumps(
                    {
                        "name": f"Demo Student {idx}",
                        "email": f"{user_id}@example.local",
                        "student_profile_id": student_profile_id,
                    }
                ),
            ),
        )

        grade_entity_id = f"grade-{student_number}"
        cur.execute(
            """
            INSERT INTO app_platform_context_entities
              (tenant_id, entity_type, entity_id, data_json, created_at, updated_at)
            VALUES
              (%s, 'grade', %s, %s::jsonb, NOW(), NOW())
            ON CONFLICT (tenant_id, entity_type, entity_id) DO UPDATE SET
              data_json = EXCLUDED.data_json,
              updated_at = NOW()
            """,
            (
                TENANT_ID,
                grade_entity_id,
                json.dumps(
                    {
                        "grade_value": round(student_best_grade, 2),
                        "source": "demo_seed",
                        "recorded_at": datetime.now(timezone.utc).isoformat(),
                    }
                ),
            ),
        )

        cur.execute(
            """
            INSERT INTO app_platform_context_relations
              (tenant_id, source_entity_type, source_entity_id, relation_type, target_entity_type, target_entity_id, metadata_json, created_at)
            VALUES
              (%s, 'student', %s, 'has_grade', 'grade', %s, '{}'::jsonb, NOW())
            ON CONFLICT (tenant_id, source_entity_type, source_entity_id, relation_type, target_entity_type, target_entity_id)
            DO UPDATE SET metadata_json = '{}'::jsonb
            """,
            (TENANT_ID, student_number, grade_entity_id),
        )

        if student_best_grade < 50:
            severe_count += 1
            severe_students.append((student_profile_id, student_number, student_best_grade))
        if student_best_grade < 60:
            at_risk_count += 1
            at_risk_students.append((student_profile_id, student_number, student_best_grade))

    cur.execute(
        """
        INSERT INTO app_risk_thresholds
          (tenant_id, risk_category, rule_name, metric, threshold_value, comparison, severity_level, signal_type, enabled, auto_create_case, window_days, escalate_to_refs_json, created_at, updated_at)
        VALUES
          (%s, 'failed_assessment', 'demo_severe_grade', 'quiz_best_score', 50, 'lte', 'high', 'assessment_risk', true, true, 30, '["dean_office"]'::jsonb, NOW(), NOW())
        ON CONFLICT (tenant_id, rule_name) DO UPDATE SET
          threshold_value = EXCLUDED.threshold_value,
          severity_level = EXCLUDED.severity_level,
          enabled = true,
          updated_at = NOW()
        RETURNING id
        """,
        (TENANT_ID,),
    )
    severe_threshold_id = cur.fetchone()[0]

    cur.execute(
        """
        INSERT INTO app_risk_thresholds
          (tenant_id, risk_category, rule_name, metric, threshold_value, comparison, severity_level, signal_type, enabled, auto_create_case, window_days, escalate_to_refs_json, created_at, updated_at)
        VALUES
          (%s, 'failed_assessment', 'demo_risk_grade', 'quiz_best_score', 60, 'lte', 'medium', 'assessment_risk', true, true, 30, '["faculty_advisor"]'::jsonb, NOW(), NOW())
        ON CONFLICT (tenant_id, rule_name) DO UPDATE SET
          threshold_value = EXCLUDED.threshold_value,
          severity_level = EXCLUDED.severity_level,
          enabled = true,
          updated_at = NOW()
        RETURNING id
        """,
        (TENANT_ID,),
    )
    risk_threshold_id = cur.fetchone()[0]

    today = date.today()
    for student_profile_id, student_number, best_grade in at_risk_students:
        threshold_id = severe_threshold_id if best_grade < 50 else risk_threshold_id
        severity = "high" if best_grade < 50 else "medium"

        cur.execute(
            """
            INSERT INTO app_risk_signals
              (tenant_id, student_profile_id, threshold_id, signal_type, detected_at, detected_on, current_value, threshold_value, severity, signal_data_json)
            VALUES
              (%s, %s, %s, 'assessment_risk', NOW(), %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (tenant_id, student_profile_id, threshold_id, detected_on)
            DO UPDATE SET
              current_value = EXCLUDED.current_value,
              threshold_value = EXCLUDED.threshold_value,
              severity = EXCLUDED.severity,
              signal_data_json = EXCLUDED.signal_data_json,
              detected_at = NOW()
            """,
            (
                TENANT_ID,
                student_profile_id,
                threshold_id,
                today,
                float(best_grade),
                50.0 if severity == "high" else 60.0,
                severity,
                json.dumps({"student_number": student_number, "source": "demo_seed"}),
            ),
        )

    for student_profile_id, student_number, best_grade in severe_students[: min(20, len(severe_students))]:
        cur.execute(
            """
            INSERT INTO app_intervention_cases
              (tenant_id, case_type, student_profile_id, severity, status, title, description, risk_snapshot_json, assignee_type, assignee_ref, due_at, opened_at, metadata_json, version, created_by, updated_by, created_at, updated_at)
            VALUES
              (
                %s,
                'academic_risk',
                %s,
                'high',
                'open',
                %s,
                %s,
                %s::jsonb,
                'group',
                'dean_office',
                NOW() + interval '7 day',
                NOW(),
                '{}'::jsonb,
                1,
                'demo.seed',
                'demo.seed',
                NOW(),
                NOW()
              )
            ON CONFLICT DO NOTHING
            """,
            (
                TENANT_ID,
                student_profile_id,
                f"Academic risk escalation: {student_number}",
                "Grade below critical threshold; requires dean/advisor intervention.",
                json.dumps({"student_number": student_number, "best_grade": round(best_grade, 2)}),
            ),
        )
        if cur.rowcount > 0:
            case_count += 1

    event_counts = {
        "student.created": STUDENT_COUNT,
        "enrollment.created": max(enrollment_count, STUDENT_COUNT * 3),
        "grade.submitted": max(grade_submission_count, STUDENT_COUNT * 3),
    }
    total_events = int(sum(event_counts.values()))

    cur.execute(
        """
        INSERT INTO app_platform_tenant_kpi_snapshots
          (tenant_id, snapshot_date, event_counts_json, total_events, version)
        VALUES
          (%s, %s::date, %s::jsonb, %s, 1)
        ON CONFLICT (tenant_id, snapshot_date) DO UPDATE SET
          event_counts_json = EXCLUDED.event_counts_json,
          total_events = EXCLUDED.total_events,
          updated_at = NOW(),
          version = app_platform_tenant_kpi_snapshots.version + 1
        """,
        (TENANT_ID, today, json.dumps(event_counts), total_events),
    )

    # Assign academic roles for demo users in RBAC so dashboards switch by role.
    for user_id in dean_user_ids:
        cur.execute(
            """
        INSERT INTO app_user_roles (user_id, role_id, tenant_id)
        SELECT %s, r.id, %s
        FROM app_roles r
        WHERE r.tenant_id = %s AND r.name = 'dean'
        ON CONFLICT (user_id, role_id) DO NOTHING
            """,
        (user_id, TENANT_ID, TENANT_ID),
        )
    for user_id in teacher_user_ids:
        cur.execute(
            """
        INSERT INTO app_user_roles (user_id, role_id, tenant_id)
        SELECT %s, r.id, %s
        FROM app_roles r
        WHERE r.tenant_id = %s AND r.name = 'teacher'
        ON CONFLICT (user_id, role_id) DO NOTHING
            """,
        (user_id, TENANT_ID, TENANT_ID),
        )
    for user_id in student_user_ids:
        cur.execute(
            """
        INSERT INTO app_user_roles (user_id, role_id, tenant_id)
        SELECT %s, r.id, %s
        FROM app_roles r
        WHERE r.tenant_id = %s AND r.name = 'student'
        ON CONFLICT (user_id, role_id) DO NOTHING
            """,
        (user_id, TENANT_ID, TENANT_ID),
        )

conn.commit()
conn.close()

print(
    json.dumps(
        {
            "tenant_id": TENANT_ID,
            "students": STUDENT_COUNT,
            "teachers": TEACHER_COUNT,
            "deans": DEAN_COUNT,
            "at_risk_students": at_risk_count,
            "severe_risk_students": severe_count,
            "new_intervention_cases": case_count,
            "kpi_event_counts": event_counts,
        },
        ensure_ascii=True,
        indent=2,
    )
)
PY

echo "[pilot-seed-demo] done"
echo "[pilot-seed-demo] demo LDAP users: student_001..student_$(printf '%03d' "${STUDENT_COUNT}"), teacher_001..teacher_$(printf '%03d' "${TEACHER_COUNT}"), dean_01..dean_$(printf '%02d' "${DEAN_COUNT}")"
echo "[pilot-seed-demo] demo password: ${DEMO_PASSWORD}"
