# Research Projects — Module Foundation Registry
# Maturity: L1 (A-023.1 foundation lift from L0)
# Category: Planned Expansion — Research & Innovation
# Action: A-023.1 — Academic/Education Level 1–2 Foundation Lift

## Purpose

The `research_projects` module tracks active research projects, principal
investigators, team members, milestones, and deliverables within the
multi-tenant university platform.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `ResearchProject` | Project record (title, PI, start/end, status) |
| `ProjectMember` | Team membership with role (PI / Co-PI / Researcher / RA) |
| `Milestone` | Scheduled deliverable or review point |
| `Deliverable` | Output artefact (report, dataset, publication stub) |

## Planned Capabilities (roadmap)

- Project lifecycle: DRAFT → ACTIVE → COMPLETED / CANCELLED
- PI assignment and co-investigator management
- Milestone tracking with overdue alerts
- Link to `research_grants` for funding source
- Link to `publication_registry` for output registration
- Ethics clearance reference from `research_ethics`

## Dependencies

| Module | Relationship |
|---|---|
| `research_grants` | Optional funding source reference |
| `research_ethics` | Ethics approval gate |
| `publication_registry` | Registers outputs |
| `lab_operations` | Lab resource allocation |

## Integration Points (L2 scope, not yet implemented)

- `POST /research/projects` — register new project
- `GET /research/projects/{id}` — project detail
- `POST /research/projects/{id}/milestones` — add milestone
- `PATCH /research/projects/{id}/status` — lifecycle transition

## Maturity Gate Checklist

- [x] L1: Module registered; key entities and dependencies documented
- [ ] L2: Pydantic schemas + service skeleton
- [ ] L3: Backend tests, tenant guard, FSM, events
- [ ] L4: REST router, frontend integration
