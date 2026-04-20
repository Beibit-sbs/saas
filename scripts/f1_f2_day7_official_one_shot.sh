#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

echo "[day7-one-shot] running official F1 day7 review"
bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_day_review.sh" --phase day7

echo "[day7-one-shot] running official F2 day7 review"
bash "${ROOT_DIR}/scripts/f2_playbooks_post_release_day_review.sh" --phase day7

echo "[day7-one-shot] validating post-release gates"
bash "${ROOT_DIR}/scripts/risk_phase_f1_post_release_gate.sh"
bash "${ROOT_DIR}/scripts/f2_playbooks_post_release_gate.sh"

echo "[day7-one-shot] generating final DoD sign-off artifacts"
bash "${ROOT_DIR}/scripts/f1_risk_dod_signoff.sh"
bash "${ROOT_DIR}/scripts/f2_playbooks_dod_signoff.sh"

echo "[day7-one-shot] PASS: official F1/F2 day7 + sign-off flow completed"
