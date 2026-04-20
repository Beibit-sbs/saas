# Wave 1 Prep Design Brief: #53 Admin Copilot (Operations)

Дата: 2026-04-18
Task ID: #53
Статус: PREP-OPEN
Owner: AI Platform Team
Reviewers: Backend Lead, Product

## 1) Контекст и цель

Admin Copilot уже работает в production как детерминированный retrieval + rule engine. Он не использует AI Gateway для генерации ответов — всё keyword matching + SQL retrieval + 7 правил рекомендаций. Цель hardening: подключить LLM для natural language understanding, добавить role-specific system prompts, и сохранить deterministic fallback.

## 2) Текущее состояние (as-is)

### Что EXISTS:

| Компонент | Файлы | LOC | Статус |
|-----------|-------|-----|--------|
| AI Copilot Service | `platform/ai/service.py` | ~300 | ✅ Keyword classifier → retrieval → response |
| Retrieval Layer | `platform/ai/retrieval.py` | ~200 | ✅ Per-query-type SQL retrieval |
| Query Types | `platform/ai/query_types.py` | ~50 | ✅ 10 типов (KPI, risk, health, context, skills) |
| Rule Catalog | `platform/ai/recommendations/rule_catalog.py` | ~150 | ✅ 7 детерминированных правил |
| Recommendation Service | `platform/ai/recommendations/service.py` | ~100 | ✅ Генерация рекомендаций |
| DB Tools (PII-safe) | `platform/ai/db_tools.py` | ~200 | ✅ Whitelist tables, PII redaction, aggregate-only |
| Interventions Automation | `platform/ai/interventions_automation.py` | ~100 | ✅ Auto-create cases при severe risk |
| Query Log | `platform/ai/repository.py`, `models.py` | ~100 | ✅ SQLAlchemy logging |
| Frontend | `console/ai/copilot/page.tsx` | ~200 | ✅ Textarea + insights + recommendations |

**Эндпоинты:**
- `POST /api/v1/admin/platform/ai/copilot/ask`
- `GET /api/v1/admin/platform/ai/copilot/logs`
- `GET/PUT /api/v1/admin/platform/ai/risk-thresholds`

**Текущий flow:**
```
User question → keyword classifier → query_type → retrieval(DB) → deterministic response + rules
```

**Безопасность DB tools:**
- `PII_COLUMNS` frozenset — 20+ columns always redacted
- `ALLOWED_TABLES` frozenset — 13 whitelisted таблиц
- SQL identifier validation regex
- Max 50 aggregate rows, only COUNT(*)/GROUP BY queries

### Тесты:
- `test_platform_ai_copilot_foundation_v1.py` — foundation tests
- `test_platform_ai_recommendation_layer_v1.py` — recommendation tests
- `AICopilotPage.test.tsx` — 7 frontend tests

## 3) Gaps для закрытия (to-be, post-day7)

### Gap 1: LLM Integration (HIGH)

**Проблема:** Copilot не использует AI Gateway — всё deterministic keyword matching. Не может понять вопросы в свободной форме.

**Решение (draft, hybrid approach):**
```
User question → LLM classifier (via AI Gateway) → query_type → retrieval(DB) → LLM summarizer → response
                         ↓ (fallback)
              keyword classifier (deterministic)
```

- Шаг 1: Заменить keyword classifier на LLM-based classification (structured output, function calling)
- Шаг 2: Добавить LLM summarizer для retrieved contexts → human-readable ответ
- Шаг 3: Сохранить deterministic fallback при недоступности AI Gateway

**Skeleton test list:**
- `test_llm_classifier_falls_back_to_keyword_on_ai_unavailable`
- `test_llm_classifier_returns_valid_query_type`
- `test_llm_summarizer_respects_max_tokens`
- `test_copilot_hybrid_mode_uses_llm_when_available`

### Gap 2: Role-Specific System Prompts (HIGH)

**Проблема:** Нет различия между platform_admin, institution_admin, academic_admin. Все получают одинаковый ответ.

**Решение (draft):**
- Определить 3 admin personas: `platform_admin`, `institution_admin`, `academic_admin`
- Для каждой — system prompt template с ролевым контекстом:
  - `platform_admin` — глобальные метрики, cross-tenant, infrastructure
  - `institution_admin` — свой вуз, KPIs, бюджет, staff
  - `academic_admin` — кафедра, курсы, студенты, grades
- System prompt инжектируется перед user question при LLM call
- Prompt хранится в `platform/ai/prompts/` (файлы, не DB, для version control)

**Skeleton test list:**
- `test_platform_admin_gets_cross_tenant_system_prompt`
- `test_institution_admin_gets_scoped_system_prompt`
- `test_academic_admin_gets_department_scoped_prompt`
- `test_system_prompt_injection_into_llm_call`

### Gap 3: Conversational Memory (MEDIUM)

**Проблема:** Каждый запрос изолирован — нет контекста предыдущих вопросов.

**Решение (draft):**
- Session-scoped message history (in-memory or Redis, TTL 30 min)
- При каждом вопросе отправлять last N messages как context
- `GET /api/v1/admin/platform/ai/copilot/sessions` — список сессий
- `DELETE /api/v1/admin/platform/ai/copilot/sessions/{id}` — очистка

**Skeleton test list:**
- `test_copilot_session_retains_context`
- `test_copilot_session_expires_after_ttl`
- `test_copilot_session_clear_removes_history`

### Gap 4: Enhanced Query Type Taxonomy (MEDIUM)

**Проблема:** 10 query types покрывают базовые вопросы, но не хватает operational queries.

**Предлагаемые добавки:**
- `compliance_status` — SOC 2 / GDPR compliance state
- `billing_summary` — тенант billing/usage overview
- `integration_health` — статус внешних интеграций (LDAP, AI providers)
- `incident_analysis` — error rate trends, recent incidents
- `capacity_planning` — storage, user counts, growth

**Skeleton test list:**
- `test_query_type_compliance_status_returns_data`
- `test_query_type_billing_summary_returns_data`
- `test_query_type_integration_health_returns_data`

### Gap 5: Prompt Templates Versioning (LOW)

**Решение (draft):**
- Файловые шаблоны в `backend/app/platform/ai/prompts/` (Jinja2 или f-string)
- Версия в имени файла или header: `# v1.0`
- A/B testing через feature flags

## 4) Execution Priority (post-day7)

| Шаг | Gap | Приоритет | Зависимости |
|-----|-----|-----------|-------------|
| 1 | Role-Specific System Prompts | P0 | Нет (можно сделать для deterministic тоже) |
| 2 | LLM Integration (hybrid) | P0 | AI Gateway (#54 routing), #56 guardrails |
| 3 | Enhanced Query Types | P1 | Нет |
| 4 | Conversational Memory | P1 | LLM Integration |
| 5 | Prompt Templates Versioning | P2 | Role-Specific Prompts |

## 5) Архитектурные решения

### Hybrid Architecture (recommended):
```
                   ┌─ LLM Classifier (AI Gateway) ─┐
User Question ─────┤                                 ├─→ query_type ─→ Retrieval ─→ LLM Summary
                   └─ Keyword Classifier (fallback) ─┘                           └─→ Rules
```

### Safety Constraints:
1. **Deterministic fallback обязателен** — при любом AI failure copilot возвращает keyword-based ответ
2. **PII redaction сохраняется** — DB tools whitelist не изменяется
3. **Audit trail** — каждый LLM call логируется с prompt hash + response hash
4. **Cost cap** — max tokens per request, per user per day limit
5. **No raw DB access для LLM** — только retrieval layer результаты, не SQL

## 6) Риски и ограничения

1. LLM Integration создаёт зависимость от AI Gateway — при его падении copilot деградирует до deterministic mode (acceptable)
2. Role-specific prompts требуют тестирования на утечку информации между ролями
3. Conversational memory в Redis — при Redis restart история теряется (acceptable для pilot)
4. Billing quotas должны считать и copilot LLM calls

## 7) Definition of Done (для перехода #53 из HARDENING → EXISTS)

- [ ] Role-specific system prompts (≥3 personas)
- [ ] LLM classifier + deterministic fallback
- [ ] LLM summarizer для retrieved context
- [ ] ≥5 additional query types
- [ ] Audit logging для LLM calls
- [ ] Regression: все существующие copilot тесты green
- [ ] Coverage: ≥80% на новый код
