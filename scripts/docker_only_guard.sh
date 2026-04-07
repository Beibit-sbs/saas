#!/usr/bin/env bash
set -euo pipefail

# Hard preflight guard: prevent mixed runtime (Docker + host dev servers).

if ! command -v docker >/dev/null 2>&1; then
  echo "[guard] FAIL: docker CLI not found"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "[guard] FAIL: docker daemon is not reachable"
  exit 1
fi

if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  echo "[guard] FAIL: active Python virtualenv detected: ${VIRTUAL_ENV}"
  echo "[guard] Deactivate it first: deactivate"
  exit 1
fi

if [[ "${DOCKER_ONLY_GUARD_SKIP_PROCESS_CHECK:-0}" == "1" ]]; then
  echo "[guard] WARN: process check skipped by DOCKER_ONLY_GUARD_SKIP_PROCESS_CHECK=1"
  exit 0
fi

PROHIBITED_REGEX='(uvicorn|hypercorn|gunicorn .*app\.main|next dev|vite( |$)|webpack-dev-server|npm run dev|pnpm dev|yarn dev)'
RAW_PROCS="$(ps -eo pid=,args= | rg -i "${PROHIBITED_REGEX}" | rg -vi "docker|container|guard|rg -i|grep -E" || true)"

# Filter out processes that are running inside Docker/container cgroups (they appear
# on the host as root-owned processes but are NOT host-native dev servers).
HOST_DEV_PROCS=""
while IFS= read -r line; do
  [[ -z "${line}" ]] && continue
  pid="${line%% *}"
  cgroup="$(cat "/proc/${pid}/cgroup" 2>/dev/null || true)"
  if echo "${cgroup}" | grep -qE "docker-|kubepods|lxc"; then
    continue  # container process — not a host dev server
  fi
  HOST_DEV_PROCS="${HOST_DEV_PROCS}${line}"$'\n'
done <<< "${RAW_PROCS}"
HOST_DEV_PROCS="${HOST_DEV_PROCS%$'\n'}"

if [[ -n "${HOST_DEV_PROCS}" ]]; then
  echo "[guard] FAIL: host dev processes detected (mixed mode is forbidden):"
  echo "${HOST_DEV_PROCS}"
  echo "[guard] Stop these processes, then run docker commands again."
  exit 1
fi

echo "[guard] OK: docker-only mode confirmed"
