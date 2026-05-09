# LMS Assessment Center — Module Foundation Registry
# Maturity: L1 (A-023.1 foundation lift from L0)
# Category: Planned Expansion — Academic Technology
# Action: A-023.1 — Academic/Education Level 1–2 Foundation Lift

## Purpose

The `lms_assessment_center` module provides a unified gateway for Learning
Management System (LMS) integration: submission intake, grade synchronisation,
and assessment tracking within the multi-tenant university platform.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `LmsSubmission` | Student assignment/quiz submission record |
| `LmsGrade` | Grade entry tied to a submission and course enrolment |
| `LmsAssessment` | Assessment definition (quiz, assignment, exam) per course |
| `LmsSyncJob` | Periodic sync task that pulls grades from external LMS |

## Planned Capabilities (roadmap)

- Ingest submission events from LMS (Moodle / Canvas webhook adapters)
- Grade normalisation to the platform's 100-point scale
- Roster sync with `enrollments` module
- Conflict detection: duplicate grade entries per student/assessment
- Read API: per-student, per-course grade summary for degree-progress module

## Dependencies

| Module | Relationship |
|---|---|
| `enrollments` | Validate student is enrolled before accepting submission |
| `courses` | Resolve course context |
| `degree_progress` | Downstream consumer of normalised grades |
| `academic_records` | Source of truth for final grade commit |

## Integration Points (L2 scope, not yet implemented)

- `POST /lms/submissions` — submit assignment/quiz attempt
- `GET /lms/grades?student_id=&course_id=` — fetch grade summary
- `POST /lms/sync` — trigger grade pull from external LMS

## Maturity Gate Checklist

- [x] L1: Module registered; key entities and dependencies documented
- [ ] L2: Pydantic schemas + service skeleton
- [ ] L3: Backend tests, tenant guard, FSM, events
- [ ] L4: REST router, frontend integration
