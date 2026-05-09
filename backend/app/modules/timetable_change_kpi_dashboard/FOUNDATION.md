# Timetable Change KPI Dashboard — Module Foundation Registry
# Maturity: L1 (A-023.5 foundation lift from L0)
# Category: Planned Expansion — Governance / Reporting
# Action: A-023.5 — Governance / Rector / Ministry / Reporting Level 1–2 Foundation Lift

## Purpose

The `timetable_change_kpi_dashboard` module defines tenant-scoped KPI metadata
contracts for timetable-change reporting, governance visibility, and evidence
indexing references.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `TimetableKpiSnapshotRef` | KPI snapshot reference metadata |
| `TimetableKpiIndicator` | Indicator catalog metadata |
| `TimetableDashboardEvidenceRef` | Evidence pointer for reporting review |

## Planned Capabilities (roadmap)

- Store KPI indicator metadata contracts
- Preserve snapshot references for governance reporting
- Provide evidence pointers for rector/ministry review trails
- Expose read-only data contracts only

## Dependencies

| Module | Relationship |
|---|---|
| `analytics` | KPI source linkage |
| `scheduling` | Timetable-change context linkage |
| `audit` | Evidence trace references |

## Safety Notes

- No synthetic KPI generation.
- No fake dashboard value injection.
- No automatic ministry submission.

## Maturity Gate Checklist

- [x] L1: module foundation documented
- [ ] L2: schemas + service skeleton
- [ ] L3: tests + tenant guard + FSM/events
- [ ] L4: API/frontend/KPI integration
