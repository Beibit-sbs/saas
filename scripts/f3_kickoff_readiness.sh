#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="${ROOT_DIR}/scripts"

echo "=========================================="
echo "F3 Complete Readiness Gate (2026-04-21)"
echo "Pre-Phase-1 Kickoff Validation"
echo "Date: $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
echo "=========================================="
echo ""

# Execute docker-only guard
bash "${ROOT_DIR}/scripts/docker_only_guard.sh"

# Collect results from each subgate
echo "[f3-kickoff] running F3.3 unfreeze validation..."
F3_3_OUTPUT=$(bash "${SCRIPT_DIR}/f3_unfreeze_validation.sh" 2>&1 || true)
F3_3_STATUS=$(echo "$F3_3_OUTPUT" | grep -o 'F3.3_VALIDATION=[A-Z_]*' | tail -n1 || true)
if [[ -z "$F3_3_STATUS" ]]; then
  F3_3_STATUS="F3.3_VALIDATION=UNKNOWN"
fi

echo "[f3-kickoff] running F3.4 frontend readiness gate..."
F3_4_OUTPUT=$(bash "${SCRIPT_DIR}/f3_4_frontend_kickoff_readiness.sh" 2>&1 || true)
F3_4_STATUS=$(echo "$F3_4_OUTPUT" | grep -o 'F3.4_KICKOFF_READY=[A-Z_]*' | tail -n1 || true)
if [[ -z "$F3_4_STATUS" ]]; then
  F3_4_STATUS="F3.4_KICKOFF_READY=UNKNOWN"
fi

echo "[f3-kickoff] running F3.5 observability readiness gate..."
F3_5_OUTPUT=$(bash "${SCRIPT_DIR}/f3_5_observability_kickoff_readiness.sh" 2>&1 || true)
F3_5_STATUS=$(echo "$F3_5_OUTPUT" | grep -o 'F3.5_KICKOFF_READY=[A-Z_]*' | tail -n1 || true)
if [[ -z "$F3_5_STATUS" ]]; then
  F3_5_STATUS="F3.5_KICKOFF_READY=UNKNOWN"
fi

# Parse individual results
F3_3_RESULT=$(echo "$F3_3_STATUS" | cut -d'=' -f2)
F3_4_RESULT=$(echo "$F3_4_STATUS" | cut -d'=' -f2)
F3_5_RESULT=$(echo "$F3_5_STATUS" | cut -d'=' -f2)

# Unified gate logic
UNIFIED_STATUS="UNKNOWN"
UNIFIED_EXIT=1

if [[ "$F3_3_RESULT" == "PASS" ]] && [[ "$F3_4_RESULT" == "PASS" ]] && [[ "$F3_5_RESULT" == "PASS" ]]; then
  UNIFIED_STATUS="PASS"
  UNIFIED_EXIT=0
elif [[ "$F3_3_RESULT" == "PASS" ]] && [[ "$F3_5_RESULT" == "PASS" ]] && [[ "$F3_4_RESULT" == "BLOCKED" || "$F3_4_RESULT" == "PASS" ]]; then
  # Allow kickoff preparation to continue when frontend gate is blocked only by backend availability.
  UNIFIED_STATUS="CONDITIONAL_PASS"
  UNIFIED_EXIT=0
elif [[ "$F3_3_RESULT" == "FAIL" ]]; then
  UNIFIED_STATUS="FAIL"
  UNIFIED_EXIT=1
else
  UNIFIED_STATUS="PENDING"
  UNIFIED_EXIT=1
fi

echo ""
echo "=========================================="
echo "F3 Readiness Summary"
echo "=========================================="
echo "F3.3 Unfreeze validation: $F3_3_RESULT"
echo "F3.4 Frontend kickoff:    $F3_4_RESULT"
echo "F3.5 Observability kick: $F3_5_RESULT"
echo ""
echo "Unified Status: $UNIFIED_STATUS"
echo ""

if [[ "$UNIFIED_STATUS" == "PASS" ]]; then
  echo "✓ F3 ready for Phase 1 kickoff (2026-04-21 11:30 UTC)"
  echo "  - F3.3 unfreeze validated"
  echo "  - F3.4 frontend API health OK"
  echo "  - F3.5 observability rules loaded"
  echo ""
  echo "Next steps:"
  echo "  1. Review F3_KICKOFF_SEQUENCE.md for phase timeline"
  echo "  2. Start F3.4 Phase 1 (data layer, ~5-7 days)"
  echo "  3. Start F3.5 Phase 1 (metrics, parallel to F3.4)"
  echo ""
elif [[ "$UNIFIED_STATUS" == "CONDITIONAL_PASS" ]]; then
  echo "⚠ F3 partially ready (backend may not be online)"
  echo "  - F3.3 unfreeze OK"
  echo "  - F3.4 frontend checks incomplete (backend offline?)"
  echo ""
  echo "Recommended action:"
  echo "  1. Bring up backend docker stack: make up"
  echo "  2. Re-run: make f3-kickoff-readiness"
  echo ""
else
  echo "✗ F3 readiness FAILED"
  echo "  Please review individual gate outputs above"
  echo ""
  echo "To debug:"
  echo "  - F3.3: bash scripts/f3_unfreeze_validation.sh"
  echo "  - F3.4: bash scripts/f3_4_frontend_kickoff_readiness.sh"
  echo "  - F3.5: bash scripts/f3_5_observability_kickoff_readiness.sh"
  echo ""
fi

echo "F3_KICKOFF_STATUS=$UNIFIED_STATUS"
echo "F3.3_VALIDATION=$F3_3_RESULT"
echo "F3.4_KICKOFF_READY=$F3_4_RESULT"
echo "F3.5_KICKOFF_READY=$F3_5_RESULT"

exit $UNIFIED_EXIT
