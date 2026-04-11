#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

run_backend_checks() {
  "${COMPOSE[@]}" run --rm --no-deps backend-tests "$@"
}

FRONTEND_DOMAIN_TESTS=(
  "__tests__/admin/AdmissionsPage.test.tsx"
  "__tests__/admin/CoursesPage.test.tsx"
  "__tests__/admin/EnrollmentsPage.test.tsx"
  "__tests__/admin/FacultyPage.test.tsx"
  "__tests__/admin/GradesPage.test.tsx"
  "__tests__/admin/ProgramsPage.test.tsx"
  "__tests__/admin/SchedulingPage.test.tsx"
  "__tests__/admin/StudentDetailPage.test.tsx"
  "__tests__/admin/StudentsPage.test.tsx"
  "__tests__/admin/TranscriptsPageList.test.tsx"
)

bash "${ROOT_DIR}/scripts/preflight_checks.sh"

pushd "${ROOT_DIR}/infra" >/dev/null
"${COMPOSE[@]}" up -d db redis

echo "[domain-gate] backend domain services and routers"
run_backend_checks pytest -q --disable-warnings \
  tests/modules/admissions/ \
  tests/modules/students/ \
  tests/modules/enrollments/ \
  tests/modules/grades/ \
  tests/modules/scheduling/ \
  tests/modules/transcripts/ \
  tests/modules/degree_progress/ \
  tests/modules/org_structure/ \
  tests/modules/interventions/

echo "[domain-gate] domain tenant safety invariants"
run_backend_checks pytest -q --disable-warnings \
  tests/modules/admissions/test_tenant_isolation.py \
  tests/test_saas_tenant_cross_user_isolation.py \
  tests/test_tenant_fail_closed.py \
  tests/test_tenant_fail_closed_schema.py

echo "[domain-gate] frontend domain workflows"
"${COMPOSE[@]}" run --rm frontend-tests npm run test:frontend -- "${FRONTEND_DOMAIN_TESTS[@]}"

popd >/dev/null

echo "[domain-gate] PASS: educational domain checks are green"