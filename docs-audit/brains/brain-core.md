# Brain: Brain Core (движок принятия решений)

[← Каталог Brain](README.md) · [Обзор Brain](../07_BRAIN_MODULES.md)

Модуль: `backend/app/modules/brain_core/` · API prefix `/api/admin/brain` (guard `admin.dashboard.read`)

## Назначение
Централизованный слой принятия решений над доменными модулями. Читает сигналы, собирает межтенантно‑изолированный контекст, классифицирует ситуацию, приоритизирует, генерирует решение, проверяет политику, оркестрирует действия, объясняет, учитывает исход, обучается. **Не заменяет** workflow/RBAC/event‑bus и не хранит доменные master‑данные.

## Функции (10 архитектурных возможностей)
Signal intake · Context aggregation · Situation classification · Priority scoring · Decision generation · Policy validation · Action orchestration · Explainability · Outcome ingestion · Learning support.

## Входные данные
Доменные события (70+ типов) через `signal_listener.py`; ночной `early_warning_sweep` (композитный риск по студентам, score>55).

## Обработка (жизненный цикл)
| Стадия | Файл | Компоненты |
|--------|------|-----------|
| Signal intake | `signal_listener.py`, `signal_normalizer.py` | нормализация сигналов |
| Context build | `context_builder.py`, `context_sources/` | 7 источников (academic, student_success, faculty, finance, operations, platform, scheduling) |
| Classify | `classifiers/` | risk, compliance, operational, optimization |
| Reason | `reasoning/` | composite_risk_scorer, anomaly_detector, predictor, rules_engine, explanation, ai_adapter, scenario_selector, scoring, optimizer, knowledge_retriever (12) |
| Policy guard | `policy/` | TenantPolicyResolver, ApprovalPolicy, DecisionPolicyGuard |
| Action plan | `actions/planner.py` | ActionPlanner |
| Dispatch | `actions/dispatcher.py`, `action_bridge.py` | workflow/notification/module‑handler (≤3 ретрая) |
| Outcome | `outcome_listener.py` | приём исходов кейсов |
| Learning | `learning/` | PolicyTuningEngine, DecisionQualityTracker, SignalQualityTracker, model_eval_hooks |

## Выходные данные
Решения (`DecisionRegistry`, 36), действия (workflow‑задачи, уведомления, jobs), объяснения (`/explanations/{id}`), рекомендации, executive‑KPI.

## Реестры
- **SignalRegistry: 66** сигналов (Academic 17, Faculty 4, Financial 9, Procurement 6, Compliance 12, Platform 3, Research 4, Campus 19, Operational 11, Supply/Finance 4).
- **DecisionRegistry: 36** решений (см. [../07_BRAIN_MODULES.md](../07_BRAIN_MODULES.md) §8.3).

## API
`GET /health`, `/tenants/{id}/signals`, `/tenants/{id}/decisions`, `/decisions/{id}`, `/explanations/{id}`, `/dispatch/snapshot`, `/policy/{tenant}` (GET/PUT), `/recommendations/{tenant}`, `/executive-kpi/{tenant}`; `POST /simulate/{student-risk,what-if,thesis-delay,faculty-overload,budget-variance,vendor-sla-degraded,contract-risk-high,supply-low}`, `/predict`, `/anomalies`. Изоляция тенанта: `_assert_tenant_match()` (A‑009).

## Данные / БД
`brain_core_signal_definitions`, `brain_core_signals`, decisions/explanations (миграции `fa12bc34de56`, `fb23cd45ef67`, `lh01ij23kl45` signal dedup). Все tenant‑scoped.

## Связанные Runtime Shell
Все доменные shell'ы (Student Success, Academic Operations, Quality Accreditation, Research, Reporting, Executive Governance) — окна соответствующих brain‑вертикалей.

## Human gating
ApprovalPolicy (`policy/approval_policy.py`): критические решения → одобрение человека (роль из tenant‑policy). Никаких автономных исполнений.

## Проблемы
Граница LLM (`llm_bridge`) не полностью прослежена; `model_eval_hooks` scope не задокументирован; алгоритм composite‑risk не раскрыт до конца в статике.
