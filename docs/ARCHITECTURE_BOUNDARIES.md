# Architecture Boundaries

## Purpose

This document defines the stable architectural layer model for the platform baseline and the dependency boundaries that prevent erosion over time.

Scope:
- backend platform modules
- domain/product modules
- intelligence modules
- automation modules
- interface entry points

Non-goals:
- feature redesign
- large refactors
- product behavior changes

## Layer Model

### 1) Platform Core Layer

Primary responsibility: platform-wide governance and shared runtime capabilities.

Included modules:
- auth
- rbac
- tenants
- federation
- developer platform
- events
- webhooks
- jobs
- observability
- release gates

Code areas:
- `backend/app/platform/*` (core submodules)
- `backend/app/modules/auth/*`
- `backend/app/modules/rbac/*`
- `backend/app/modules/observability/*`
- `scripts/release_check.sh`

### 2) Domain / Product Core Layer

Primary responsibility: product business entities and workflows.

Included domains:
- students
- enrollments
- grades
- scheduling
- transcripts
- degree progress

Code areas:
- `backend/app/modules/students/*`
- `backend/app/modules/enrollments/*`
- `backend/app/modules/grades/*`
- `backend/app/modules/scheduling/*`
- `backend/app/modules/transcripts/*`
- `backend/app/modules/degree_progress/*`

### 3) Intelligence Layer

Primary responsibility: read-oriented intelligence and insights.

Included modules:
- analytics sink
- kpi engine
- semantic context
- education data graph
- ai copilot
- recommendations

Code areas:
- `backend/app/platform/analytics/*`
- `backend/app/platform/kpi/*`
- `backend/app/platform/context/*`
- `backend/app/platform/education_graph/*`
- `backend/app/platform/ai/*`

### 4) Automation Layer

Primary responsibility: deterministic event-driven orchestration.

Included modules:
- rules
- actions
- executions
- templates

Code areas:
- `backend/app/platform/automation/*`

### 5) Interface Layer

Primary responsibility: external surfaces and operational consoles.

Included interfaces:
- admin console
- rector dashboard
- ops console
- public APIs
- future marketplace UI (reserved)

Code areas:
- `backend/app/platform/router_admin.py`
- `backend/app/platform/router_public.py`
- `backend/app/platform/router_internal.py`
- `frontend/app/(admin)/console/*`
- `frontend/modules/platform/*`

## Dependency Direction

Allowed direction (top-level):
- Interface -> Platform Core
- Interface -> Intelligence
- Interface -> Automation
- Intelligence -> Platform Core
- Automation -> Platform Core
- Platform Core -> Domain/Product Core (only via approved services/repositories)

Disallowed direction examples:
- Interface -> internal implementation details (repositories, private module internals)
- AI -> raw domain table bypass (direct domain DB/table coupling)
- Automation -> ad-hoc side effects outside action registry
- Developer public API -> internal admin routes

## Public vs Internal Contracts

Public contracts:
- `/api/v1/public/*`
- stable frontend hooks/services in `frontend/modules/platform/*`

Internal contracts:
- `/api/v1/internal/*` for controlled system-to-system operations
- `/api/v1/admin/*` for privileged operator workflows

Rule:
- public clients never depend on internal/admin route contracts.

## Tenant Safety Boundary

Tenant safety requirements:
- no trust in client-provided tenant context without guard checks
- write/read operations remain tenant scoped
- cross-tenant access requires explicit privileged control-plane policy
- federation aggregation must remain institution/tenant scoped

## Governance Baseline

This layer model is normative for new modules and changes.
Any exception requires an explicit architecture note and approval in review checklist.
