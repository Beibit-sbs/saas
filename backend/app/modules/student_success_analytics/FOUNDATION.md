# Student Success Analytics — Module Foundation Registry
# Maturity: L1 (A-023.1 foundation lift from L0)
# Category: Planned Expansion — Academic Services
# Action: A-023.1 — Academic/Education Level 1–2 Foundation Lift

## Purpose

The `student_success_analytics` module aggregates early-warning signals,
retention risk scores, and intervention tracking to support academic
advisors and institutional effectiveness staff within the multi-tenant
university platform.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `RiskProfile` | Per-student retention risk score and contributing factors |
| `EarlyWarningFlag` | Alert raised by a trigger rule (e.g., absences, grade drop) |
| `Intervention` | Advisor-initiated action in response to a flag |
| `SuccessPlan` | Personalised support plan attached to a student |

## Planned Capabilities (roadmap)

- Risk scoring based on grade trajectory, attendance, engagement
- Configurable trigger rules (thresholds per tenant)
- Early-warning flag lifecycle: OPEN → ASSIGNED → RESOLVED
- Intervention logging and outcome tracking
- Aggregated cohort dashboard (downstream of Brain Core KPIs)
- Feed from `enrollments`, `grades`, `attendance` modules

## Dependencies

| Module | Relationship |
|---|---|
| `enrollments` | Active enrolment status |
| `grades` | Grade trajectory input |
| `counseling_case_management` | Escalate to counseling |
| `degree_progress` | Degree risk context |

## Integration Points (L2 scope, not yet implemented)

- `GET /student-success/risk?student_id=` — risk profile
- `POST /student-success/flags` — raise early-warning flag
- `PATCH /student-success/flags/{id}/resolve` — close flag
- `POST /student-success/interventions` — log intervention

## Maturity Gate Checklist

- [x] L1: Module registered; key entities and dependencies documented
- [ ] L2: Pydantic schemas + service skeleton
- [ ] L3: Backend tests, tenant guard, FSM, events
- [ ] L4: REST router, frontend integration
