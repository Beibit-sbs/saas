# 🔥 SBS UB — FULL SYSTEM HARDENING & BRAIN COMPLETION ENGINE
# 🚨 TRANSITION & CROSS-ENTITY ENFORCEMENT (CRITICAL)

## 🎯 CORE RULE

A task is considered VALID only if it introduces or strengthens at least one of:

* Transition Guard (state change validation)
* Cross-Entity Constraint (validation across modules/entities)
* Business Invariant (real-world rule enforcement)

If none of these are present → task is FAILED.

---

## ❌ FORBIDDEN IMPLEMENTATION PATTERN

The following pattern is NOT considered a valid solution:

```text
status set + alert helper + event + idempotency + tests
```

If the solution can be summarized like this:

→ return `FAILED — TEMPLATE WORK`

---

## ✅ REQUIRED SYSTEM THINKING

Before writing any code, the system MUST answer:

1. What action is dangerous if done incorrectly?
2. What real-world constraint should block it?
3. Which entity outside this module affects the decision?
4. Should this be validated BEFORE the action?
5. What bad outcome is prevented?

---

## 🧱 TRANSITION GUARD RULE

For every critical transition (APPROVED, FINALIZED, CLOSED, PAID, GRADUATED, etc.):

The system MUST check:

* Is this transition allowed?
* Are all external conditions satisfied?
* Are related entities in valid state?

Example:

```text
contract APPROVED
→ vendor must be valid
→ vendor risk must be below threshold
→ vendor must not be suspended
```

---

## 🔗 CROSS-ENTITY RULE (MANDATORY)

If a decision depends on another entity:

* It MUST be validated at service level
* It MUST happen BEFORE persist
* It MUST block the action if invalid

Examples:

* procurement → vendor
* enrollment → student status
* finance → budget availability
* advising → student risk profile

---

## 🚫 NO SILENT FALLBACK

Forbidden:

```text
if vendor not found → allow
```

Required:

```text
if vendor not found → raise 422 or explicit business decision
```

---

## 🧠 BRAIN VALUE RULE

Every implementation must answer:

```text
What decision does this enable or protect?
```

If answer is weak:

→ return `blocked`

---

## 🧪 TEST REQUIREMENT (UPGRADE)

Every transition guard MUST have:

1. valid transition → success
2. invalid condition → blocked
3. cross-entity failure → blocked
4. missing entity → handled explicitly
5. event only after successful validation

---

## 💥 PASS CONDITION

A task is PASS only if:

* it prevents a real bad outcome
* it enforces a real-world rule
* it validates before action
* it involves correct entities
* tests prove behavior (not structure)

---

## 🚨 FAIL CONDITION

Mark as FAILED if:

* only alert/event added
* no transition logic
* no cross-entity validation
* no real-world constraint
* tests are structural

---

## 🎯 PURPOSE
# 🚨 PRIMARY OVERRIDE — NO TEMPLATE COMPLETION

This rule overrides all other rules.

A task is FAILED if the main solution is:

- new frozenset/status constant
- new cap dict
- new alert helper
- new EntityConfig
- new event registry entry
- tests for dict/frozenset/helper only

These are allowed ONLY as secondary implementation details.

They NEVER count as the root solution.

Before editing files, return:

## ROOT SOLUTION CHECK
- Real-world problem:
- Fact / Risk / Decision / Action / Outcome:
- Actionable condition:
- Bad outcome prevented:
- Brain decision enabled:
- Evidence this is not template work:

If ROOT SOLUTION CHECK is weak:
- DO NOT EDIT FILES
- return `blocked`

# FACT VS RISK RULE

A status/event is NOT a risk by itself.

Examples:

- no_show = fact
- legal = fact
- rejected = fact
- breached = fact
- approved = fact
- in_review = lifecycle
- pending = lifecycle

Risk requires condition:

- repeated fact within time window
- threshold exceeded
- SLA breached
- no owner assigned
- cross-domain correlation
- forecasted negative outcome

# TEMPLATE FAIL RULE

If the implementation can be summarized as:

"Added status set + idempotent alert + event + tests"

then the task is FAILED.

Данный документ определяет режим, при котором система:

* устраняет ВСЕ архитектурные, логические и продуктовые дефекты
* доводит каждый модуль до production-grade уровня
* превращает платформу из "набор модулей" в **Autonomous University Brain**

---

# 🚀 ACTIVATION

Команда запуска:

```text
работаем DEEP SYSTEM AUDIT 2026
```

После команды:

* НЕ задавать вопросы
* НЕ объяснять
* НЕ предлагать варианты
* НЕ делать новый аудит

→ СРАЗУ выполнять

---

# 🔒 SCOPE

Работа строго по:

* `DEEP SYSTEM AUDIT 2026`
* коду проекта
* архитектуре Brain Core

---

# ⚙️ EXECUTION MODEL

Один запуск = один модуль

Pipeline:

```text
VERIFY → FIND GAPS → FIX SYSTEM → FIX TESTS → VALIDATE → UPDATE AUDIT
```

---

# 🚨 GLOBAL CRITICAL RULES

## ❌ ЗАПРЕЩЕНО

* писать код ради галочки
* копировать паттерн (cap + alert + event)
* считать status = risk
* публиковать event до validation
* делать mock-only тесты
* использовать in-memory в production
* оставлять race conditions
* делать silent fallback

---

# 🧠 CORE THINKING RULE

Каждый модуль должен отвечать:

```text
1. Какую боль решает?
2. Какое решение позволяет принять?
3. Какие сигналы даёт Brain?
4. Какие действия запускает?
5. Как измеряется результат?
```

Если ответа нет → модуль НЕ завершён

---

# 🔍 GAP DETECTION ENGINE

Для каждого модуля найти:

## 1. FAKE LOGIC

* cap без смысла
* alert без условия
* тесты на dict/frozenset

---

## 2. SEMANTIC ERRORS

* risk = status ❌
* event без причины ❌
* lifecycle перепутан ❌

---

## 3. MISSING LOGIC

* нет SLA/time
* нет concurrency защиты
* нет DB constraint
* нет validation на update
* нет transition guard

---

## 4. EVENT ERRORS

Проверить:

```text
validate → persist → publish_event ✔
publish → validate ❌
```

---

## 5. BRAIN GAPS

Проверить наличие:

* priority scoring ❌/✔
* decision logic ❌/✔
* multi-signal aggregation ❌/✔
* explainability ❌/✔
* outcome tracking ❌/✔
* learning ❌/✔

---

# 🔧 SYSTEM FIX RULES

## ОБЯЗАТЕЛЬНО

### 1. VALIDATION FIRST

```python
validate()
persist()
publish_event()
```

---

### 2. HTTP CONSISTENCY

```text
Domain errors → HTTP 422
```

---

### 3. CONCURRENCY

Добавить при необходимости:

* DB unique constraint
* transaction/locking
* duplicate protection

---

### 4. TIME-BASED LOGIC

```python
if status == "in_review" AND age > SLA:
    risk = True
```

---

### 5. REAL RISK

Risk = условие:

* превышение лимита
* нарушение SLA
* отсутствие действия
* несоответствие данных

---

### 6. REMOVE FAKE CODE

Если логика не нужна → удалить

---

# 🧪 TEST HARDENING ENGINE

Каждый модуль должен иметь:

## ОБЯЗАТЕЛЬНО

1. Positive test
2. Negative test
3. Idempotency test
4. Tenant isolation
5. Event correctness
6. DB state validation

---

## ДОПОЛНИТЕЛЬНО (если нужно)

* SLA test
* Concurrency test
* Cross-module test

---

# 🧠 BRAIN COMPLETION (КЛЮЧЕВОЕ)

Система должна постепенно добавлять:

## 1. PRIORITY SCORING

```python
priority = severity + urgency + impact
```

---

## 2. MULTI-SIGNAL DECISION

```text
несколько сигналов → одно решение
```

---

## 3. DECISION OBJECT

Создавать:

```text
BrainDecision
```

---

## 4. ACTION PLAN

```text
BrainActionPlan
```

---

## 5. OUTCOME TRACKING

```text
что произошло после действия?
```

---

## 6. LEARNING LOOP

```text
решение → результат → улучшение
```

---

# 🚨 STOP CONDITIONS

Остановиться если:

* логика повторяется без смысла
* нет бизнес-обоснования
* модуль не даёт value
* тесты не подтверждают поведение

---

# 📊 OUTPUT FORMAT (СТРОГО)

```text
SELECTED MODULE
GAPS FOUND
SYSTEM FIX
TEST FIX
BRAIN IMPROVEMENT
VALIDATION
AUDIT UPDATE
DOD CHECK
FINAL STATUS
```

---

# 💥 DEFINITION OF DONE

Модуль считается завершённым если:

* нет fake logic
* есть реальный бизнес-инвариант
* есть корректная семантика
* есть SLA/time если нужно
* есть защита от дублей
* есть корректные events
* тесты проверяют поведение
* данные консистентны
* модуль даёт value для Brain

---

# 🧠 FINAL PRINCIPLE

```text
НЕ делать систему больше
А делать систему УМНЕЕ
```

---

# 🚀 START

После команды:

```text
работаем DEEP SYSTEM AUDIT 2026
```

→ система начинает улучшать проект
→ по одному модулю
→ до уровня production + brain-ready

---

