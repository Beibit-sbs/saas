#!/usr/bin/env bash
# F3.2 schema approval gate for F3.3 unfreeze.
# Usage:
#   bash scripts/f3_schema_review_gate.sh
#   F3_SCHEMA_SIGNOFF_FILE=/path/to/signed.md bash scripts/f3_schema_review_gate.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"

find_latest_signoff() {
  ls -1t "${ARTIFACTS_DIR}"/f3_schema_approval_signoff_*.md 2>/dev/null | grep -v '_DRAFT\.md$' | head -n1 || true
}

SIGNOFF_FILE="${F3_SCHEMA_SIGNOFF_FILE:-}"
if [[ -z "${SIGNOFF_FILE}" ]]; then
  SIGNOFF_FILE="$(find_latest_signoff)"
fi

if [[ -z "${SIGNOFF_FILE}" ]]; then
  echo "[f3-schema-gate] BLOCKED: signed schema approval artifact not found"
  echo "[f3-schema-gate] Expected pattern: docs/runbooks/artifacts/f3_schema_approval_signoff_*.md"
  echo "[f3-schema-gate] Tip: create a signed copy from docs/templates/f3-schema-approval-signoff.md"
  echo "F3.2_GATE=FAIL"
  echo "SIGNOFF_FILE=N/A"
  echo "APPROVAL_MARK=FAIL"
  echo "SIGNATURES=0/3"
  echo "DECISION_DATE=FAIL"
  exit 1
fi

if [[ ! -f "${SIGNOFF_FILE}" ]]; then
  echo "[f3-schema-gate] BLOCKED: file not found: ${SIGNOFF_FILE}"
  echo "F3.2_GATE=FAIL"
  echo "SIGNOFF_FILE=${SIGNOFF_FILE}"
  echo "APPROVAL_MARK=FAIL"
  echo "SIGNATURES=0/3"
  echo "DECISION_DATE=FAIL"
  exit 1
fi

approval_mark="FAIL"
if grep -Eq '^- \[x\] APPROVED for F3\.3 unfreeze' "${SIGNOFF_FILE}"; then
  approval_mark="PASS"
fi

decision_date="FAIL"
if grep -Eq '^\*\*Decision Date:\*\* [0-9]{4}-[0-9]{2}-[0-9]{2}$' "${SIGNOFF_FILE}"; then
  decision_date="PASS"
fi

signatures="0"
if grep -q '^## 6\. Signatures' "${SIGNOFF_FILE}"; then
  signatures="$(awk '
    /^- Backend Lead:/ {
      if ($0 !~ /_{3,}/ && $0 !~ /Date: _{3,}/) c++
    }
    /^- DBA\/Platform Engineer:/ {
      if ($0 !~ /_{3,}/ && $0 !~ /Date: _{3,}/) c++
    }
    /^- Security\/Compliance Representative:/ {
      if ($0 !~ /_{3,}/ && $0 !~ /Date: _{3,}/) c++
    }
    END { print c+0 }
  ' "${SIGNOFF_FILE}")"
fi

if [[ "${approval_mark}" == "PASS" && "${decision_date}" == "PASS" && "${signatures}" -ge 3 ]]; then
  echo "[f3-schema-gate] PASS: F3.2 approval is ready for unfreeze"
  echo "F3.2_GATE=PASS"
  echo "SIGNOFF_FILE=$(basename "${SIGNOFF_FILE}")"
  echo "APPROVAL_MARK=PASS"
  echo "SIGNATURES=${signatures}/3"
  echo "DECISION_DATE=PASS"
  exit 0
fi

echo "[f3-schema-gate] BLOCKED: approval artifact is incomplete"
echo "[f3-schema-gate] File: ${SIGNOFF_FILE}"
echo "F3.2_GATE=FAIL"
echo "SIGNOFF_FILE=$(basename "${SIGNOFF_FILE}")"
echo "APPROVAL_MARK=${approval_mark}"
echo "SIGNATURES=${signatures}/3"
echo "DECISION_DATE=${decision_date}"
exit 1
