# Parking Permit Ops — Module Foundation Registry
# Maturity: L1 (A-023.2 foundation lift from L0)
# Category: Planned Expansion — Student Lifecycle / Campus Operations
# Action: A-023.2 — Student Lifecycle / Student Success Level 1–2 Foundation Lift

## Purpose

The `parking_permit_ops` module defines tenant-scoped permit application,
approval, issuance, and renewal lifecycle contracts.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `ParkingPermitApplication` | Permit application request |
| `ParkingPermit` | Active permit metadata |
| `PermitRenewal` | Renewal record and decision status |

## Planned Capabilities (roadmap)

- Submit and review permit applications
- Issue permit with validity period
- Process renewals and status changes
- Link permits to vehicle and owner records

## Dependencies

| Module | Relationship |
|---|---|
| `students` | Student owner identity |
| `parking_enforcement` | Compliance and violation linkage |
| `notification_center` | Status and renewal reminders |

## Maturity Gate Checklist

- [x] L1: module foundation documented
- [ ] L2: schemas + service skeleton
- [ ] L3: tests + tenant guard + FSM/events
- [ ] L4: API/frontend/KPI integration
