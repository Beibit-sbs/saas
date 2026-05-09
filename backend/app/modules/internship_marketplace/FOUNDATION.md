# Internship Marketplace — Module Foundation Registry
# Maturity: L1 (A-023.2 foundation lift from L0)
# Category: Planned Expansion — Student Lifecycle / Employability
# Action: A-023.2 — Student Lifecycle / Student Success Level 1–2 Foundation Lift

## Purpose

The `internship_marketplace` module manages internship postings, student
applications, and placement tracking for multi-tenant university operations.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `InternshipPosting` | Internship opportunity definition |
| `InternshipApplication` | Student application record |
| `PlacementRecord` | Accepted placement lifecycle record |

## Planned Capabilities (roadmap)

- Publish and retire internship postings
- Student application submission and status tracking
- Placement confirmation and completion status
- Employer feedback linkage

## Dependencies

| Module | Relationship |
|---|---|
| `career_services` | Opportunity curation |
| `students` | Applicant profile linkage |
| `notification_center` | Application status alerts |

## Maturity Gate Checklist

- [x] L1: module foundation documented
- [ ] L2: schemas + service skeleton
- [ ] L3: tests + tenant guard + FSM/events
- [ ] L4: API/frontend/KPI integration
