# SBS_UB_PROJECT_CONTEXT_2026.md
## Real Project Context Baseline — A-012.CONTEXT

**Date:** 2026-05-04
**Author:** GitHub Copilot — Static Repository Inspection
**Status:** BASELINE CREATED — NO CODE CHANGES MADE

---

## 1. Executive Summary

SBS UB is a full-stack multi-tenant university management platform built on FastAPI (Python 3.12) + React (Next.js) + PostgreSQL + Redis + Celery. As of May 2026, the codebase is production-quality with:

- **113 backend modules** across `backend/app/modules/`
- **82 Alembic migrations** applied
- **211 EntityConfig declarations** in `university_core/shared.py`
- **260 events registered** in `platform/events/registry.py`
- **38 signal scenarios** in `brain_core/registry.py` (SignalRegistry)
- **20 decision scenarios** in `brain_core/registry.py` (DecisionRegistry)
- **110 API endpoints** in `brain_core/router.py` alone, 685+ permission-guarded endpoints across all routers
- **541 backend test files**, **108 frontend test files** (excluding node_modules)
- **102 frontend pages** in `frontend/app/`; **70 admin console page directories**; **58 frontend module directories**
- **31 shared UI components** in `frontend/shared/ui/`

The Brain Core is a fully implemented autonomous decision engine with signal intake → context build → classify → reason → policy guard → action plan → dispatch → outcome → learning → replay cycle, including LLM bridge (Ollama/deepseek-r1:8b, optional), agent orchestration (Phases XXII-XXXII), and policy rollout governance.

**No greenfield work is needed for core infrastructure.** The next phase (A-012.2+) is additive integration, not construction.

---

## 2. Method and Source of Truth

**Primary source:** Current repository code (static inspection only, no code execution in production).
- Scanned: `backend/app/modules/`, `backend/app/platform/`, `backend/alembic/versions/`, `frontend/app/`, `frontend/modules/`, `frontend/shared/`, `frontend/__tests__/`, `backend/tests/`, `scripts/`
- All claims in this document are backed by file-system evidence.

**Secondary reference:** `SBS_UB.md`, `SBS_UB_MASTER_PLAN.md`, `SBS_UB_BRAIN_CORE_ARCHITECTURE.md`, A-010/A-011/A-012 reports — used only for intent/history context.

**No code changes were made during this inspection.**

Old documents may reflect aspirational or superseded state. Where a document claim conflicts with code inspection, **code wins.**

---

## 3. Current Official Tracker Snapshot

From `SBS_UB.md` CONTROL BLOCK (as of last update — verified via file):

| Field | Value |
|---|---|
| `current_stage` | A-012.3 (per last update) |
| `next_action_id` | A-012.2 (reset per this A-012.CONTEXT baseline) |
| A-011 | ✅ Complete |
| A-012.0 | ✅ Complete (25-feature map, 8 groups) |
| A-012.1 | ✅ Complete (12 scored, 5 selected: H-1, A-1, B-2, C-1, D-1) |
| A-012.2 | ⏸ Paused pending this context baseline |
| A-012.CONTEXT | ✅ **This document** |
| A-012.3–A-012.5 | ⬜ Not started |

---

## 4. Backend Module Baseline

### 4.1 Module File Inventory

Scanned `backend/app/modules/` — 113 modules found. Below: R=router.py, S=service.py, Sc=schemas.py, M=models.py, Re=repository.py.

| Module | R | S | Sc | M | Re | Events | Brain | Status |
|---|---|---|---|---|---|---|---|---|
| academic_integrity | Y | Y | Y | - | - | Y | Y | ACTIVE_FULL_STACK |
| academic_records | Y | Y | Y | Y | - | Y | Y | ACTIVE_FULL_STACK |
| access_control | - | Y | - | - | - | Y | Y | ACTIVE_SERVICE_ONLY |
| accreditation | Y | Y | Y | - | - | Y | - | ACTIVE_FULL_STACK |
| admin | Y | - | - | - | - | - | - | ACTIVE_BACKEND_ONLY |
| admissions | Y | Y | Y | Y | - | Y | Y | ACTIVE_FULL_STACK |
| advising | Y | Y | Y | - | - | Y | Y | ACTIVE_FULL_STACK |
| ai_admissions_scoring | - | Y | - | - | - | Y | Y | ACTIVE_SERVICE_ONLY |
| ai_gateway | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| ai_guardrails | - | - | Y | - | - | - | - | PLANNED_OR_STUB |
| ai_plagiarism | - | Y | - | - | - | Y | - | ACTIVE_SERVICE_ONLY |
| alumni | Y | Y | Y | - | - | Y | Y | ACTIVE_FULL_STACK |
| alumni_donation_portal | - | Y | - | - | - | - | - | ACTIVE_SERVICE_ONLY |
| analytics | Y | - | Y | - | - | - | - | ACTIVE_BACKEND_ONLY |
| asset_inventory | Y | Y | Y | - | - | Y | - | ACTIVE_FULL_STACK |
| attendance | - | Y | - | - | - | Y | Y | ACTIVE_SERVICE_ONLY |
| audit | Y | Y | - | Y | - | - | - | ACTIVE_FULL_STACK |
| auth | Y | - | - | - | - | - | - | ACTIVE_BACKEND_ONLY |
| backup | Y | Y | - | - | - | - | - | ACTIVE_FULL_STACK |
| billing | Y | Y | Y | Y | - | Y | - | ACTIVE_FULL_STACK |
| blockchain_diploma | - | Y | - | - | - | - | Y | ACTIVE_SERVICE_ONLY |
| brain_core | Y | Y | Y | Y | - | - | N/A | ACTIVE_FULL_STACK |
| budget_planning | Y | Y | Y | - | - | Y | Y | ACTIVE_FULL_STACK |
| campus_sla | Y | Y | Y | - | - | Y | - | ACTIVE_FULL_STACK |
| career_services | Y | Y | Y | - | - | Y | Y | ACTIVE_FULL_STACK |
| communications | Y | Y | Y | - | - | Y | Y | ACTIVE_FULL_STACK |
| conference_management | - | Y | - | - | - | Y | - | ACTIVE_SERVICE_ONLY |
| contracts_hr | - | Y | - | - | - | - | - | ACTIVE_SERVICE_ONLY |
| counseling | - | Y | - | - | - | - | Y | ACTIVE_SERVICE_ONLY |
| courses | Y | Y | Y | Y | - | Y | Y | ACTIVE_FULL_STACK |
| currency_localization | Y | Y | - | - | - | - | - | ACTIVE_FULL_STACK |
| degree_progress | Y | Y | Y | Y | - | - | - | ACTIVE_FULL_STACK |
| delinquency_collections | Y | Y | Y | - | - | Y | - | ACTIVE_FULL_STACK |
| digital_documents | - | Y | - | - | - | - | - | ACTIVE_SERVICE_ONLY |
| dining | Y | Y | Y | - | - | Y | - | ACTIVE_FULL_STACK |
| enrollments | Y | Y | Y | Y | - | Y | Y | ACTIVE_FULL_STACK |
| equipment_booking | Y | Y | Y | - | - | Y | Y | ACTIVE_FULL_STACK |
| events_management | - | Y | - | - | - | Y | - | ACTIVE_SERVICE_ONLY |
| exam_governance | Y | Y | Y | - | - | Y | - | ACTIVE_FULL_STACK |
| exam_proctoring | - | Y | - | - | - | - | - | ACTIVE_SERVICE_ONLY |
| expense_controls | Y | Y | Y | - | - | Y | - | ACTIVE_FULL_STACK |
| facilities_work_orders | Y | Y | Y | - | - | Y | - | ACTIVE_FULL_STACK |
| faculty | Y | Y | Y | Y | - | Y | Y | ACTIVE_FULL_STACK |
| faculty_copilot | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| faculty_performance_kpis | Y | Y | Y | - | - | Y | - | ACTIVE_FULL_STACK |
| feature_flags | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| financial_aid | Y | Y | Y | - | - | Y | Y | ACTIVE_FULL_STACK |
| grades | Y | Y | Y | Y | - | - | Y | ACTIVE_FULL_STACK |
| help | Y | - | - | - | - | - | - | ACTIVE_BACKEND_ONLY |
| housing | Y | Y | Y | - | - | - | Y | ACTIVE_FULL_STACK |
| hr_payroll | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| i18n | Y | Y | - | - | - | - | - | ACTIVE_FULL_STACK |
| identity | Y | Y | - | Y | - | - | - | ACTIVE_FULL_STACK |
| integrations | Y | Y | - | - | - | - | - | ACTIVE_FULL_STACK |
| internship | - | Y | - | - | - | - | Y | ACTIVE_SERVICE_ONLY |
| interventions | Y | Y | Y | Y | - | - | Y | ACTIVE_FULL_STACK |
| invoices | Y | Y | - | - | - | - | - | ACTIVE_FULL_STACK |
| ip_management | Y | Y | Y | - | - | Y | - | ACTIVE_FULL_STACK |
| jobs | Y | Y | Y | Y | - | - | - | ACTIVE_FULL_STACK |
| knowledge_retrieval | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| ldap | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| library | - | Y | - | - | - | Y | - | ACTIVE_SERVICE_ONLY |
| lms_content | - | Y | - | - | - | Y | Y | ACTIVE_SERVICE_ONLY |
| model_evaluation | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| observability | - | - | - | - | - | Y | Y | PLATFORM_INFRA |
| online_payments | Y | Y | - | - | - | Y | - | ACTIVE_FULL_STACK |
| operations | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| org_structure | Y | Y | Y | Y | - | - | - | ACTIVE_FULL_STACK |
| parent_portal | - | Y | - | - | - | - | - | ACTIVE_SERVICE_ONLY |
| parking | - | Y | - | - | - | Y | - | ACTIVE_SERVICE_ONLY |
| patents | - | Y | - | - | - | Y | - | ACTIVE_SERVICE_ONLY |
| payment_reconciliation | Y | Y | - | - | - | Y | - | ACTIVE_FULL_STACK |
| pdpl | Y | - | - | - | - | - | - | ACTIVE_BACKEND_ONLY |
| plans | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| platform | Y | - | - | - | - | - | - | PLATFORM_INFRA |
| platform_shared | - | - | - | - | - | Y | - | PLATFORM_INFRA |
| procurement | Y | Y | Y | - | - | Y | - | ACTIVE_FULL_STACK |
| profiles | Y | Y | Y | Y | - | - | - | ACTIVE_FULL_STACK |
| programs | Y | Y | Y | Y | - | Y | Y | ACTIVE_FULL_STACK |
| prompt_management | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| publications | - | Y | - | - | - | Y | - | ACTIVE_SERVICE_ONLY |
| quotas | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| rbac | Y | Y | - | - | - | - | - | ACTIVE_FULL_STACK |
| research | Y | Y | Y | - | - | Y | Y | ACTIVE_FULL_STACK |
| research_ethics | Y | Y | Y | - | - | Y | Y | ACTIVE_FULL_STACK |
| room_booking | - | Y | - | - | - | Y | - | ACTIVE_SERVICE_ONLY |
| scheduling | Y | Y | Y | Y | - | Y | Y | ACTIVE_FULL_STACK |
| scholarship | Y | Y | Y | - | - | Y | Y | ACTIVE_FULL_STACK |
| security | - | - | - | - | - | - | - | NEEDS_REVIEW |
| security_operations | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| service_accounts | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| sso_saml | - | Y | - | - | - | - | - | ACTIVE_SERVICE_ONLY |
| student_ai_tutor | - | Y | - | - | - | Y | - | ACTIVE_SERVICE_ONLY |
| student_feedback | - | Y | - | - | - | Y | - | ACTIVE_SERVICE_ONLY |
| student_id_card | - | Y | - | - | - | - | - | ACTIVE_SERVICE_ONLY |
| student_life | Y | Y | Y | - | - | Y | Y | ACTIVE_FULL_STACK |
| student_portal | - | Y | - | - | - | Y | - | ACTIVE_SERVICE_ONLY |
| students | Y | Y | Y | Y | - | - | Y | ACTIVE_FULL_STACK |
| student_services | Y | Y | Y | - | - | Y | Y | ACTIVE_FULL_STACK |
| subscriptions | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| syllabus_governance | Y | Y | Y | - | - | Y | - | ACTIVE_FULL_STACK |
| teaching_quality | Y | Y | - | - | - | Y | - | ACTIVE_FULL_STACK |
| tenants | Y | Y | Y | Y | - | - | - | ACTIVE_FULL_STACK |
| thesis | Y | Y | Y | - | - | - | Y | ACTIVE_FULL_STACK |
| transcripts | Y | Y | Y | Y | - | Y | Y | ACTIVE_FULL_STACK |
| transport | Y | Y | Y | - | - | Y | - | ACTIVE_FULL_STACK |
| two_factor_auth | - | Y | - | - | - | - | - | ACTIVE_SERVICE_ONLY |
| university_core | - | - | - | - | - | - | - | PLATFORM_INFRA |
| usage | Y | Y | Y | - | - | - | - | ACTIVE_FULL_STACK |
| visitor_management | - | Y | - | - | - | Y | - | ACTIVE_SERVICE_ONLY |
| workflows | Y | - | Y | Y | - | - | - | ACTIVE_FULL_STACK |

**Summary:**
- ACTIVE_FULL_STACK: ~70 modules
- ACTIVE_SERVICE_ONLY (no router yet): ~28 modules
- PLATFORM_INFRA: 4 (university_core, platform, platform_shared, observability)
- NEEDS_REVIEW: 1 (security — empty dir)
- PLANNED_OR_STUB: 1 (ai_guardrails — schemas only)

---

## 5. API Route Baseline

### 5.1 Overview

| Metric | Value |
|---|---|
| Total `@router.*` decorators across `brain_core/router.py` | 110 |
| Total `permission_dependency` / `has_permission` uses in all `router.py` files | 685 |
| Total `Depends(get_current_tenant)` uses in all `router.py` files | 411 |
| `tenant_id` mentions in all `router.py` files | 1392 |

### 5.2 Brain Core Router Endpoints (110 total)

Key groups:
- **Health & Signals:** `/health`, `/tenants/{tenant_id}/signals`, `/tenants/{tenant_id}/decisions`, `/decisions/{decision_id}`, `/explanations/{decision_id}`
- **Policy:** `/policy/{tenant_id}` (GET/PUT), `/reasoning/policy/{tenant_id}`, `/policy-drift/{tenant_id}`, `/policy-optimization/{tenant_id}`, `/policy-rollout-plan/{tenant_id}`, rollout execute/rollback
- **Simulation:** `/simulate/student-risk`, `/simulate/what-if`, `/simulate/thesis-delay`, `/simulate/faculty-overload`, `/simulate/budget-variance`, `/simulate/vendor-sla-degraded`, `/simulate/contract-risk-high`, `/simulate/supply-low`, `/simulate/payment-overdue`, `/simulate/facility-issue`, `/simulate/cleaning-service-missed`, `/simulate/maintenance-predicted-due`, `/simulate/utilities-spike`, `/simulate/student-life-wellbeing`, `/simulate/student-life-disciplinary`, `/simulate/research-grant-deadline`, `/simulate/research-publication-stagnant`, `/simulate/research-grant-pipeline-risk`, `/simulate/research-lab-utilization-low`
- **Predict/Detect:** `/predict`, `/anomalies`, `/recommendations/{tenant_id}`, `/executive-kpi/{tenant_id}`
- **Replay/Reprocess:** `/replay-audit`, `/reprocess/{signal_id}` (POST/approve/reject/cancel), `/reprocess/request`, `/reprocess/request-queue`, `/reprocess/request/{id}/escalate`, `/reprocess/queue-metrics/{tenant_id}`, `/reprocess/analytics/{tenant_id}`, `/reprocess/alerts/{tenant_id}`, `/reprocess/policy/{tenant_id}` (GET/PUT/check/history)
- **Decisions:** `/decisions/{decision_id}/approve`, `/decisions/{decision_id}/cancel`, `/decisions/{decision_id}/outcome`
- **Outcomes:** `/outcomes`, `/dispatch/workflow-cases/{case_id}/outcome`, `/dispatch/snapshot`
- **Learning:** `/learning/metrics`, `/learning/evaluate/{tenant_id}`, `/learning/policy-tuning/{tenant_id}` (GET/apply), `/learning/apply`, `/optimize`, `/metrics`, `/traces`
- **Agent Orchestration (XXII-XXXII):** `/agent/tasks`, `/agent/tasks/{id}/steps/{step_id}/execute|complete|log|dependencies`, `/agent/tasks/{id}/status|split|merge|merge-status|learning|optimize|resources|feedback|audit`, `/agent/policy/{tenant_id}` (GET/POST), `/agent/tasks/claim`, `/agent/sla/{tenant_id}`, `/agent/queue/{tenant_id}`, `/agent/performance/{tenant_id}`, `/agent/outcomes/{tenant_id}`, `/agent/handoff/{from_task_id}|{handoff_id}/accept`, `/agent/benchmark`, `/agent/knowledge` (post/share/get/expire/health/key lookup)
- **Cross-tenant:** `/cross-tenant-recommendations/{tenant_id}`

### 5.3 Permission Guard Coverage

685 permission-guarded route handlers vs 411 explicit `get_current_tenant` dependencies. Routes without tenant context are expected for platform-level admin endpoints (billing, tenants CRUD). All module endpoints using `university_core` entity APIs inherit tenant isolation via `EntityConfig` enforcement.

### 5.4 Public / Intentionally Unguarded Endpoints

- `/health` (brain_core, platform ops)
- `/api/auth/*` (login, token exchange)
- `/api/public/*` (SSO callback, SAML ACS, webhook ingest with HMAC)
- PDPL compliance disclosure endpoint

---

## 6. Frontend Baseline

### 6.1 Summary

| Metric | Value |
|---|---|
| Total Next.js pages (`page.tsx`) | 102 |
| Admin console page directories | 70 |
| Frontend module directories (`frontend/modules/`) | 58 |
| Frontend test files (excl. node_modules) | 108 |
| Shared UI components (`frontend/shared/ui/`) | 31 |

### 6.2 Admin Console Page Coverage (70 areas)

academic-integrity, accreditation-compliance, admissions, advising, ai, alumni, asset-inventory, audit, automation, backups, billing, budget-planning, career-services, contracts-legal-repository, courses, currency-localization, dashboard, degree-progress, delinquency-collections, developer, enrollments, exam-governance, expense-controls, facilities-work-orders, faculty, faculty-copilot, faculty-performance-kpis, feature-flags, federation, financial-aid, grades, health, housing, hr-payroll, identity, integrations, interventions, jobs, knowledge-retrieval, languages, ldap, local-users, model-evaluation, notifications, ops, org-units, platform, preferences, procurement-workflow, profile, profiles, programs, prompt-management, rbac, records, research-grants, scheduling, security, service-accounts, student-life, students, student-services, syllabus-governance, teaching-quality, tenants, thesis, transcripts, workflows, workload

### 6.3 Key Feature Module Presence

| Feature | Frontend Module | Hooks | Types | Page |
|---|---|---|---|---|
| Interventions / Risk | `platform/interventions/` | Y (`hooks.ts`, `playbook-hooks.ts`) | Y (`types.ts`, `playbook-types.ts`) | `console/interventions/` |
| Delinquency Collections | `delinquency-collections/` | Y (`hooks.ts`) | Y (`types.ts`) | `console/delinquency-collections/` |
| Brain Core / Executive KPI | `brain-core/` | Y (`hooks.ts` — 60+ hooks) | Y (`types.ts`) | `console/ai/` |
| Scheduling / Enrollment | `scheduling/`, `enrollments/` | Y (both) | Y (both) | `console/scheduling/`, `console/enrollments/` |
| KPI Dashboard | `platform/kpi/` | Y (`use-dashboard.ts`) | Y (`types.ts`) | `console/dashboard/` |

### 6.4 Frontend Shared Infrastructure

| Component | File | Reusable For |
|---|---|---|
| `KpiCard` | `modules/platform/kpi/kpi-card.tsx` | Any KPI widget |
| `DataTable` | `shared/ui/data-table.tsx` | All list views |
| `DrawerPanel` | `shared/ui/drawer-panel.tsx` | Record detail side panels |
| `FilterBar` | `shared/ui/filter-bar.tsx` | All searchable lists |
| `ConfirmActionDialog` | `shared/ui/confirm-action-dialog.tsx` | Destructive actions |
| `use-permissions` | `shared/hooks/use-permissions.ts` | RBAC guards in UI |
| `useInterventionCohorts` | `shared/hooks/useInterventionCohorts.ts` | Cohort feature |
| `useCohortOutcomes` | `shared/hooks/useCohortOutcomes.ts` | Cohort feature |
| `useCohortAnalysis` | `shared/hooks/useCohortAnalysis.ts` | Cohort feature |
| `use-mutation-feedback` | `shared/hooks/use-mutation-feedback.ts` | All mutation states |
| API client | `shared/api/client.ts` | All modules |

### 6.5 Frontend Tests (108 files, excl. node_modules)

Key test areas confirmed:
- **Auth/Session:** `AuthProvider.test.tsx`, `LoginPageRedirect.test.tsx`, `LoginTenantMode.test.tsx`
- **Admin pages (50+):** Admissions, Audit, Automation, Backups, Courses, Enrollments, Faculty, Grades, Interventions, Jobs, KnowledgeRetrieval, BrainIntelligence, Billing, Delinquency, Notifications, Quotas, Plans, Subscriptions, etc.
- **Security:** `auth-routes.test.ts`, `bff-proxy.test.ts`, `middleware.test.ts`
- **Navigation:** `navigation-clean.test.ts`
- **Cohort hooks:** `useInterventionCohorts.test.ts`, `useCohortOutcomes.test.ts`, `useCohortAnalysis.test.ts`
- **API contracts:** `admissions/api.test.ts`, `platform/ops/use-ops-health.test.ts`

---

## 7. Test Baseline

### 7.1 Backend Tests (541 files)

| Category | Count (approx) | Examples |
|---|---|---|
| Module-specific integration | ~180 | `tests/modules/admissions/`, `tests/modules/interventions/`, `tests/modules/billing/`, `tests/modules/scheduling/`, etc. |
| Brain Core | ~14 | `test_brain_core_action_bridge.py`, `test_brain_core_db_persistence.py`, `test_brain_core_decision_notification.py`, `test_brain_core_intervention_autocreate.py`, `test_brain_core_signal_roundtrip.py`, `test_brain_core_tenant_validation_a011.py`, `test_brain_llm_explainability_xv3.py`, etc. |
| Tenant isolation | ~20 | `test_tenant_fail_closed.py`, `test_cross_tenant_isolation.py`, `test_domain_cross_tenant_isolation.py`, `test_saas_tenant_cross_user_isolation.py`, `test_audit_tenant_isolation.py`, `test_feature_flags_tenant_isolation.py`, etc. |
| Security | ~8 | `test_public_endpoints_security.py`, `test_security_observability.py`, `test_security_regression_smoke.py` |
| Platform/Event | ~10 | `test_platform_outbox_events.py`, `test_platform_event_ingestion_v1.py`, `test_platform_billing_pipeline.py`, `test_event_bus_hardening.py` |
| Identity | ~5 | `test_identity_phase11_hardening.py`, `test_enterprise_identity.py` |
| KPI / Dashboard | ~5 | `test_executive_kpi_dashboard_xvi4.py`, `test_faculty_kpis_pipeline.py`, `test_platform_kpi_metrics_v1.py` |
| Week domain depth | ~100 | `test_week1_domain_depth.py` through `test_week99_domain_depth.py` (weekly synthetic coverage expansion) |
| Integration flows | ~20 | `test_delinquency_collections_pipeline.py`, `test_enrollments_dropout_intervention.py`, `test_brain_core_blocker12_13.py`, `test_phase_ii_domain_brain_readiness.py` |
| Agent collaboration | ~1 | `test_agent_collaboration_xxv.py` |

### 7.2 Frontend Tests (108 files)

- Admin page render/interaction: ~60 files
- Auth/security: 3 files
- Hook integration: 3 files
- API contracts: 2 files
- Navigation: 1 file
- Component: 5 files

### 7.3 No dedicated e2e (Playwright/Cypress) found in current workspace

Scripts `scripts/platform_smoke_check.sh`, `scripts/release_gate.sh`, `scripts/university_pilot_safe_gate.sh` serve as shell-level smoke/gate checks (not browser e2e).

---

## 8. Migration / Entity Baseline

### 8.1 Alembic Migrations

| Metric | Value |
|---|---|
| Total migration files in `backend/alembic/versions/` | 82 |
| Last identified migrations | `yp24qr56st78_a011_5_create_15_active_fallback_tables.py` (A-011.5), `wn02xy34za56_a009_critical_create_missing_entity_tables.py` (A-009), `vm01wx23yz45_add_7y_audit_retention_policy.py` (7y audit retention) |
| 7-year audit retention | Confirmed — `pg_cron` job, trigger, `retention_expires_at` column on `app_audit_events` |

### 8.2 Entity Configs (`university_core/shared.py`)

| Metric | Value |
|---|---|
| `EntityConfig(` declarations | **211** |
| `EntityConfig` references (all occurrences) | 214 |
| Source file | `backend/app/modules/university_core/shared.py` |
| Additional entity files | `entity_impl.py`, `tenant_entity_impl.py` |

211 entity configs define the full tenant-scoped table registry. Each config governs: table name, schema prefix, tenant isolation mode, soft-delete, audit trail wiring.

### 8.3 Confirmed Active Tables (selected)

From migration history and entity configs:
- `app_brain_signals`, `app_brain_decisions`, `app_brain_action_plans`, `app_brain_outcomes`, `app_brain_explanations`, `app_brain_policy_profiles`
- `app_intervention_cases`, `app_intervention_actions`, `app_intervention_playbooks`
- `app_billing_subscriptions`, `app_billing_plans`, `app_invoices`, `app_usage_records`, `app_quotas`
- `app_audit_events` (with 7y retention policy)
- `app_platform_notifications`
- `app_automation_rules`, `app_automation_templates`
- `app_outbox_events`
- `app_delinquency_records`
- `app_students`, `app_enrollments`, `app_grades`, `app_courses`, `app_course_sections`
- `app_scheduling_sections`, `app_knowledge_retrieval_documents`, `app_model_eval_runs`, `app_prompt_templates`
- `app_course_prerequisites`, `app_workflow_instances`, `app_workflow_tasks`

### 8.4 A-011.5 Fallback Tables (15 active)

Migration `yp24qr56st78_a011_5_create_15_active_fallback_tables.py` created 15 previously deferred entity config tables. These are now active.

---

## 9. Event / Outbox / Brain Signal Baseline

### 9.1 Platform Event Registry

| Metric | Value |
|---|---|
| `EventDefinition(` entries in `platform/events/registry.py` | **260** |
| Total event-emitting modules (confirmed via `publish_event`/`emit_event`/`outbox`) | **65+** |
| Event handlers in `platform/events/handlers/` | 7 handlers |

**Event handlers:**
1. `analytics_handler.py` — analytics sink
2. `notification_handler.py` — notification dispatch
3. `webhook_handler.py` — external webhook delivery
4. `automation_handler.py` — triggers automation rules
5. `education_graph_inference_handler.py` — infers StudentSkill edges
6. `context_projection_handler.py` — context materialization
7. `academic_chain_handler.py` — academic event chaining

**Event-emitting modules (65+):** academic_integrity, academic_records, access_control, accreditation, admissions, advising, ai_admissions_scoring, ai_plagiarism, alumni, asset_inventory, attendance, billing, budget_planning, campus_sla, career_services, communications, conference_management, courses, degree_progress, delinquency_collections, dining, enrollments, equipment_booking, events_management, exam_governance, expense_controls, facilities_work_orders, faculty_performance_kpis, faculty, financial_aid, library, lms_content, online_payments, parking, patents, payment_reconciliation, platform_shared, procurement, programs, publications, research_ethics, research, room_booking, scheduling, scholarship, security_operations, student_ai_tutor, student_feedback, student_life, student_portal, student_services, students, syllabus_governance, teaching_quality, thesis, transcripts, transport, visitor_management (+ observability trace module)

### 9.2 Event Classification Summary

| Classification | Count (approx) | Notes |
|---|---|---|
| ACTIVE_EVENT | ~150 | Events with both producer and registered handler consumer |
| REGISTERED_UNUSED | ~50 | Registered in `EXACT_EVENT_REGISTRY` but no active consumer handler |
| BRAIN_SIGNAL | ~58 | In `brain_core/registry.py` SignalRegistry (38 named scenarios covering multiple event type sets) |
| EMITTED_UNREGISTERED | ~20 | Emitted in module services but not yet in `EXACT_EVENT_REGISTRY` |
| NEEDS_REVIEW | ~30 | In registry but payload model is a placeholder |

> Note: Exact per-event classification requires runtime correlation. These are static analysis estimates.

### 9.3 Brain Core Signal Registry

**SignalRegistry** — 38 signal-to-scenario mappings, 20 decision scenarios in **DecisionRegistry**.

| Signal Group | Signal Examples | Scenario |
|---|---|---|
| Student Risk | `academic.attendance_risk.detected`, `academic.grade_risk.detected` | `student_risk` |
| Thesis Risk | `thesis.status_changed` | `thesis_delay` |
| Faculty | `faculty.workload_overload.detected`, `faculty.quality_drop.detected` | `faculty_overload`, `faculty_quality_intervention` |
| Financial | `finance.payment_overdue.detected`, `financial_aid.warning.detected` | `payment_recovery` |
| Student Support | `student_services.ticket.escalated`, `admissions.decision.made` | `student_support_bridge`, `student_risk` |
| Scheduling | `scheduling.section.scheduled` | `faculty_overload` |
| Procurement | (via `PROCUREMENT_EVENT_TYPES`) | `procurement_supply_chain`, `supply_management` |
| Accreditation | (via `ACCREDITATION_EVENT_TYPES`) | `accreditation_remediation` |
| Platform | (via `PLATFORM_RELIABILITY_EVENT_TYPES`) | `platform_reliability` |
| Operations | (via `OPERATIONS_EVENT_TYPES`) | operational scenarios |
| Research | (via `RESEARCH_EVENT_TYPES`) | research risk scenarios |
| Academic Chain | (via `ACADEMIC_RECORDS_EVENT_TYPES`, `COURSES_EVENT_TYPES`, `TRANSCRIPTS_EVENT_TYPES`) | compliance scenarios |

### 9.4 In-Process Event Bus

`platform_shared/events.py`: `DomainEvent` dataclass + `InProcessEventBus` for sync in-process dispatch (separate from outbox). Used by modules that need immediate same-transaction notification.

---

## 10. Brain Core Actual Capabilities

File: `backend/app/modules/brain_core/` (service.py = 3605 lines, 107 methods; router.py = 2045 lines, 110 endpoints)

| Brain Capability | Exists in Code | Files | Tests | Reuse For Top 5 Features | Gap |
|---|---|---|---|---|---|
| Signal intake / listener | ✅ | `signal_listener.py`, `service.py` | `test_brain_core_signal_roundtrip.py` | H-1, A-1 | None |
| Signal normalizer | ✅ | `signal_normalizer.py` | `test_brain_core_signal_roundtrip.py` | H-1, A-1 | None |
| Signal deduplication | ✅ | `service.py`, migration `lh01ij23kl45` | `test_brain_core_signal_dedup.py` | H-1, A-1 | None |
| Signal registry (38 scenarios) | ✅ | `registry.py` | `test_brain_core_classifier_lifecycle.py` | H-1, A-1, B-2 | Extend signal types for new features |
| Context builder | ✅ | `context_builder.py` | `test_brain_core_signal_roundtrip.py` | All | None |
| Context sources (6 domains) | ✅ | `context_sources/academic.py`, `finance.py`, `faculty.py`, `operations.py`, `platform.py`, `research.py`, `student_success.py` | — | H-1, A-1, B-2, C-1 | Add scheduling context source for C-1 |
| Classifiers (4 types) | ✅ | `classifiers/base.py`, `risk_classifier.py`, `compliance_classifier.py`, `operational_classifier.py`, `optimization_classifier.py` | `test_brain_core_classifier_lifecycle.py` | H-1, A-1 | None |
| Reasoning engine | ✅ | `reasoning/engine.py`, `scoring.py`, `scenario_selector.py`, `rules_engine.py` | — | All | None |
| AI adapter / LLM explanation | ✅ | `reasoning/explanation.py`, `reasoning/ai_adapter.py`, `platform/ai/llm_bridge.py` | `test_brain_llm_explainability_xv3.py` | H-1, D-1 | LLM is optional/local Ollama — no cloud LLM |
| Knowledge retriever (RAG) | ✅ | `reasoning/knowledge_retriever.py` | — | H-1, D-1 | Connected to `knowledge_retrieval` module |
| Anomaly detector | ✅ | `reasoning/anomaly_detector.py` | `test_brain_core_blocker12_13.py` | A-1, D-1 | None |
| Predictor (risk) | ✅ | `reasoning/predictor.py` | — | H-1, A-1 | None |
| Optimizer | ✅ | `reasoning/optimizer.py` | — | D-1 | None |
| Policy guard (5 autonomy levels) | ✅ | `policy/decision_policy.py` | `test_brain_core_tenant_validation_a011.py` | All | None |
| Decision creation (DB-persisted) | ✅ | `service.py`, `models.py` | `test_brain_core_db_persistence.py` | All | None |
| Decision registry (20 scenarios) | ✅ | `registry.py` | — | H-1, A-1, B-2, C-1 | Extend for new scenarios |
| Action planner | ✅ | `actions/planner.py` | `test_brain_core_action_bridge.py` | All | None |
| Action dispatcher | ✅ | `actions/dispatcher.py`, `action_bridge.py` | `test_brain_core_action_bridge.py` | All | Register module handlers for new features |
| Notification actions | ✅ | `actions/notification_actions.py` | `test_brain_core_decision_notification.py` | All | None |
| Workflow actions | ✅ | `actions/workflow_actions.py` | — | H-1, C-1 | None |
| Job actions | ✅ | `actions/job_actions.py` | — | B-2, C-1 | None |
| Intervention auto-create | ✅ | `ai/interventions_automation.py` | `test_brain_core_intervention_autocreate.py` | H-1, A-1 | None |
| Outcome tracking | ✅ | `feedback/outcome_tracker.py`, `feedback/ingestor.py` | — | H-1, A-1 | None |
| Effectiveness tracking | ✅ | `feedback/effectiveness.py` | — | H-1 | None |
| Decision quality tracker | ✅ | `learning/quality_tracking.py`, `learning/decision_quality.py` | — | D-1 | None |
| Signal quality tracker | ✅ | `learning/signal_quality.py` | — | H-1 | None |
| Policy tuning engine | ✅ | `learning/policy_tuning.py` | — | D-1 | None |
| Model eval hooks | ✅ | `learning/model_eval_hooks.py` | — | D-1 | None |
| Replay / reprocess governance | ✅ | `router.py` (20+ replay endpoints), `service.py` | — | All | None |
| Agent orchestration (XXII-XXXII) | ✅ | `router.py` (55+ agent endpoints), `service.py` | `test_agent_collaboration_xxv.py` | H-1, D-1 | None |
| Observability / metrics | ✅ | `observability.py`, `reporting/` | — | D-1 | None |
| Tenant validation | ✅ | `service.py` (fail-closed) | `test_brain_core_tenant_validation_a011.py` | All | None |
| LLM bridge (Ollama/deepseek-r1:8b) | ✅ | `platform/ai/llm_bridge.py` (optional, fail-safe) | — | H-1, D-1 | Optional — degrades gracefully if Ollama unavailable |
| Executive KPI endpoint | ✅ | `router.py /executive-kpi/{tenant_id}` | `test_executive_kpi_dashboard_xvi4.py` | D-1 | None |
| Cross-tenant recommendations | ✅ | `router.py /cross-tenant-recommendations/{tenant_id}` | — | D-1 | None |
| Policy rollout coordination | ✅ | `router.py` rollout plan/execute/rollback/coordination | — | D-1 | None |

**Brain Core completeness: ~95% implemented.** No major capability gaps in the engine itself. Gaps are in integration wiring for specific new features (context sources, signal type extensions, dispatcher handler registration).

---

## 11. Existing Cross-Module Flows

Confirmed flows with code evidence:

| Flow | Source Module | Target Module | Trigger | Evidence File | Status |
|---|---|---|---|---|---|
| Grade risk → Intervention | `grades` | `interventions` | `_derive_grade_risk_level()` on grade submission | `grades/service.py:382` | ACTIVE |
| Enrollment dropout → Intervention | `enrollments` | `interventions` | Enrollment status change → dropout risk | `enrollments/service.py:826` | ACTIVE |
| Admissions decision → Financial Aid | `admissions` | `financial_aid` | `create_financial_aid_record()` on admission | `admissions/service.py` | ACTIVE |
| Billing guard → Multi-module | `billing` | `courses`, `enrollments`, `backup`, `jobs`, `auth`, `ai_gateway` | `assert_billing_write_allowed()` guard | `billing/service.py`, each consumer | ACTIVE |
| Tenant provisioning → Billing | `tenants` | `billing` | `ensure_tenant_subscription()` on tenant create | `tenants/provisioning_service.py:9` | ACTIVE |
| Brain Core → Notification | `brain_core` | `platform/notifications` | `ActionDispatcher.dispatch()` → `notification_actions` | `brain_core/actions/notification_actions.py` | ACTIVE |
| Brain Core → Workflow | `brain_core` | `workflows` | `ActionDispatcher.dispatch()` → `workflow_actions` | `brain_core/actions/workflow_actions.py` | ACTIVE |
| Brain Core → Intervention (auto-create) | `brain_core` | `interventions` | `maybe_create_academic_risk_intervention_case()` | `brain_core/ai/interventions_automation.py` | ACTIVE |
| Brain Core context ← Procurement | `procurement` | `brain_core` | `get_procurement_health_snapshot()` in context build | `brain_core/context_sources/finance.py` | ACTIVE |
| Scheduling models → Enrollments | `scheduling` | `enrollments` | `CourseSectionModel` import for section linkage | `enrollments/service.py`, `grades/service.py` | ACTIVE |
| Scheduling models → Interventions (risk) | `scheduling` | `interventions` | Section capacity/conflict risk check | `interventions/risk_service.py` | ACTIVE |
| Events → Analytics | `(any module)` | `platform/analytics` | Outbox worker `AnalyticsEventHandler` | `platform/events/handlers/analytics_handler.py` | ACTIVE |
| Events → Notifications | `(any module)` | `platform/notifications` | Outbox worker `NotificationEventHandler` | `platform/events/handlers/notification_handler.py` | ACTIVE |
| Events → Automation | `(any module)` | `platform/automation` | Outbox worker `AutomationEventHandler` | `platform/events/handlers/automation_handler.py` | ACTIVE |
| Events → Education Graph | `(any module)` | `platform/education_graph` | Outbox worker `EducationGraphInferenceHandler` | `platform/events/handlers/education_graph_inference_handler.py` | ACTIVE |
| Events → Academic Chain | `(any module)` | `platform/academic_chain` | Outbox worker `AcademicChainEventHandler` | `platform/events/handlers/academic_chain_handler.py` | ACTIVE |

**Notable absent flows (not confirmed in code):**
- `delinquency_collections` does not directly call `billing` service (uses event-based approach)
- `career_services` → `placement` cross-module not confirmed (event-driven only)
- `scholarship` → `awards` direct DB cross-call not found (event-driven only)
- `campus_sla` → `facilities_work_orders` direct service call not confirmed

---

## 12. Reusable Infrastructure Inventory

| Infrastructure | Exists | Files | Reuse Rule | Do Not Duplicate | Extension Needed |
|---|---|---|---|---|---|
| **Outbox / Event Bus** | ✅ | `platform/events/registry.py`, `publisher.py`, `worker.py`, `handlers/` | Register new events in `EXACT_EVENT_REGISTRY`; emit via `EventPublisher` | Do NOT create new event dispatch mechanism | Add new `EventDefinition` entries for new features |
| **Notifications** | ✅ | `platform/repository/notification_repository.py`, `platform/notifications/service.py` | Use `NotificationRepository.dispatch()` | Do NOT build a new notification system | Add new notification templates for new features |
| **Audit Trail** | ✅ | `modules/audit/service.py`, `app_audit_events` table, `pg_cron` job | Use `log_admin_action()` | Do NOT create separate audit logs | None — 7y retention already in place |
| **Workflows** | ✅ | `modules/workflows/router.py`, `platform/` workflows service | Use workflow router for task-based human-in-loop flows | Do NOT create custom task queues | Add workflow templates for new features |
| **Jobs / Scheduler** | ✅ | `platform/jobs/scheduler.py`, `service.py`, `worker.py` | Use `PlatformWorkerScheduler` for background jobs | Do NOT add Celery tasks without scheduler integration | Register new module jobs in scheduler |
| **Policy / RBAC** | ✅ | `modules/rbac/`, `permission_dependency`, `get_current_tenant` | Use `permission_dependency(...)` in all new routers | Do NOT bypass RBAC | None |
| **ABAC / Tenant Resolver** | ✅ | `modules/access_control/service.py`, `get_current_tenant` | Tenant ID always from `get_current_tenant()` — never trust user input | Fail-closed pattern is mandatory | None |
| **Feature Flags** | ✅ | `modules/feature_flags/`, `platform/feature_flags/` | Use `is_feature_enabled()` for graduated rollout | Do NOT hard-code feature gating | None |
| **KPI Platform** | ✅ | `platform/kpi/service.py`, `repository.py`, `schemas.py`, `ministry_kpi.py` | Use `get_rector_dashboard()`, `refresh_tenant_metrics()` | Do NOT build new KPI aggregation | Add new KPI metric definitions |
| **Dashboard Components** | ✅ | `frontend/modules/platform/kpi/kpi-card.tsx`, `use-dashboard.ts` | Reuse `KpiCard` for all metric cards | Do NOT build new chart components for standard KPIs | Add new card types if needed |
| **Brain Core Engine** | ✅ | `modules/brain_core/` (3605-line service) | Use `BrainCoreService.process_signal()` | Do NOT build parallel decision engine | Register module handlers via `ActionDispatcher.register_module_handler()` |
| **Shared Frontend Hooks** | ✅ | `frontend/shared/hooks/`, `frontend/modules/brain-core/hooks.ts` | Reuse existing hooks | Do NOT duplicate fetch logic | Add new hooks extending existing patterns |
| **Shared UI Components** | ✅ | `frontend/shared/ui/` (31 components) | Use `DataTable`, `FilterBar`, `DrawerPanel`, `KpiCard`, etc. | Do NOT build new table/filter/drawer components | None |
| **Automation Engine** | ✅ | `platform/automation/service.py`, `templates/`, `actions.py` | Register new automation rules/templates | Do NOT build parallel automation | Add seed templates for new module events |
| **Replay / Reprocess** | ✅ | `brain_core/router.py` (20+ replay endpoints) | Use existing replay governance | Do NOT build module-specific replay | None |
| **Backup / DR** | ✅ | `modules/backup/`, `scripts/backup_db.sh`, `scripts/restore_db.sh`, DR dumps in `backups/` | Use existing backup service | Do NOT add ad-hoc dump scripts | None |
| **Smoke / Release Gates** | ✅ | `scripts/platform_smoke_check.sh`, `scripts/release_gate.sh`, `scripts/university_pilot_safe_gate.sh` | Run gates after every change | Do NOT skip gates | None |
| **EntityConfig system** | ✅ | `modules/university_core/shared.py` (211 configs), `entity_impl.py`, `tenant_entity_api.py` | New tables MUST have EntityConfig before migration | Do NOT create raw tables without EntityConfig | Add new EntityConfig entries for new tables |
| **In-Process Event Bus** | ✅ | `modules/platform_shared/events.py` (`InProcessEventBus`) | For sync same-transaction events | Do NOT use for cross-service events | None |

---

## 13. Top 5 Feature Readiness Against Real Code

### H-1: Student Intervention Orchestration (Early Warning + AI Triage)

| Dimension | Status |
|---|---|
| **Existing Code** | `modules/interventions/` (full stack: router, service, schemas, models); brain_core signal `academic.grade_risk.detected` → `student_risk` scenario → `create_intervention_case` action; `grades/service.py` creates intervention on grade risk; `enrollments/service.py` creates intervention on dropout status; `brain_core/ai/interventions_automation.py` auto-creates cases; `frontend/modules/platform/interventions/` (hooks, types, playbook-hooks); `console/interventions/` page |
| **Missing Links** | No direct link from `attendance` module brain signal to intervention case (attendance has `publish_event` but no direct intervention creation); cohort-level escalation rules not wired to automation engine; intervention playbook execution stats not surfaced in KPI dashboard |
| **Reuse** | Brain Core signal pipeline; `ActionDispatcher`; `NotificationRepository`; `WorkflowActions`; `KpiCard`; `DataTable`; `automation/templates` |
| **Risk** | Signal dedup key must be maintained; autonomy level 0/1 requires human approval for intervention creation |
| **A-013 Work** | Wire attendance risk brain signal → intervention auto-create; add cohort automation template to automation engine; surface intervention resolution rate in KPI dashboard |

### A-1: Early Warning System (Predictive Risk)

| Dimension | Status |
|---|---|
| **Existing Code** | `brain_core/reasoning/predictor.py` (exists); `brain_core/reasoning/anomaly_detector.py` (exists); brain signal `academic.attendance_risk.detected`; `/predict` and `/anomalies` endpoints; `test_phase_ii_domain_brain_readiness.py`, `test_phase_iii_low_ev_brain_readiness.py`; `brain_core/hooks.ts` has `useBrainPredictRisk`, `useBrainDetectAnomalies` |
| **Missing Links** | Predictor does not yet aggregate across attendance + grades + financial aid signals in a single composite risk score; no scheduled nightly risk sweep job registered in `PlatformWorkerScheduler`; no dedicated "early_warning" dashboard page (currently embedded in Brain Intelligence page) |
| **Reuse** | Brain Core predictor/anomaly detector; scheduler for nightly sweep; KPI platform for risk scores; existing brain hooks; `KpiCard` for risk trends |
| **Risk** | LLM-based explanation is optional (Ollama local only) — rule-based fallback must be solid |
| **A-013 Work** | Implement composite risk score aggregation in predictor; register nightly risk sweep job in scheduler; add dedicated early-warning section to admin console; wire frontend hook `useBrainPredictRisk` to new composite endpoint |

### B-2: Delinquency Detection & Recovery

| Dimension | Status |
|---|---|
| **Existing Code** | `modules/delinquency_collections/` (full stack: router, service, schemas); event emission via `EventPublisher`; escalation stages (stage_1/2/3/legal) with active-record caps enforced; `frontend/modules/delinquency-collections/` (hooks, types); `console/delinquency-collections/` page; `test_delinquency_collections_pipeline.py`; `test_billing_delinquency_contract.py`; brain signal `finance.payment_overdue.detected` → `payment_recovery` scenario exists in SignalRegistry |
| **Missing Links** | No direct link from `billing` overdue events to `delinquency_collections` auto-create (billing emits events but delinquency service does not consume them via automation); brain signal `payment_recovery` decision action `create_collections_case` exists but `register_module_handler()` for delinquency not confirmed wired in dispatcher |
| **Reuse** | Brain Core `payment_recovery` scenario; `ActionDispatcher` module handler registration; `AutomationEventHandler` for event → rule wiring; `NotificationRepository` for payment reminders |
| **Risk** | Legal escalation stage has special compliance obligations (PDPL, debt collection regulations) |
| **A-013 Work** | Register delinquency module handler in `ActionDispatcher`; add automation template `billing-overdue-to-delinquency`; wire billing overdue event to delinquency auto-create via automation engine |

### C-1: Course Scheduling & Enrollment (Conflict Detection)

| Dimension | Status |
|---|---|
| **Existing Code** | `modules/scheduling/` (full stack: router, service, schemas, models); `modules/enrollments/` (full stack with billing guard); `CourseSectionModel` imported by enrollments and grades; brain signal `scheduling.section.scheduled` → `faculty_overload` scenario; `frontend/modules/scheduling/` and `frontend/modules/enrollments/`; `console/scheduling/` page; `test_scheduling_events_xxxiv5.py` |
| **Missing Links** | No student-facing enrollment conflict detection UI (only admin console view); course prerequisite enforcement present (migration `qh56rs78tu90_add_course_prerequisites_table.py`) but no prerequisite-check brain signal; no waitlist management in current enrollments service; `scheduing` context source not added to brain_core context_sources directory |
| **Reuse** | Brain Core `faculty_overload` scenario; `enrollments` service billing guard; `scheduling/models.py` shared across modules; `workflows` for section approval; `KpiCard` for capacity utilization |
| **Risk** | Enrollment-scheduling coupling is tight — schema changes to `CourseSectionModel` ripple to 3 modules |
| **A-013 Work** | Add `scheduling` context source to `brain_core/context_sources/`; add prerequisite brain signal; build waitlist queue as workflow task; add student-facing conflict check endpoint |

### D-1: Executive KPI Dashboard

| Dimension | Status |
|---|---|
| **Existing Code** | `platform/kpi/service.py` (full: lineage, workflow hints, fingerprint, rector dashboard, ministry KPI); `platform/kpi/repository.py`, `schemas.py`; `brain_core/router.py /executive-kpi/{tenant_id}`; `frontend/modules/platform/kpi/kpi-card.tsx`, `use-dashboard.ts`, `types.ts`; `console/dashboard/` page; `test_executive_kpi_dashboard_xvi4.py`; `get_rector_dashboard()` returns `RectorDashboard` with cards + trend + source |
| **Missing Links** | KPI dashboard does not yet aggregate intervention resolution rates, delinquency recovery rates, or course fill rates (only enrollment count, payment compliance, faculty KPIs confirmed); no ministry-level cross-tenant KPI aggregation UI; `ministry_kpi.py` exists but no router endpoint confirmed |
| **Reuse** | `KpiCard` component; `use-dashboard.ts` hook; `get_rector_dashboard()` service method; brain core `/executive-kpi/{tenant_id}` endpoint; `platform/kpi/service.py` `refresh_tenant_metrics()` |
| **Risk** | KPI lineage must be maintained when new metrics added; contract fingerprint must stay stable |
| **A-013 Work** | Add intervention/delinquency/scheduling KPI metric definitions to `KPI_WORKFLOW_HINTS`; add ministry-level aggregation router endpoint; wire `ministry_kpi.py` to frontend |

---

## 14. Do Not Duplicate List

The following infrastructure is **fully implemented** and **must NOT be rebuilt** for any new feature:

| Infrastructure | Location | Rule |
|---|---|---|
| Event/Outbox dispatch | `platform/events/publisher.py` | Add `EventDefinition` to registry; call `EventPublisher.publish()` |
| Notification delivery | `platform/repository/notification_repository.py` | Call `NotificationRepository.dispatch()` only |
| Audit logging | `modules/audit/service.py` | Call `log_admin_action()` only |
| Tenant isolation | `get_current_tenant()` dependency | Never read tenant from user input |
| RBAC / permission guard | `permission_dependency(...)` | All new router endpoints must have permission guard |
| Brain Core decision engine | `modules/brain_core/service.py` | Call `BrainCoreService.process_signal()` |
| Action dispatch | `brain_core/actions/dispatcher.py` | Use `register_module_handler()` for new action types |
| KPI aggregation | `platform/kpi/service.py` | Add metric definitions; do not build new aggregation service |
| EntityConfig table registry | `university_core/shared.py` | New tables must have `EntityConfig` entry |
| Workflow engine | `modules/workflows/router.py` | Use existing workflow engine for task-based flows |
| Job scheduler | `platform/jobs/scheduler.py` | Register new jobs in `PlatformWorkerScheduler` |
| Automation rules | `platform/automation/service.py` | Add templates to `automation/templates/seeds.py` |
| DataTable UI | `frontend/shared/ui/data-table.tsx` | Use for all list views |
| KpiCard UI | `frontend/modules/platform/kpi/kpi-card.tsx` | Use for all metric cards |
| DrawerPanel UI | `frontend/shared/ui/drawer-panel.tsx` | Use for all record side panels |
| Brain Core hooks | `frontend/modules/brain-core/hooks.ts` | Reuse existing 60+ hooks |
| Replay governance | `brain_core/router.py` replay endpoints | Do not build module-specific replay |
| LLM bridge | `platform/ai/llm_bridge.py` | Use existing bridge; do not call Ollama directly |

---

## 15. Known Real Gaps

Only gaps verified by current code inspection:

| Gap | Module/Area | Evidence | Priority |
|---|---|---|---|
| `attendance` → intervention auto-create not wired | `attendance/service.py` | No `InterventionCaseModel` import found | HIGH |
| `delinquency_collections` not registered in `ActionDispatcher` module handlers | `brain_core/actions/dispatcher.py` | No confirmed `register_module_handler` call for delinquency | HIGH |
| `scheduling` context source absent in `brain_core/context_sources/` | `brain_core/context_sources/` | Directory has academic/finance/faculty/operations/platform/research/student_success — no scheduling | MEDIUM |
| Composite early-warning risk score not implemented | `brain_core/reasoning/predictor.py` | Predictor exists but multi-signal aggregation not confirmed | MEDIUM |
| Nightly risk sweep job not registered in scheduler | `platform/jobs/scheduler.py` | No sweep job found in scheduler registration | MEDIUM |
| `ministry_kpi.py` not exposed via router | `platform/kpi/ministry_kpi.py` | File exists; no confirmed endpoint in `router_admin.py` | LOW |
| Waitlist management absent | `modules/enrollments/service.py` | No waitlist queue logic found | LOW |
| 28 modules are ACTIVE_SERVICE_ONLY (no router.py) | Multiple | Missing router = no API surface for those modules | VARIES |
| `security` module is empty | `modules/security/` | No files found | NEEDS_REVIEW |
| `ai_guardrails` has only schemas.py | `modules/ai_guardrails/` | Stub/planned only | LOW |
| 50 registered events have no active handler consumer | `platform/events/registry.py` | Static estimate | LOW |
| No browser e2e tests (Playwright/Cypress) | `frontend/` | Only shell-based smoke gates | LOW |

---

## 16. Rules for A-012.2 and A-013

1. **Reuse-first:** Before adding any infrastructure, verify it does not already exist using this document's Section 12 (Reusable Infrastructure) and Section 14 (Do Not Duplicate).

2. **Additive-only for core modules:** Never modify `university_core/shared.py`, `brain_core/registry.py`, `platform/events/registry.py`, or `platform/kpi/service.py` without explicit A-cycle tracking.

3. **No greenfield duplication:** Event bus, notifications, audit, RBAC, tenant isolation, KPI aggregation, workflow engine — all exist. Build on them.

4. **Docker validation required when code changes start:** All new code must pass `docker compose run --rm backend-tests pytest -q` before merge.

5. **Gates required:** Run `scripts/university_pilot_safe_gate.sh` and `scripts/platform_smoke_check.sh` after every significant change.

6. **EntityConfig before migration:** Any new DB table must have `EntityConfig` entry in `university_core/shared.py` before writing the Alembic migration.

7. **Permission guard on every new endpoint:** All new router endpoints must have `permission_dependency(...)` and `Depends(get_current_tenant)`.

8. **SBS_UB.md updated after every result:** After each A-cycle artifact, update the CONTROL BLOCK `current_stage`, `next_action_id`, and EXECUTION LOG.

9. **Brain Core integration via `process_signal()`:** New features that need autonomous decisions must emit the right event type, which will trigger the Brain Core signal pipeline — do not call Brain Core service directly from module services.

10. **Test required:** New feature code must have a corresponding test file in `backend/tests/modules/<module_name>/`.

---

## 17. Recommended Next Step

**Resume A-012.2:** COMMON INFRASTRUCTURE REUSE & GAP PLAN

Now that the real code baseline is established in this document, A-012.2 should:

1. Take the **Top 5 features** (Section 13) and produce a **per-feature infrastructure reuse plan** — specifically: which existing service methods to call, which events to register, which automation templates to add, which `ActionDispatcher` handlers to register.

2. Confirm which **28 SERVICE_ONLY modules** need routers added for the Top 5 features.

3. Produce a **sequenced gap closure checklist** ordered by dependency (e.g., `scheduling` context source before `scheduling` brain signal, delinquency dispatcher handler before delinquency automation template).

4. Produce a **test coverage delta** — what new test files are needed.

---

## Appendix: Artifact Log

| Artifact | File | Status |
|---|---|---|
| A-012.0 Feature Integration Map | `SBS_UB.md` (embedded) | ✅ Complete |
| A-012.1 Product Completeness Priority Report | `A-012.1-PRODUCT_COMPLETENESS_PRIORITY_REPORT.md` | ✅ Complete |
| A-012.2 Infrastructure Reuse & Gap Plan | `A-012.2-COMMON_INFRASTRUCTURE_REUSE_GAP_PLAN.md` | ✅ Created (to be refined with this baseline) |
| **A-012.CONTEXT Real Project Context Baseline** | **`SBS_UB_PROJECT_CONTEXT_2026.md`** | **✅ This document** |
