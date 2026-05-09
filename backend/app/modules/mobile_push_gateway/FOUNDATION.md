# Mobile Push Gateway — Module Foundation Registry
# Maturity: L1 (A-023.2 foundation lift from L0)
# Category: Planned Expansion — Student Lifecycle / Communications
# Action: A-023.2 — Student Lifecycle / Student Success Level 1–2 Foundation Lift

## Purpose

The `mobile_push_gateway` module defines tenant-scoped push notification
delivery contracts, token registry, and outbound message dispatch policy.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `DeviceToken` | Registered mobile device token |
| `PushDispatch` | Outbound push delivery request |
| `DeliveryReceipt` | Provider delivery acknowledgement |

## Planned Capabilities (roadmap)

- Register/revoke device tokens
- Dispatch push notifications by audience segment
- Capture provider delivery outcomes
- Respect tenant notification preferences

## Dependencies

| Module | Relationship |
|---|---|
| `notification_center` | Notification source of truth |
| `student_portal` | Student channel preferences |
| `mobile_app` | Device integration surface |

## Maturity Gate Checklist

- [x] L1: module foundation documented
- [ ] L2: schemas + service skeleton
- [ ] L3: tests + tenant guard + FSM/events
- [ ] L4: API/frontend/KPI integration
