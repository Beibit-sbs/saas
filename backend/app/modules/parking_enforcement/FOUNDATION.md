# Parking Enforcement — Module Foundation Registry
# Maturity: L1 (A-023.2 foundation lift from L0)
# Category: Planned Expansion — Student Lifecycle / Campus Operations
# Action: A-023.2 — Student Lifecycle / Student Success Level 1–2 Foundation Lift

## Purpose

The `parking_enforcement` module defines tenant-scoped parking violation
tracking, notice issuance, and compliance status workflows.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `ParkingViolation` | Violation record with rule reference |
| `EnforcementNotice` | Notice sent to vehicle owner/permit holder |
| `AppealRecord` | Appeal request and disposition metadata |

## Planned Capabilities (roadmap)

- Record parking violations with policy linkage
- Issue and track enforcement notices
- Process appeal workflow metadata
- Integrate with permit records and payment status

## Dependencies

| Module | Relationship |
|---|---|
| `parking_permit_ops` | Permit ownership validation |
| `students` | Student owner context |
| `notification_center` | Notice delivery channel |

## Maturity Gate Checklist

- [x] L1: module foundation documented
- [ ] L2: schemas + service skeleton
- [ ] L3: tests + tenant guard + FSM/events
- [ ] L4: API/frontend/KPI integration
