# 07 — Полный аудит Brain‑модулей

[← 06 Runtime Shells](06_RUNTIME_SHELLS.md) · [Индекс](README.md) · Далее: [08 Workflows →](08_WORKFLOWS.md)

Отдельные файлы: [brains/README.md](brains/README.md). Источники: `app/modules/brain_core/*`, доменные `*_runtime`, `*_signal_registry`, `digital_twin`.

---

## 8.1 Brain Core — назначение

**Brain Core** (`app/modules/brain_core/`) — централизованный слой принятия решений над доменными модулями. Не хранит доменные master‑данные и не заменяет workflow/RBAC/event‑bus. Отвечает за: чтение сигналов, сбор межтенантно‑изолированного контекста, классификацию ситуации, приоритизацию, генерацию решения, проверку политики, оркестрацию действий, объяснение, учёт исхода, обучение.

**Ключевой принцип:** человеко‑контролируемый (`HUMAN_APPROVAL_REQUIRED`), никаких автономных исполнений.

---

## 8.2 Полный жизненный цикл решения

```text
Signal intake → Context build → Classify → Reason → Policy guard
   → Action plan → Dispatch → Outcome → Learning
```

| Стадия | Файл | Что делает |
|--------|------|-----------|
| Signal intake | `signal_listener.py` | Подписка на 70+ типов доменных событий |
| Context build | `context_builder.py` | Tenant‑scoped снапшоты из 7 источников (academic, student_success, faculty, finance, operations, platform, scheduling) |
| Classify | `classifiers/` | 4 классификатора: risk, compliance, operational, optimization |
| Reason | `reasoning/` | Composite risk scorer, anomaly detector, predictor, rules engine, explanation engine (12 компонентов) |
| Policy guard | `policy/` | TenantPolicyResolver, ApprovalPolicy, DecisionPolicyGuard (критические решения → одобрение человека) |
| Action plan | `actions/planner.py` | ActionPlanner строит исполнимые элементы |
| Dispatch | `actions/dispatcher.py` | Маршрутизация в workflow/notification/module‑handler (до 3 ретраев) |
| Outcome | `outcome_listener.py` | Приём исходов кейсов (completed/resolved/closed) |
| Learning | `learning/` | PolicyTuningEngine, DecisionQualityTracker, SignalQualityTracker |

**Batch:** `early_warning_sweep.py` — ночной composite‑risk sweep по всем студентам тенанта; студенты со score > 55 → в Brain (идемпотентно, fail‑closed, изоляция по тенанту).

---

## 8.3 Реестр сигналов и решений (`registry.py`)

- **SignalRegistry: 66** сценариев сигналов, домены: Academic Risk (17), Faculty Risk (4), Financial Risk (9), Procurement Risk (6), Compliance Risk (12), Platform Risk (3), Research Risk (4), Campus Operations (19), Operational Risk (11), Supply/Finance Ops (4).
- **DecisionRegistry: 36** сценариев решений. Примеры:

| Решение | Тип | Действия |
|---------|-----|----------|
| `student_risk` | risk | create_intervention_case, create_attendance_recovery_plan, notify_advisor/faculty |
| `thesis_delay` | preventive | create_intervention_case, create_supervision_task, notify_advisor |
| `faculty_overload` | optimization | create_workload_review_task, notify_faculty |
| `payment_recovery` | risk | create_collections_case, notify_finance |
| `budget_overrun_prevention` | risk | create_intervention_case, notify_finance |
| `procurement_approval_automation` | procurement | create_procurement_approval_case, notify_procurement_team |
| `accreditation_remediation` | compliance | create_accreditation_remediation_workflow, notify_compliance |
| `academic_integrity_violation` | integrity | integrity_review, request_manual_review, escalate_to_committee |
| `exam_proctoring_violation` | integrity | create_integrity_review, escalate_to_committee, collect_evidence |
| `section_conflict` / `enrollment_capacity_risk` | operational/risk | create_*_task, notify_scheduling/enrollment_office |
| `room_allocation_recommendation` | operational | review recommendations, request_human_review, notify_scheduling |
| `campus_security` / `visitor_management_ops` / `security_operations_ops` | security | notify_security_team, create_incident_task, suspend_card/escalate |
| `inventory_low_stock` / `finance_operations_health` | supply/finance | create_procurement_request, reorder_review, health_review_task |

Полный перечень — [brains/brain-core.md](brains/brain-core.md).

---

## 8.4 Доменные Brain‑вертикали (6)

| Brain | Модуль | Префикс | Под‑роутеры |
|-------|--------|---------|-------------|
| **Student Success** | `student_success_runtime` | `/api/v1/student-success` | 8 (registry, retention, academic_risk, attendance_risk, intervention, advisor, signals, dashboard) |
| **Academic Operations** | `academic_operations_runtime` | `/api/v1/academic-operations` | 9 (registry, assessment, attendance, curriculum, internship, timetable, teaching_load, dashboard, signals) |
| **Reporting (Ministry)** | `reporting_runtime` | `/api/v1/reporting` | 8 сервисов (accreditation, compliance, ministry, nobd, ranking, regulatory, dashboard, registry) |
| **Executive Governance** | `executive_governance` | `/api/v1/executive-governance` | control tower, decision registry, risk heatmap, KPI, strategic initiative, rector dashboard |
| **Research Science** | `research_science` | `/api/admin/research-science` | shell + research API (researchers, scientometrics, risk) |
| **Quality Accreditation** | `quality_accreditation` | `/api/admin/quality-accreditation` | 8 (evidence, registry, audit_findings, corrective_action, dashboard, improvement_plan, readiness, self_assessment) |

Детали по каждому — [brains/](brains/).

---

## 8.5 Сигнальные реестры (L2‑конверты, 5)

Контракты уровня L2 (версия A‑027.6), UCE‑ID присвоены, **все запрещают автономное исполнение** (`HUMAN_APPROVAL_REQUIRED=True`, `BRAIN_EXECUTION_ALLOWED=False`):

| Реестр | UCE‑ID | Домен |
|--------|--------|-------|
| `student_risk_signal_registry` | UCE‑049 | Student Success |
| `curriculum_gap_signal_registry` | UCE‑132 | Curriculum Governance |
| `finance_anomaly_signal_registry` | UCE‑050 | Finance |
| `procurement_risk_signal_registry` | UCE‑129 | Procurement/Contracts/Assets |
| `academic_quality_signal_registry` | UCE‑051 | Academic Affairs |

---

## 8.6 Digital Twin

`app/modules/digital_twin/` — предиктивная симуляция операций и capacity what‑if (A‑056).
- **Измерения:** студенты, персонал, аудитории/здания, расписания, бюджеты, инвентарь, нагрузка сервисов, события безопасности.
- **Источники (reuse):** 5 сигнальных реестров + capacity‑модули (enrollments, scheduling, room_booking, asset_inventory, dormitory_management, dining).
- **API:** `GET /tenants/{id}/state`, `GET /tenants/{id}/safety-boundaries`.
- **Запрещённые действия (fail‑closed):** autonomous_budget_commitment, autonomous_academic/disciplinary_decision, hidden_scoring, any_execution_without_human_approval, supplier_order_without_human_approval.
- **Гарантия:** только чтение; при сбое БД честно возвращает None; не фабрикует числа симуляций.

Детали — [brains/digital-twin.md](brains/digital-twin.md).

---

## 8.7 Человеческий контроль (human gating)

- **ApprovalPolicy** (`policy/approval_policy.py`): `ApprovalRoute(required, role, reason)`; при `require_approval_for_critical` и priority=critical → требуется одобрение (роль из tenant‑policy).
- **Human‑Approved Timetable Workflow:** DRAFT → PENDING_HUMAN_REVIEW → HUMAN_APPROVED → (ручное применение); запрещены AUTO_APPLY/AUTO_OPTIMIZE/AUTONOMOUS_ROLLBACK/AUTO_RESCHEDULE.
- **Safe Task Drafting Agent** (UCE‑146) и **Safe Evidence Summary Agent** (UCE‑145): `RUNTIME_EXECUTION_ALLOWED=False`; требуют governance_policy_reference, tenant_scope_context, human_review_record.
- **Timetable Approval Queue:** детерминированные маршруты одобрения по приоритету/сложности.

---

## 8.8 AI‑слой (в связке с Brain)

- **AI Gateway** (`ai_gateway`): реестр моделей, адаптеры провайдеров (OpenAI, Gemini, Anthropic, custom/Ollama), единый `POST /api/ai/chat`, usage‑логирование, audit‑hooks, частично RLS.
- **Reasoning ai_adapter / ExplanationEngine:** генерация объяснений решений; `llm_bridge` упоминается в service (граница интеграции LLM — частично неясна, см. оговорки).
- **Сопутствующие AI‑модули:** `faculty_copilot`, `knowledge_retrieval` (RAG), `prompt_management`, `model_evaluation`, `ai_copilot_ops`, `ai_cost_governance`, `ai_routing_control`, `ai_guardrails`, `ai_plagiarism`, `ai_admissions_scoring`, `student_ai_tutor`.

---

## 8.9 Проблемы (аудит)

- Граница интеграции LLM (`llm_bridge`) не полностью прослежена в статике.
- `model_eval_hooks.py` (learning/) — полный scope интеграции не задокументирован в коде.
- Алгоритм `compute_composite_risk_score()` в статике не раскрыт до конца.
- Дубли runtime‑пакетов (см. §7.6 в [06_RUNTIME_SHELLS.md](06_RUNTIME_SHELLS.md)).
