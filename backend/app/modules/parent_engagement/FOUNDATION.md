# Parent Engagement — Module Foundation Registry
# Maturity: L1 (A-023.2 foundation lift from L0)
# Category: Planned Expansion — Student Lifecycle / Family Communication
# Action: A-023.2 — Student Lifecycle / Student Success Level 1–2 Foundation Lift

## Purpose

The `parent_engagement` module defines tenant-scoped parent communication
profiles, consent markers, and student-associated communication workflows.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `ParentProfile` | Parent/guardian contact profile |
| `StudentParentLink` | Student-to-parent relationship mapping |
| `ConsentRecord` | Consent preferences by communication type |

## Planned Capabilities (roadmap)

- Register and maintain parent/guardian contacts
- Track explicit communication consent state
- Route student status notifications to approved contacts
- Maintain tenant-specific compliance boundaries

## Dependencies

| Module | Relationship |
|---|---|
| `students` | Student identity linkage |
| `notification_center` | Message delivery channel |
| `student_services` | Case-related communication context |

## Maturity Gate Checklist

- [x] L1: module foundation documented
- [ ] L2: schemas + service skeleton
- [ ] L3: tests + tenant guard + FSM/events
- [ ] L4: API/frontend/KPI integration
