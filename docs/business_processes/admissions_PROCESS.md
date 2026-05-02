# Admissions Process — Business Process Documentation

> **Module**: `app.modules.admissions`  
> **Phase**: XXXIII.4 — Transition Guard Matrix  
> **Status**: Production-ready  

---

## Overview

The Admissions module manages the end-to-end lifecycle of student applications from initial creation through final decision. All stage transitions are enforced by the **Transition Guard Matrix** (`ADMISSIONS_ALLOWED_STAGE_TRANSITIONS`) defined in `service.py`.

---

## Application Stage Machine

```
NEW ──→ RECEIVED ──→ UNDER_REVIEW ──→ DECISION_PENDING ──→ CONCLUDED
          ↑               ↑
          └──── (back)    └──── (back, for clarification)
```

### Stages

| Stage              | Value               | Description                                  |
|--------------------|---------------------|----------------------------------------------|
| `NEW`              | `new`               | Application created, not yet submitted        |
| `RECEIVED`         | `received`          | Application submitted by applicant            |
| `UNDER_REVIEW`     | `under_review`      | Admissions staff reviewing the application    |
| `DECISION_PENDING` | `decision_pending`  | Awaiting final decision from leadership       |
| `CONCLUDED`        | `concluded`         | Final decision made (see `conclusion_type`)   |

### Conclusion Types (within `CONCLUDED`)

| Conclusion   | Value      | Meaning                         |
|--------------|------------|---------------------------------|
| `ACCEPTED`   | `accepted` | Application approved             |
| `REJECTED`   | `rejected` | Application denied               |

---

## Transition Guard Matrix

Defined as `ADMISSIONS_ALLOWED_STAGE_TRANSITIONS` in `backend/app/modules/admissions/service.py`.

| From Stage         | Allowed Target Stages                              |
|--------------------|----------------------------------------------------|
| `NEW`              | `RECEIVED`                                         |
| `RECEIVED`         | `UNDER_REVIEW`, `NEW` (resubmit)                  |
| `UNDER_REVIEW`     | `DECISION_PENDING`, `RECEIVED` (clarification)    |
| `DECISION_PENDING` | `CONCLUDED`, `UNDER_REVIEW` (more review)         |
| `CONCLUDED`        | _(none — terminal state)_                          |

### Explicitly Blocked Transitions

| Blocked Transition              | Reason                                                  |
|---------------------------------|---------------------------------------------------------|
| `NEW → CONCLUDED`               | Must follow full review pipeline                        |
| `RECEIVED → CONCLUDED`          | Must follow full review pipeline                        |
| `UNDER_REVIEW → CONCLUDED`      | Decision must be formally recorded in DECISION_PENDING  |
| `CONCLUDED → any`               | Terminal state — final decisions are immutable          |
| `REJECTED → ACCEPTED` (via re-open) | CONCLUDED is terminal; no conclusion_type reversal |

---

## Guard Function

```python
def _assert_stage_transition_allowed(
    current_stage: ApplicationStage,
    target_stage: ApplicationStage,
) -> None:
    ...
```

- Called in `transition_stage()`, `submit_application()`, and `finalize_workflow_decision()`.
- Raises `ValueError` with a descriptive message when the transition is blocked.
- Blocked transitions produce **no DB mutations** and **no domain events**.

---

## Workflow Integration

1. **Submit** (`submit_application`): `NEW → RECEIVED` + starts admissions workflow instance.
2. **Transition** (`transition_stage`): Manual stage moves via admin console.
3. **Decision** (`make_decision`): Creates `ApplicationDecisionModel` when stage is `DECISION_PENDING`.
4. **Finalize** (`finalize_workflow_decision`): Workflow engine callback; `DECISION_PENDING → CONCLUDED`.

---

## Domain Events Emitted

| Event Type                                          | Trigger                          |
|-----------------------------------------------------|----------------------------------|
| `admissions.application.submitted`                  | `submit_application` succeeds    |
| `admissions.application.stage_changed`              | `transition_stage` succeeds      |
| `admissions.application.decision_made`              | `make_decision` succeeds         |
| `admissions.application.workflow_decision_finalized`| `finalize_workflow_decision` succeeds |

Events are published **after** successful `db.flush()` and before `db.commit()`, ensuring event ordering is tied to persistence.

---

## Tenant Isolation

- Every service method requires `tenant_id` as a mandatory parameter.
- All DB queries include `AND tenant_id = :tenant_id`.
- No implicit tenant defaults or fallbacks.
- Cross-tenant requests receive a `ValueError` (application not found), surfaced as HTTP 404/403.

---

## Test Coverage

Transition Guard Matrix tests: `backend/tests/test_admissions_transition_guard_xxxiii4.py`

| # | Test                                              |
|---|---------------------------------------------------|
| 1 | valid NEW→RECEIVED succeeds                       |
| 2 | valid transition emits `admissions.application.submitted` |
| 3 | invalid NEW→CONCLUDED is blocked                  |
| 4 | invalid RECEIVED→CONCLUDED is blocked             |
| 5 | CONCLUDED terminal state has no outbound transitions |
| 6 | DECISION_PENDING→CONCLUDED is the only valid path |
| 7 | blocked transition emits no event                 |
| 8 | blocked transition does not persist state change  |
| 9 | tenant mismatch remains blocked (isolation)       |
|10 | valid transition publishes event after persistence |
