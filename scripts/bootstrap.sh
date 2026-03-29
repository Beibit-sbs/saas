#!/usr/bin/env bash
set -euo pipefail

# User-space bootstrap only: installs project dependencies without sudo.

ensure_npm() {
  if command -v npm >/dev/null 2>&1; then
    return
  fi

  if [[ -s "$HOME/.nvm/nvm.sh" ]]; then
    # Load nvm for shells where Node is installed in user-space only.
    # shellcheck disable=SC1090
    source "$HOME/.nvm/nvm.sh"
    nvm use --lts >/dev/null || true
  fi

  if ! command -v npm >/dev/null 2>&1; then
    echo "npm not found. Install Node.js/npm (system) or nvm (user-space)."
    exit 1
  fi
}

if [[ -d "backend" ]]; then
  python3 -m venv backend/.venv
  source backend/.venv/bin/activate
  pip install --upgrade pip
  pip install -r backend/requirements.txt
  if [[ -n "${DATABASE_URL:-}" ]]; then
    (
      cd backend
      alembic upgrade head
    )
  else
    echo "DATABASE_URL not set; skipping backend migrations."
  fi
  deactivate
fi

if [[ -d "frontend" ]]; then
  ensure_npm
  cd frontend
  npm install
  cd - >/dev/null
fi

echo "Bootstrap complete."
