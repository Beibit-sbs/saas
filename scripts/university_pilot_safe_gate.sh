#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE=(docker compose --env-file .env)

require_env_in_file() {
  local env_file="$1"
  local key="$2"
  local value

  value="$(grep -E "^${key}=" "${env_file}" | tail -n1 | cut -d'=' -f2- || true)"
  if [[ -z "${value}" ]]; then
    echo "[pilot-safe-gate] FAIL: ${key} is missing in ${env_file}"
    return 1
  fi
}

get_env_from_file() {
  local env_file="$1"
  local key="$2"
  grep -E "^${key}=" "${env_file}" | tail -n1 | cut -d'=' -f2- || true
}

echo "[pilot-safe-gate] starting non-destructive university pilot gate"
bash "${ROOT_DIR}/scripts/preflight_checks.sh"

ENV_FILE="${ROOT_DIR}/infra/.env"
require_env_in_file "${ENV_FILE}" "JWT_SECRET"

LDAP_MAP_RAW="$(get_env_from_file "${ENV_FILE}" "LDAP_GROUP_ROLE_MAP_JSON")"
LDAP_MAP_FILE="$(get_env_from_file "${ENV_FILE}" "LDAP_GROUP_ROLE_MAP_FILE")"
LDAP_MAP_SOURCE="LDAP_GROUP_ROLE_MAP_JSON"

if [[ -z "${LDAP_MAP_RAW}" || "${LDAP_MAP_RAW}" == "{}" || "${LDAP_MAP_RAW}" == '"{}"' ]]; then
  if [[ -n "${LDAP_MAP_FILE}" ]]; then
    LDAP_MAP_FILE="${LDAP_MAP_FILE%\"}"
    LDAP_MAP_FILE="${LDAP_MAP_FILE#\"}"
    if [[ "${LDAP_MAP_FILE}" != /* ]]; then
      LDAP_MAP_FILE="${ROOT_DIR}/infra/${LDAP_MAP_FILE}"
    fi
    if [[ ! -f "${LDAP_MAP_FILE}" ]]; then
      echo "[pilot-safe-gate] FAIL: LDAP_GROUP_ROLE_MAP_FILE points to missing file: ${LDAP_MAP_FILE}"
      exit 1
    fi
    LDAP_MAP_RAW="$(cat "${LDAP_MAP_FILE}")"
    LDAP_MAP_SOURCE="LDAP_GROUP_ROLE_MAP_FILE (${LDAP_MAP_FILE})"
  fi
fi

if [[ -z "${LDAP_MAP_RAW}" || "${LDAP_MAP_RAW}" == "{}" || "${LDAP_MAP_RAW}" == '"{}"' ]]; then
  echo "[pilot-safe-gate] FAIL: provide non-empty LDAP mapping via LDAP_GROUP_ROLE_MAP_JSON or LDAP_GROUP_ROLE_MAP_FILE"
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  if ! LDAP_MAP_RAW="${LDAP_MAP_RAW}" python3 - <<'PY'
import json
import os

raw = os.environ.get("LDAP_MAP_RAW", "")
if not raw:
    raise SystemExit(1)

raw = raw.strip()
if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
    raw = raw[1:-1]

obj = json.loads(raw)
if not isinstance(obj, dict) or len(obj) == 0:
    raise SystemExit(1)

required_roles = {
  "platform_admin",
  "institution_admin",
  "academic_admin",
  "it_support",
  "developer",
  "ops_engineer",
}
mapped_roles = set()
for value in obj.values():
  if isinstance(value, str):
    mapped_roles.add(value)
  elif isinstance(value, list):
    mapped_roles.update(v for v in value if isinstance(v, str))

missing = sorted(required_roles - mapped_roles)
if missing:
  print("missing required pilot roles in LDAP mapping:", ", ".join(missing))
  raise SystemExit(1)
PY
  then
  echo "[pilot-safe-gate] FAIL: LDAP mapping from ${LDAP_MAP_SOURCE} is invalid or incomplete"
    exit 1
  fi
fi

echo "[pilot-safe-gate] LDAP mapping source: ${LDAP_MAP_SOURCE}"

pushd "${ROOT_DIR}/infra" >/dev/null

echo "[pilot-safe-gate] ensuring core dependencies are available"
"${COMPOSE[@]}" up -d db redis

run_backend_checks() {
  "${COMPOSE[@]}" run --rm --no-deps backend-tests "$@"
}

echo "[pilot-safe-gate] tenant isolation and architecture guardrails"
run_backend_checks pytest -q tests/platform/test_platform_tenant_safety_audit_v1.py
run_backend_checks pytest -q tests/platform/test_platform_architecture_guardrails_v1.py

echo "[pilot-safe-gate] readiness and auth regression checks"
run_backend_checks pytest -q tests/test_sre_ops_layer.py tests/test_auth.py

echo "[pilot-safe-gate] frontend security/middleware gate"
"${COMPOSE[@]}" run --rm frontend-tests npm run lint
"${COMPOSE[@]}" run --rm frontend-tests npm run test:frontend -- __tests__/security/middleware.test.ts

popd >/dev/null

echo "[pilot-safe-gate] PASS: non-destructive pilot gate is green"
echo "[pilot-safe-gate] next recommended step: bash scripts/release_gate.sh"