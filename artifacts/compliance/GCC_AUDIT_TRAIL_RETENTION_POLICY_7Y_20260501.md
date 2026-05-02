# Audit Trail Retention Policy (7 Years)

## Policy Statement

Audit-relevant records for security, operational changes, and release control evidence are retained for 7 years from creation date, unless a stricter legal hold applies.

- Effective date (UTC): 2026-05-01
- Policy owner: Platform Engineering
- Review cadence: Quarterly

## Retention Scope

The retention scope includes:

- Gate execution evidence and release verification artifacts
- Security and compliance audit logs retained in artifact storage
- Change tracking artifacts tied to release decisions and rollback readiness

Representative locations in repository baseline:

- [artifacts/audits](../audits)
- [artifacts/compliance](.)
- [docs/runbooks/artifacts](../../docs/runbooks/artifacts)

## Operational Controls

- Time-based retention labels applied to archived audit artifacts
- Storage lifecycle policy configured for minimum 7-year preservation target
- Deletion prevention for active legal-hold datasets
- Integrity checks performed on archived bundles

## Access and Integrity

- Read access to retained audit records is limited to authorized operations, security, and compliance roles.
- Write/delete operations require elevated approval and are logged.

## Exceptions

- Legal hold: retention extends beyond 7 years until hold release.
- Regulatory supersession: stricter local law takes precedence.

## Review and Evidence

- Gate and rollback evidence references:
  - [scripts/release_gate.sh](../../scripts/release_gate.sh)
  - [scripts/platform_smoke_check.sh](../../scripts/platform_smoke_check.sh)
- Index of compliance evidence baseline:
  - [C_TRACK_EVIDENCE_INDEX.md](C_TRACK_EVIDENCE_INDEX.md)

## Approval

- Engineering owner: Pending signature
- Compliance owner: Pending signature
- Security owner: Pending signature
