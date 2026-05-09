# Health Services — Module Foundation Registry
# Maturity: L1 (A-023.2 foundation lift from L0)
# Category: Planned Expansion — Student Lifecycle / Student Wellbeing
# Action: A-023.2 — Student Lifecycle / Student Success Level 1–2 Foundation Lift

## Purpose

The `health_services` module tracks tenant-scoped student health-service
appointments, referrals, and non-clinical service coordination metadata.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `HealthAppointment` | Appointment booking metadata |
| `Referral` | Internal/external referral record |
| `ServiceQueueEntry` | Intake and queue position |

## Planned Capabilities (roadmap)

- Appointment intake and scheduling metadata
- Service queue prioritization markers
- Referral tracking and closure status
- Confidentiality-aware access model

## Dependencies

| Module | Relationship |
|---|---|
| `student_services` | Case coordination |
| `counseling_case_management` | Escalation/hand-off linkage |
| `notification_center` | Appointment reminders |

## Maturity Gate Checklist

- [x] L1: module foundation documented
- [ ] L2: schemas + service skeleton
- [ ] L3: tests + tenant guard + FSM/events
- [ ] L4: API/frontend/KPI integration
