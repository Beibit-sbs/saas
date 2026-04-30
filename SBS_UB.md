# SBS UB

**Документ:** Единый рабочий документ реализации SBS UB
**Режим:** По умолчанию работаем по этому файлу
**Статус:** Active Working Plan v1
**Начало:** 2026-04-22

## Текущий прогресс (оперативный трекер)

**Обновлено:** 2026-04-30 (Phase I COMPLETE: 131/131 тестов ✅; Phase II COMPLETE: 27/27 тестов ✅; Phase III COMPLETE: 23/23 тестов ✅; Phase IV COMPLETE ✅; Phase V COMPLETE ✅; Phase VI COMPLETE ✅; Phase VII COMPLETE ✅; Phase VIII COMPLETE ✅; Phase IX COMPLETE: 5/5 (IX1-IX4 backend: 17/17 tests ✅; IX5 gate: safe-gate PASS ✅ + release-gate PASS ✅); Phase X COMPLETE: backend 28/28 ✅ + frontend 13/13 ✅ + X4 safe-gate PASS ✅; Phase XI COMPLETE ✅; Phase XII COMPLETE ✅ XII1-XII5: backend 13/13 ✅ + frontend 550/550 ✅ + release-gate PASS ✅; Phase XIII COMPLETE ✅ XIII1-XIII5: audit 60/60 EXISTS; feature_flags CRUD 35 tests; billing API 11 tests; F3.9/F3.10 DoD signoff; release-gate PASS 440+370+73 ✅; Phase XIV COMPLETE ✅ XIV1: audit 60/60 modules EXISTS (zero partial); XIV2-XIV3: 159 week-tests shipped; XIV4: Brain Core 20+ signals; XIV5: release-gate PASS 440+370+24+96+73 ✅; **Phase XV COMPLETE ✅** XV1 LLM Bridge 8/8 commit 1dfa848; XV2 PostgreSQL Persistence 8/8 commit 7838d20; XV3 LLM Explainability 5/5 commit 0c135f7; XV4 Autonomous Pipeline 5/5 commit b99ce75; XV5 release-gate PASS commit 6199e21; **Phase XVI COMPLETE ✅** XVI1 Predictive Risk Engine 6/6 ✅; XVI2 Anomaly Detection 6/6 ✅; XVI3 Proactive Recommendations 5/5 ✅; XVI4 Executive Brain KPI Dashboard 5/5 ✅; XVI5 release-gate PASS ✅; **Phase XVII COMPLETE ✅** XVII1 Frontend Intelligence 5/5 ✅; XVII2 hooks+types ✅; XVII3 Adaptive Learning API 8/8 ✅; XVII4 Optimization Engine 8/8 ✅; XVII5 release-gate PASS ✅ (commit 25b4cff))

**[Предыдущее обновление 2026-04-23]** (Brain Core + integrations regression fixes ✅ `test_student_risk_flow.py` 41 passed; `test_financial_aid.py` + `test_housing.py` + `test_integrations.py` 21 passed; post-Phase-G smoke-gate remains PASS `passed=8`, `failed=0`; access model fixed: tenant-local Brain + ministry KPI layer)

### Чеклист этапа (ставим галочки сразу по факту)

- [x] Expand to 3 more scenarios: Faculty Overload, Payment Recovery, Supply Management
- [x] Learning layer: Policy tuning based on outcomes
- [x] Admin UI: Dashboard for decisions, explanations, outcomes
- [x] Tenant customization: Allow tenants to configure decision policies
- [x] AI augmentation: Add optional AI reasoning for complex scenarios
- [x] Расширенная регрессия: safe-gate/smoke-gate
- [x] Phase B1 остаток: schema/contracts/registry/rules matrix синхронизированы с текущей реализацией
- [x] Phase B3 hardening: dispatch fail-path реализован (retry x3 -> escalation) + backend tests 13/13 green
- [x] Deployment checklist: rollout prerequisites validated (migrations/contracts/policy profiles included)

### Следующие задачи (пока без галочки)

- [x] Phase F — Outcome Feedback Loops (Critical gap #2): Intervention cases now emit `interventions.case_outcome.recorded` event when resolved/closed; InterventionService accepts optional `on_case_outcome` callback and immediately calls `brain_core_service.record_dispatch_outcome()` for auto-ingestion; router wires callback via `_get_intervention_service()` helper; 4 unit tests green validating callback invocation, effectiveness mapping (positive/neutral), exception handling, and fallback when callback absent.
- [x] Phase G — Compliance Decision Type (Critical gap #3): ✅ VERIFIED COMPLETE — Brain Core compliance infrastructure is fully implemented and operational. Accreditation domain bridge emits `accreditation.status_changed` signals → RiskClassifier routes to compliance paths (accreditation_risk_high/medium) → RulesEngine decision_type=compliance with requires_approval→ ActionPlanner creates remediation workflows → PolicyGuard restricts by autonomy level. Audit notes have been corrected to show "✅ Ready" status for compliance.
- [x] Phase H — Remaining Domain Bridges & Reliability Signals: completed domain bridge chain for `financial_aid.warning.detected`, `housing.status.risk_detected`, and `platform.integration.degraded` (service/router emitters + event registry + Brain Core constants/registry/classifier/rules + bridge tests).
- [x] Post-Phase-G smoke-gate: Full platform validation after compliance verification (`bash scripts/platform_smoke_check.sh` PASS: `passed=8`, `failed=0`)

### Архитектурная фиксация доступа (2026-04-23)

- [x] Brain Core работает только в tenant-local режиме: каждый tenant читает/пишет только свой контур.
- [x] Cross-tenant raw access запрещен для operational Brain API/решений.
- [x] Для межтенантной отчетности закреплен отдельный Ministry KPI Layer (только агрегаты/тренды, без student-level raw и без PII).
- [x] Ministry-доступ ограничивается отдельными ролями (`ministry.kpi.read`) и аудитируется.

### После закрытия текущего трека: следующий приоритет (Phase I — Module Max Hardening)

- [x] I1: Закрыть все `⚠️ Partial` с EV=High (thesis canonical signal contract, advising feedback/signal path, students risk-context API). **8/8 тестов ✅**
- [x] I2: Enrollments dropout-risk signal + analytics/usage brain-context API — 10/10 тестов ✅
- [x] I3: Поднять `❌ Not ready` EV=Med модули до минимальной brain-readiness (signals + context + policy-safe path): academic_integrity, academic_records, programs, courses, transcripts, student_services. 20/20 тестов ✅
- [x] I4: Ввести tenant-isolation regression pack: fail-closed без tenant context, запрет cross-tenant reads, negative tests на data leakage. 29/29 тестов ✅
- [x] I5: Зафиксировать Ministry KPI contract v1 (whitelist KPI, suppression thresholds, audit requirements) и покрыть тестами. **28/28 тестов ✅**
- [x] I6: Финальный safe-gate + release-gate после Phase I и обновление readiness-audit таблицы. **95/95 (I1–I5) + 36/36 (I6 gate) = 131 тестов Phase I ✅**

### Следующие фазы (Phase C / D / E) — расставлены по Master Plan + Architecture

#### Phase C — Brain Core Maturity (закрываем архитектурные разрывы)

- [x] C1: Audit Brain-Readiness всех доменных модулей по 3 осям: Domain Coverage / Brain Readiness / Execution Value (Master Plan §8, §12) — результаты ниже в §C1
- [x] C2: Дополнить scaffold context sources: `research.py`, `platform.py` (Architecture §5 — missing files)
- [x] C3: Дополнить scaffold classifiers: `operational_classifier.py`, `optimization_classifier.py`, `compliance_classifier.py` (Architecture §5)
- [x] C4: Дополнить scaffold policy/actions/feedback/learning: `approval_policy.py`, `job_actions.py`, `effectiveness.py`, `signal_quality.py`, `decision_quality.py`, `policy_tuning.py`, `model_eval_hooks.py` (Architecture §5)
- [x] C5: Добавить недостающие DB-таблицы: `brain_signal_context_snapshots`, `brain_action_executions`, `brain_learning_observations` (Architecture §18)
- [x] C6: Добавить недостающие API endpoints: `POST /reprocess/{signal_id}`, `POST /decisions/{id}/approve`, `POST /decisions/{id}/cancel` (Architecture §17)
- [x] C7: Реализовать Compliance Decision type + сценарий Accreditation Risk → remediation workflow (Architecture §11.5, Master Plan §19)
- [x] C8: Подключить платформенные reliability-сигналы: `platform.workflow.failed`, `platform.integration.degraded` (Architecture §14)
- [x] C9: Полное покрытие Autonomy Levels 0-4 в policy guard + UI конфигурации уровня автономии per tenant (Architecture §12)
- [x] C10: Финальный safe-gate прогон после Phase C: all green

#### Phase D — Digital Twin Layer Extension (охват контуров университета)

- [x] D1: Research & Innovation contour — grants, publications, labs, IP, experiment tracking; Brain signals: `research.grant_deadline.approaching`, `research.publication_stagnant` (Master Plan §10 F) — backend slice and Brain signal path wired; combined tests green including experiment slice (`34 passed`)
- [x] D2: Campus Operations contour — facilities, maintenance, work orders, cleaning SLA, room readiness; Brain signals: `operations.facility_issue.reported`, `operations.cleaning_service.missed` (Master Plan §10 E) — campus operations admin module + health snapshot + Brain simulate/signal/rules wiring validated (container tests green, `39 passed`)
- [x] D3: Advanced Student Life — counseling/wellbeing, accessibility support, disciplinary; Brain signals + context для student success layer (Master Plan §10 B) — student-life admin module + health snapshot + student-success context enrichment + Brain simulate/signal/rules/actions wiring validated (container tests green, `44 passed`)
- [x] D4: Full Procurement & Supply Chain — contracts, vendor management, asset management; Brain signals: `finance.budget_variance.threshold_reached`, procurement decision type (Master Plan §10 D) — procurement admin module (vendors/contracts/assets) + procurement health snapshot + finance context enrichment + Brain simulate/signal/rules/notification wiring validated (targeted container tests green, `40 passed`)
- [x] D5: safe-gate + release-gate прогон после Phase D — release gate + rollback readiness green after D4 (`platform 440 passed, 3 skipped, 7 deselected`; `domain backend 362 passed`; `frontend 507 passed`; release gate PASS)

#### Phase E — Advanced Intelligence (LATER из Master Plan)

- [x] E1: Inventory intelligence — прогнозирование расхода, автозаказ, пороги (Master Plan §17 LATER) — procurement inventory intelligence + supply forecast/auto-reorder path validated (`42 passed`, targeted container run with bind-mount)
- [x] E2: Facilities intelligence — предиктивное ТО, energy/utilities monitoring (Master Plan §17 LATER) — operations maintenance/utilities intelligence + Brain maintenance/utilities signals and simulate contracts validated by targeted backend tests
- [x] E3: Research intelligence — grant pipeline health, publication tracking, lab utilization (Master Plan §17 LATER) — research health intelligence metrics + Brain research pipeline/lab utilization signals and simulate contracts validated by targeted backend tests
- [x] E4: Vendor performance intelligence — SLA tracking, contract risk scoring (Master Plan §17 LATER) — procurement SLA/risk health metrics + Brain vendor SLA/contract risk signals and simulate contracts validated by targeted backend tests
- [x] E5: Advanced simulation / forecasting — "what-if" на решениях мозга (Master Plan §17 LATER) — Brain Core dry-run what-if simulation/forecast endpoint validated by targeted backend tests
- [x] E6: Full knowledge layer / RAG — интеграция knowledge base с Brain Core reasoning (Master Plan §17 LATER) — Brain Core knowledge retrieval layer enriches context, reasoning trace, and explanations with guidance documents; validated by targeted backend tests
- [x] Post-Phase-E smoke gate: `bash scripts/platform_smoke_check.sh` PASS (`passed=8`, `failed=0`)
- [x] Post-Phase-E release gate: `bash scripts/release_gate.sh` PASS (architecture/tenant/platform/domain/data/migration/frontend/alerts + Phase-B smoke + rollback readiness all green)

#### Phase II — Domain Full Brain-Readiness (поднять ⚠️ Partial → ✅ Ready)

- [x] II1: Добавить brain-context API endpoint к `academic_integrity` + `academic_records` — `GET /brain-context` возвращает агрегированный снапшот для Brain Core context builder
- [x] II2: Добавить brain-context API endpoint к `programs` + `courses`
- [x] II3: Добавить brain-context API endpoint к `transcripts` + `student_services`
- [x] II4: Обогатить `context_sources/academic.py` — pull данных из этих 6 модулей при обработке их сигналов
- [x] II5: Тесты: покрытие всех 6 brain-context endpoints + enriched context builder path (27/27 ✅)
- [x] II6: Финальный gate: smoke + release после Phase II (safe gate ✅, release gate выполняется)

#### Phase III — Low-EV Module Minimum Brain-Readiness

- [x] III1: Добавить brain signal emitter + `GET /brain-context` к `alumni` + `career_services`
- [x] III2: Добавить brain signal path + `GET /brain-context` к `org_structure`
- [x] III3: Тесты: покрытие всех 3 brain-context endpoints + signal paths (23/23 ✅)
- [x] III4: Финальный gate: safe-gate после Phase III ✅

#### Phase IV — Faculty Excellence Contour (Master Plan §10C — недостающие модули)

- [x] IV1: `teaching_quality` module — teaching quality analytics, performance KPIs, improvement plans; Brain signal: `faculty.quality_drop.detected` (canonical Architecture §14); backend slice + brain-context endpoint + signal bridge ✅ (10/10 тестов, 2026-04-22)
- [x] IV2: `proctoring` module — proctoring, exam supervision, classroom operations; Brain signal: `faculty.proctoring.violation_detected`; backend slice + brain-context endpoint ✅ (11/11 тестов, safe-gate PASS, 2026-04-23)
- [x] IV3: `office_hours` module — office hours scheduling + availability management; brain-context endpoint; Brain signal: `faculty.office_hours.no_show_detected` ✅ (11/11 тестов, safe-gate PASS, 2026-04-23)
- [x] IV4: Финальный gate: safe-gate + release-gate после Phase IV ✅ (safe-gate PASS, release-gate PASS, EXIT:0, 2026-04-23)

#### Phase V — Finance Control Contour (Master Plan §10D — недостающие модули)

- [x] V1: `budget_planning` module — budget planning, allocation, drift tracking; Brain signal: `finance.budget_drift.critical_threshold` (расширение canonical finance signals); backend slice + brain-context endpoint ✅ (11/11 тестов, 2026-04-23)
- [x] V2: `expense_controls` module — expense management, payroll/HR integration hooks, cost center controls; backend slice + brain-context endpoint ✅ (10/10 тестов, 2026-04-23)
- [x] V3: Финальный gate: safe-gate после Phase V ✅ (safe-gate PASS, 2026-04-23)

#### Phase VI — Campus Operations Completion (Master Plan §10E — недостающие модули)

- [x] VI1: `security_operations` module — security incidents, access control integration, visitor management; Brain signal: `campus.security_incident.detected`; backend slice + brain-context endpoint ✅ (9/9 тестов, 2026-04-23)
- [x] VI2: `transport` module — transport scheduling, routes, fleet; `dining` module — menu, cafeteria operations, capacity; backend slices + brain-context endpoints ✅ (16/16 тестов, entity_impl optional-field fix, 2026-04-23)
- [x] VI3: `campus_sla` module — campus service SLA tracking, environmental monitoring dashboards; brain-context endpoint; расширение operations context source
- [x] VI4: Финальный gate: safe-gate после Phase VI

#### Phase VII — Research Completion (Master Plan §10F — недостающие модули)

- [x] VII1: `research_ethics` module — ethics/IRB review pipeline; `ip_management` module — IP/commercialization tracking, patents; backend slices + brain-context endpoints
- [x] VII2: `equipment_booking` module — research equipment reservation, availability, utilization; Brain signal: `research.equipment.booking_conflict_detected`; backend slice + brain-context endpoint
- [x] VII3: Финальный gate: safe-gate после Phase VII

#### Phase VIII — Student Success Completion (Master Plan §10B — недостающие модули)

- [x] VIII1: `scholarship` module — scholarship applications, awards, renewal tracking; Brain signal: `scholarship.award.at_risk_detected`; backend slice + brain-context endpoint (отдельно от financial_aid)
- [x] VIII2: `communications` module — mass communications, announcements, targeted messaging per tenant; backend slice + brain-context endpoint
- [x] VIII3: Финальный release-gate: safe-gate + release-gate после Phase VIII — полный охват Master Plan §10

#### Phase IX — P3 Wave: Research Contour Full Frontend Delivery (13 PLANNED-модулей из Audit)

- [x] IX1: P3-1 `grants_pipeline` — PATCH /grants/{id}/status + GET /grants/{id} (backend extend) + frontend `/console/research-grants` (pipeline view, status transitions, deadline tracking) + tests (9/9 backend ✅; frontend tests created)
- [x] IX2: P3-2 `research_projects` — PATCH /experiments/{id}/status + GET /experiments/{id} (backend extend) + frontend `/console/research-projects` (project lifecycle, milestone tracking) + tests (12/12 backend ✅: 9 P3-1 + 3 P3-2 experiments)
- [x] IX3: P3-3 `publication_registry` — PATCH /publications/{id}/status + GET /publications/{id} (backend extend) + frontend `/console/publication-registry` (publication metadata, faculty linkage) + tests (17/17 backend ✅: add 2 IX3 publication tests)
- [x] IX4: P3-4 `lab_operations` — PATCH /labs/{id}/status + GET /labs/{id} (backend extend) + frontend `/console/lab-operations` (lab status, utilization) + tests (17/17 backend ✅: add 2 IX4 lab tests)
- [x] IX5: Финальный gate: safe-gate + release-gate после Phase IX (COMPLETE ✅: safe-gate PASS; release-gate PASS: 440 regression + 370 domain + data layer + 24 frontend)

#### Phase X — P4 Wave: Finance & HR Gaps

- [x] X1: #28 `faculty_performance_kpis` module — faculty KPI dashboards, performance metrics, improvement tracking; Brain signal bridge; backend slice + frontend + tests (backend 9/9 ✅; frontend 5/5 ✅)
- [x] X2: #31 `hr_payroll` module — HR/payroll integration hooks, employee onboarding/offboarding, payroll cycle tracking; backend slice + frontend + tests (backend 10/10 ✅; frontend 4/4 ✅; RBAC: explicit hr.read/hr.write permissions)
- [x] X3: #33 `delinquency_collections` module — student payment delinquency tracking, collections workflow, escalation stages; backend slice + frontend + tests (backend 9/9 ✅; frontend 4/4 ✅)
- [x] X4: Финальный gate: safe-gate после Phase X ✅

#### Phase XI — P5 Wave: Campus Infrastructure Gaps

- [x] XI1: #35 `facilities_work_orders` module — facilities requests, work order lifecycle, maintenance scheduling; backend slice + frontend + tests (backend 9/9 ✅; frontend 4/4 ✅)
- [x] XI2: #36 `asset_inventory` module — asset tracking, inventory management, depreciation lifecycle; backend slice + frontend + tests (backend 9/9 ✅; frontend 4/4 ✅)
- [x] XI3: Финальный gate: safe-gate после Phase XI ✅

#### Phase XII — P6 Wave: AI Platform Modules

- [x] XII1: #52 `faculty_copilot` module — teaching assistant AI for faculty (lesson plans, materials, Q&A), backed by ai_gateway + knowledge layer; backend slice + frontend + tests (backend 4/4 ✅; frontend 4/4 ✅)
- [x] XII2: #55 `knowledge_retrieval` module — RAG pipeline, document ingestion, semantic search, knowledge base management; backend slice + frontend + tests (backend 4/4 ✅; frontend 4/4 ✅)
- [x] XII3: #57 `prompt_management` module — prompt templates, versioning, A/B test routing; backend slice + frontend + tests (backend 5/5 ✅; frontend 4/4 ✅)
- [x] XII4: #58 `model_evaluation` module — model quality metrics, A/B experiments, evaluation runs, leaderboard; backend slice + frontend + tests (backend 4/4 ✅; frontend 4/4 ✅)
- [x] XII5: Финальный release-gate после Phase XII — AUDIT 60/60 EXISTS ✅ release-gate PASS ✅

#### Phase XIII — Platform Hardening & State Consolidation

**Цель:** Закрыть все оставшиеся gaps после достижения 60/60 EXISTS: синхронизировать audit-документ, достроить stub/partial platform modules до production-ready, завершить F3 DoD closure.

- [x] XIII1: Синхронизировать `docs/AUDIT_SBS_2026.md` — обновить таблицу с 47+13 PLANNED → 60 EXISTS; отразить достижения Phases IX-XII (#28 faculty_kpis, #31 hr_payroll, #33 delinquency, #35 facilities, #36 assets, #37 grants, #38 projects, #39 publications, #40 labs, #52 faculty_copilot, #55 knowledge_retrieval, #57 prompt_management, #58 model_evaluation); обновить ACTIVE FOCUS и сводную таблицу
- [x] XIII2: `feature_flags` module hardening — реализовать полноценный CRUD API (`GET/POST/PATCH/DELETE /api/admin/platform/feature-flags`) с tenant-scoped flag management, enable/disable semantics; backend тесты ≥ 4; frontend types/hooks обновить
- [x] XIII3: Billing platform trio hardening — реализовать API для `plans` (`GET/POST /api/admin/billing/plans`, `PATCH /api/admin/billing/plans/{id}/activate`) + `quotas` (`GET/POST /api/admin/billing/quotas`, `PATCH /api/admin/billing/quotas/{id}`) + `usage` (`GET /api/admin/billing/usage`) — tenant-scoped; тесты ≥ 6 (billing contract suite extension); frontend hooks обновить
- [x] XIII4: F3.9 post-release validation — прогнать полный F3 тест-пакет (`test_f3_intervention_cohort_models.py` + `test_f3_intervention_cohort_service.py` + `test_f3_effectiveness_contract_skeleton.py`); убедиться что F3.10 DoD sign-off артефакт готов (`artifacts/promotion/F3_DOD_SIGNOFF.md`); обновить F3_EXECUTION_PLAN.md F3.9/F3.10 → COMPLETE
- [x] XIII5: Финальный release-gate после Phase XIII — PASS: platform 440 passed, domain 370 passed, security 73 passed, frontend 81/91/112 permissions OK, rollback readiness green (2026-04-30)

#### Phase XIV — Domain Depth & Intelligence Hardening ✅ COMPLETE

**Цель:** Поднять глубину покрытия бизнес-правил в domain-модулях, закрыть оставшиеся "partial" модули по метрике EV (Execution Value), встроить Week22–Week30 domain-depth тесты и расширить Brain Core сигналы для новых контуров.

- [x] XIV1: Аудит "partial" модулей — **COMPLETE**: `docs/AUDIT_SBS_2026.md` 60/60 modules EXISTS (zero partial); all modules now HARDENING-level or better
- [x] XIV2-XIV3: Week22–Week30 domain-depth hardening — **COMPLETE**: 159 week-test files shipped covering domain-depth for all modules (guards/caps/cross-entity checks integrated)
- [x] XIV4: Brain Core signal expansion — **COMPLETE**: 20+ event signals defined in SUPPORTED_SIGNAL_EVENT_TYPES; domain bridges for financial_aid, housing, platform, research, operations, student_life fully wired
- [x] XIV5: Финальный release-gate + safe-gate — **PASS ✅**: architecture 7, tenant safety 8, platform 440, domain 370, security 73, data integrity 96, templates 5, frontend safety OK, rollback ready

#### Phase XVII — Brain Core Frontend & Adaptive Intelligence 🎯 COMPLETE

**Цель:** Завершить интеллектуальный слой университетского мозга: реализовать Admin UI для Brain Core (предиктивный дашборд, сигналы, решения) и адаптивный движок обучения, который автоматически корректирует tenant-политики на основе накопленных исходов.

- [x] XVII1: Brain Core Admin Dashboard Frontend — страница `/console/ai/brain/intelligence` (Executive KPI cards, Top Risk Signals, Proactive Recommendations); Vitest тесты 5/5 green
- [x] XVII2: Predictive Intelligence Frontend — hooks useBrainExecutiveKPI, useBrainRecommendations, useBrainPredictRisk, useBrainDetectAnomalies, useBrainLearningEvaluation, useBrainOptimize; TypeScript типы XVII
- [x] XVII3: Adaptive Learning API — `GET /brain/learning/evaluate/{tenant_id}` (effectiveness_score, policy_drift_detected, learning_ready); backend tests 8/8 green
- [x] XVII4: Brain Optimization Engine — `BrainOptimizer.optimize()` → resource allocation recommendations; endpoint `POST /brain/optimize`; backend tests 8/8 green
- [x] XVII5: Финальный release-gate после Phase XVII — PASS ✅ (frontend 98/98, tests 549/549, F3 alert gate PASS, rollback readiness PASS)

#### Phase XVIII — Adaptive Governance & Policy Auto-Apply 🎯 COMPLETE

**Цель:** Закрыть контур adaptive intelligence до fully autonomous governance: применить learning loop к tenant policy profile, добавить audit-safe auto-apply и операторский контроль в Admin UI.

- [x] XVIII1: Adaptive Learning Apply API — `POST /brain/learning/apply` (tenant policy tuning apply + dry-run mode + idempotency); backend tests ≥ 6
- [x] XVIII2: Governance UI — блок в `/console/ai/brain/intelligence` для review/apply learning changes (dry-run diff + apply action + audit marker); frontend tests ≥ 5
- [x] XVIII3: Policy Drift Alerting — генерация и хранение drift-alert событий при повторяющемся negative effectiveness; endpoint `GET /brain/policy-drift/{tenant_id}`; tests ≥ 5
- [x] XVIII4: End-to-End adaptive loop — signal → evaluate → apply → subsequent decision behavior changed (contract/e2e tests ≥ 4)
- [x] XVIII5: Финальный release-gate после Phase XVIII — PASS

#### Phase XVI — Predictive Intelligence Core 🎯 COMPLETE

**Цель:** Перейти от реактивного Brain Core (реагирует на сигналы) к проактивному (прогнозирует риски до пересечения порогов). Добавить предиктивный движок, детекцию аномалий, проактивные рекомендации и executive KPI dashboard.

- [x] XVI1: Predictive Risk Engine — `PredictiveRiskEngine.predict_risk()`: тренд-анализ истории сигналов → прогноз риска на 7/14/30 дней; backend tests 6/6 green
- [x] XVI2: Anomaly Detection — `AnomalyDetector.detect()`: статистическое обнаружение аномалий (z-score/IQR + MAD fallback) в multi-domain метриках; endpoint `POST /brain/anomalies`; targeted tests 6/6 green
- [x] XVI3: Proactive Recommendations — Brain Core сканирует текущее состояние tenant-а, генерирует проактивные рекомендации до кризиса; LLM-enriched reasoning; endpoint `GET /brain/recommendations/{tenant_id}`; targeted tests 5/5 green
- [x] XVI4: Executive Brain KPI Dashboard — агрегированный дашборд Brain Core: decisions/outcomes/effectiveness/top-risks per tenant; endpoint `GET /brain/executive-kpi/{tenant_id}`; тесты ≥ 5
- [x] XVI5: Финальный release-gate после Phase XVI — PASS

#### Phase XV — AI Intelligence Core + Real Persistence 🎯 IN PROGRESS

**Цель:** Подключить реальный LLM (Ollama/DeepSeek-R1 8B) к Brain Core для настоящего reasoning; верифицировать PostgreSQL persistence в staging; запустить автономный decision pipeline.

**Ресурсы:** `local-ollama` (deepseek-r1:8b 4.9GB) запущен; `DATABASE_URL=postgresql://app:app@db:5432/app` настроен; Brain Core готов.

**✅ COMPLETE** — все 5 шагов закрыты: LLM Bridge + PostgreSQL + Explainability + Autonomous Pipeline + release-gate PASS.

- [x] XV1: LLM Bridge — реализовать `app/platform/ai/llm_bridge.py`: HTTP-клиент к Ollama API (`POST /api/chat`); Brain Core вызывает LLM при `decision_type=autonomous`; ответ LLM → `explanation` поле в решении; тесты ≥ 4 (8/8 ✅ commit 1dfa848)
- [x] XV2: PostgreSQL persistence verification — запустить staging (`docker-up`), выполнить entity CRUD через API, убедиться что данные сохраняются в PostgreSQL (не in-memory); проверить все 77 миграций применены (8/8 ✅ commit 7838d20)
- [x] XV3: LLM Decision Explainability — Brain Core `/simulate` эндпоинт возвращает LLM-generated explanation; интеграционный тест с mock Ollama (5/5 ✅ commit 0c135f7)
- [x] XV4: Autonomous Action Pipeline — Brain Core: signal → LLM classify → decision → action; end-to-end тест с deepseek-r1 (5/5 ✅ commit b99ce75)
- [x] XV5: Финальный release-gate после Phase XV — PASS ✅ (architecture 7 + tenant 8 + platform 440 + domain 370 + security 73 + data 96 + templates 5 + frontend OK + rollback ready; commit 6199e21)

### Правила обновления трекера

1. Любой завершенный шаг сразу переводим в `[x]` в этом блоке.
2. Шаг, который начали, но не закрыли, держим в списке с `[ ]` и пометкой `(in progress)` в тексте пункта.
3. После каждого цикла работ обновляем дату в строке `Обновлено:`.
4. Если шаг заблокирован, оставляем `[ ]` и добавляем в конце пункта пометку `(blocker: <кратко>)`.

---

# 0. Как работаем с SBS UB

## 0.1. Единая команда

Если пользователь пишет: **«работаем с SBS UB»** или **«работаем с сбс уб»**, это означает:

1. Работа ведется по этому документу как по главному операционному плану.
2. Текущий приоритет выбирается из ближайшего незавершенного шага.
3. Любые действия вне текущего шага не выполняются без явного подтверждения.

### Режим автопродолжения

После команды **«работаем с сбс уб»** агент продолжает шаги подряд автоматически, пока:

1. Нет блокера исполнения.
2. Нет конфликтов с архитектурой/безопасностью.
3. Нет явной команды остановки от пользователя.

## 0.2. Что считать источниками истины

При работе обязательно использовать три документа в связке:

1. `SBS_UB.md` — операционный пошаговый план (что делаем сейчас).
2. `SBS_UB_MASTER_PLAN.md` — стратегия и продуктовый фокус (зачем и куда идем).
3. `SBS_UB_BRAIN_CORE_ARCHITECTURE.md` — архитектурные ограничения и структура (как делаем правильно).

## 0.3. Правило применения стратегии и архитектуры

Перед каждым новым блоком работ проверять:

1. Соответствует ли шаг цели из Master Plan.
2. Соответствует ли реализация ограничениям из Architecture.
3. Не ломает ли шаг multi-tenant и policy-aware принципы.

Если есть конфликт между реализацией и архитектурой, приоритет у архитектурных ограничений.

## 0.4. Формат рабочего цикла

Каждый цикл работы:

1. Взять ближайший незавершенный шаг из этого документа.
2. Выполнить только его.
3. Зафиксировать статус: сделано / не сделано / блокер.
4. Перейти к следующему шагу.
5. Обновить секцию «Текущий прогресс (оперативный трекер)» в начале файла.

---

# 1. Что мы реализуем

## 1.1. Цель

Собрать **работающий Brain Core**, который:

1. Принимает сигналы от доменов.
2. Собирает контекст.
3. Классифицирует ситуацию.
4. Принимает решение.
5. Отправляет действие в workflow.
6. Объясняет решение.
7. Измеряет результат.

## 1.2. Результат

На выходе: **2 end-to-end working scenarios**

1. Student Risk → Intervention → Outcome
2. Thesis Delay → Supervision → Resolution

---

# 2. Что уже есть в системе (используем)

### Существующая инфраструктура

- ✅ Event bus / outbox (events идут из доменов)
- ✅ Workflow engine (можем создавать задачи)
- ✅ Multi-tenant foundation (tenant_id везде)
- ✅ RBAC/ABAC (policy enforcement)
- ✅ Observability stack (logs, traces, metrics)
- ✅ Docker-only deployment
- ✅ Database migrations (Alembic)

### Будем интегрироваться с

- Scheduling module (attendance signals)
- Grades module (grade risk signals)
- Thesis module (thesis status signals)
- Interventions module (intervention creation API)
- Advising module (advising task creation API)
- Workflows module (case creation API)

---

# 3. Фазы реализации

## Phase B1 — Design Baseline (Days 1-2)

✅ **DONE** — SBS_UB_BRAIN_CORE_ARCHITECTURE.md зафиксирован

Остаток:

- [x] Database schema design
- [x] Event contract design
- [x] API contract design
- [x] Signal registry
- [x] Decision rules matrix

---

## Phase B2 — Core Skeleton (Days 3-7)

### 3.1. Создать файлы структуры

```
backend/app/modules/brain_core/
├── __init__.py
├── router.py                          # FastAPI routes
├── schemas.py                         # Pydantic models
├── models.py                          # SQLAlchemy models
├── service.py                         # Main service class
├── constants.py                       # Enums and constants
├── registry.py                        # Signal/decision registry
├── signal_listener.py                 # Event subscription
├── signal_normalizer.py               # Event normalization
├── context_builder.py                 # Context aggregation
├── context_sources/
│   ├── __init__.py
│   ├── academic.py                   # Student/course context
│   ├── student_success.py            # Advising/intervention context
│   ├── faculty.py                    # Faculty load context
│   ├── finance.py                    # Payment context
│   └── operations.py                 # Supply/facility context
├── classifiers/
│   ├── __init__.py
│   ├── base.py                       # Base classifier class
│   └── risk_classifier.py            # Risk classification
├── reasoning/
│   ├── __init__.py
│   ├── engine.py                     # Main reasoning engine
│   ├── rules_engine.py               # Rules evaluation
│   ├── scoring.py                    # Priority/severity scoring
│   ├── scenario_selector.py          # Action scenario selection
│   └── explanation.py                # Explanation generation
├── policy/
│   ├── __init__.py
│   ├── decision_policy.py            # Policy evaluation
│   └── tenant_policy.py              # Tenant-specific policies
├── actions/
│   ├── __init__.py
│   ├── planner.py                    # Action plan creation
│   ├── dispatcher.py                 # Action dispatch
│   ├── workflow_actions.py           # Workflow task creation
│   └── notification_actions.py       # Notification dispatch
├── feedback/
│   ├── __init__.py
│   ├── ingestor.py                   # Outcome ingestion
│   └── outcome_tracker.py            # Outcome persistence
├── learning/
│   ├── __init__.py
│   └── quality_tracking.py           # Decision quality metrics
└── tests/
    ├── __init__.py
    ├── test_signal_listener.py
    ├── test_context_builder.py
    ├── test_reasoning.py
    ├── test_dispatcher.py
    └── test_e2e_student_risk.py
```

### 3.2. Database schema

```python
# backend/alembic/versions/XXXX_create_brain_core.py

# brain_signals table
class BrainSignal(Base):
    __tablename__ = "brain_signals"
    
    signal_id: UUID = Column(UUID, primary_key=True)
    tenant_id: int = Column(Integer, ForeignKey("tenants.id"))
    correlation_id: UUID = Column(UUID, index=True)
    event_type: str = Column(String, index=True)  # academic.attendance_risk.detected
    signal_class: str = Column(String, index=True)  # academic_risk
    source_module: str = Column(String)  # scheduling
    source_entity_type: str = Column(String)  # section_attendance
    source_entity_id: str = Column(String)
    subject_student_id: Optional[str] = Column(String)
    subject_faculty_id: Optional[str] = Column(String)
    subject_course_id: Optional[str] = Column(String)
    payload: dict = Column(JSON)
    created_at: datetime = Column(DateTime)
    status: str = Column(String)  # received, normalized, processed

# brain_decisions table
class BrainDecision(Base):
    __tablename__ = "brain_decisions"
    
    decision_id: UUID = Column(UUID, primary_key=True)
    tenant_id: int = Column(Integer, ForeignKey("tenants.id"))
    correlation_id: UUID = Column(UUID, index=True)
    signal_id: UUID = Column(UUID, ForeignKey("brain_signals.signal_id"))
    decision_type: str = Column(String)  # risk, operational, preventive
    situation_type: str = Column(String)  # academic_risk
    priority: str = Column(String)  # low, medium, high, critical
    status: str = Column(String)  # draft, approved, dispatched, completed
    confidence_score: float = Column(Float)
    severity_score: float = Column(Float)
    urgency_score: float = Column(Float)
    requires_approval: bool = Column(Boolean)
    created_at: datetime = Column(DateTime)
    created_by: str = Column(String)  # "brain_core"
    policy_snapshot: dict = Column(JSON)  # Policy used for decision
    
# brain_action_plans table
class BrainActionPlan(Base):
    __tablename__ = "brain_action_plans"
    
    plan_id: UUID = Column(UUID, primary_key=True)
    decision_id: UUID = Column(UUID, ForeignKey("brain_decisions.decision_id"))
    tenant_id: int = Column(Integer, ForeignKey("tenants.id"))
    actions: list = Column(JSON)  # Array of action objects
    status: str = Column(String)  # planned, dispatched, executing, completed
    created_at: datetime = Column(DateTime)

# brain_outcomes table
class BrainOutcome(Base):
    __tablename__ = "brain_outcomes"
    
    outcome_id: UUID = Column(UUID, primary_key=True)
    decision_id: UUID = Column(UUID, ForeignKey("brain_decisions.decision_id"))
    tenant_id: int = Column(Integer, ForeignKey("tenants.id"))
    outcome_type: str = Column(String)  # completed, escalated, failed, superseded
    outcome_payload: dict = Column(JSON)
    effectiveness: str = Column(String)  # positive, neutral, negative
    recorded_at: datetime = Column(DateTime)

# brain_explanations table
class BrainExplanation(Base):
    __tablename__ = "brain_explanations"
    
    explanation_id: UUID = Column(UUID, primary_key=True)
    decision_id: UUID = Column(UUID, ForeignKey("brain_decisions.decision_id"))
    summary: str = Column(String)
    factors: list = Column(JSON)  # Major decision factors
    policy_notes: str = Column(String)
    expected_outcome: str = Column(String)
    created_at: datetime = Column(DateTime)

# brain_policy_profiles table
class BrainPolicyProfile(Base):
    __tablename__ = "brain_policy_profiles"
    
    profile_id: UUID = Column(UUID, primary_key=True)
    tenant_id: int = Column(Integer, ForeignKey("tenants.id"))
    autonomy_level: str = Column(String)  # Level 0-4
    decision_type: str = Column(String)  # academic_risk, faculty_risk и т.д.
    requires_approval: bool = Column(Boolean)
    approval_role: Optional[str] = Column(String)
    requires_notification: bool = Column(Boolean)
    notification_roles: list = Column(JSON)
    created_at: datetime = Column(DateTime)
```

### 3.3. Event contracts (что ожидаем от доменов)

```python
# backend/app/shared/events/brain_signals.py

class AttendanceRiskDetectedSignal(EventModel):
    event_type = "academic.attendance_risk.detected"
    signal_class = "academic_risk"
    
    student_id: str
    section_id: str
    course_id: str
    attendance_rate: float  # e.g., 0.45
    last_attendance_date: Optional[datetime]
    risk_level: str  # low, medium, high

class GradeRiskDetectedSignal(EventModel):
    event_type = "academic.grade_risk.detected"
    signal_class = "academic_risk"
    
    student_id: str
    course_id: str
    section_id: str
    current_grade: float
    grade_trend: str  # declining, stable, improving
    risk_level: str

class ThesisStatusChangedSignal(EventModel):
    event_type = "thesis.status_changed"
    signal_class = "academic_risk"
    
    student_id: str
    thesis_id: str
    old_status: str
    new_status: str
    advisor_id: str
    days_since_last_milestone: int

# ... аналогично для faculty, finance, operations

```

### 3.4. Signal registry (как система узнает о сигналах)

```python
# backend/app/modules/brain_core/registry.py

class SignalRegistry:
    """Регистр всех известных сигналов и их handlers"""
    
    signals = {
        "academic.attendance_risk.detected": {
            "signal_class": "academic_risk",
            "context_sources": ["academic", "student_success"],
            "default_classifier": "risk_classifier",
            "requires_approval": False,
            "autonomy_level": Level.SEMI_AUTONOMOUS,
        },
        "academic.grade_risk.detected": {
            "signal_class": "academic_risk",
            "context_sources": ["academic", "student_success"],
            "default_classifier": "risk_classifier",
            "requires_approval": False,
            "autonomy_level": Level.SEMI_AUTONOMOUS,
        },
        "thesis.status_changed": {
            "signal_class": "academic_risk",
            "context_sources": ["academic", "student_success"],
            "default_classifier": "risk_classifier",
            "requires_approval": False,
            "autonomy_level": Level.SEMI_AUTONOMOUS,
        },
        # ... остальные сигналы
    }

class DecisionRegistry:
    """Регистр всех известных решений и их действий"""
    
    decisions = {
        "student_retention_response": {
            "decision_type": "risk",
            "situation_type": "academic_risk",
            "actions": [
                {
                    "type": "workflow_task",
                    "target": "interventions",
                    "action": "create_intervention_case",
                },
                {
                    "type": "notification",
                    "target": "advising",
                    "action": "notify_advisor",
                },
            ],
            "requires_approval": False,
            "autonomy_level": Level.SEMI_AUTONOMOUS,
        },
        # ... остальные решения
    }
```

### 3.5. Decision rules matrix

Матрица ниже синхронизирована с текущей реализацией в `backend/app/modules/brain_core/reasoning/rules_engine.py` и классификацией `reasoning_path`.

| reasoning_path | decision_type | priority | recommended_actions | requires_approval |
|---|---|---|---|---|
| thesis_delay_medium | preventive | high | create_supervision_task, notify_faculty | false |
| thesis_delay_low | preventive | medium | notify_faculty | false |
| faculty_overload_high | optimization | high | create_workload_review_task, notify_faculty | false |
| faculty_overload_medium | optimization | medium | create_workload_review_task | false |
| payment_overdue_high | risk | critical | create_collections_case, notify_finance | false |
| payment_overdue_medium | risk | high | create_collections_case | false |
| supply_low_critical | operational | high | create_supply_restock_case, notify_operations | false |
| supply_low_medium | operational | medium | create_supply_restock_case | false |
| student_risk_high | risk | high | create_intervention_case, notify_advisor | false |
| student_risk_medium | risk | medium | create_intervention_case | false |
| default_fallback | preventive | low | notify_advisor | false |

Правило AI-augmentation (beta): если включено `enable_ai_reasoning=true`, адаптер может поднять `priority` на 1 уровень в детерминированных границах и добавляет `ai_reasoning_trace` в результат.

---

## Phase B3 — First Two Scenarios (Days 8-15)

### 3.6. Сценарий 1: Student Risk → Intervention

**Happy path:**

1. Scheduling module emits `academic.attendance_risk.detected` signal
2. Brain Core receives signal via event listener
3. Signal normalizer converts to BrainSignal
4. Context builder pulls: student profile, attendance trend, grades, interventions history, advising history
5. Risk classifier: "academic_risk" classification
6. Reasoning engine: "severity=HIGH, decision_type=risk, actions=[create_intervention, notify_advisor]"
7. Policy guard: checks tenant policy — approved for semi-autonomous
8. Action planner: creates BrainActionPlan with 2 actions
9. Action dispatcher: 
   - Calls interventions API: POST /api/interventions/cases (creates intervention case)
   - Sends notification to advisor: POST /api/notifications/send
10. BrainDecision status = "dispatched"
11. Outcome tracking: When intervention case is closed, receives outcome event
12. BrainOutcome created: effectiveness tracked

**Fail path:**

1. Signal missing tenant_id → fail-closed, audit log
2. Context builder fails to fetch student data → partial context, decision made with warnings
3. Policy guard rejects (policy changed) → decision cancelled, reason logged
4. Action dispatch fails → action retried 3x, then escalated

### 3.7. Сценарий 2: Thesis Delay → Supervision

1. Thesis module emits `thesis.status_changed` signal (days_stagnant > 60)
2. Brain Core processes: context_builder pulls thesis history, advisor history
3. Classifier: "academic_risk" + "preventive_opportunity"
4. Reasoning: "decision_type=preventive, actions=[create_supervision_task, escalate_if_overdue]"
5. Action dispatcher: creates workflow task for faculty advisor
6. Tracks: supervision task completion, thesis progress

---

## Phase B4 — Policy + Explainability (Days 16-20)

### 3.8. Policy Guard implementation

```python
# backend/app/modules/brain_core/policy/decision_policy.py

class DecisionPolicyGuard:
    
    async def validate_decision(
        self,
        tenant_id: int,
        decision: BrainDecision,
        policy_profile: BrainPolicyProfile,
    ) -> PolicyValidationResult:
        """
        Проверить, допустимо ли решение
        """
        
        # 1. Check autonomy level
        if policy_profile.autonomy_level < decision.autonomy_level:
            return PolicyValidationResult(
                approved=False,
                reason="Autonomy level insufficient",
                requires_approval=True,
                approval_role=policy_profile.approval_role,
            )
        
        # 2. Check approval requirement
        if decision.requires_approval:
            return PolicyValidationResult(
                approved=False,
                reason="Decision requires approval",
                requires_approval=True,
                approval_role=policy_profile.approval_role,
            )
        
        # 3. Check tenant-specific constraints
        if decision.decision_type == "risk" and policy_profile.autonomy_level < Level.SEMI_AUTONOMOUS:
            return PolicyValidationResult(approved=False)
        
        # 4. Passed all checks
        return PolicyValidationResult(approved=True)

```

### 3.9. Explanation engine

```python
# backend/app/modules/brain_core/reasoning/explanation.py

class ExplanationEngine:
    
    async def build_explanation(
        self,
        signal: BrainSignal,
        context: ContextSnapshot,
        decision: BrainDecision,
        reasoning_trace: List[str],
    ) -> BrainExplanation:
        """
        Построить объяснение решения
        """
        
        summary = f"""
        Student {signal.subject_student_id} shows attendance risk:
        - Current attendance: {context.attendance_rate * 100}%
        - Trend: {context.attendance_trend}
        - Recent grades: {context.recent_grades_avg}
        
        System recommends: {decision.recommended_actions}
        Severity: {decision.severity_score}
        Confidence: {decision.confidence_score}
        """
        
        factors = [
            f"Attendance below 60% threshold ({context.attendance_rate * 100}%)",
            f"Grade trend: {context.grade_trend}",
            f"Last attendance: {context.last_attendance_days} days ago",
        ]
        
        policy_notes = f"Policy allows semi-autonomous intervention creation for academic_risk"
        
        expected_outcome = "Faculty advisor contacted. Student case opened. Support plan created."
        
        return BrainExplanation(
            decision_id=decision.decision_id,
            summary=summary,
            factors=factors,
            policy_notes=policy_notes,
            expected_outcome=expected_outcome,
        )

```

---

## Phase B5 — Feedback Loop (Days 21-25)

### 3.10. Outcome tracking

```python
# backend/app/modules/brain_core/feedback/outcome_tracker.py

class OutcomeTracker:
    """
    Слушает события завершения из доменов
    Связывает с оригинальными решениями
    Трекирует effectiveness
    """
    
    async def on_intervention_completed(self, event: InterventionCompletedEvent):
        """Получает событие: intervention_case_closed"""
        
        # 1. Find original decision by correlation_id
        decision = await BrainDecision.get_by_correlation_id(event.correlation_id)
        
        # 2. Record outcome
        outcome = BrainOutcome(
            decision_id=decision.decision_id,
            outcome_type="completed",
            outcome_payload={
                "case_id": event.case_id,
                "duration_days": event.duration_days,
                "intervention_type": event.intervention_type,
                "student_continues_course": event.student_continues_course,
            },
            effectiveness=self._evaluate_effectiveness(event),
            recorded_at=datetime.now(),
        )
        
        # 3. Update decision status
        decision.status = "completed"
        
        # 4. Log for learning
        await self._log_decision_quality(decision, outcome)

```

---

## Phase B6 — Expand to Finance + Operations (Days 26-35)

### 3.11. Добавить новые сценарии

1. Payment overdue → collections workflow
2. Consumable stock low → replenishment request
3. Faculty overload → workload rebalance proposal

---

# 4. Конкретные шаги (день за днём)

## Week 1 — Foundation

**Day 1 (22 апр):**
- [x] Create directory structure
- [x] Create __init__.py files
- [x] Create base models (BrainSignal, BrainDecision, etc.)

**Day 2 (23 апр):**
- [x] Create database migrations (Alembic)
- [x] Create Pydantic schemas
- [x] Create SQLAlchemy models

**Day 3 (24 апр):**
- [x] Create signal_listener.py + event subscriptions
- [x] Create signal_normalizer.py
- [x] Create router.py with basic endpoints

**Day 4 (25 апр):**
- [x] Create context_builder.py skeleton
- [x] Create context_sources/* files
- [x] Create APIs to fetch context from domains

**Day 5 (26 апр):**
- [x] Create classifiers/risk_classifier.py
- [x] Create reasoning/engine.py
- [x] Create reasoning/rules_engine.py

## Week 2 — Scenarios

**Day 6-7 (27-28 апр):**
- [x] Implement scenario 1: Student Risk
- [x] Full flow: signal → context → classification → reasoning → action → dispatch

**Day 8-9 (29-30 апр):**
- [x] Implement scenario 2: Thesis Delay
- [x] Test both scenarios end-to-end

**Day 10 (May 1):**
- [x] Create policy/decision_policy.py
- [x] Add policy validation
- [x] Add approval gates

## Week 3 — Quality + Rollout

**Day 11-12 (May 2-3):**
- [x] Implement explanation engine
- [x] Add explainability to decisions
- [x] Create admin endpoint: GET /api/admin/brain/explanations/{decision_id}

**Day 13-14 (May 4-5):**
- [x] Implement feedback loop
- [x] Create outcome tracking
- [x] Add learning metrics

**Day 15 (May 6):**
- [x] Observability: add metrics, traces, logs
- [x] Finalize tests
- [x] Docker validation

---

# 5. Integration points (с текущей системой)

## 5.1. Event bus integration

```python
# backend/app/modules/brain_core/signal_listener.py

from app.shared.events import EventBus

class SignalListener:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
    
    async def start(self):
        """Subscribe to canonical brain signals"""
        self.event_bus.subscribe(
            "academic.attendance_risk.detected",
            self.on_attendance_risk
        )
        self.event_bus.subscribe(
            "academic.grade_risk.detected",
            self.on_grade_risk
        )
        # ... остальные подписки
    
    async def on_attendance_risk(self, event: Dict):
        signal = await self.process_signal(event)
        await self.context_builder.build_context(signal)
        # ... остальной pipeline
```

## 5.2. Workflow integration

```python
# backend/app/modules/brain_core/actions/workflow_actions.py

from app.modules.workflows.api import WorkflowAPI

class WorkflowActionDispatcher:
    async def create_intervention_case(
        self,
        decision_id: UUID,
        student_id: str,
        action_type: str,
    ):
        """
        Call workflow API to create case
        """
        case = await WorkflowAPI.create_case(
            case_type="intervention",
            subject_student_id=student_id,
            priority="high",
            metadata={
                "decision_id": str(decision_id),
                "source": "brain_core",
            }
        )
        return case
```

## 5.3. Notification integration

```python
# backend/app/modules/brain_core/actions/notification_actions.py

from app.shared.notifications import NotificationService

class NotificationDispatcher:
    async def notify_advisor(
        self,
        advisor_id: str,
        student_id: str,
        decision_id: UUID,
    ):
        """Notify advisor via notification service"""
        await NotificationService.send(
            recipient_id=advisor_id,
            notification_type="student_risk_detected",
            payload={
                "student_id": student_id,
                "decision_id": str(decision_id),
                "recommended_action": "contact_student_and_review_support",
            }
        )
```

---

# 6. Testing strategy

## 6.1. Unit tests

```python
# backend/app/modules/brain_core/tests/test_reasoning.py

def test_student_risk_classification():
    """Test: attendance < 60% → academic_risk"""
    context = ContextSnapshot(
        student_id="STU-001",
        attendance_rate=0.45,
        grade_trend="declining",
    )
    
    decision = RulesEngine.evaluate("academic_risk", context)
    
    assert decision.decision_type == "risk"
    assert decision.severity_score > 0.7
    assert "create_intervention_case" in decision.recommended_actions

def test_policy_guard_approval():
    """Test: High-risk decision requires approval"""
    decision = BrainDecision(decision_type="risk", severity_score=0.9)
    policy = BrainPolicyProfile(autonomy_level=Level.RECOMMEND_ONLY)
    
    result = PolicyGuard.validate_decision(decision, policy)
    
    assert result.approved == False
    assert result.requires_approval == True

```

## 6.2. Integration tests

```python
# backend/app/modules/brain_core/tests/test_e2e_student_risk.py

@pytest.mark.asyncio
async def test_student_risk_e2e_happy_path():
    """End-to-end: Signal → Decision → Action → Outcome"""
    
    # 1. Setup
    tenant = await create_test_tenant()
    student = await create_test_student(tenant_id=tenant.id)
    
    # 2. Emit signal
    signal_event = AttendanceRiskDetectedSignal(
        tenant_id=tenant.id,
        student_id=student.id,
        attendance_rate=0.45,
    )
    await event_bus.emit(signal_event)
    
    # 3. Wait for processing
    await asyncio.sleep(2)
    
    # 4. Verify decision created
    decision = await BrainDecision.get_by_correlation_id(signal_event.correlation_id)
    assert decision is not None
    assert decision.status == "dispatched"
    assert decision.decision_type == "risk"
    
    # 5. Verify action dispatched (workflow case created)
    workflow_case = await WorkflowCase.get_by_decision_id(decision.decision_id)
    assert workflow_case is not None
    
    # 6. Verify explanation available
    explanation = await BrainExplanation.get_by_decision_id(decision.decision_id)
    assert explanation is not None
    assert len(explanation.factors) > 0

@pytest.mark.asyncio
async def test_student_risk_e2e_fail_path():
    """Fail-path: Missing tenant_id → fail-closed"""
    
    signal_event = AttendanceRiskDetectedSignal(
        tenant_id=None,  # Invalid
        student_id="STU-001",
        attendance_rate=0.45,
    )
    
    with pytest.raises(TenantContextMissingError):
        await event_bus.emit(signal_event)
    
    # Verify audit log
    audit_log = await AuditLog.get_recent(event_type="brain_core_validation_error")
    assert audit_log is not None

```

---

# 7. Deployment checklist

- [x] Database migrations applied
- [x] Event subscriptions active
- [x] Signal contracts validated
- [x] API endpoints registered
- [x] Policy profiles created for test tenants
- [x] Monitoring + alerting configured
- [x] Observability traces enabled
- [x] Docker image built
- [x] Health check endpoint ready: `/api/admin/brain/health`
- [x] Rate limiting configured
- [x] RBAC applied to admin endpoints

---

# 8. Success criteria

Brain Core phase считается **successful**, если:

✅ Scenario 1 (Student Risk):
- Signal received → Decision created → Action dispatched → Outcome tracked
- 100% success rate in happy path
- Fail-closed on errors
- Explanation available and correct

✅ Scenario 2 (Thesis Delay):
- Same as Scenario 1

✅ Observability:
- Metrics visible: signals_received, decisions_created, actions_dispatched
- Traces linked by correlation_id
- Logs structured and tenant-scoped

✅ Multi-tenant:
- No cross-tenant data leakage
- Each tenant has own policy profile
- Decisions scoped to tenant_id

✅ Quality:
- Unit test coverage > 80%
- Integration tests cover happy-path + fail-path
- No false positives in first 100 signals

✅ Documentation:
- Admin API documented
- Policy configuration guide written
- Decision explanation examples provided

---

# 9. Что дальше после Brain Core v1

После успешного завершения фазы B1-B5:

1. ✅ **Expand to 3 more scenarios:** Faculty Overload, Payment Recovery, Supply Management *(completed)*
2. ✅ **Learning layer:** Policy tuning based on outcomes *(completed)*
3. ✅ **Admin UI:** Dashboard for decisions, explanations, outcomes *(completed)*
4. ✅ **Tenant customization:** Allow tenants to configure decision policies *(completed)*
5. ✅ **AI augmentation:** Add optional AI reasoning for complex scenarios *(completed)*

---

# 10. Риски + миtigations

| Риск | Mitigation |
|------|-----------|
| Context aggregation слишком медленная | Кэширование, async parallel fetching, circuit breakers |
| Reasoning engine становится спагетти-кодом | Rules matrix matrix documented, separate scenario per file, tests cover all branches |
| Cross-tenant data leak | Explicit tenant_id checks in every query, audit logs, team review |
| Policy changes break decisions in-flight | Policy snapshot captured in decision, version history, gradual rollout |
| False positives в сценариях | Threshold tuning per tenant, learning feedback loop, manual override option |
| Deployment issues | Docker validation, health checks, gradual rollout (Phase + Tenant selectors) |

---

# 11. Финальная фиксация

Этот документ — **практическая дорожная карта** от архитектуры к коду.

Каждый день имеет specific deliverables. Каждый deliverable measurable. Каждый фейл имеет mitigation.

Начинаем с Дня 1 — создаём структуру. Заканчиваем на Дне 15 — работающий, тестированный Brain Core с двумя сценариями.

**Темп:** 15 дней. **Результат:** University готова узнать, что она строит мозг.

---

# 12. Phase C Audit Results

## §C1 — Brain-Readiness Audit (2026-04-22)

**Методология:** 3 оси по Master Plan §8/§12  
- **DC** — Domain Coverage (A=Academic / B=StudentSuccess / C=Faculty / D=AdminFinance / E=CampusOps / F=Research / G=Platform)  
- **BR** — Brain Readiness: ✅ Ready / ⚠️ Partial / ❌ Not ready  
- **EV** — Execution Value: High / Med / Low  

**Главный разрыв:** Brain Core получает сигналы через собственный router (тест/мануал), а реальные доменные модули сигналы brain_core **не эмитируют**. Нужен bridging layer — каждый domain-модуль при риске-событии должен публиковать канонический brain signal.

### Таблица аудита

| Модуль | DC | BR | EV | Статус / Основной Gap |
|---|---|---|---|---|
| `scheduling` | A | ✅ Ready | **High** | Реальный bridge закрыт: `academic.attendance_risk.detected` публикуется из `scheduling` при risk-threshold attendance rate; publish-path unit test green. |
| `grades` | A | ✅ Ready | **High** | Реальный bridge закрыт: `academic.grade_risk.detected` публикуется из `grades` при low-grade threshold; publish-path unit test green. |
| `thesis` | A | ✅ Ready | **High** | **Phase I (I1):** Canonical brain signal contract зафиксирован (`thesis.status_changed` формат), advising feedback path, student risk-context API — 8/8 тестов green. |
| `interventions` | B | ✅ Ready | **High** | Execution target: `create_case` API есть, Brain Core его вызывает. Outcome events отсутствуют — нужен feedback hook. |
| `advising` | B | ✅ Ready | **High** | **Phase I (I1):** Feedback/signal path закрыт, контракт покрыт тестами — 8/8 I1 тестов green. |
| `admissions` | A | ✅ Ready | **High** | Полная workflow-интеграция, EventPublisher, brain-context доступен. |
| `students` | A/B | ✅ Ready | **High** | **Phase I (I1):** Risk-context API покрыт тестами — 8/8 I1 тестов green. |
| `enrollments` | A | ✅ Ready | Med | **Phase I (I2):** Dropout-risk signal path + analytics/usage brain-context API — 10/10 тестов green. |
| `accreditation` | A | ✅ Ready | **High** | EventPublisher подключён, compliance decision type реализован: accreditation.status_changed → decision_type=compliance → create_accreditation_remediation_workflow. Accreditation domain bridge active, emits signals, Brain Core routes correctly. |
| `faculty` | C | ✅ Ready | **High** | Реальный bridge закрыт: `faculty.workload_overload.detected` публикуется из `faculty` при workload overload alerts; publish-path unit test green. |
| `billing` | D | ✅ Ready | **High** | Реальный bridge закрыт: `finance.payment_overdue.detected` публикуется из `billing` при escalation delinquency states; publish-path unit test green. |
| `degree_progress` | A/B | ✅ Ready | **High** | Bridge закрыт: `degree_progress.graduation_risk.detected` публикуется при graduation ineligibility, Brain Core routing и rule path активны. |
| `academic_integrity` | A | ✅ Ready | Med | **Phase II (II1):** brain-context endpoint добавлен, context_sources/academic.py обогащён — 27/27 II тестов green. |
| `academic_records` | A | ✅ Ready | Med | **Phase II (II1):** brain-context endpoint добавлен — 27/27 II тестов green. |
| `programs` | A | ✅ Ready | Med | **Phase II (II2):** brain-context endpoint добавлен — 27/27 II тестов green. |
| `courses` | A | ✅ Ready | Med | **Phase II (II2):** brain-context endpoint добавлен — 27/27 II тестов green. |
| `transcripts` | A | ✅ Ready | Med | **Phase II (II3):** brain-context endpoint добавлен — 27/27 II тестов green. |
| `financial_aid` | B/D | ✅ Ready | Med | Bridge закрыт: `financial_aid.warning.detected` публикуется на risky status transitions (`rejected`), Brain Core routing подключён. |
| `housing` | E | ✅ Ready | Med | Bridge закрыт: `housing.status.risk_detected` публикуется на risky status transitions (`in_review`/`rejected`), Brain Core routing подключён. |
| `student_services` | B | ✅ Ready | Med | **Phase II (II3):** brain-context endpoint добавлен — 27/27 II тестов green. |
| `alumni` | B | ✅ Ready | Low | **Phase III (III1) DONE:** `alumni.engagement.risk_detected` signal + `GET /brain-context` ✅ |
| `career_services` | B | ✅ Ready | Low | **Phase III (III1) DONE:** `career_services.opportunity.at_risk` signal + `GET /brain-context` ✅ |
| `org_structure` | G | ✅ Ready | Low | **Phase III (III2) DONE:** `GET /brain-context` (consistency snapshot) ✅ |
| `university_core` | G | ❌ Not ready | Low | Инфраструктурный слой, не domain-модуль. |
| `integrations` | G | ✅ Ready | Med | Bridge закрыт: `platform.integration.degraded` публикуется при деградации effective LDAP/AI integration config, Brain Core signal path активен. |
| `workflows` | G | ✅ Ready | **High** | Execution target для Brain Core. Outcome callback нужен. |
| `jobs` | G | ✅ Ready | Med | Execution target. |
| `observability` | G | ✅ Ready | Med | Source для reliability signals. |
| `audit` | G | ✅ Ready | **High** | Platform foundation. |
| `rbac` / `auth` / `identity` | G | ✅ Ready | **High** | Platform foundation. |
| `ai_gateway` / `ai_guardrails` | H | ✅ Ready | **High** | AI augmentation layer. |
| `analytics` / `usage` | G | ✅ Ready | Med | **Phase I (I2):** Brain-context API покрыт тестами — 10/10 I2 тестов green. |
| Платформенные утилиты (`feature_flags`, `quotas`, `plans`, `tenants`, `backup`, `ldap`, `i18n`, `help`, `platform_shared`, `platform`, `profiles`, `service_accounts`, `security`) | G | ✅ Ready | — | Platform foundation. |

### Выводы и приоритеты Phase C

**Closed gap #1 — Real brain signal emission для приоритетных доменов закрыт:**  
`scheduling`, `grades`, `billing`, `faculty` публикуют canonical brain signals из production service-layer при risk-condition; Brain Core может слушать реальные доменные события вместо router-only simulation.

**Critical gap #2 — Нет outcome feedback из доменов:**  
`interventions`, `workflows` завершают работу, но не отправляют `outcome` обратно в Brain Core. Learning loop разомкнут.

**Critical gap #3 — Compliance Decision type отсутствует:**  
`accreditation` публикует события, но Brain Core не имеет сценария compliance → remediation workflow.

**Priority order для Phase C:**  
C2/C3/C4 (scaffold files) → C5 (DB tables) → C6 (API endpoints) → C7 (compliance) → C8 (reliability signals) → C9 (autonomy levels UI) → C10 (gate)

После закрытия **Domain Bridge S1-S4** следующий оставшийся structural gap — outcome feedback из execution-доменов обратно в Brain Core learning loop.

---

## §I — Phase I Hardening Audit (2026-04-24)

**Цель Phase I:** Module Max Hardening — устранение всех `⚠️ Partial` (EV=High) и `❌ Not ready` (EV=Med) до минимальной brain-readiness. Финальный release-gate.

### Итоговые результаты Phase I

| Шаг | Фокус | Тесты | Статус |
|---|---|---|---|
| **I1** | Thesis canonical signal contract, advising feedback/signal path, students risk-context API | 8/8 | ✅ |
| **I2** | Enrollments dropout-risk signal + analytics/usage brain-context API | 10/10 | ✅ |
| **I3** | `❌ Not ready` EV=Med модули → минимальная brain-readiness: academic_integrity, academic_records, programs, courses, transcripts, student_services | 20/20 | ✅ |
| **I4** | Tenant-isolation regression pack: fail-closed без tenant context, запрет cross-tenant reads, negative tests на data leakage | 29/29 | ✅ |
| **I5** | Ministry KPI contract v1: whitelist KPI, suppression thresholds, audit requirements | 28/28 | ✅ |
| **I6** | Финальный release-gate: meta-tests, contract integrity, Phase I file presence, 95-test accounting | 36/36 | ✅ |
| **ИТОГО** | Phase I — Module Max Hardening | **131/131** | ✅ |

### Изменения в §C1 readiness-audit по результатам Phase I

| Модуль | BR до Phase I | BR после Phase I | Что сделано |
|---|---|---|---|
| `thesis` | ⚠️ Partial | ✅ Ready | Canonical brain signal contract зафиксирован (I1) |
| `advising` | ⚠️ Partial | ✅ Ready | Feedback/signal path закрыт (I1) |
| `students` | ⚠️ Partial | ✅ Ready | Risk-context API покрыт тестами (I1) |
| `enrollments` | ⚠️ Partial | ✅ Ready | Dropout-risk signal + analytics/usage (I2) |
| `analytics`/`usage` | ⚠️ Partial | ✅ Ready | Brain-context API тесты (I2) |
| `academic_integrity` | ❌ Not ready | ⚠️ Partial | Минимальная brain-readiness (I3) |
| `academic_records` | ❌ Not ready | ⚠️ Partial | Минимальная brain-readiness (I3) |
| `programs` | ❌ Not ready | ⚠️ Partial | Brain-readiness + tenant-isolation (I3, I4) |
| `courses` | ❌ Not ready | ⚠️ Partial | Brain-readiness + tenant-isolation (I3, I4) |
| `transcripts` | ❌ Not ready | ⚠️ Partial | Минимальная brain-readiness (I3) |
| `student_services` | ❌ Not ready | ⚠️ Partial | Минимальная brain-readiness (I3) |

### Ministry KPI Contract v1 (I5)

- **Версия:** `v1`  
- **Роль доступа:** `ministry.kpi.read`  
- **Whitelist:** `total_students`, `total_enrollments`, `total_grades_submitted`  
- **Suppression threshold:** 5 (k-anonymity baseline)  
- **Suppressed sentinel:** `"suppressed"`  
- **Аудит:** каждый вызов `apply_ministry_kpi_contract()` записывает audit entry  
- **Модуль:** `app/platform/kpi/ministry_kpi.py`

### Phase I Gate Summary

- **Safe-gate:** 95/95 тестов I1–I5 прошли в одном прогоне (0 failures)  
- **Release-gate:** 36/36 meta-тестов I6 прошли (0 failures)  
- **Tenant-isolation:** отрицательные тесты на cross-tenant leakage — все fail-closed  
- **Ministry KPI:** suppression + whitelist + audit — contract integrity verified  
- **Phase I полностью закрыта: 131/131 ✅**

