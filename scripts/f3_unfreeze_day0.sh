#!/usr/bin/env bash
# F3.3 Unfreeze — Day-0 Readiness Capture
#
# Run BEFORE manual wiring (Steps 2–3 from F3_3_UNFREEZE_QUICK_REFERENCE.md).
# Confirms Gate 0 passes, verifies skeleton tests are green, and emits an
# immutable pre-wiring baseline artifact for audit trail.
#
# Usage:
#   bash scripts/f3_unfreeze_day0.sh
#
# Optional env:
#   F3_SCHEMA_SIGNOFF_FILE=/path/to/signed.md   — override gate artifact path
#   DOCKER_ONLY_GUARD_SKIP_PROCESS_CHECK=1       — skip local-process guard in dev
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
OUT_FILE="${ARTIFACTS_DIR}/f3_unfreeze_day0_baseline_${STAMP}.md"

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"
mkdir -p "${ARTIFACTS_DIR}"

pushd "${ROOT_DIR}/infra" >/dev/null

# ── Gate 0: F3.2 Schema Approval ───────────────────────────────────────────────
echo "[f3-day0] running Gate 0: F3.2 schema approval"
if ! bash "${ROOT_DIR}/scripts/f3_schema_review_gate.sh"; then
  echo "[f3-day0] BLOCKED: Gate 0 failed — complete schema approval before unfreeze"
  exit 1
fi
GATE_RESULT="PASS"

# ── Step 1a: docker services health ────────────────────────────────────────────
echo "[f3-day0] checking docker compose service health"
DOCKER_PS_OUTPUT="$("${COMPOSE[@]}" ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}' 2>&1)"

# ── Step 1b: alembic current ───────────────────────────────────────────────────
echo "[f3-day0] checking alembic migration state"
ALEMBIC_CURRENT="$("${COMPOSE[@]}" run --rm --no-deps -e DATABASE_URL= backend-tests alembic current 2>&1 || true)"
ALEMBIC_HEADS="$("${COMPOSE[@]}" run --rm --no-deps -e DATABASE_URL= backend-tests alembic heads 2>&1 || true)"

# ── Step 1c: F3 skeleton tests (40/40 expected pre-wiring) ─────────────────────
echo "[f3-day0] running F3 skeleton tests (pre-wiring baseline)"
F3_TEST_OUTPUT="$("${COMPOSE[@]}" run --rm --no-deps backend-tests pytest -q \
  tests/modules/interventions/test_f3_*.py \
  --no-cov -rA 2>&1)"

# ── Verify router is NOT wired yet (expected pre-wiring state) ─────────────────
echo "[f3-day0] verifying router is not yet wired into main.py"
if grep -q "effectiveness_router" "${ROOT_DIR}/backend/app/main.py" 2>/dev/null; then
  ROUTER_STATE="ALREADY_WIRED — run this script before wiring for a clean baseline"
else
  ROUTER_STATE="NOT_WIRED (expected pre-wiring state)"
fi

popd >/dev/null

# ── Emit baseline artifact ─────────────────────────────────────────────────────
DAY0_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat >"${OUT_FILE}" <<EOF
# F3.3 Unfreeze — Day-0 Pre-Wiring Baseline

- Captured at (UTC): ${DAY0_UTC}
- Scope: F3.3 pre-wiring readiness snapshot
- Gate 0 (F3.2 schema approval): ${GATE_RESULT}
- Router wiring state: ${ROUTER_STATE}

## Gate 0 Output

\`\`\`text
$(bash "${ROOT_DIR}/scripts/f3_schema_review_gate.sh" 2>&1 || true)
\`\`\`

## Docker Compose Service Health

\`\`\`text
${DOCKER_PS_OUTPUT}
\`\`\`

## Alembic State

### alembic current
\`\`\`text
${ALEMBIC_CURRENT}
\`\`\`

### alembic heads
\`\`\`text
${ALEMBIC_HEADS}
\`\`\`

## F3 Skeleton Tests (pre-wiring)

\`\`\`text
${F3_TEST_OUTPUT}
\`\`\`

## Next Steps (after this script passes)

1. Remove freeze guards from \`backend/app/modules/interventions/effectiveness_service.py\`:
   - \`finalize_cohort()\`: delete the \`raise DomainValidationError("F3 finalize_cohort is frozen...")\` line
   - \`analyze_cohort()\`: delete the \`raise DomainValidationError("F3 analyze_cohort is frozen...")\` line

2. Wire router into \`backend/app/main.py\`:
   - Add import: \`from app.modules.interventions.effectiveness_router import router as effectiveness_router\`
   - Add: \`app.include_router(effectiveness_router)\`

3. Apply migration and rebuild:
   \`\`\`bash
   cd /home/sbs/AI/infra
   docker compose exec backend alembic upgrade head
   docker compose build --no-cache backend && docker compose up -d backend
   \`\`\`

4. Post-wiring verification:
   \`\`\`bash
   RELEASE_ENABLE_F3_SCHEMA_GATE=true bash scripts/release_check.sh
   \`\`\`

See full day-of command card: docs/runbooks/artifacts/F3_3_UNFREEZE_QUICK_REFERENCE.md
EOF

echo "[f3-day0] baseline artifact: ${OUT_FILE}"
echo "[f3-day0] READY — Gate 0 PASS, skeleton tests verified, proceed with manual wiring (Steps 2–3)"
