# Notification Center — Module Foundation Registry
# Maturity: L1 (A-023.2 foundation lift from L0)
# Category: Planned Expansion — Student Lifecycle / Communications
# Action: A-023.2 — Student Lifecycle / Student Success Level 1–2 Foundation Lift

## Purpose

The `notification_center` module defines the central, tenant-scoped inbox and
dispatch contracts for student lifecycle alerts, reminders, and status updates.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `NotificationMessage` | Notification payload and metadata |
| `NotificationPreference` | Channel and category preferences |
| `NotificationReadState` | Recipient read/unread tracking |

## Planned Capabilities (roadmap)

- Create and route notifications by channel policy
- Track delivery/read state for recipients
- Manage opt-in and preference constraints
- Support student and parent communication contexts

## Dependencies

| Module | Relationship |
|---|---|
| `students` | Recipient identity and tenant scope |
| `parent_engagement` | Parent-facing communication bridge |
| `mobile_push_gateway` | Push channel integration |

## Maturity Gate Checklist

- [x] L1: module foundation documented
- [ ] L2: schemas + service skeleton
- [ ] L3: tests + tenant guard + FSM/events
- [ ] L4: API/frontend/KPI integration
