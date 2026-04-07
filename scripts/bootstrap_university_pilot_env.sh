#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/infra/.env"
MAP_EXAMPLE="${ROOT_DIR}/infra/ldap_group_role_map.example.json"
MAP_FILE="${ROOT_DIR}/infra/ldap_group_role_map.json"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[pilot-bootstrap] FAIL: ${ENV_FILE} not found"
  echo "[pilot-bootstrap] hint: copy infra/.env.example to infra/.env first"
  exit 1
fi

if [[ ! -f "${MAP_EXAMPLE}" ]]; then
  echo "[pilot-bootstrap] FAIL: ${MAP_EXAMPLE} not found"
  exit 1
fi

TS="$(date +%Y%m%d_%H%M%S)"
cp "${ENV_FILE}" "${ENV_FILE}.bak.${TS}"

echo "[pilot-bootstrap] backup created: ${ENV_FILE}.bak.${TS}"

if [[ ! -f "${MAP_FILE}" ]]; then
  cp "${MAP_EXAMPLE}" "${MAP_FILE}"
  echo "[pilot-bootstrap] created ${MAP_FILE} from example"
else
  echo "[pilot-bootstrap] keeping existing ${MAP_FILE}"
fi

if ! grep -q '^LDAP_GROUP_ROLE_MAP_FILE=' "${ENV_FILE}"; then
  printf '\n# LDAP role mapping file for university pilot gate\nLDAP_GROUP_ROLE_MAP_FILE=./ldap_group_role_map.json\n' >> "${ENV_FILE}"
  echo "[pilot-bootstrap] appended LDAP_GROUP_ROLE_MAP_FILE"
else
  echo "[pilot-bootstrap] LDAP_GROUP_ROLE_MAP_FILE already set"
fi

if ! grep -q '^LDAP_GROUP_ROLE_MAP_JSON=' "${ENV_FILE}"; then
  printf 'LDAP_GROUP_ROLE_MAP_JSON={}\n' >> "${ENV_FILE}"
  echo "[pilot-bootstrap] appended LDAP_GROUP_ROLE_MAP_JSON={}"
else
  echo "[pilot-bootstrap] LDAP_GROUP_ROLE_MAP_JSON already set"
fi

echo "[pilot-bootstrap] DONE"
echo "[pilot-bootstrap] next step: make pilot-safe-gate"
