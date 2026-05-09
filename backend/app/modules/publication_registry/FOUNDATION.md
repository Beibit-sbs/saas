# Publication Registry — Module Foundation Registry
# Maturity: L1 (A-023.5 foundation lift from L0)
# Category: Planned Expansion — Governance / Reporting
# Action: A-023.5 — Governance / Rector / Ministry / Reporting Level 1–2 Foundation Lift

## Purpose

The `publication_registry` module defines tenant-scoped publication registry
metadata for governance reporting catalogs and evidence-ready publication
indexing references.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `PublicationEntry` | Publication metadata index |
| `PublicationPolicyTag` | Governance/policy classification labels |
| `PublicationEvidenceRef` | Evidence reference pointer for reporting |

## Planned Capabilities (roadmap)

- Register publication metadata for governance reporting scopes
- Tag publication entries with policy/compliance labels
- Provide evidence references for audit/reporting workflows
- Support read-only reporting contracts

## Dependencies

| Module | Relationship |
|---|---|
| `research` | Upstream publication source linkage |
| `audit` | Evidence traceability references |
| `knowledge_retrieval` | Retrieval-index linkage |

## Safety Notes

- No automatic ministry submission.
- No automatic compliance scoring.
- No synthetic KPI/dashboard values.

## Maturity Gate Checklist

- [x] L1: module foundation documented
- [ ] L2: schemas + service skeleton
- [ ] L3: tests + tenant guard + FSM/events
- [ ] L4: API/frontend/KPI integration
