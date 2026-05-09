# Event Registration Portal — Module Foundation Registry
# Maturity: L1 (A-023.2 foundation lift from L0)
# Category: Planned Expansion — Student Lifecycle / Campus Engagement
# Action: A-023.2 — Student Lifecycle / Student Success Level 1–2 Foundation Lift

## Purpose

The `event_registration_portal` module manages student and parent registration
for campus events, confirmations, attendance capacity, and waitlist handling
in a multi-tenant context.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `CampusEventRegistration` | Registration record per event and participant |
| `EventWaitlistEntry` | Waitlist queue entry |
| `RegistrationTicket` | Access/confirmation token |

## Planned Capabilities (roadmap)

- Register participant to an event with capacity checks
- Waitlist support when event is full
- Cancel registration and release spot
- Export attendance roster for event operations

## Dependencies

| Module | Relationship |
|---|---|
| `events_management` | Source of event definitions |
| `student_portal` | Student-facing registration surface |
| `notification_center` | Confirmation and reminder notices |

## Maturity Gate Checklist

- [x] L1: module foundation documented
- [ ] L2: schemas + service skeleton
- [ ] L3: tests + tenant guard + FSM/events
- [ ] L4: API/frontend/KPI integration
