# Timetable Approval Queue — Module Foundation Registry
# Maturity: L1 (A-023.5 foundation lift from L0)
# Category: Planned Expansion — Governance / Rector Review Workflow
# Action: A-023.5 — Governance / Rector / Ministry / Reporting Level 1–2 Foundation Lift

## Purpose

The `timetable_approval_queue` module defines tenant-scoped queue metadata for
human-governed timetable approval reviews and decision tracking references.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `TimetableApprovalItem` | Approval queue record metadata |
| `TimetableReviewerAssignment` | Human reviewer assignment pointer |
| `TimetableDecisionRef` | Decision trail reference marker |

## Planned Capabilities (roadmap)

- Track approval queue entries for governance review
- Attach reviewer assignment metadata
- Preserve read-only decision trail references
- Provide non-destructive reporting contract inputs

## Dependencies

| Module | Relationship |
|---|---|
| `human_approved_timetable_workflow` | Parent workflow linkage |
| `scheduling` | Timetable source metadata linkage |
| `audit` | Decision evidence trace linkage |

## Safety Notes

- No automatic approval execution.
- No automatic timetable mutation.
- No auto-apply behavior.

## Maturity Gate Checklist

- [x] L1: module foundation documented
- [ ] L2: schemas + service skeleton
- [ ] L3: tests + tenant guard + FSM/events
- [ ] L4: API/frontend/KPI integration
