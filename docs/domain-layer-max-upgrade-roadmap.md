# Domain Layer Max Upgrade Roadmap

Date: 2026-04-08
Scope: Education domain layer uplift to advanced operational maturity.

## Target State

The education domain should move from usable baseline to advanced maturity with:
- stable role-based end-to-end workflows
- explicit business state machines and invariants
- domain-level observability and SLOs
- release gate enforcement for domain regressions

## 30-Day Plan (Stabilize)

1. Build and enforce domain quality gate
- Done: added `scripts/domain_layer_gate.sh` and wired into release check.
- Keep default on in release checks.

2. Expand critical backend domain test coverage
- Admissions transitions and tenant isolation edge-cases.
- Enrollment + grades lifecycle invalid-transition tests.
- Transcript generation consistency checks.

3. Lock critical frontend role workflows
- Student profile and transcript reads.
- Faculty grade entry and attendance flows.
- Registrar enrollment and scheduling workflows.

Acceptance criteria:
- Domain gate always green on main.
- No untested state transition in admissions/enrollment/grades/transcripts.

## 60-Day Plan (Harden)

1. Formal state machines
- Define explicit status graph per domain aggregate:
  - admission_application
  - enrollment
  - transcript_request
  - intervention_case
- Enforce transition guards in services.

2. Idempotency and replay safety
- Add idempotency keys to write-heavy flows.
- Guard duplicate external trigger paths.

3. Domain observability baseline
- Domain metrics:
  - application decision latency
  - enrollment completion latency
  - grade finalization latency
  - transcript issuance latency
- Alerting for stuck statuses and failure spikes.

Acceptance criteria:
- Invalid transition attempts rejected and audited.
- p95 latency SLOs defined and tracked for key workflows.
- Alert coverage for top-5 domain incidents.

## 90-Day Plan (Scale)

1. Full role journey E2E packs
- Student, Faculty, Registrar, Platform Admin scenario packs.
- Failure-mode scenarios for partial outages.

2. Data quality and reconciliation
- Cross-module consistency checks:
  - enrollments vs scheduling roster
  - grades vs transcript snapshots
- Nightly reconciliation reports.

3. Release readiness policy
- Add domain risk scoring into release gate outputs.
- Enforce no-go on failed journey packs or data-reconciliation errors.

Acceptance criteria:
- 15+ critical role journeys consistently green.
- Reconciliation failures produce actionable alerts.
- Release gate includes domain risk summary.

## KPI Set

Product KPIs:
- Journey completion rate >= 99% for critical role workflows.
- User-visible domain error rate <= 0.5%.

Engineering KPIs:
- Domain gate pass rate >= 98% on main.
- Change failure rate in domain modules <= 10%.
- Mean time to recover domain incidents <= 60 minutes.

## Execution Cadence

- Weekly domain quality review (test failures, SLO drift, incidents).
- Bi-weekly architecture review for state machine and invariants.
- Monthly release-governance checkpoint against KPI set.
