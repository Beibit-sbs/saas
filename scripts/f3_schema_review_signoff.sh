#!/usr/bin/env bash
# Generate F3.2 schema approval sign-off artifact from template.
# Does not require Docker; this is a documentation workflow helper.
#
# Usage examples:
#   bash scripts/f3_schema_review_signoff.sh
#   bash scripts/f3_schema_review_signoff.sh --approved \
#     --backend-lead "Alice" --dba "Bob" --security "Carol" --product-owner "Diana"
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_FILE="${ROOT_DIR}/docs/templates/f3-schema-approval-signoff.md"
ARTIFACTS_DIR="${ROOT_DIR}/docs/runbooks/artifacts"

decision_date="$(date +%Y-%m-%d)"
approved="false"
backend_lead=""
dba_engineer=""
security_rep=""
product_owner=""
output_file=""

usage() {
  cat <<EOF
Usage:
  bash scripts/f3_schema_review_signoff.sh [options]

Options:
  --approved                 Mark decision as approved for F3.3 unfreeze.
  --decision-date YYYY-MM-DD Set decision date (default: today local date).
  --backend-lead NAME        Backend lead signer name.
  --dba NAME                 DBA/Platform engineer signer name.
  --security NAME            Security/Compliance representative signer name.
  --product-owner NAME       Product owner acknowledgement name.
  --output FILE              Explicit output file path.
  -h, --help                 Show this help.

Output:
  docs/runbooks/artifacts/f3_schema_approval_signoff_<UTC_TIMESTAMP>.md
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --approved)
      approved="true"
      shift
      ;;
    --decision-date)
      decision_date="${2:-}"
      shift 2
      ;;
    --backend-lead)
      backend_lead="${2:-}"
      shift 2
      ;;
    --dba)
      dba_engineer="${2:-}"
      shift 2
      ;;
    --security)
      security_rep="${2:-}"
      shift 2
      ;;
    --product-owner)
      product_owner="${2:-}"
      shift 2
      ;;
    --output)
      output_file="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[f3-signoff] ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! "${decision_date}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "[f3-signoff] ERROR: invalid --decision-date format (expected YYYY-MM-DD)" >&2
  exit 1
fi

if [[ ! -f "${TEMPLATE_FILE}" ]]; then
  echo "[f3-signoff] ERROR: template not found: ${TEMPLATE_FILE}" >&2
  exit 1
fi

mkdir -p "${ARTIFACTS_DIR}"

if [[ -z "${output_file}" ]]; then
  stamp="$(date -u +%Y%m%d_%H%M%S)"
  output_file="${ARTIFACTS_DIR}/f3_schema_approval_signoff_${stamp}.md"
fi

cp "${TEMPLATE_FILE}" "${output_file}"

# Update decision date.
sed -i -E "s/^\*\*Decision Date:\*\* .*/**Decision Date:** ${decision_date}/" "${output_file}"

# Toggle approval checkboxes.
if [[ "${approved}" == "true" ]]; then
  sed -i -E 's/^- \[ \] APPROVED for F3\.3 unfreeze/- [x] APPROVED for F3.3 unfreeze/' "${output_file}"
  sed -i -E 's/^- \[ \] APPROVED WITH CONDITIONS/- [ ] APPROVED WITH CONDITIONS/' "${output_file}"
  sed -i -E 's/^- \[ \] REJECTED/- [ ] REJECTED/' "${output_file}"
fi

# Populate signers if provided.
if [[ -n "${backend_lead}" ]]; then
  sed -i -E "s|^- Backend Lead: .*$|- Backend Lead: ${backend_lead} Date: ${decision_date}|" "${output_file}"
fi
if [[ -n "${dba_engineer}" ]]; then
  sed -i -E "s|^- DBA/Platform Engineer: .*$|- DBA/Platform Engineer: ${dba_engineer} Date: ${decision_date}|" "${output_file}"
fi
if [[ -n "${security_rep}" ]]; then
  sed -i -E "s|^- Security/Compliance Representative: .*$|- Security/Compliance Representative: ${security_rep} Date: ${decision_date}|" "${output_file}"
fi
if [[ -n "${product_owner}" ]]; then
  sed -i -E "s|^- Product Owner \(ack\): .*$|- Product Owner (ack): ${product_owner} Date: ${decision_date}|" "${output_file}"
fi

echo "[f3-signoff] artifact created: ${output_file}"
echo "APPROVED=${approved}"
echo "DECISION_DATE=${decision_date}"
echo "NEXT=run_f3_schema_gate"
echo "COMMAND=bash scripts/f3_schema_review_gate.sh"
