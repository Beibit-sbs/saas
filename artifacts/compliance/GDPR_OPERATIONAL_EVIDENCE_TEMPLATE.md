# GDPR Operational Evidence Template

## Scope

- Processing activities in scope: authentication, authorization, audit logging, intervention workflows, analytics summaries
- Data categories: account identifiers, role/permission data, operational event metadata, student profile references
- Data subjects: students, faculty, staff, platform administrators
- Systems: backend API, frontend admin console, PostgreSQL, Redis, observability stack
- DPO/owner: Compliance Representative (pending named owner)

## Record Of Processing Snapshot

| Processing Activity | Purpose | Lawful Basis | Data Categories | Retention Rule | Owner | Evidence Location |
|---|---|---|---|---|---|---|
| Authentication and session handling | Secure access control | Legitimate interests / contract performance | user_id, tenant_id, roles, auth metadata | Policy pending formal citation | Security | ../../docs/AUDIT_SBS_2026.md |
| Audit event collection | Accountability and incident traceability | Legal obligation / legitimate interests | actor, action, path, timestamp, correlation_id | Policy pending formal citation | Security + SRE | ../../docs/runbooks/artifacts/f1_risk_dod_signoff_20260417_174010.md |
| Intervention workflow operations | Student support process execution | Public task / legitimate interests | student_profile_id, workflow metadata | Policy pending formal citation | Product + Platform | ../../docs/runbooks/artifacts/f2_playbooks_day3_review_20260417_180346.md |

## Data Subject Rights (DSR) Evidence

| DSR Type | Request ID | Request Date (UTC) | Response Date (UTC) | SLA Met | Evidence Location |
|---|---|---|---|---|---|
| Access | N/A-PRELIVE-001 | N/A | N/A | N/A — pre-launch | No live data subjects enrolled; pilot not yet started (local workspace only) |
| Rectification | N/A-PRELIVE-002 | N/A | N/A | N/A — pre-launch | No live data subjects enrolled; pilot not yet started (local workspace only) |
| Erasure | N/A-PRELIVE-003 | N/A | N/A | N/A — pre-launch | No live data subjects enrolled; pilot not yet started (local workspace only) |
| Restriction | N/A-PRELIVE-004 | N/A | N/A | N/A — pre-launch | No live data subjects enrolled; pilot not yet started (local workspace only) |
| Portability | N/A-PRELIVE-005 | N/A | N/A | N/A — pre-launch | No live data subjects enrolled; pilot not yet started (local workspace only) |

## Retention And Deletion Evidence

| Dataset | Retention Policy | Deletion Job/Procedure | Last Execution (UTC) | Evidence Location | Status |
|---|---|---|---|---|---|
| Audit and operational logs | Policy citation pending | Scheduled purge/rotation process (to be referenced) |  | Evidence pack not attached yet | Open |
| Backup and recovery datasets | Policy citation pending | Backup lifecycle controls (to be referenced) |  | ../../docs/runbooks/artifacts/f3_schema_approval_signoff_20260417_035212.md | Partial |

## Cross-Border/Data Transfer Notes

| Transfer Scenario | Safeguard | Evidence |
|---|---|---|
| No confirmed external transfer in current baseline scope | Contractual and access controls | Pending explicit legal/compliance attestation |

## Gaps And Actions

| Gap | Risk | Remediation | Owner | Due Date | Status |
|---|---|---|---|---|---|
| No attached DSR execution evidence bundle | N/A (pre-launch) | Pilot not yet live; no real data subjects enrolled. Re-open when first external pilot cohort is onboarded. | Compliance + Support | At pilot launch | Closed (pre-launch — no live data subjects) |
| Retention/deletion policy references are not linked to signed policy docs | Medium | Add policy citations and operational job evidence before pilot launch | Compliance + Platform | At pilot launch | Open |
| DR-linked personal data recovery evidence incomplete | Closed | DR rehearsal executed 2026-03-25; backup 499 ms, restore 1229 ms, 8/8 smoke PASS. See docs/BACKUP_RESTORE_DRILL.md | Platform + SRE | 2026-03-25 | Closed (rehearsal PASS) |

## Approval

- Compliance owner: Pilot Owner (pending named person at launch)
- Security owner: Pilot Owner (pending named person at launch)
- Legal owner: Pending (pre-launch; no live data subjects)
- Date (UTC): 2026-04-20 (pre-launch baseline sign-off)

## Notes

- This is a baseline operational snapshot; GDPR status is fail-closed until DSR and retention evidence are fully attached and approved.
