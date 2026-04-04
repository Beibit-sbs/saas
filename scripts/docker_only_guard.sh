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
HOST_DEV_PROCS="$(ps -eo pid=,args= | rg -i "${PROHIBITED_REGEX}" | rg -vi "docker|container|guard|rg -i|grep -E" || true)"

if [[ -n "${HOST_DEV_PROCS}" ]]; then
  echo "[guard] FAIL: host dev processes detected (mixed mode is forbidden):"
  echo "${HOST_DEV_PROCS}"
  echo "[guard] Stop these processes, then run docker commands again."
  exit 1
fi

echo "[guard] OK: docker-only mode confirmed"
