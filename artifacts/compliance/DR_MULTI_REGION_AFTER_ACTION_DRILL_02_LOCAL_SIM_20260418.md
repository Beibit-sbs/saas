# DR Multi-Region After-Action Report (Local Simulation)

## Drill Metadata

- Drill ID: DR-LOCAL-SIM-02
- Date (UTC): 2026-04-18
- Commander: Platform Engineering (local operator)
- Regions in scope: emulated region-a, emulated region-b (single host)
- Scenario type: degraded dependency and recovery simulation on one laptop
- Systems in scope: backend API, PostgreSQL, Redis, alerting gate, consistency checks

## Timeline (UTC)

| Event | Timestamp |
|---|---|
| Incident start | 2026-04-18T10:15:00Z |
| Failover start | 2026-04-18T10:15:25Z |
| Data restore start | 2026-04-18T10:17:10Z |
| Smoke checks start | 2026-04-18T10:18:05Z |
| Service restored | 2026-04-18T10:18:55Z |
| Drill closed | 2026-04-18T10:23:00Z |

## Measured Outcomes

- RTO_target: 00:05:00
- RTO_actual: 00:03:55 (single-host simulation)
- RPO_target: 00:01:00
- RPO_actual: NOT MEASURABLE (single-host, no region-separated replica)
- SLO met: NO

## Validation Results

| Check | Result | Evidence |
|---|---|---|
| API health endpoints | PASS | ../../artifacts/audits/data-layer-gate-latest.log |
| Authentication path | PASS | ../../docs/runbooks/artifacts/f1_risk_dod_signoff_20260417_174010.md |
| Critical workflows | PASS | ../../artifacts/audits/admissions-consistency-targeted.log |
| Data consistency checks | PASS | ../../artifacts/audits/academic-records-targeted.log |
| Audit logging continuity | PASS | ../../docs/runbooks/artifacts/f2_playbooks_day1_review_20260417_180332.md |

## Gaps And Corrective Actions

| Gap | Impact | Corrective Action | Owner | Due Date | Status |
|---|---|---|---|---|---|
| Single-node failure domain remains | No independent region fault isolation | Re-run drills in two actual regions/fault domains | Platform + SRE | 2026-04-20 | Open |
| Replication lag and cross-region restore not testable locally | RPO cannot be attested for compliance | Collect replicated datastore metrics in multi-region drill | Platform + DBA | 2026-04-20 | Open |

## Sign-off

- Operations lead: PENDING
- Security lead: PENDING
- Platform lead: PENDING
- Sign-off date (UTC): PENDING

## Notes

- This report is valid as lab evidence only.
- This report does not satisfy C-Track requirement for multi-region DR proof.