#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="${ROOT_DIR}/scripts"

echo "=========================================="
echo "F1/F2 Day7 Pre-Execution Validation"
echo "Date: $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VALIDATION_PASS=0
VALIDATION_FAIL=0

check_item() {
  local name=$1
  local check=$2
  
  if eval "$check" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} $name"
    ((VALIDATION_PASS+=1))
    return 0
  else
    echo -e "${RED}✗${NC} $name"
    ((VALIDATION_FAIL+=1))
    # Keep scanning to report all issues in one run.
    return 0
  fi
}

check_warn() {
  local name=$1
  local check=$2
  
  if eval "$check" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} $name"
    return 0
  else
    echo -e "${YELLOW}⚠${NC} $name (non-blocking)"
    return 0
  fi
}

# ========== ENVIRONMENT CHECKS ==========
echo "🔍 Environment Setup"
echo "---"

check_item "Working directory accessible" "[[ -d '$ROOT_DIR' ]]"
check_item "Docker daemon running" "docker ps > /dev/null 2>&1"
check_item "Docker compose available" "docker compose version > /dev/null 2>&1"

# ========== SCRIPT CHECKS ==========
echo ""
echo "🔍 Required Scripts Exist & Executable"
echo "---"

REQUIRED_SCRIPTS=(
  "docker_only_guard.sh"
  "f1_f2_day7_official_one_shot.sh"
  "risk_phase_f1_post_release_day_review.sh"
  "f2_playbooks_post_release_day_review.sh"
  "risk_phase_f1_post_release_gate.sh"
  "f2_playbooks_post_release_gate.sh"
  "f1_risk_dod_signoff.sh"
  "f2_playbooks_dod_signoff.sh"
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
  check_item "Script exists: $script" "[[ -f '$SCRIPT_DIR/$script' ]]"
  check_item "Script executable: $script" "[[ -x '$SCRIPT_DIR/$script' ]]"
done

# ========== DOCKER-ONLY GUARD CHECK ==========
echo ""
echo "🔍 Docker-Only Guard"
echo "---"

# Check if host dev processes exist (should be none)
HOST_PROCS=$("$SCRIPT_DIR/docker_only_guard.sh" 2>&1 || true)
if echo "$HOST_PROCS" | grep -q "host dev process"; then
  echo -e "${YELLOW}⚠${NC} Found host dev processes (should be killed before day7 run)"
  echo "   Processes: $(echo "$HOST_PROCS" | grep -o 'uvicorn\|next dev\|vite\|webpack' | sort -u | tr '\n' ', ')"
  ((VALIDATION_FAIL+=1))
else
  echo -e "${GREEN}✓${NC} No host dev processes detected (docker-only mode)"
  ((VALIDATION_PASS+=1))
fi

# ========== COMPOSE STACK CHECK ==========
echo ""
echo "🔍 Docker Compose Stack"
echo "---"

check_item "infra/.env exists" "[[ -f '$ROOT_DIR/infra/.env' ]]"
check_item "docker-compose.yml exists" "[[ -f '$ROOT_DIR/infra/docker-compose.yml' ]]"

# Dry-run compose config (no actual startup)
check_item "Docker compose config valid" "docker compose -f '$ROOT_DIR/infra/docker-compose.yml' --env-file '$ROOT_DIR/infra/.env' config > /dev/null 2>&1"

# ========== DEPENDENCY CHECKS ==========
echo ""
echo "🔍 Required Dependencies"
echo "---"

check_warn "PostgreSQL image available locally" "docker image inspect postgres:16 > /dev/null 2>&1"
check_warn "Redis image available locally" "docker image inspect redis:7 > /dev/null 2>&1"
check_item "Python available (for test execution)" "python3 --version > /dev/null 2>&1"
check_warn "jq available (for JSON parsing in gates)" "command -v jq > /dev/null 2>&1"

# ========== GATE SCRIPT STRUCTURE CHECKS ==========
echo ""
echo "🔍 Gate Script Structure"
echo "---"

# Check F1 gate script has expected functions/patterns
check_item "F1 gate has exit code check" "grep -q 'F1.9_GATE=' '$SCRIPT_DIR/risk_phase_f1_post_release_gate.sh'"
check_item "F2 gate has exit code check" "grep -q 'F2.9_GATE=' '$SCRIPT_DIR/f2_playbooks_post_release_gate.sh'"

# Check sign-off scripts have expected patterns
check_item "F1 sign-off guarded by F1.9 gate" "grep -q 'F1.9_GATE' '$SCRIPT_DIR/f1_risk_dod_signoff.sh'"
check_item "F2 sign-off guarded by F2.9 gate" "grep -q 'F2.9_GATE' '$SCRIPT_DIR/f2_playbooks_dod_signoff.sh'"

# ========== CHECKLIST ARTIFACT CHECK ==========
echo ""
echo "🔍 Day7 Review Artifacts"
echo "---"

check_item "Day7 review checklist exists" "[[ -f '$ROOT_DIR/docs/F1_F2_DAY7_REVIEW_CHECKLIST.md' ]]"
check_item "Day7 runbook exists" "[[ -f '$ROOT_DIR/docs/runbooks/F1_RISK_POST_RELEASE_VALIDATION.md' ]] || compgen -G '$ROOT_DIR/docs/runbooks/F1_*.md' > /dev/null"

# ========== AUDIT REGISTRY CHECK ==========
echo ""
echo "🔍 Audit Registry"
echo "---"

check_item "Audit file exists" "[[ -f '$ROOT_DIR/docs/AUDIT_SBS_2026.md' ]]"
check_item "Day7 entry in audit" "grep -q 'day7\|F1.9\|F2.9' '$ROOT_DIR/docs/AUDIT_SBS_2026.md'"

# ========== FINAL SUMMARY ==========
echo ""
echo "=========================================="
TOTAL=$((VALIDATION_PASS + VALIDATION_FAIL))
PASS_PERCENT=$((VALIDATION_PASS * 100 / TOTAL))

echo -e "Validation Results: ${GREEN}${VALIDATION_PASS}/${TOTAL}${NC} checks passed (${PASS_PERCENT}%)"

if [[ $VALIDATION_FAIL -eq 0 ]]; then
  echo -e "Status: ${GREEN}✓ READY${NC} for day7 execution"
  echo ""
  echo "Next Steps:"
  echo "  1. Review F1_F2_DAY7_REVIEW_CHECKLIST.md for manual review items"
  echo "  2. On 2026-04-20, run: make day7-f1f2-one-shot"
  echo "  3. Monitor for any gate failures"
  echo ""
  echo "Expected Timeline:"
  echo "  - Day 7 review execution: ~30-45 minutes"
  echo "  - Gate + sign-off: ~15-20 minutes"
  echo "  - Total: ~1 hour"
  echo ""
  exit 0
else
  echo -e "Status: ${RED}✗ VALIDATION FAILED${NC} - ${VALIDATION_FAIL} critical issue(s)"
  echo ""
  echo "Before running day7 script, please fix:"
  echo "  - All marked with ✗ (critical failures)"
  echo "  - Consider addressing ⚠ warnings"
  echo ""
  exit 1
fi
