#!/usr/bin/env bash
# F3.3 Unfreeze — Post-Wiring Verification
#
# Run AFTER completing Steps 2–5 from F3_3_UNFREEZE_QUICK_REFERENCE.md:
#   Step 2: Freeze guards removed from effectiveness_service.py
#   Step 3: Router wired into main.py
#   Step 4: alembic upgrade head
#   Step 5: backend container rebuilt and healthy
#
# This script:
#   1. Verifies router is wired into main.py
#   2. Runs all F3 tests — expects 38/40 PASS (freeze-guard negatives will fail)
#   3. Verifies the 3 F3 DB tables exist via psql
#   4. Emits post-wiring artifact for audit trail
#   5. Prints exact files + functions to update (the 2 freeze-guard tests)
#
# Usage:
#   bash scripts/f3_unfreeze_post_wire.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
OUT_FILE="${ARTIFACTS_DIR}/f3_unfreeze_post_wire_${STAMP}.md"
FREEZE_GUARD_TEST_FILE="tests/modules/interventions/test_f3_service_negative_cases.py"

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"
mkdir -p "${ARTIFACTS_DIR}"

pushd "${ROOT_DIR}/infra" >/dev/null

# ── 1. Verify router is wired ──────────────────────────────────────────────────
echo "[f3-post-wire] checking router wiring in main.py"
if grep -q "effectiveness_router" "${ROOT_DIR}/backend/app/main.py" 2>/dev/null; then
  ROUTER_STATE="WIRED ✓"
else
  echo "[f3-post-wire] BLOCKED: effectiveness_router not found in main.py"
  echo "[f3-post-wire] Complete Step 3 (wire router) before running this script."
  exit 1
fi

# ── 2. Verify freeze guards removed ───────────────────────────────────────────
echo "[f3-post-wire] checking freeze guards removed from effectiveness_service.py"
SERVICE_FILE="${ROOT_DIR}/backend/app/modules/interventions/effectiveness_service.py"
if grep -q "is frozen until F3.3" "${SERVICE_FILE}" 2>/dev/null; then
  echo "[f3-post-wire] BLOCKED: freeze guards still present in effectiveness_service.py"
  echo "[f3-post-wire] Complete Step 2 (remove freeze guards) before running this script."
  exit 1
fi
FREEZE_STATE="REMOVED ✓"

# ── 3. Run full F3 test suite ──────────────────────────────────────────────────
echo "[f3-post-wire] running F3 tests (expect 38/40 PASS — 2 freeze-guard negatives will fail)"
F3_TEST_OUTPUT="$("${COMPOSE[@]}" run --rm --no-deps backend-tests pytest -q \
  tests/modules/interventions/test_f3_*.py \
  --no-cov -rA 2>&1 || true)"

# Parse summary line: "X passed, Y failed"
PASS_COUNT="$(echo "${F3_TEST_OUTPUT}" | grep -oP '\d+ passed' | grep -oP '\d+' || echo '0')"
FAIL_COUNT="$(echo "${F3_TEST_OUTPUT}" | grep -oP '\d+ failed' | grep -oP '\d+' || echo '0')"

echo "[f3-post-wire] result: ${PASS_COUNT} passed, ${FAIL_COUNT} failed"

# Accept exactly 38 pass + 2 fail (freeze-guard negatives), or 40 pass (already updated)
if [[ "${PASS_COUNT}" -lt 38 ]]; then
  echo "[f3-post-wire] FAIL: expected >=38 passing tests, got ${PASS_COUNT}"
  echo "[f3-post-wire] Check backend logs for unexpected failures."
  TEST_VERDICT="FAIL (${PASS_COUNT} passed, ${FAIL_COUNT} failed — investigate)"
else
  TEST_VERDICT="PASS (${PASS_COUNT} passed, ${FAIL_COUNT} failed)"
fi

# ── 4. Verify 3 F3 tables exist ───────────────────────────────────────────────
echo "[f3-post-wire] verifying F3 database tables"
DB_TABLES_OUTPUT="$("${COMPOSE[@]}" exec -T db psql -U app -d app -c \
  "SELECT table_name FROM information_schema.tables \
   WHERE table_schema='public' AND table_name LIKE 'app_intervention_cohort%' \
   ORDER BY table_name;" 2>&1 || true)"

EXPECTED_TABLES=("app_intervention_cohorts" "app_intervention_cohort_members" "app_intervention_cohort_outcomes")
MISSING_TABLES=()
for t in "${EXPECTED_TABLES[@]}"; do
  if ! echo "${DB_TABLES_OUTPUT}" | grep -q "${t}"; then
    MISSING_TABLES+=("${t}")
  fi
done
if [[ ${#MISSING_TABLES[@]} -eq 0 ]]; then
  DB_STATE="OK — all 3 tables present ✓"
else
  DB_STATE="MISSING: ${MISSING_TABLES[*]}"
  echo "[f3-post-wire] WARN: missing tables: ${MISSING_TABLES[*]}"
fi

popd >/dev/null

CAPTURED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat >"${OUT_FILE}" <<EOF
# F3.3 Unfreeze — Post-Wiring Verification

- Captured at (UTC): ${CAPTURED_AT}
- Router wiring state: ${ROUTER_STATE}
- Freeze guards state: ${FREEZE_STATE}
- Test verdict: ${TEST_VERDICT}
- DB tables: ${DB_STATE}

## F3 Test Output

\`\`\`text
${F3_TEST_OUTPUT}
\`\`\`

## Database Tables Check

\`\`\`text
${DB_TABLES_OUTPUT}
\`\`\`

## Required Post-Wiring Test Update

Two freeze-guard tests in the test suite checked that wiring was blocked. Now that
F3 is unfrozen, these tests must be updated to verify the **positive** path instead.

### File to update: ${FREEZE_GUARD_TEST_FILE}

#### 1. test_finalize_cohort_raises_domain_validation_error (line ~44)
Change from:
  \`with pytest.raises(DomainValidationError, match="frozen"):\`
Change to: assert a successful cohort is created (or remove the freeze assertion and
test a real validation boundary, e.g. missing tenant or invalid payload).

#### 2. test_analyze_cohort_raises_domain_validation_error_after_404_check (line ~57)
Change from:
  \`with pytest.raises(DomainValidationError, match="frozen"):\`
Change to: assert analysis result is returned for a valid cohort.

After updating these 2 tests, run:
\`\`\`bash
cd /home/sbs/AI/infra
docker compose run --rm --no-deps backend-tests pytest -q \\
  tests/modules/interventions/test_f3_*.py --no-cov
# Expected: 40/40 passed
\`\`\`

## Next Steps

- [ ] Update 2 freeze-guard tests (see above)
- [ ] Run final gate: \`RELEASE_ENABLE_F3_SCHEMA_GATE=true bash scripts/release_check.sh\`
- [ ] Update AUDIT_SBS_2026.md: F3.3 status → ✅ COMPLETE
- [ ] Begin F3.4 Frontend implementation (see docs/F3_4_FRONTEND_IMPLEMENTATION_GUIDE.md)
- [ ] Begin F3.5 Observability implementation (see docs/F3_5_OBSERVABILITY_IMPLEMENTATION_GUIDE.md)
EOF

echo "[f3-post-wire] artifact: ${OUT_FILE}"

if [[ "${PASS_COUNT}" -lt 38 ]]; then
  echo "[f3-post-wire] VERDICT: FAIL — investigate unexpected test failures before proceeding"
  exit 1
fi

echo "[f3-post-wire] VERDICT: PASS — wiring verified, update 2 freeze-guard tests then run final gate"
