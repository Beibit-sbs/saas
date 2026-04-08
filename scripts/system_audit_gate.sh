#!/usr/bin/env bash
set -euo pipefail

# One-shot full quality/security gate for local validation.
# Safe mode: does not reset volumes and does not mutate DB schema beyond normal app startup.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

bash "${ROOT_DIR}/scripts/preflight_checks.sh"

pushd "${ROOT_DIR}/infra" >/dev/null

"${COMPOSE[@]}" up -d db redis backend frontend nginx

# Backend gates
"${COMPOSE[@]}" exec -T backend ruff check .
"${COMPOSE[@]}" run --rm --no-deps backend-tests pytest -q --disable-warnings

# RBAC parity guardrail
"${ROOT_DIR}/scripts/check_permission_parity.sh"

# Frontend gates
"${COMPOSE[@]}" run --rm -T frontend-tests npm run lint
"${COMPOSE[@]}" run --rm -T frontend-tests npm run test:frontend

popd >/dev/null

echo "[system-audit] OK: backend/frontend lint+tests and RBAC parity checks passed."
