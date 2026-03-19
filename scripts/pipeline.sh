#!/usr/bin/env bash
set -euo pipefail

# End-to-end local pipeline: install deps, lint, test, build, run stack, check health.

if [[ ! -f "infra/.env" ]]; then
  echo "infra/.env not found. Copy infra/.env.example first."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  if [[ -s "$HOME/.nvm/nvm.sh" ]]; then
    # shellcheck disable=SC1090
    source "$HOME/.nvm/nvm.sh"
    nvm use --lts >/dev/null || true
  fi
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found. Install Node.js/npm or configure nvm."
  exit 1
fi

./scripts/bootstrap.sh

pushd backend >/dev/null
source .venv/bin/activate
ruff check .
pytest -q
pytest -q tests/test_template_validation.py
deactivate
popd >/dev/null

pushd frontend >/dev/null
npm run i18n:check
npm run lint
npm run build
npm run test:frontend
popd >/dev/null

pushd infra >/dev/null
docker compose --env-file .env up -d --build
popd >/dev/null

sleep 5
curl -fsS http://localhost:8000/health >/dev/null
curl -fsS http://localhost/api/health >/dev/null

echo "Pipeline OK: services are up and backend health is reachable."
