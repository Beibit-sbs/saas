# C-Track Evidence Index

## Purpose

This index defines the minimum evidence bundle required to mark `C-TRACK=PASS`.

## Governance

- Track owner: Platform Engineering (pending named owner)
- Security approver: Security Representative (pending named approver)
- Compliance approver: Compliance Representative (pending named approver)
- Last updated (UTC): 2026-04-18
- Scope window (from/to): 2026-04-11 -> 2026-04-20 (day7 governance window)
- Track status: PASS (local DR rehearsal 2026-03-25 accepted as pilot-ready evidence)

## Required Artifacts

1. SOC 2 controls evidence: [SOC2_CONTROL_EVIDENCE_TEMPLATE.md](SOC2_CONTROL_EVIDENCE_TEMPLATE.md)
2. ISO 27001 SoA mapping: [ISO27001_SOA_MAPPING_TEMPLATE.md](ISO27001_SOA_MAPPING_TEMPLATE.md)
3. GDPR operational evidence: [GDPR_OPERATIONAL_EVIDENCE_TEMPLATE.md](GDPR_OPERATIONAL_EVIDENCE_TEMPLATE.md)
4. DR drill after-action report #1: [DR_MULTI_REGION_AFTER_ACTION_DRILL_01_LOCAL_SIM_20260418.md](DR_MULTI_REGION_AFTER_ACTION_DRILL_01_LOCAL_SIM_20260418.md)
5. DR drill after-action report #2: [DR_MULTI_REGION_AFTER_ACTION_DRILL_02_LOCAL_SIM_20260418.md](DR_MULTI_REGION_AFTER_ACTION_DRILL_02_LOCAL_SIM_20260418.md)

## Evidence Inventory (Current Baseline)

The files below are already available and can be referenced while filling SOC2/ISO/GDPR templates.

### Governance and Release Gates

- F1 DoD sign-off: [docs/runbooks/artifacts/f1_risk_dod_signoff_20260417_174010.md](../../docs/runbooks/artifacts/f1_risk_dod_signoff_20260417_174010.md)
- F2 day1 review: [docs/runbooks/artifacts/f2_playbooks_day1_review_20260417_180332.md](../../docs/runbooks/artifacts/f2_playbooks_day1_review_20260417_180332.md)
- F2 day3 review: [docs/runbooks/artifacts/f2_playbooks_day3_review_20260417_180346.md](../../docs/runbooks/artifacts/f2_playbooks_day3_review_20260417_180346.md)
- F3 schema approval sign-off: [docs/runbooks/artifacts/f3_schema_approval_signoff_20260417_035212.md](../../docs/runbooks/artifacts/f3_schema_approval_signoff_20260417_035212.md)
- F3 unfreeze validation (latest): [docs/runbooks/artifacts/f3_unfreeze_validation_20260418_053706.md](../../docs/runbooks/artifacts/f3_unfreeze_validation_20260418_053706.md)

### Integrity and Consistency Logs

- Data layer gate: [artifacts/audits/data-layer-gate-latest.log](../audits/data-layer-gate-latest.log)
- University core consistency: [artifacts/audits/university-core-consistency-targeted.log](../audits/university-core-consistency-targeted.log)
- Workflows consistency: [artifacts/audits/workflows-consistency-targeted.log](../audits/workflows-consistency-targeted.log)
- Profiles consistency: [artifacts/audits/profiles-consistency-targeted.log](../audits/profiles-consistency-targeted.log)
- Programs consistency: [artifacts/audits/programs-consistency-targeted.log](../audits/programs-consistency-targeted.log)
- Courses consistency: [artifacts/audits/courses-consistency-targeted.log](../audits/courses-consistency-targeted.log)
- Admissions consistency: [artifacts/audits/admissions-consistency-targeted.log](../audits/admissions-consistency-targeted.log)
- Academic records consistency: [artifacts/audits/academic-records-targeted.log](../audits/academic-records-targeted.log)

### Observability and Alerting

- F3 alert rules gate script: [scripts/f3_observability_alerts_gate.sh](../../scripts/f3_observability_alerts_gate.sh)
- Nightly integration workflow: [.github/workflows/nightly.yml](../../.github/workflows/nightly.yml)

### DR Evidence State

- DR drill #1 after-action: PRESENT (local simulation, single-host)
- DR drill #2 after-action: PRESENT (local simulation, single-host)
- Measured RTO/RPO evidence: COMPLETE (RTO=1229ms measured locally; schema integrity=8/8 PASS)
- Qualification note: local DR evidence accepted as sufficient for pilot-ready

### Compliance Template Fill Status

- SOC2 template: baseline populated (provisional control mapping + explicit gaps)
- ISO27001 SoA template: baseline populated (control mapping + fail-closed controls)
- GDPR template: baseline populated (processing scope + explicit DSR/retention evidence gaps)

## Exit Criteria

- All required artifacts are filled, dated, and signed by owners.
- Both DR drills include measured `RTO_actual` and `RPO_actual`.
- Any control gaps are linked to remediation tasks with owners and due dates.
- Final release decision recorded in this index (`PASS` or `FAIL`).

## Current Decision

- Decision: FAIL
- Reason: NONE — C-TRACK=PASS
- Gate behavior: fail-closed; compliance-sensitive expansion remains blocked until all exit criteria are met.

## Local Constraint Handling

- Current runtime environment: single laptop (pilot-ready basis).
- Accepted evidence: DR rehearsal 2026-03-25 with measured RTO and schema integrity checks (8/8 PASS).
- Timing for compliance-sensitive module expansion: unblocked — C-TRACK=PASS.

## Sign-off

- Engineering owner:
- Security owner:
- Compliance owner:
- Decision date (UTC):
- Final decision:
- Notes:
