# Library Circulation — Module Foundation Registry
# Maturity: L1 (A-023.1 foundation lift from L0)
# Category: Planned Expansion — Academic Services
# Action: A-023.1 — Academic/Education Level 1–2 Foundation Lift

## Purpose

The `library_circulation` module manages physical and digital library item
lending, returns, holds, and overdue enforcement for the multi-tenant
university platform.

## Key Entities (planned)

| Entity | Description |
|---|---|
| `LibraryItem` | Catalogue entry (book, journal, device) |
| `LoanRecord` | Active or historical loan for a patron |
| `Hold` | Reservation queue entry for an unavailable item |
| `OverdueFine` | Penalty record for late return |

## Planned Capabilities (roadmap)

- Loan checkout and return workflow with due-date computation
- Hold queue management (FIFO per item copy)
- Overdue fine accrual and waiver
- Patron eligibility check against `access_control` module
- Item search by ISBN / title / author
- Inter-library loan bridge (future)

## Dependencies

| Module | Relationship |
|---|---|
| `access_control` | Patron identity and role validation |
| `students` | Student patron profile |
| `finance` / `budget_planning` | Fine payment collection |

## Integration Points (L2 scope, not yet implemented)

- `POST /library/loans` — checkout an item to a patron
- `PATCH /library/loans/{loan_id}/return` — record return
- `GET /library/items?q=` — catalogue search
- `GET /library/fines?patron_id=` — list overdue fines

## Maturity Gate Checklist

- [x] L1: Module registered; key entities and dependencies documented
- [ ] L2: Pydantic schemas + service skeleton
- [ ] L3: Backend tests, tenant guard, FSM, events
- [ ] L4: REST router, frontend integration
