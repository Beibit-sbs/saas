# SOC 2 Control Evidence Template

## Scope

- Tenant(s): Default tenant (tenant_id=1) and platform admin surface
- Environment(s): Docker-based production-like validation environment
- Period covered: 2026-04-11 -> 2026-04-18
- Evidence owner: Platform Engineering (pending named owner)

## Control Matrix

| Control ID | Control Objective | Implemented Mechanism | Evidence Location | Sample Timestamp (UTC) | Owner | Status |
|---|---|---|---|---|---|---|
| CC6.1 | Logical access restriction | RBAC/ABAC enforcement | ../../docs/runbooks/artifacts/f1_risk_dod_signoff_20260417_174010.md | 2026-04-17T17:43:28Z | Security + Platform | PASS (provisional) |
| CC6.2 | Access provisioning/deprovisioning | Local users + role assignment flow | ../../docs/runbooks/artifacts/f1_risk_dod_signoff_20260417_174010.md | 2026-04-17T17:43:28Z | Security + Platform | PASS (provisional) |
| CC6.3 | MFA and session control | MFA service + token/session controls | ../../docs/AUDIT_SBS_2026.md | 2026-04-18 | Security + Platform | PASS (provisional) |
| CC7.2 | Change management | Release gate + audit artifacts | ../../docs/runbooks/artifacts/f3_unfreeze_validation_20260418_053706.md | 2026-04-18T05:37:06Z | Engineering | PASS (provisional) |
| CC7.3 | Monitoring and anomaly response | Health/alerts/metrics coverage | ../../scripts/f3_observability_alerts_gate.sh | 2026-04-18 | SRE | PASS (provisional) |
| CC8.1 | Incident response readiness | Incident runbook + execution logs | ../../docs/runbooks/artifacts/f2_playbooks_day3_review_20260417_180346.md | 2026-04-17T18:03:46Z | SRE + Security | PASS (provisional) |
| A1.2 | Availability and recovery readiness | Backup/restore and DR drill evidence | ../../docs/BACKUP_RESTORE_DRILL.md | 2026-03-25T02:03:51Z | Platform + SRE | PASS (local DR rehearsal: RTO=1229ms, smoke=8/8) |

## Exceptions And Gaps

| Control ID | Gap Description | Risk | Remediation | Owner | Due Date | Status |
|---|---|---|---|---|---|---|
| CC6.3 | MFA/session evidence is referenced at policy level; sampled execution evidence bundle is not attached yet | Medium | Attach sampled auth evidence extract and approval note before pilot launch | Security | At pilot launch | Open |

## Evidence Checklist

- [x] Access control evidence attached (provisional)
- [x] Change management evidence attached (provisional)
- [x] Monitoring and alerting evidence attached (provisional)
- [x] Incident response execution evidence attached (provisional)
- [x] Backup/restore evidence attached (DR rehearsal 2026-03-25: RTO=1229ms, smoke=8/8 PASS)

## Approval

- Prepared by: Platform Engineering
- Reviewed by: Pilot Owner (pending named person at launch)
- Approved by: Pilot Owner (pending named person at launch)
- Approval date (UTC): 2026-04-20 (pre-launch baseline)

## Notes

- Provisional PASS means evidence exists but final sign-off is not complete.
- Final SOC2 status for C-Track is fail-closed until A1.2 gaps are closed.
