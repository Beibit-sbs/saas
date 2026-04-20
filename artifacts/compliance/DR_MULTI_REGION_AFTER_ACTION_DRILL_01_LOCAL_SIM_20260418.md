# DR Multi-Region After-Action Report (Local Simulation)

## Drill Metadata

- Drill ID: DR-LOCAL-SIM-01
- Date (UTC): 2026-04-18
- Commander: Platform Engineering (local operator)
- Regions in scope: emulated region-a, emulated region-b (single host)
- Scenario type: controlled failover simulation on one laptop
- Systems in scope: backend API, PostgreSQL, Redis, PgBouncer, observability checks

## Timeline (UTC)

| Event | Timestamp |
|---|---|
| Incident start | 2026-04-18T09:00:00Z |
| Failover start | 2026-04-18T09:00:20Z |
| Data restore start | 2026-04-18T09:01:40Z |
| Smoke checks start | 2026-04-18T09:02:30Z |
| Service restored | 2026-04-18T09:03:20Z |
| Drill closed | 2026-04-18T09:07:00Z |

## Measured Outcomes

- RTO_target: 00:05:00
- RTO_actual: 00:03:20 (single-host simulation)
- RPO_target: 00:01:00
- RPO_actual: NOT MEASURABLE (single-host, no real inter-region replication)
- SLO met: NO

## Validation Results

| Check | Result | Evidence |
|---|---|---|
| API health endpoints | PASS | ../../artifacts/audits/data-layer-gate-latest.log |
| Authentication path | PASS | ../../docs/runbooks/artifacts/f1_risk_dod_signoff_20260417_174010.md |
| Critical workflows | PASS | ../../artifacts/audits/workflows-consistency-targeted.log |
| Data consistency checks | PASS | ../../artifacts/audits/university-core-consistency-targeted.log |
| Audit logging continuity | PASS | ../../docs/runbooks/artifacts/f2_playbooks_day3_review_20260417_180346.md |

## Gaps And Corrective Actions

| Gap | Impact | Corrective Action | Owner | Due Date | Status |
|---|---|---|---|---|---|
| No real multi-region infrastructure on local laptop | Cannot claim enterprise DR evidence | Execute 2 real multi-region drills in non-local environment | Platform + SRE | 2026-04-20 | Open |
| RPO_actual cannot be measured in one-host emulation | A1.2 and ICT readiness controls stay fail-closed | Run replication-aware drill with region-separated data plane | Platform + DBA | 2026-04-20 | Open |

## Sign-off

- Operations lead: PENDING
- Security lead: PENDING
- Platform lead: PENDING
- Sign-off date (UTC): PENDING

## Notes

- This report is valid as lab evidence only.
- This report does not satisfy C-Track requirement for multi-region DR proof.