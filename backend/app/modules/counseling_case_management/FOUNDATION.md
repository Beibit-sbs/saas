# Counseling Case Management — Module Foundation Registry
# Maturity: L1 (A-023.1 foundation lift from L0)
# Category: Planned Expansion — Student Services
# Action: A-023.1 — Academic/Education Level 1–2 Foundation Lift

## Purpose

The `counseling_case_management` module supports university counseling staff
in managing student welfare and mental-health cases, appointments, referrals,
and confidential case notes within the multi-tenant university platform.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `CounselingCase` | Case record linking student, counselor, and presenting issue |
| `Appointment` | Scheduled counseling session |
| `CaseNote` | Confidential session note (access-restricted) |
| `Referral` | External or internal referral record |

## Planned Capabilities (roadmap)

- Case intake and triage workflow: OPEN → ACTIVE → REFERRED / CLOSED
- Appointment scheduling with calendar integration stub
- Confidential note storage (role-restricted: counselor + student only)
- Referral management (internal health_services, external providers)
- Caseload dashboard for counseling coordinators
- Integration with `student_success_analytics` early-warning flags

## Dependencies

| Module | Relationship |
|---|---|
| `access_control` | Role-restricted note access |
| `student_success_analytics` | Receives escalated early-warning flags |
| `health_services` | Internal referral target |
| `scheduling` | Appointment slot availability |

## Integration Points (L2 scope, not yet implemented)

- `POST /counseling/cases` — open new case
- `GET /counseling/cases/{id}` — case detail (role-restricted)
- `POST /counseling/cases/{id}/appointments` — schedule appointment
- `POST /counseling/cases/{id}/notes` — add confidential note
- `POST /counseling/cases/{id}/referrals` — create referral

## Maturity Gate Checklist

- [x] L1: Module registered; key entities and dependencies documented
- [ ] L2: Pydantic schemas + service skeleton
- [ ] L3: Backend tests, tenant guard, FSM, events
- [ ] L4: REST router, frontend integration
