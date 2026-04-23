# SBS UB — Brain Core Architecture

**Документ:** Архитектура ядра мозга платформы SBS UB
**Статус:** Architecture Baseline (ограничения/структура, без оперативных чекбоксов)
**Назначение:** зафиксировать точную архитектуру `brain_core`, чтобы развитие University Brain шло по единому инженерному плану, без хаоса, без дрейфа и без поверхностных решений.

**Оперативная синхронизация статусов:**
1. Ход реализации по фазам и факт закрытия задач фиксируются в `SBS_UB.md`.
2. Аудит модулей и тестовые метрики фиксируются в `docs/AUDIT_SBS_2026.md`.
3. Этот документ задает архитектурные границы; при конфликте реализации с архитектурой приоритет у архитектурных ограничений, а не у ad-hoc статусов.

---

# 1. Назначение Brain Core

## Brain Core — это

> **центральный слой принятия решений платформы SBS UB**

Он существует поверх доменных модулей и не заменяет их.

### Доменные модули отвечают за:

* хранение предметных данных;
* исполнение локальной бизнес-логики;
* интерфейсы пользователя;
* domain CRUD / workflows / status transitions.

### Brain Core отвечает за:

* чтение сигналов из разных контуров;
* сбор междоменного контекста;
* понимание ситуации;
* определение приоритета;
* формирование решения;
* запуск действия через execution layer;
* объяснение решения;
* учёт результата;
* улучшение качества будущих решений.

---

# 2. Роль Brain Core в общей архитектуре SBS UB

```text
Domain Modules
    ↓
Events / Signals
    ↓
Brain Core
    ↓
Decisions
    ↓
Workflow / Automation / Notifications / Jobs
    ↓
Execution in University Operations
    ↓
Outcome / Feedback
    ↓
Learning / Policy Refinement
```

## Главный принцип

Brain Core не должен превращаться в хаотичный "божественный сервис", который содержит всё подряд.

Он должен быть:

* централизованным по decision logic;
* модульным по внутренним компонентам;
* policy-aware;
* explainable;
* tenant-safe;
* event-driven;
* outcome-oriented.

---

# 3. Архитектурные цели Brain Core

Brain Core обязан обеспечить 10 ключевых возможностей:

1. **Signal intake** — принимать сигналы от доменов.
2. **Context aggregation** — собирать полный междоменный контекст.
3. **Situation classification** — понимать, что именно происходит.
4. **Priority scoring** — вычислять важность, срочность и критичность.
5. **Decision generation** — формировать управленческое решение.
6. **Policy validation** — проверять допустимость решения.
7. **Action orchestration** — передавать действия в execution layer.
8. **Explainability** — объяснять, почему принято решение.
9. **Outcome ingestion** — понимать, что произошло после исполнения.
10. **Learning support** — создавать основу для обучения и улучшения.

---

# 4. Brain Core boundaries

## Что входит в Brain Core

* signal intake
* context building
* reasoning
* decision lifecycle
* policy checks for decisions
* action planning
* explanation generation
* outcome capture
* learning hooks

## Что НЕ входит в Brain Core

* прямое хранение domain master-data
* raw CRUD предметных сущностей
* UI logic конкретных модулей
* замена workflow engine
* замена RBAC/ABAC
* замена event bus
* замена observability stack

## Правило

Brain Core использует инфраструктуру платформы, но не дублирует её.

---

# 5. Место в кодовой базе

Рекомендуемая директория:

```text
backend/app/modules/brain_core/
```

Рекомендуемая внутренняя структура:

```text
brain_core/
├── __init__.py
├── router.py
├── schemas.py
├── models.py
├── service.py
├── constants.py
├── registry.py
├── signal_listener.py
├── signal_normalizer.py
├── context_builder.py
├── context_sources/
│   ├── __init__.py
│   ├── academic.py
│   ├── student_success.py
│   ├── faculty.py
│   ├── finance.py
│   ├── operations.py
│   ├── research.py
│   └── platform.py
├── classifiers/
│   ├── __init__.py
│   ├── risk_classifier.py
│   ├── operational_classifier.py
│   ├── optimization_classifier.py
│   └── compliance_classifier.py
├── reasoning/
│   ├── __init__.py
│   ├── engine.py
│   ├── rules_engine.py
│   ├── scoring.py
│   ├── scenario_selector.py
│   └── explanation.py
├── policy/
│   ├── __init__.py
│   ├── decision_policy.py
│   ├── approval_policy.py
│   └── tenant_policy.py
├── actions/
│   ├── __init__.py
│   ├── planner.py
│   ├── dispatcher.py
│   ├── workflow_actions.py
│   ├── notification_actions.py
│   └── job_actions.py
├── feedback/
│   ├── __init__.py
│   ├── ingestor.py
│   ├── outcome_tracker.py
│   └── effectiveness.py
├── learning/
│   ├── __init__.py
│   ├── signal_quality.py
│   ├── decision_quality.py
│   ├── policy_tuning.py
│   └── model_eval_hooks.py
└── tests/
```

---

# 6. Внутренние компоненты Brain Core

## 6.1. Signal Listener

### Назначение

Принимать события из event bus / outbox pipeline и передавать их в brain_core pipeline.

### Обязанности

* подписка на канонические события;
* приём событий только в tenant-scoped режиме;
* базовая валидация envelope;
* передача в normalizer / classifier.

### Не должен делать

* принимать решения;
* обращаться напрямую к UI;
* исполнять workflow.

---

## 6.2. Signal Normalizer

### Назначение

Приводить события разных доменов к единому формату мозга.

### Обязанности

* нормализация поля `event_type`;
* унификация correlation data;
* приведение payload к canonical brain signal format;
* контроль наличия обязательных идентификаторов.

---

## 6.3. Context Builder

### Назначение

Собирать единый контекст по ситуации из нескольких доменов.

### Пример

Если пришёл сигнал `academic.attendance_risk.detected`, context builder должен иметь возможность дополнительно подтянуть:

* student profile
* attendance trend
* grades trend
* interventions history
* advising history
* faculty assignment
* financial delinquency status
* housing / wellbeing context (если релевантно)

### Принцип

Context Builder — это не ad hoc запросы, а структурированный сбор междоменного контекста.

---

## 6.4. Situation Classifier

### Назначение

Определить тип ситуации.

### Базовые классы ситуаций

* academic_risk
* faculty_risk
* financial_risk
* operational_risk
* compliance_risk
* optimization_opportunity
* service_degradation
* preventive_opportunity

### Результат

Классификатор должен вернуть:

* situation_type
* severity
* urgency
* recommended reasoning path

---

## 6.5. Reasoning Engine

### Назначение

Центральный интеллектуальный компонент, который определяет, **что делать**.

### Внутренние подкомпоненты

* rules engine
* scoring engine
* scenario selector
* recommendation composer
* explanation builder

### На первом этапе

Reasoning engine может быть hybrid:

* deterministic rules
* weighted scoring
* policy checks
* optional AI augmentation

### На зрелом этапе

* policy-aware AI reasoning
* simulation and comparison of multiple actions
* dynamic action planning

---

## 6.6. Decision Engine

### Назначение

Фиксировать итоговое решение как formal object.

### Обязанности

* создать decision record;
* назначить priority;
* назначить required approvals;
* сформировать action plan;
* сохранить explainability snapshot.

---

## 6.7. Policy Guard Layer

### Назначение

Проверить, допустимо ли решение в данном tenant-контуре.

### Проверяет

* tenant-specific policy
* autonomy limits
* approval requirement
* data sensitivity
* regulatory constraints
* role / permission constraints

### Пример

Система может:

* автоматически создать задачу уборщице;
* автоматически открыть кейс сопровождения;
* автоматически отправить уведомление;

Но не может без policy allow:

* отчислить студента;
* изменить критическую оценку;
* списать бюджет;
* подписать договор.

---

## 6.8. Action Planner

### Назначение

Развернуть решение в исполнимый набор действий.

### Результат

Decision → one or more action items:

* create workflow task
* create case
* send notification
* schedule follow-up
* request approval
* create procurement request
* create work order
* assign faculty action

---

## 6.9. Action Dispatcher

### Назначение

Передать действия в существующий execution contour платформы.

### Интеграции

* workflows
* jobs
* notifications
* automation rules
* integrations

### Принцип

Brain Core не исполняет физически действия сам. Он dispatches actions в существующую платформенную инфраструктуру.

---

## 6.10. Explanation Engine

### Назначение

Сформировать объяснение решения для человека и для аудита.

### Объяснение должно отвечать:

* какой сигнал пришёл;
* какой контекст был собран;
* почему система решила именно так;
* какие альтернативы были отвергнуты;
* нужен ли human approval;
* какие риски предотвращаются.

### Explainability обязательна

Без explanation Brain Core не считается production-grade.

---

## 6.11. Feedback Ingestor

### Назначение

Получать outcome после исполнения действий.

### Примеры outcome

* intervention completed
* payment recovered
* thesis milestone updated
* consumable replenished
* work order closed
* overload reduced

### Используется для

* оценки качества решения;
* измерения эффективности;
* последующего обучения.

---

## 6.12. Learning Support Layer

### Назначение

Создать основу для повышения качества мозга.

### На первом этапе

* outcome metrics
* decision quality tracking
* false-positive / false-negative logging
* scenario effectiveness tracking

### На следующем этапе

* policy tuning
* model evaluation
* decision optimization
* reinforcement loops

---

# 7. Canonical Brain Signal Model

Все сигналы, поступающие в Brain Core, должны приводиться к единому формату.

## 7.1. BrainSignal envelope

```json
{
  "signal_id": "uuid",
  "tenant_id": "uuid-or-int",
  "correlation_id": "uuid",
  "event_type": "academic.attendance_risk.detected",
  "signal_class": "academic_risk",
  "source_module": "scheduling",
  "source_entity_type": "section_attendance",
  "source_entity_id": "...",
  "occurred_at": "ISO-8601",
  "subject": {
    "student_id": "...",
    "faculty_id": null,
    "course_id": "...",
    "section_id": "..."
  },
  "payload": {},
  "metadata": {}
}
```

---

# 8. Canonical Decision Model

Каждое решение мозга фиксируется как formal decision object.

## 8.1. BrainDecision

```json
{
  "decision_id": "uuid",
  "tenant_id": "uuid-or-int",
  "correlation_id": "uuid",
  "decision_type": "risk|optimization|preventive|operational|compliance",
  "situation_type": "academic_risk",
  "priority": "low|medium|high|critical",
  "status": "draft|approved|dispatched|completed|cancelled|expired",
  "confidence_score": 0.0,
  "severity_score": 0.0,
  "urgency_score": 0.0,
  "recommended_actions": [],
  "requires_approval": true,
  "explanation": {
    "summary": "...",
    "factors": [],
    "policy_notes": [],
    "expected_outcome": "..."
  },
  "created_at": "ISO-8601",
  "created_by": "brain_core",
  "metadata": {}
}
```

---

# 9. Canonical Action Plan Model

## 9.1. BrainActionPlan

```json
{
  "plan_id": "uuid",
  "decision_id": "uuid",
  "tenant_id": "uuid-or-int",
  "actions": [
    {
      "action_type": "workflow_task|notification|job|case_create|procurement_request|work_order",
      "target_module": "workflows",
      "payload": {},
      "requires_approval": false,
      "deadline_at": "ISO-8601"
    }
  ]
}
```

---

# 10. Decision lifecycle

Brain Core должен использовать единый decision lifecycle.

## 10.1. Lifecycle states

1. `detected` — сигнал принят.
2. `context_built` — контекст собран.
3. `classified` — ситуация классифицирована.
4. `reasoned` — логика решения построена.
5. `policy_checked` — policy validation выполнен.
6. `decision_created` — formal decision object создан.
7. `approval_pending` — если нужен human approval.
8. `approved` — решение разрешено.
9. `dispatched` — action plan отправлен в execution layer.
10. `executing` — действия исполняются.
11. `completed` — решение отработано.
12. `outcome_recorded` — outcome сохранён.
13. `learned` — effect / learning metrics зафиксированы.

---

# 11. Decision types

Brain Core на первом этапе должен поддерживать пять типов решений.

## 11.1. Risk Decision

Когда нужно предотвратить ущерб.

Примеры:

* student dropout risk
* faculty overload risk
* overdue payment risk
* accreditation risk

## 11.2. Operational Decision

Когда нужно выполнить операционное действие.

Примеры:

* создать work order
* инициировать пополнение расходников
* назначить задачу персоналу

## 11.3. Preventive Decision

Когда ущерба ещё нет, но система видит приближение.

Примеры:

* consumables shortage soon
* thesis delay likely
* budget overrun likely

## 11.4. Optimization Decision

Когда можно улучшить эффективность.

Примеры:

* workload rebalance
* room utilization optimization
* procurement optimization

## 11.5. Compliance Decision

Когда нужно запустить процесс соблюдения требований.

Примеры:

* evidence request
* remediation follow-up
* policy violation handling

---

# 12. Brain policies

Brain Core не может принимать автономные действия без policy guard.

## 12.1. Уровни автономии

### Level 0 — Observe only

Система только фиксирует и показывает.

### Level 1 — Recommend only

Система рекомендует, но не запускает действие.

### Level 2 — Semi-autonomous

Система может создавать задачи / кейсы / уведомления.

### Level 3 — Controlled autonomy

Система может запускать approved workflows в заранее разрешённых сценариях.

### Level 4 — Restricted autonomous execution

Возможно только для строго ограниченных low-risk operational use cases.

---

# 13. Context Builder design

Context Builder должен быть построен как набор источников контекста.

## 13.1. Базовые context domains

* academic context
* student success context
* faculty context
* finance context
* operations context
* compliance context
* research context
* platform context

## 13.2. Правило сборки

Контекст не должен тянуть всё подряд.

Он собирается по:

* signal class
* subject type
* policy scope
* tenant configuration

### Пример

`academic.attendance_risk.detected`:

* обязательный context: student, attendance, grades, interventions
* optional context: faculty, finance, housing
* не подтягивать research/lab context без причины

---

# 14. Первые canonical signals

На первом этапе обязателен следующий набор.

## Academic / Student

* academic.attendance_risk.detected
* academic.grade_risk.detected
* thesis.status_changed
* accreditation.status_changed

## Faculty

* faculty.workload_overload.detected
* faculty.quality_drop.detected

## Finance

* finance.payment_overdue.detected
* finance.budget_variance.threshold_reached

## Operations

* operations.consumable_stock.low
* operations.facility_issue.reported

## Platform / Reliability

* platform.workflow.failed
* platform.integration.degraded

---

# 15. Первые canonical decisions

## Decision 1 — Student Retention Response

Signal:

* attendance risk / grade risk

Actions:

* open intervention case
* assign advisor task
* notify relevant roles

## Decision 2 — Thesis Delay Response

Signal:

* thesis stagnant / delayed review

Actions:

* open supervision task
* create advising follow-up
* escalate if SLA breached

## Decision 3 — Faculty Overload Response

Signal:

* workload threshold exceeded

Actions:

* create review workflow
* propose rebalance
* notify department head

## Decision 4 — Billing Recovery Response

Signal:

* payment overdue risk

Actions:

* trigger collections playbook
* notify student / finance role
* escalate on repeated non-response

## Decision 5 — Supply Replenishment Response

Signal:

* consumable stock low

Actions:

* create replenishment task
* if below threshold → initiate procurement request
* escalate if critical service risk

---

# 16. Минимальная интеграция с текущими модулями

## Brain Core v1 должен интегрироваться минимум с:

### Domain sources

* scheduling / attendance
* grades
* thesis
* accreditation
* interventions
* advising
* faculty
* billing / finance
* procurement / contracts
* future inventory / operations

### Execution targets

* workflows
* jobs
* notifications
* audit
* observability

---

# 17. API surface Brain Core

На первом этапе нужен ограниченный, но правильный API.

## 17.1. Admin / Ops endpoints

* `GET /api/admin/brain/decisions`
* `GET /api/admin/brain/decisions/{decision_id}`
* `GET /api/admin/brain/signals`
* `GET /api/admin/brain/signals/{signal_id}`
* `POST /api/admin/brain/reprocess/{signal_id}`
* `POST /api/admin/brain/decisions/{decision_id}/approve`
* `POST /api/admin/brain/decisions/{decision_id}/cancel`
* `GET /api/admin/brain/outcomes`
* `GET /api/admin/brain/explanations/{decision_id}`
* `GET /api/admin/brain/policies`
* `PATCH /api/admin/brain/policies/{policy_id}`

## 17.2. Internal endpoints

* internal signal intake hook
* internal action dispatch callback
* internal feedback ingestion hook

---

# 18. Data model suggestions

## 18.1. New entities

Рекомендуемые таблицы:

* `brain_signals`
* `brain_signal_context_snapshots`
* `brain_decisions`
* `brain_action_plans`
* `brain_action_executions`
* `brain_outcomes`
* `brain_policy_profiles`
* `brain_explanations`
* `brain_learning_observations`

## 18.2. Важные поля

Обязательно во всех сущностях:

* tenant_id
* correlation_id
* created_at
* status
* source_module
* subject identifiers
* policy snapshot
* audit linkage

---

# 19. Multi-tenant requirements for Brain Core

Brain Core обязан быть tenant-safe по умолчанию.

## Требования

1. Все сигналы всегда tenant-scoped.
2. Контекст строится только внутри tenant-контуров.
3. Решения принимаются в пределах tenant policy profile.
4. Cross-tenant raw data mixing запрещён.
5. Shared intelligence допускается только на агрегированном / анонимизированном уровне.
6. Policy overrides могут различаться между tenant-ами.
7. Нельзя hardcode поведение под одного клиента.

## 19.1. Tenant-local execution contract (ENFORCED)

Для operational Brain Core применяется строгое tenant-local исполнение с fail-closed моделью.

### Access and Context

1. Любой запрос к Brain API обязан содержать валидный tenant context (из auth/session claims).
2. При отсутствии или неконсистентности tenant context — fail-closed (HTTP 403/401).
3. Tenant context не может передаваться через пользовательские headers без валидации (защита от spoofing).

### Data Isolation

1. Все чтения/записи в Brain Core выполняются с обязательным tenant filter на уровне ORM/Query layer.
2. Любые cross-tenant joins, вычисления и indirect inference запрещены.
3. Кэш (Redis и др.) обязан быть tenant-scoped (ключи включают tenant_id).

### Service-to-Service

1. Все internal service-to-service вызовы обязаны передавать tenant context.
2. Tenant context обязан валидироваться на стороне получателя.
3. Internal API без tenant context запрещены (кроме явно whitelisted system endpoints).

### Enforcement

1. Глобальный middleware обязан извлекать tenant_id.
2. Глобальный middleware обязан валидировать tenant_id.
3. Глобальный middleware обязан инжектить tenant_id в request context.
4. Любой доступ к данным без tenant filter считается security violation.

## 19.2. Ministry KPI Layer (cross-tenant, aggregate-only, GOVERNED)

Ministry KPI Layer реализуется как отдельный read-model слой, не связанный напрямую с operational data path.

### Scope

1. Назначение: межтенантные KPI, тренды, агрегированные индикаторы.
2. Ministry KPI Layer не участвует в operational decision execution.

### Data Restrictions

1. Разрешены только агрегированные данные.
2. Разрешены только анонимизированные значения.
3. Запрещены student-level данные.
4. Запрещены case-level payload.
5. Запрещены любые PII.
6. Запрещены любые идентификаторы, позволяющие восстановить субъект.

### Access Control

1. Доступ только через отдельные роли: ministry.kpi.read.
2. Роли ministry не имеют tenant-admin прав.
3. Роли ministry не имеют доступа к operational API.

### Storage and Architecture

1. KPI Layer использует отдельный storage/read-model.
2. KPI Layer использует ETL/event-driven aggregation.
3. Прямой доступ к tenant operational DB запрещен.

### Audit

1. Каждый запрос к KPI Layer логируется (user_id, role, timestamp, query scope).
2. Каждый запрос к KPI Layer подлежит аудиту.
3. Для всех KPI-запросов поддерживается audit trail.

## 19.3. Data minimization and privacy guardrails (MANDATORY)

### KPI Whitelist

1. Все метрики публикуются только через утвержденный whitelist.
2. Любая новая метрика требует явного утверждения (policy-level change).

### Suppression and Anti-Reidentification

1. Вводится suppression threshold: если выборка меньше N, данные скрываются или обобщаются.
2. Запрещены комбинации фильтров, приводящие к deanonymization.

### Aggregation Rules

1. Все ответы KPI должны быть только aggregation-only.
2. Все ответы KPI должны быть без прямых идентификаторов.
3. Все ответы KPI должны быть без trace-back к individual entity.

### Data Separation

1. KPI read-model физически и логически отделен от operational data.
2. Прямой bypass tenant-level security через KPI слой запрещен.

### Continuous Validation

1. Обязательны automated tests на cross-tenant leakage.
2. Обязательны регулярные security audits.
3. Любое нарушение isolation считается критическим инцидентом.

---

# 20. Explainability requirements

Каждое значимое решение мозга должно объясняться.

## Минимум explanation payload

* signal summary
* detected risk / opportunity
* major factors
* confidence level
* selected action path
* why approval required or not
* expected outcome

## Use cases

Объяснение должно быть пригодно для:

* ректора / руководства
* администратора
* операционного менеджера
* аудита
* compliance review

---

# 21. Observability for Brain Core

Brain Core должен быть полностью наблюдаем.

## Метрики

* signals_received_total
* decisions_created_total
* decisions_by_type_total
* decisions_by_priority_total
* decisions_requiring_approval_total
* action_dispatch_success_total
* action_dispatch_failure_total
* outcome_recorded_total
* false_positive_total
* false_negative_total
* reasoning_latency_ms
* context_build_latency_ms

## Tracing

Весь decision flow должен быть связан по:

* tenant_id
* correlation_id
* signal_id
* decision_id

## Logs

Логи обязаны быть:

* structured
* safe
* tenant-aware
* correlation-linked

---

# 22. Security requirements

Brain Core — один из самых чувствительных контуров системы.

## Обязательные требования

* RBAC/ABAC on admin brain endpoints
* fail-closed on missing tenant context
* no unsafe raw prompts in logs
* no cross-tenant context leakage
* approval policy enforced
* audit record for every decision override / approval / cancellation

---

# 23. Brain Core DoD

Brain Core phase считается завершённой только если:

1. Есть canonical signal model.
2. Есть canonical decision model.
3. Есть context builder.
4. Есть situation classifier.
5. Есть reasoning engine.
6. Есть policy guard.
7. Есть action planner/dispatcher.
8. Есть explanation engine.
9. Есть feedback ingestion.
10. Есть observability.
11. Есть admin/API surface.
12. Есть минимум 2 working end-to-end brain scenarios.
13. Есть docker-only validation.
14. Есть tests: unit + integration + fail-path.
15. Есть tenant isolation proof.

---

# 24. Phased implementation plan

## Phase B1 — Design Baseline

Нужно зафиксировать:

* schemas
* entities
* lifecycle
* signal classes
* decision classes
* policy model

## Phase B2 — Core Skeleton

Собрать:

* router
* schemas
* models
* signal_listener
* context_builder
* reasoning skeleton
* decision persistence

## Phase B3 — First Two Scenarios

Подключить:

1. Student risk scenario
2. Thesis delay scenario

## Phase B4 — Policy + Explainability

Добавить:

* approval policies
* explanation payloads
* admin review surface

## Phase B5 — Feedback Loop

Добавить:

* outcomes
* effectiveness tracking
* decision quality observations

## Phase B6 — Expand to Finance + Operations

Подключить:

* billing / collections
* procurement / consumables
* facilities / work orders

---

# 25. Первые тестовые сценарии

## Happy-path

1. attendance risk signal received
2. context built
3. student retention decision created
4. workflow case created
5. advisor task dispatched
6. outcome recorded

## Fail-path

1. signal received without tenant context
2. processing blocked fail-closed
3. audit entry written
4. no unsafe action dispatched

## Approval-path

1. decision requires approval
2. action dispatch blocked until approval
3. approval granted
4. action plan executed

---

# 26. Что нельзя делать при реализации Brain Core

Нельзя:

* тащить domain CRUD внутрь brain_core;
* писать giant service на тысячи строк без внутренних слоёв;
* делать всё через if/else без signal classes;
* запускать actions без policy checks;
* делать opaque black-box AI without explanation;
* смешивать tenant data;
* терять correlation_id;
* начинать с UI before core lifecycle.

---

# 27. Следующий документ после этого

После данного документа должен быть создан практический implementation-документ:

## `SBS_UB_BRAIN_CORE_IMPLEMENTATION_PLAN.md`

Он должен содержать:

* file-by-file plan
* migration plan
* endpoint plan
* first schema definitions
* first event contracts
* test plan
* rollout order

---

# 28. Финальная фиксация

Brain Core — это тот слой, который превращает SBS UB из сильной university platform в настоящий **University Brain**.

Финальная формула:

> **Domain modules дают картину мира. Brain Core даёт понимание и решения. Execution layer даёт действие. Feedback layer даёт развитие.**
