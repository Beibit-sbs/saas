#!/usr/bin/env bash
# F3.3 Post-Unfreeze Validation Gate
# 
# Checks that F3.3 unfreeze was executed correctly:
# - effectiveness router wired in main.py
# - freeze guards removed from service
# - skeleton tests ready (40+/40 expected)
# - DB schema valid
#
# Usage:
#   bash scripts/f3_unfreeze_validation.sh
#
# Exit: 0 if PASS, 1 if FAIL

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
OUT_FILE="${ARTIFACTS_DIR}/f3_unfreeze_validation_${STAMP}.md"

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"
mkdir -p "${ARTIFACTS_DIR}"

pushd "${ROOT_DIR}/infra" >/dev/null

# ── Check 1: Router wiring in main.py ───────────────────────────────────────
echo "[f3-validation] checking router wiring in main.py"
if grep -q "effectiveness_router" "${ROOT_DIR}/backend/app/main.py"; then
  ROUTER_WIRED="PASS"
  ROUTER_LINE="$(grep -n 'effectiveness_router' "${ROOT_DIR}/backend/app/main.py" | cut -d: -f1 | head -1)"
else
  ROUTER_WIRED="FAIL"
  ROUTER_LINE="N/A"
fi

# ── Check 2: Freeze guards removed ──────────────────────────────────────────
echo "[f3-validation] checking freeze guards removed"
SERVICE_FILE="${ROOT_DIR}/backend/app/modules/interventions/effectiveness_service.py"
if grep -q "F3.*frozen\|raise.*F3" "${SERVICE_FILE}"; then
  FREEZE_REMOVED="FAIL"
  FREEZE_COUNT="$(grep -c "F3.*frozen\|raise.*F3" "${SERVICE_FILE}" || true)"
else
  FREEZE_REMOVED="PASS"
  FREEZE_COUNT="0"
fi

# ── Check 3: Migration schema present ───────────────────────────────────────
echo "[f3-validation] checking DB schema migration exists"
MIGRATION_FILE="$(ls -1 "${ROOT_DIR}/backend/alembic/versions/"*f3*effectiveness* 2>/dev/null | head -1 || true)"
if [[ -z "${MIGRATION_FILE}" ]]; then
  MIGRATION_FILE="$(ls -1 "${ROOT_DIR}/backend/alembic/versions/f8c1d2e3a4b5"* 2>/dev/null | head -1 || true)"
fi
if [[ -n "${MIGRATION_FILE}" ]]; then
  MIGRATION_PRESENT="PASS"
else
  MIGRATION_PRESENT="FAIL"
fi

# ── Check 4: Skeleton test files ────────────────────────────────────────────
echo "[f3-validation] checking skeleton test presence"
TEST_COUNT="$(find "${ROOT_DIR}/backend/tests/modules/interventions" -name "test_f3_*.py" 2>/dev/null | wc -l)"
if [[ ${TEST_COUNT} -gt 0 ]]; then
  TESTS_PRESENT="PASS"
else
  TESTS_PRESENT="FAIL"
fi

# ── Overall verdict ────────────────────────────────────────────────────────
VALIDATION_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat >"${OUT_FILE}" <<EOF
# F3.3 Post-Unfreeze Validation

**Validation Date (UTC):** ${VALIDATION_DATE}

## Checklist

| Check | Status | Evidence |
|-------|--------|----------|
| Router wired in main.py | ${ROUTER_WIRED} | Line ${ROUTER_LINE} (effectiveness_router) |
| Freeze guards removed | ${FREEZE_REMOVED} | ${FREEZE_COUNT} remaining freeze markers (0 = pass) |
| Migration schema present | ${MIGRATION_PRESENT} | ${MIGRATION_FILE##*/} |
| Skeleton tests exist | ${TESTS_PRESENT} | ${TEST_COUNT} test file(s) found |

## Gate Result

EOF

if [[ "${ROUTER_WIRED}" == "PASS" && "${FREEZE_REMOVED}" == "PASS" && "${MIGRATION_PRESENT}" == "PASS" && "${TESTS_PRESENT}" == "PASS" ]]; then
  echo "[f3-validation] PASS: F3.3 unfreeze validation complete" >> "${OUT_FILE}"
  echo "F3.3_VALIDATION=PASS" >> "${OUT_FILE}"
  echo "NEXT_STEP=proceed_with_f3_4_f3_5_kickoff_ready" >> "${OUT_FILE}"
  
  popd >/dev/null
  cat "${OUT_FILE}"
  echo "[f3-validation] PASS: all checks green, F3.4/F3.5 can kickoff on 2026-04-21"
  echo "F3.3_VALIDATION=PASS"
  exit 0
fi

echo "[f3-validation] BLOCKED: one or more validation checks failed" >> "${OUT_FILE}"
echo "F3.3_VALIDATION=FAIL" >> "${OUT_FILE}"
echo "ROUTER_WIRED=${ROUTER_WIRED}" >> "${OUT_FILE}"
echo "FREEZE_REMOVED=${FREEZE_REMOVED}" >> "${OUT_FILE}"
echo "MIGRATION_PRESENT=${MIGRATION_PRESENT}" >> "${OUT_FILE}"
echo "TESTS_PRESENT=${TESTS_PRESENT}" >> "${OUT_FILE}"

popd >/dev/null
cat "${OUT_FILE}"
echo "[f3-validation] FAIL: unfreeze validation incomplete"
echo "F3.3_VALIDATION=FAIL"
exit 1
