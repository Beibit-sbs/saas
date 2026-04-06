# Guardrails

## Objective

Prevent architectural erosion while allowing controlled platform growth.

## Core Rule

No layer may bypass its approved access contracts.

## Access Contracts

### AI Layer Contracts

Allowed:
- `app.platform.ai.retrieval` -> `app.platform.analytics.service`
- `app.platform.ai.retrieval` -> `app.platform.kpi.service`
- `app.platform.ai.retrieval` -> `app.platform.context.service`
- `app.platform.ai.retrieval` -> `app.platform.automation.service`
- `app.platform.ai.retrieval` -> `app.platform.education_graph.service`

Forbidden shortcuts:
- direct coupling from AI services to raw domain table paths as a primary retrieval path
- direct import of internal/admin routers into AI services

Policy:
- AI answers are retrieval-oriented and tenant-scoped.

### Automation Layer Contracts

Allowed:
- automation engine dispatches side effects through action registry entrypoint (`execute_action`)
- action executors perform explicit, auditable operations

Forbidden shortcuts:
- direct ad-hoc mutation side effects from engine loop bypassing action registry
- opaque dynamic execution paths without typed action `type`
- direct graph writes from automation modules bypassing graph service contracts

Policy:
- automation side effects must remain deterministic and registry-controlled.

### Developer Platform Contracts

Allowed:
- developer integrations consume `/api/dev/*` routes and scope-checked credentials
- backend developer auth validates app key/secret + tenant + scope

Forbidden shortcuts:
- developer consumers depending on `/api/v1/admin/*` or `/api/v1/internal/*`
- public router imports from internal/admin router modules

Policy:
- developer platform remains public-contract-only.

### Federation Contracts

Allowed:
- institution/tenant-scoped federation queries and aggregation

Forbidden shortcuts:
- unscoped cross-tenant aggregation
- federation logic bypassing tenant/institution constraints

### Education Data Graph Contracts

Allowed:
- graph writes through `app.platform.education_graph.service`
- event-driven updates through dedicated outbox handler

Forbidden shortcuts:
- direct cross-tenant graph reads
- direct graph table access from UI or AI service layer bypassing retrieval

### UI Contracts

Allowed:
- frontend pages depend on stable API/hook modules (`frontend/modules/platform/*`)

Forbidden shortcuts:
- UI dependencies on backend internals or private implementation modules

## Tenant Boundary Guardrails

1. Do not trust tenant_id from client input without guard/validation.
2. Admin/control-plane routes require actor/permission controls.
3. Public API routes require scope validation for developer apps.
4. Internal routes require internal token where configured.

## Lightweight Enforcement in Codebase

Implemented enforcement helpers:
- architecture tests for forbidden imports and route-surface isolation
- checks for admin actor dependency pattern in platform admin router
- checks that automation engine executes via action registry entrypoint
- checks that AI retrieval path uses approved platform retrieval services

File:
- `backend/tests/platform/test_platform_architecture_guardrails_v1.py`

Mandatory CI gate:
- job: `architecture-governance-gate`
- command: `pytest -q tests/platform/test_platform_architecture_guardrails_v1.py`
- behavior: isolated failure surface; any failure blocks merge/release

## Architectural Review Checklist

Use this checklist for every new module/endpoint:

1. Does this change bypass approved layer contracts?
2. Does this endpoint trust tenant_id from client input?
3. Does AI access raw domain tables directly?
4. Does automation mutate domain state outside approved actions?
5. Does developer platform touch internal admin routes?
6. Does federation aggregate beyond allowed scope?
7. Does UI depend on unstable backend internals?
8. Are tenant guards and permission checks explicit and test-covered?
9. Are new dependencies aligned with `ARCHITECTURE_BOUNDARIES.md`?
10. If an exception is needed, is it documented and approved?

## Change Control

For each architecture-impacting PR:
- include a brief boundary-impact note
- update tests/docs if a contract changes
- block merge if guardrails test fails
