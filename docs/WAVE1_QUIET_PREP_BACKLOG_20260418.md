# Wave 1 Quiet-Prep Backlog (до day7)

Дата: 2026-04-18
Режим: quiet-prep only (без full-delivery и без финального closure до day7)
Ограничения: One Active Delivery, No Jump Rule, fail-closed governance

## Цель

Подготовить исполнимые заготовки для пост-day7 запуска Wave 1 без расползания scope.

## В работе после day7: 9 задач

### HARDENING (4)

1. Billing router + models (#32)
- Owner: Platform Backend Team
- Prep-результат: API contract draft, model map, migration outline, тест-матрица.
- Artifact: `docs/WAVE1_PREP_32_BILLING_ROUTER_MODELS_BRIEF_20260418.md`
- Ready-критерий: документы и skeleton tests готовы, без релизного включения.
- **Статус: ✅ PREP-API-PARITY-EXPANDED** (scaffold + flag-gated wiring done)
- **Статус: ✅ PREP-API-PARITY-EXPANDED** (scaffold + flag-gated wiring done)

2. Event bus + outbox patterns (#47)
- Owner: Platform Architecture Team
- Artifact: `docs/WAVE1_PREP_47_EVENT_BUS_BRIEF_20260418.md`
- Ready-критерий: описаны события и гарантии доставки, есть skeleton integration tests.
- **Статус: ✅ PREP-BRIEF-READY** (as-is audit + 6 gaps + skeleton tests + priority plan)
- Artifact: `docs/WAVE1_PREP_47_EVENT_BUS_BRIEF_20260418.md`
- Ready-критерий: описаны события и гарантии доставки, есть skeleton integration tests.
- **Статус: ✅ PREP-BRIEF-READY** (as-is audit + 6 gaps + skeleton tests + priority plan)

3.Artifact: `docs/WAVE1_PREP_53_ADMIN_COPILOT_BRIEF_20260418.md`
- Ready-критерий: готовы шаблоны и ограничения, без прод-активации.
- **Статус: ✅ PREP-BRIEF-READY** (hybrid architecture + 5 gaps + role prompts + skeleton tests)
- Owner: AI Platform Team
- Prep-результат: prompt policy draft, role-context matrix, audit hooks checklist.
- Artifact: `docs/WAVE1_PREP_53_ADMIN_COPILOT_BRIEF_20260418.md`
- Ready-критерий: готовы шаблоны и ограничения, без прод-активации.
- Artifact: `docs/WAVE1_PREP_56_AI_GUARDRAILS_BRIEF_20260418.md`
- Ready-критерий: описаны блокирующие правила и трассировка решений.
- **Статус: ✅ PREP-BRIEF-READY** (module structure + 8 components + injection/content/PII detectors + skeleton tests)e prompts + skeleton tests)

4. AI guardrails standalone (#56)
- Owner: AI Safety Team
- Prep-результат: guardrail ruleset draft, deny/allow policy, fallback behavior spec.
- Artifact: `docs/WAVE1_PREP_56_AI_GUARDRAILS_BRIEF_20260418.md`
- Ready-критерий: описаны блокирующие правила и трассировка решений.
- Artifact: `docs/WAVE1_PREP_22_FACULTY_WORKLOAD_BRIEF_20260418.md`
- Ready-критерий: есть контракт и тест-кейсы на расчет нагрузки.
- **Статус: ✅ PREP-BRIEF-READY** (model extension + workload service + business rules + API contract)s + injection/content/PII detectors + skeleton tests)

### PLANNED (5)

5. Faculty workload planning (#22)
- Artifact: `docs/WAVE1_PREP_33_DELINQUENCY_BRIEF_20260418.md`
- Ready-критерий: определены этапы взыскания и контрольные события.
- **Статус: ✅ PREP-BRIEF-READY** (dunning lifecycle + status machine + data model + compliance notes)
- Prep-результат: domain schema draft, workload calc rules, UI wireframe notes.
- Artifact: `docs/WAVE1_PREP_22_FACULTY_WORKLOAD_BRIEF_20260418.md`
- Ready-критерий: есть контракт и тест-кейсы на расчет нагрузки.
- **Статус: ✅ PREP-BRIEF-READY** (model extension + workload service + business rules + API contract)
Artifact: `docs/WAVE1_PREP_54_AI_ORCHESTRATION_BRIEF_20260418.md`
- Ready-критерий: зафиксированы правила маршрутизации и failover.
- **Статус: ✅ PREP-BRIEF-READY** (routing engine + fallback chain + circuit breaker + A/B + API contract)
6. Delinquency / collections (#33)
- Owner: Finance Domain Team
- Prep-результат: dunning lifecycle draft, status machine, compliance notes.
- Artifact: `docs/WAVE1_PREP_33_DELINQUENCY_BRIEF_20260418.md`
- Ready-критерий: определены этапы взыскания и контро
- **Статус: ✅ MERGED INTO #56** (covered by WAVE1_PREP_56_AI_GUARDRAILS_BRIEF_20260418.md)льные события.
- **Статус: ✅ PREP-BRIEF-READY** (dunning lifecycle + status machine + data model + compliance notes)

7. AI orchestration full routing (#54)
- Owner: AI Platform Team
- Artifact: `docs/WAVE1_PREP_60_AI_COST_GOVERNANCE_BRIEF_20260418.md`
- Ready-критерий: defined KPI/SLO and cost anomaly criteria.
- **Статус: ✅ PREP-BRIEF-READY** (token pricing + cost aggregation + budgets + anomaly detection + SLO)strategy draft.
- Artifact: `docs/WAVE1_PREP_54_AI_ORCHESTRATION_BRIEF_20260418.md`
- Ready-критерий: зафиксированы правила маршрутизации и failover.
- **Статус: ✅ PREP-BRIEF-READY** (routing engine + fallback chain + circuit breaker + A/B + API contract)
**PREP-BRIEFS-COMPLETE** (9/9 tasks have design briefs)
8. Guardrails standalone promotion (#56 -> EXISTS)
- Owner: AI Safety Team
- Prep-результат: migration path from embedded to standalone guardrails.
- Ready-критерий: план перехода без downtime и drift.
- **Статус: ✅ MERGED INTO #56** (covered by WAVE1_PREP_56_AI_GUARDRAILS_BRIEF_20260418.md)

9. AI cost governance (#60)
- Owner: FinOps + AI Platform
- Prep-результат: metering dimensions, quota/cost thresholds, alert policy draft.
- Artifact: `docs/WAVE1_PREP_60_AI_COST_GOVERNANCE_BRIEF_20260418.md`
- Ready-критерий: defined KPI/SLO and cost anomaly criteria.
- **Статус: ✅ PREP-BRIEF-READY** (token pricing + cost aggregation + budgets + anomaly detection + SLO)
~~Зафиксировать владельцев по 9 задачам.~~ ✅ Done
2. ~~Для каждой задачи создать 1-page design brief и skeleton test list.~~ ✅ Done (9/9)
3. После day7 перевести максимум 1 задачу в active full-delivery stream.
4. **Priority order для full-delivery:** #47 Event Bus → #56 AI Guardrails → #53 Admin Copilot → #22 Faculty Workload → #33 Delinquency → #54 AI Orchestration → #60 AI Cost Governance
5. Ревью briefs перед стартом каждой задачи — проверить что design решения не противоречат текущему коду
- Current phase: **PREP-BRIEFS-COMPLETE** (9/9 tasks have design briefs)
- Day7 dependency: BLOCKED until official day7 gate/sign-off
- Compliance dependency: C-TRACK=PASS (local DR evidence accepted)

## Правила исполнения

1. Не делать полноценную разработку новых модулей до day7 sign-off.
2. Делать только design/docs/contracts/skeleton-tests.
3. Любой prep-артефакт должен иметь owner и ready-критерий.
4. Любая попытка full-delivery до снятия блокеров считается policy violation.

## Следующий практический шаг

1. ~~Зафиксировать владельцев по 9 задачам.~~ ✅ Done
2. ~~Для каждой задачи создать 1-page design brief и skeleton test list.~~ ✅ Done (9/9)
3. После day7 перевести максимум 1 задачу в active full-delivery stream.
4. **Priority order для full-delivery:** #47 Event Bus → #56 AI Guardrails → #53 Admin Copilot → #22 Faculty Workload → #33 Delinquency → #54 AI Orchestration → #60 AI Cost Governance
5. Ревью briefs перед стартом каждой задачи — проверить что design решения не противоречат текущему коду.
