# Lab Operations — Module Foundation Registry
# Maturity: L1 (A-023.3 foundation lift from L0)
# Category: Planned Expansion — Campus / Facilities Operations
# Action: A-023.3 — Campus / Facilities / Security Level 1–2 Foundation Lift

## Purpose

The `lab_operations` module defines tenant-scoped lab resource operations,
equipment availability tracking, access windows, and safety-compliance metadata.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `LabResource` | Resource catalog item for a lab |
| `LabAccessWindow` | Allowed access slot policy |
| `LabSafetyChecklist` | Safety requirements and completion markers |

## Planned Capabilities (roadmap)

- Track lab resource availability and status
- Manage approved access windows and constraints
- Maintain non-destructive safety checklist records
- Coordinate with equipment booking workflows

## Dependencies

| Module | Relationship |
|---|---|
| `equipment_booking` | Reservation linkage |
| `facilities_work_orders` | Maintenance dependency |
| `access_control` | Policy reference only (no auto-enforcement) |

## Safety Notes

- No automatic lockout or punitive enforcement behavior at L1.
- No direct access mutation side effects.

## Maturity Gate Checklist

- [x] L1: module foundation documented
- [ ] L2: schemas + service skeleton
- [ ] L3: tests + tenant guard + FSM/events
- [ ] L4: API/frontend/KPI integration
