# Data Layer Audit Register

Date: 2026-04-09  
Owner: Platform Engineering

## Purpose

This register fixes a process gap where full audit runs did not explicitly surface data-layer checks.

Goals:
- make data-layer controls visible in every full audit run;
- preserve testable evidence for future internal/external audits;
- keep a concise source of truth for implemented data-layer safeguards.

Parent register:
- `docs/LAYER_AUDIT_REGISTER.md`

## Mandatory Audit Entry Points

1. Full audit command:
```bash
make system-audit
```

2. Data-layer-only command:
```bash
make data-layer-gate
```

3. Domain-layer-only command:
```bash
make domain-layer-gate
```

## Evidence Requirements

Every `make system-audit` run must produce and retain:
- artifact: `artifacts/audits/system-audit-<UTCSTAMP>.txt`
- explicit successful sections for:
  - backend lint/tests
  - RBAC parity
  - frontend lint/tests
  - domain layer gate
  - data layer gate

Audit evidence is invalid if data-layer section is missing.

## Implemented Data-Layer Safeguards (Current Baseline)

1. Dedicated data-layer gate
- script: `scripts/data_layer_gate.sh`
- covers migration graph safety, tenant/context integrity, domain consistency slices, and platform persistence/workflow guarantees.

2. Students consistency checks (read-only)
- active program binding anomaly detection:
  - duplicate active primary bindings
  - active bindings without primary

3. Transcripts consistency checks (read-only)
- student-level reconciliation endpoint:
  - `GET /api/admin/students/{student_id}/transcript/consistency`
- tenant-level reconciliation endpoint:
  - `GET /api/admin/transcripts/consistency`
- detected anomaly classes:
  - missing transcript record
  - duplicate transcript records for enrollment
  - transcript record mismatch (course/term/grade fields)
  - dangling transcript record

## Why This Prevents Repeat Gaps

`make system-audit` now includes domain-layer and data-layer gates directly and writes a timestamped audit artifact.

This ensures:
- no "green full audit" without data-layer validation;
- a durable evidence trail for audit review;
- deterministic reproduction of data-layer verification status.

## Auditor Checklist

1. Confirm `system-audit` artifact exists for the release candidate.
2. Confirm artifact contains successful `domain-layer-gate` and `data-layer-gate` execution.
3. If either section is absent or failed, mark release as non-compliant.
4. Attach artifact path to the release ticket/change request.
