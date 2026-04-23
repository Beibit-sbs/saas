# SBS UB — Master Plan

**Полное название:** SBS University Brain
**Модель:** Multi-tenant Autonomous University OS
**Статус документа:** Strategic Source of Truth (стратегия/рамка, без оперативных чекбоксов)
**Назначение:** единый управляющий документ проекта, чтобы не терять фокус, не расползаться по задачам и не уходить в поверхностную разработку.

**Оперативная синхронизация статусов:**
1. Текущий execution-status и фазовые чекбоксы ведутся в `SBS_UB.md`.
2. Детальная модульная инвентаризация и PASS/FAIL snapshot ведутся в `docs/AUDIT_SBS_2026.md`.
3. При расхождении между стратегической формулировкой и operational статусом приоритет у `SBS_UB.md` + `docs/AUDIT_SBS_2026.md`.

---

# 1. Главная цель проекта

Построить не просто университетскую информационную систему и не просто набор модулей, а **мозг университета** — единую multi-tenant платформу, которая:

1. покрывает **все контуры университета**, а не только академический блок;
2. является **цифровым двойником университета**;
3. понимает, что происходит в университете на основе данных;
4. выявляет отклонения, риски, дефициты и неэффективность;
5. прогнозирует последствия;
6. предлагает оптимальные действия;
7. в разрешённых контурах **сама запускает действия** через workflow/automation;
8. измеряет результат своих решений;
9. учится на результате и становится лучше;
10. работает как **единая платформа для множества университетов (multi-tenant)**.

## Короткая формула

```text
Data → Understanding → Forecast → Decision → Action → Feedback → Learning
```

---

# 2. Что мы строим на самом деле

Мы строим:

> **Autonomous Multi-Tenant University Brain**

Это не LMS, не ERP, не CRM и не просто SaaS.
Это единая интеллектуальная операционная платформа университета.

## Система должна уметь:

* видеть весь университет как единое целое;
* хранить полную связанную картину состояния;
* принимать решения на основе данных;
* запускать процессы без ручного хаоса;
* сохранять explainability и контроль;
* работать для каждого tenant отдельно, но на общей платформе.

---

# 3. Жёсткие принципы проекта

## 3.1. Не делаем систему ради количества модулей

Нельзя считать систему сильной только потому, что в ней много разделов.

### Правильный критерий:

Каждый модуль обязан отвечать на вопрос:

> **Какую реальную боль он снимает и какое решение система сможет принять благодаря ему?**

Если модуль не снимает боль, не создаёт данные для решений и не участвует в сквозных процессах — он считается слабым или лишним.

---

## 3.2. Модуль не считается завершённым, если он изолирован

Любой модуль обязан быть частью общей цепочки:

```text
UI → API → Data → Events → Brain → Workflow → Action → Feedback → UI
```

Если модуль существует изолированно, он не является частью мозга.

---

## 3.3. Система = не сумма модулей

Система считается зрелой только тогда, когда:

* все контуры связаны;
* данные не дублируются бессистемно;
* решения принимаются на общей картине;
* действия запускаются через контролируемый workflow;
* результат замыкается обратно в аналитику и обучение.

---

## 3.4. Multi-tenant — обязательный фундамент

Платформа строится не под один университет.

### Базовые правила:

1. Каждый университет = отдельный tenant.
2. Данные tenant-ов строго разделены.
3. Решения и действия выполняются в tenant-контуре.
4. Общая логика платформы переиспользуется между tenant-ами.
5. Shared intelligence допускается только в обезличенном и безопасном виде.
6. Любая логика, которая ломает tenant neutrality, считается архитектурным дефектом.

---

# 4. Текущее состояние проекта (что уже есть)

По текущему аудиту у платформы уже есть сильнейший фундамент:

## 4.1. Уже подтверждено

* Enterprise-grade backend contour
* Full regression green
* Docker-only discipline
* Multi-tenant foundation
* Event bus + outbox
* Workflow engine
* RBAC + ABAC
* Observability + alerting
* AI gateway
* Guardrails
* Routing / policy contours
* Reliability gates
* F1/F2/F3 стратегический продуктовый контур

## 4.2. Вывод по текущему состоянию

Сейчас система уже является:

> **Enterprise University OS foundation**

Но пока ещё не является полноценным **University Brain**, потому что отсутствует единый слой принятия решений поверх всех доменов.

---

# 5. Главный разрыв между текущей системой и целевым состоянием

## Сейчас уже есть:

* доменные модули;
* данные;
* события;
* workflow;
* AI-инструменты;
* automation foundations.

## Но пока ещё нет в завершённом виде:

> **Единого Brain Core / Decision Engine**

То есть отсутствует центральный слой, который:

1. читает сигналы из всех доменов;
2. собирает полный контекст;
3. понимает состояние университета;
4. выявляет проблемы и возможности;
5. принимает приоритизированные решения;
6. передаёт действия в workflow/automation;
7. контролирует результат;
8. обучается на outcome.

---

# 6. Новая рамка: не просто 60 модулей, а 5 слоёв мозга

С этого момента проект описывается не просто модульной картой, а **моделью из 5 слоёв**.

## Layer 1 — Digital Twin Layer

Это полный цифровой двойник университета.

Внутри должны быть представлены:

* студенты;
* преподаватели;
* учебные планы;
* предметы;
* расписание;
* аудитории;
* оценки;
* дипломный и диссертационный контур;
* аккредитация;
* финансы;
* бюджеты;
* договоры;
* закупки;
* склады;
* имущество;
* общежития;
* сервисные заявки;
* кадры;
* исследования;
* публикации;
* лаборатории;
* безопасность;
* документы;
* инфраструктура;
* эксплуатация кампуса;
* расходники;
* оборудование;
* все иные операционные сущности университета.

### Смысл слоя

Этот слой отвечает на вопрос:

> **Что происходит в университете прямо сейчас?**

---

## Layer 2 — Event Nervous System

Это нервная система платформы.

Все изменения состояния должны превращаться в события.

### Примеры событий:

* attendance_risk_detected
* grade_risk_detected
* faculty_overload_detected
* payment_overdue_detected
* procurement_threshold_reached
* consumable_stock_low
* thesis_status_changed
* accreditation_remediation_required
* room_equipment_fault_reported
* cleaning_service_missed
* library_item_overdue
* dorm_issue_created

### Смысл слоя

Этот слой отвечает на вопрос:

> **Какие сигналы и изменения система должна уметь замечать автоматически?**

---

## Layer 3 — Brain Core / Decision Engine

Это центральный интеллектуальный слой.

### Он обязан:

1. собирать контекст из разных модулей;
2. определять тип ситуации;
3. вычислять риск/важность/срочность;
4. прогнозировать последствия;
5. выбирать оптимальный сценарий реакции;
6. учитывать policy / permissions / tenant rules;
7. формировать решение;
8. передавать решение в execution layer.

### Это ключевой новый слой проекта.

Без него система остаётся сильной платформой, но не становится мозгом.

---

## Layer 4 — Execution / Orchestration Layer

Слой исполнения решений.

### Внутри:

* workflows
* task routing
* approvals
* escalations
* notifications
* automation rules
* orchestration
* auto-assignment
* job scheduling
* operational task closure

### Смысл слоя

Этот слой отвечает на вопрос:

> **Как решение превращается в действие?**

---

## Layer 5 — Feedback / Learning Layer

Система не должна просто запускать процессы — она должна учиться.

### Внутри:

* outcome tracking
* intervention effectiveness
* action effectiveness
* policy tuning
* model evaluation
* reasoning quality review
* false positive / false negative analysis
* continuous improvement loops

### Смысл слоя

Этот слой отвечает на вопрос:

> **Что сработало, что не сработало и как мозг станет лучше?**

---

# 7. Новая целевая архитектура проекта

```text
Domain Modules
    ↓
Digital Twin
    ↓
Events / Signals
    ↓
Brain Core / Decision Engine
    ↓
Workflow / Automation / Tasking
    ↓
Actions in the University
    ↓
Outcome Tracking
    ↓
Learning / Optimization
```

---

# 8. Что делать с текущими 60 модулями

## Важное решение

Текущие 60 модулей **не выбрасываются**.
Они сохраняются как:

> **baseline domain map**

Но теперь каждый модуль должен быть переоценён по новым правилам.

## Каждый модуль должен получить статус по 3 осям:

### 1. Domain Coverage

Покрывает ли он реальную область университета?

### 2. Brain Readiness

Даёт ли он данные, события, контекст и действия для мозга?

### 3. Execution Value

Позволяет ли он системе реально что-то улучшить или запустить?

---

# 9. Новый подход к модулю

Любой модуль теперь оценивается так.

## 9.1. Module Pain Statement

Какую боль модуль снимает?

## 9.2. Module Decisions Statement

Какие решения система сможет принимать благодаря этому модулю?

## 9.3. Module Signals Statement

Какие события и сигналы генерируются?

## 9.4. Module Actions Statement

Какие действия запускаются?

## 9.5. Module Learning Statement

Как система будет измерять эффект?

---

# 10. Новый Master Capability Map

Новая карта строится не только по модулям, но и по capability-блокам.

## 10.1. Domain Capabilities

Полный охват всех контуров университета.

### A. Academic Core

* admissions
* enrollments
* programs
* courses
* sections
* timetable
* attendance
* grades
* transcripts
* degree progress
* thesis
* academic integrity
* accreditation
* exam governance
* syllabus governance

### B. Student Success & Student Life

* risk scoring
* intervention playbooks
* advising
* case management
* student services
* scholarship
* financial aid
* housing
* alumni
* employability
* communications
* counseling / wellbeing
* disciplinary support
* accessibility support

### C. Faculty & Teaching Operations

* faculty profile
* contracts
* workload planning
* office hours
* teaching quality analytics
* performance KPIs
* teaching improvement plans
* proctoring
* exam supervision
* classroom operations

### D. Administration & Finance

* billing
* delinquency / collections
* budget planning
* procurement
* contracts/legal
* asset management
* inventory
* facilities/work orders
* vendor management
* payroll / HR integration
* expense controls

### E. Campus Operations

* cleaning operations
* consumables tracking
* room readiness
* security incidents
* access control integration
* maintenance
* transport
* dining / cafeteria
* campus service SLA
* energy / utilities
* environmental monitoring

### F. Research & Innovation

* grants pipeline
* research projects
* publications
* labs
* ethics / IRB
* IP / commercialization
* equipment booking
* experiment tracking

### G. Platform Foundation

* identity
* tenants
* RBAC / ABAC
* audit
* workflows
* events
* observability
* DR / backup
* integration layer
* policy engine
* contract governance

### H. AI & Brain Layer

* decision engine
* context engine
* reasoning engine
* orchestration engine
* recommendation engine
* optimization engine
* forecasting engine
* simulation engine
* anomaly detection
* explanation engine
* learning engine
* prompt/version management
* RAG / knowledge retrieval
* evaluation / A/B
* human approval policy

---

# 11. Что считать "идеальной системой"

Идеальной считается не система с максимальным количеством страниц, а система, где:

1. каждая ключевая боль университета покрыта;
2. все контуры интегрированы;
3. модуль даёт measurable value;
4. система умеет сама замечать проблему;
5. система умеет объяснить проблему;
6. система умеет предложить или запустить действие;
7. система умеет контролировать результат;
8. система сохраняет explainability;
9. система управляется через tenant-aware policies;
10. система не требует ручного хаоса для повседневного управления университетом.

---

# 12. Определение Brain-Ready модуля

Модуль считается **Brain-Ready**, только если выполнено всё ниже:

1. Есть domain model.
2. Есть API.
3. Есть UI.
4. Есть tenant-aware security.
5. Есть события.
6. Есть контекст для AI/decision layer.
7. Есть action hooks / workflow integration.
8. Есть metrics / observability.
9. Есть outcome tracking.
10. Есть e2e сценарий.

Если этого нет — модуль может быть functional, но не brain-ready.

---

# 13. Что считаем мусором и не делаем

Нельзя делать:

* модуль ради красивого списка;
* UI без backend;
* backend без use-case;
* данные без решения;
* локальные костыли под одного tenant-а;
* AI как просто чат без принятия решений;
* дубли master-data;
* «галочные» страницы без автоматизации и ценности.

---

# 14. Главные top-level боли, которые система обязана закрывать

## 14.1. Academic & student risks

* dropout
* low engagement
* grade decline
* progression failure
* thesis delay
* accreditation evidence gaps

## 14.2. Faculty risks

* overload
* burnout
* teaching quality decline
* exam chaos
* governance inconsistency

## 14.3. Financial risks

* overdue tuition
* uncontrolled spending
* procurement inefficiency
* contract risk
* budget drift

## 14.4. Operational risks

* maintenance gaps
* room/equipment downtime
* supply shortages
* poor service SLA
* consumable outages
* cleaning failures

## 14.5. Strategic risks

* leadership blind spots
* delayed decisions
* bad forecasting
* poor intervention ROI
* no cross-domain visibility

---

# 15. Обязательные способности мозга университета

Система должна уметь:

1. видеть текущее состояние;
2. замечать отклонения;
3. определять причину;
4. оценивать серьёзность;
5. прогнозировать последствия;
6. выбирать лучшее действие;
7. запускать действие;
8. проверять исполнение;
9. измерять эффект;
10. улучшать будущие решения.

---

# 16. Что делаем дальше — новый порядок работ

С этого момента нельзя идти хаотично.

## Правильный порядок:

### Этап 1 — Stabilize Foundation

Дозакрыть всё, что уже начато и обязательно для мозга.

### Этап 2 — Design Brain Core

Спроектировать единый decision layer.

### Этап 3 — Make Modules Brain-Compatible

Привести доменные модули к стандарту brain-ready.

### Этап 4 — Launch Cross-Domain Scenarios

Собрать реальные автономные сценарии через несколько доменов.

### Этап 5 — Expand Coverage Intelligently

Расширять охват университета только после того, как новые контуры смогут давать данные, решения и действия.

---

# 17. NOW / NEXT / LATER / NOT NOW

## NOW

### Главный активный блок:

**Brain Core Design**

Нужно спроектировать:

* decision engine
* context builder
* policy-aware reasoning
* action dispatcher
* explanation layer
* feedback ingestion

### Параллельно:

Провести re-mapping текущих модулей по принципу brain-ready / not brain-ready.

---

## NEXT

Запустить первые 5 сквозных brain-сценариев:

1. Student risk → intervention → faculty action → outcome
2. Thesis risk → advising → faculty supervision → closure
3. Delinquency risk → collections workflow → escalation → resolution
4. Procurement / consumable shortage → auto request → approval → fulfillment
5. Faculty overload → workload rebalance → quality risk mitigation

---

## LATER

После стабилизации Brain Core:

* inventory intelligence
* facilities intelligence
* campus operations intelligence
* research intelligence
* vendor performance intelligence
* advanced simulation / forecasting
* full knowledge layer / RAG

---

## NOT NOW

Нельзя сейчас:

* бесконтрольно плодить новые модули;
* расширять список только ради охвата;
* делать AI-чат без системного decision layer;
* дробить работу без master roadmap;
* терять tenant neutrality.

---

# 18. Brain Core — цель следующего большого блока

Новый крупный контур проекта:

## Название

**brain_core**

## Назначение

Центральный слой принятия решений для SBS UB.

## Brain Core обязан включать:

### 18.1. Context Engine

Собирает контекст из нескольких доменов.

### 18.2. Signal Interpreter

Понимает тип события и его важность.

### 18.3. Decision Engine

Формирует решение и рекомендуемое действие.

### 18.4. Policy Engine Integration

Проверяет, что решение допустимо для данного tenant-а.

### 18.5. Action Dispatcher

Передаёт задачи в workflows/jobs/notifications.

### 18.6. Explanation Engine

Формирует объяснение: почему принято именно это решение.

### 18.7. Outcome Feedback Loop

Читает результат исполнения и улучшает future decisions.

---

# 19. Первый список обязательных brain-driven use cases

## 19.1. Student Retention Brain

* замечает риск отчисления;
* строит контекст;
* выбирает playbook;
* создаёт кейс;
* назначает action item;
* проверяет outcome.

## 19.2. Thesis Completion Brain

* отслеживает статус thesis;
* выявляет задержки;
* открывает advising/control workflow;
* контролирует progress.

## 19.3. Faculty Load Brain

* анализирует нагрузку;
* выявляет overload/underload;
* предлагает перераспределение;
* контролирует качество.

## 19.4. Finance Recovery Brain

* выявляет задолженность;
* прогнозирует риск неоплаты;
* запускает collections workflow;
* контролирует recovery.

## 19.5. Operations Supply Brain

* отслеживает расход;
* прогнозирует дефицит;
* инициирует пополнение/закупку;
* эскалирует при критическом пороге.

---

# 20. Как теперь оценивать каждый новый модуль

Для любого нового модуля должен быть заполнен шаблон:

## Module Definition Template

### 1. Module Name

### 2. Pain Solved

Какую боль снимает?

### 3. Domain Scope

Какие сущности покрывает?

### 4. Key Signals

Какие сигналы генерирует?

### 5. Brain Context Value

Какой контекст даёт мозгу?

### 6. Decisions Enabled

Какие решения система сможет принимать?

### 7. Actions Triggered

Какие действия запускаются?

### 8. Outcome Metrics

Как измеряем эффект?

### 9. Upstream / Downstream Integrations

С чем связан?

### 10. Brain-Ready DoD

Что должно быть завершено?

---

# 21. Новый DoD уровня SBS UB

Любая новая поставка считается завершённой только если:

1. Работает в Docker-only.
2. Имеет backend + frontend.
3. Имеет tenant-aware security.
4. Использует canonical entities.
5. Генерирует или потребляет события.
6. Подключена к Brain Core.
7. Может запускать действие через workflow.
8. Имеет observability.
9. Имеет outcome metrics.
10. Имеет e2e happy-path и fail-path.
11. Имеет explainability.
12. Не нарушает tenant neutrality.

---

# 22. Что станет единым источником истины

С этого момента этот документ является:

> **главным управляющим документом развития SBS UB**

Он должен использоваться перед любым новым решением по проекту.

Перед стартом любой новой задачи нужно проверить:

1. Это усиливает Brain Core или нет?
2. Это закрывает реальную боль или нет?
3. Это tenant-aware или нет?
4. Это brain-ready или нет?
5. Это помогает автономности системы или нет?

Если ответов нет — задача не запускается.

---

# 23. Следующий практический шаг

Следующий документ, который должен быть создан после этого master plan:

## `SBS_UB_BRAIN_CORE_ARCHITECTURE.md`

В нём нужно зафиксировать:

1. внутреннюю архитектуру brain_core;
2. сущности решений;
3. типы сигналов;
4. decision lifecycle;
5. policy integration;
6. explainability model;
7. action dispatch model;
8. feedback/learning loop.

---

# 24. Финальная формулировка цели

Мы строим:

> **не просто систему университета, а multi-tenant мозг университетов, который на основе данных сам понимает, прогнозирует, принимает решения, запускает действия и улучшает управление университетом по всем контурам.**

---

# 25. Фиксация фокуса

## Что мы НЕ делаем

* не делаем MVP-поверхность;
* не делаем фичи ради галочки;
* не расползаемся по хаотичным задачам;
* не теряем multi-tenant архитектуру;
* не делаем AI как косметическую надстройку.

## Что мы ДЕЛАЕМ

* строим полную, глубокую, связанную, brain-driven University OS;
* доводим каждый контур до реальной ценности;
* делаем систему эталонной;
* сохраняем один фокус и один master roadmap.
