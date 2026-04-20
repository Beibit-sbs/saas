# ISO 27001 SoA Mapping Template

## Scope

- Organization scope: SBS platform core (multi-tenant university operations surface)
- ISMS boundary for this release: backend, frontend, infra compose stack, audit and observability gates
- Version: 2026-04-18 baseline
- Prepared by: Platform Engineering (pending named owner)

## Annex A Mapping

| Annex A Control | Applicability | Justification | Implementation Reference | Evidence Location | Owner | Status |
|---|---|---|---|---|---|---|
| A.5.15 Access control | Applicable | Tenant isolation and role-based authorization enforced across admin APIs | RBAC/ABAC and auth modules | ../../docs/runbooks/artifacts/f1_risk_dod_signoff_20260417_174010.md | Security + Platform | PASS (provisional) |
| A.5.16 Identity management | Applicable | Identity and auth lifecycle are part of platform baseline | Identity/auth routes and gate evidence | ../../docs/AUDIT_SBS_2026.md | Security + Platform | PASS (provisional) |
| A.5.23 Information security for use of cloud services | Applicable | Containerized runtime with controlled release gates | Release and safe-gate scripts | ../../scripts/release_gate.sh | Platform | PASS (provisional) |
| A.8.8 Management of technical vulnerabilities | Applicable | Security regression and quality gates are run before release | release_check and regression gates | ../../scripts/release_check.sh | Security + QA | PASS (provisional) |
| A.8.15 Logging | Applicable | Structured audit/security request logs are emitted and validated | Audit evidence from post-release reviews | ../../docs/runbooks/artifacts/f2_playbooks_day3_review_20260417_180346.md | SRE + Security | PASS (provisional) |
| A.8.16 Monitoring activities | Applicable | Prometheus rules validated by dedicated alerts gate | F3 observability alert gate | ../../scripts/f3_observability_alerts_gate.sh | SRE | PASS (provisional) |
| A.8.13 Backup | Applicable | DR rehearsal successful 2026-03-25 with measured RTO | ../../docs/BACKUP_RESTORE_DRILL.md | Platform + SRE | PASS (local DR: RTO=1229ms, schema consistency verified) |
| A.5.30 ICT readiness for business continuity | Applicable | DR readiness verified via local rehearsal 2026-03-25 | ../../docs/BACKUP_RESTORE_DRILL.md | Platform + Compliance | PASS (local DR evidence sufficient for pilot) |

## Non-Applicable Controls

| Annex A Control | Reason Not Applicable | Approved By |
|---|---|---|

## Risk Treatment Linkage

- Risk register reference:
- Open treatment actions:
	- (None — local DR evidence accepted for pilot-ready)

## Approval

- ISMS owner:
- Security lead:
- Date (UTC):

## Notes

- Current mapping is a baseline operational SoA snapshot.
- Controls with FAIL status keep C-Track in fail-closed state until remediation is evidenced.
