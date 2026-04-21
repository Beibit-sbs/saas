# Wave 1 Prep Design Brief: #56 AI Guardrails (Standalone)

Дата: 2026-04-18
Task ID: #56
Статус: ✅ SHIPPED (P0+P1 complete 2026-04-20)
Owner: AI Safety Team
Reviewers: Security Lead, Backend Lead, Product

## 1) Контекст и цель

AI Gateway имеет базовые защиты (rate limiting, billing quota, input validation, URL validation), но нет: content moderation, prompt injection detection, output sanitization, configurable safety policies. Цель — выделить guardrails в отдельный standalone layer между user input и provider call.

## 2) Текущее состояние (as-is)

### Что EXISTS (embedded в AI Gateway):

| Защита | Реализация | Файл | Статус |
|--------|-----------|------|--------|
| Rate limiting | 3-tier: per-provider, per-user, per-role | `ai_gateway/service.py` | ✅ Production |
| Billing quota | `assert_billing_write_allowed` + `assert_quota_with_increment` | `ai_gateway/service.py` | ✅ Production |
| Input validation | Pydantic: content ≤16K, messages ≤100, temperature 0–2, max_tokens 1–16384 | `ai_gateway/schemas.py` | ✅ Production |
| URL validation | `validate_external_https_url()` для custom provider endpoints | `security/url_validation.py` | ✅ Production |
| Degraded fallback | Детерминированный fallback при таймауте/ошибке провайдера | `ai_gateway/service.py` | ✅ Production |
| Fail-closed | Необработанные ошибки → 503 | `ai_gateway/public_router.py` | ✅ Production |
| Audit logging | Каждый вызов (success/failure) в `app_ai_usage_logs` | `ai_gateway/service.py` | ✅ Production |
| PII redaction (DB tools) | Whitelist tables + PII columns frozenset | `platform/ai/db_tools.py` | ✅ Production |
| Tenant isolation | `set_db_tenant_context()`, tenant_id обязателен | `ai_gateway/service.py` | ✅ Production |

### Что НЕТ:

| Gap | Severity |
|-----|----------|
| Content filtering/moderation (toxicity, profanity, harassment) | HIGH |
| Prompt injection detection | HIGH |
| Output sanitization (от provider) | HIGH |
| Configurable tenant safety policies | MEDIUM |
| Content deny/allow lists | MEDIUM |
| PII detection в свободных промптах | MEDIUM |
| `blocked_by_guardrail` audit category | MEDIUM |
| Guardrail metrics/observability (pass/block rate) | MEDIUM |
| Per-model safety config (forced system prompts, temp caps) | LOW |
| Response cost enforcement (tenant-level) | LOW |

## 3) Архитектура standalone guardrails (draft)

### Текущий flow:
```
User Input → [Pydantic validation] → [Rate limit] → [Billing quota] → Provider Call → Response
```

### Целевой flow:
```
User Input → [Pydantic validation] → [Rate limit] → [Billing quota]
           → [PRE-GUARDRAILS]
              ├── Prompt injection detector
              ├── Content moderation (input)
              ├── PII detector (input)
              ├── Deny-list pattern matcher
              └── Tenant policy evaluator
           → Provider Call
           → [POST-GUARDRAILS]
              ├── Content moderation (output)
              ├── PII detector (output)
              └── Response length/cost validator
           → Response + guardrail_metadata
```

### Модульная структура (proposal):

```
backend/app/modules/ai_guardrails/
├── __init__.py
├── engine.py              # GuardrailEngine — orchestrator: pre + post chains
├── detector_injection.py  # Prompt injection detection (pattern + heuristic)
├── detector_pii.py        # PII detection в свободном тексте
├── filter_content.py      # Content moderation (deny patterns, toxicity)
├── policy.py              # Tenant-scoped safety policy evaluator
├── schemas.py             # GuardrailResult, GuardrailPolicy, GuardrailDecision
├── metrics.py             # Prometheus: guardrail_evaluated_total, guardrail_blocked_total
└── tests/
    ├── test_guardrail_engine.py
    ├── test_detector_injection.py
    ├── test_detector_pii.py
    ├── test_filter_content.py
    └── test_policy_evaluator.py
```

## 4) Component Design Drafts

### 4.1 Prompt Injection Detector

**Подход (multi-layer):**
1. **Pattern matching** — regex для известных injection patterns:
   - `"ignore previous instructions"`, `"system: ..."`, `"<|im_start|>"`
   - Role-switching attempts: `"you are now..."`, `"act as..."`
   - Encoding evasion: base64, unicode tricks
2. **Heuristic scoring** — длина, entropy, ratio special chars, known attack templates
3. **LLM-based detection** (optional, post-pilot) — classify input as safe/suspicious via dedicated model

**Decision:** `PASS` / `WARN` (log + proceed) / `BLOCK` (reject 422 + audit)

**Skeleton test list:**
- `test_blocks_ignore_previous_instructions`
- `test_blocks_system_prompt_override_attempt`
- `test_blocks_base64_encoded_injection`
- `test_passes_normal_academic_question`
- `test_passes_complex_but_safe_query`
- `test_warn_suspicious_but_not_definitive`

### 4.2 Content Moderation Filter

**Подход:**
1. **Deny-list patterns** — configurable per-tenant regex patterns для blocked topics
2. **Category classification** — toxicity, profanity, hate speech, violence, sexual content
3. **Academic context allowance** — academic discussions about sensitive topics != violation (configurable sensitivity)

**Configuration:**
```python
class ContentPolicy:
    blocked_patterns: list[str]       # regex deny-list
    sensitivity_level: str            # "strict" | "moderate" | "academic"
    allowed_categories: set[str]      # override: allow specific categories
    audit_only_mode: bool             # log-only, don't block
```

**Skeleton test list:**
- `test_blocks_toxic_input`
- `test_blocks_denied_pattern`
- `test_allows_academic_discussion_in_academic_mode`
- `test_blocks_academic_discussion_in_strict_mode`
- `test_output_moderation_catches_provider_unsafe_response`

### 4.3 PII Detector (Free Text)

**Подход:**
1. **Regex patterns** — email, phone, SSN, passport, credit card, IP address
2. **Named entity recognition** (optional, post-pilot) — NER для имён / адресов
3. **Action:** `REDACT` (replace with `[PII_REDACTED]`) или `BLOCK`

**Skeleton test list:**
- `test_detects_email_in_prompt`
- `test_detects_phone_number`
- `test_detects_credit_card_pattern`
- `test_does_not_flag_academic_ids`
- `test_redact_mode_replaces_pii`
- `test_block_mode_rejects_request`

### 4.4 Tenant Safety Policy Evaluator

**Подход:**
- Policy хранится в DB per tenant (JSON): `ai_safety_policies` table
- Default policy встроена в код (apply если tenant не override)
- Fields: `injection_detection: bool`, `content_moderation: str`, `pii_detection: str`, `blocked_patterns: list`, `audit_only: bool`

**Skeleton test list:**
- `test_default_policy_applies_when_no_tenant_override`
- `test_tenant_policy_overrides_default`
- `test_audit_only_policy_logs_but_does_not_block`

### 4.5 Guardrail Metrics

**Prometheus series:**
- `ai_guardrail_evaluations_total{stage="pre|post", detector="injection|content|pii|policy", decision="pass|warn|block"}`
- `ai_guardrail_blocked_total{detector="...", reason="..."}`
- `ai_guardrail_evaluation_duration_seconds{stage="pre|post"}`

### 4.6 Audit Trail

Каждое guardrail решение записывается в AI usage log:
```python
{
    "guardrail_decisions": [
        {"detector": "injection", "decision": "pass", "score": 0.12},
        {"detector": "content", "decision": "pass"},
        {"detector": "pii", "decision": "warn", "redacted_count": 1}
    ],
    "guardrail_blocked": false,
    "guardrail_latency_ms": 3.2
}
```

## 5) Integration Points

### С AI Gateway:
- `GuardrailEngine.evaluate_pre(input)` вызывается перед provider call
- `GuardrailEngine.evaluate_post(output)` вызывается после provider response
- Inject в `ai_gateway/service.py` → `_execute_chat()` method

### С Admin Copilot (#53):
- Copilot LLM calls проходят через ту же guardrail chain
- Можно добавить copilot-specific policy (менее строгая, т.к. input = admin question)

### С Observability (#48):
- Guardrail metrics экспортируются в Prometheus
- Alert rules: `guardrail_blocked_rate_high`, `guardrail_evaluation_latency_high`

## 6) Execution Priority (post-day7)

| Шаг | Компонент | Приоритет | Зависимости |
|-----|-----------|-----------|-------------|
| 1 | Prompt injection detector (pattern-based) | P0 | Нет |
| 2 | Content moderation filter (deny-list) | P0 | Нет |
| 3 | GuardrailEngine + integration в AI Gateway | P0 | Шаги 1-2 |
| 4 | PII detector (regex) | P1 | Нет |
| 5 | Guardrail metrics + audit trail | P1 | Шаг 3 |
| 6 | Tenant safety policy (DB-backed) | P1 | Шаг 3 |
| 7 | Output moderation (post-provider) | P2 | Шаг 3 |
| 8 | LLM-based injection detection | P2 | AI Gateway stable |

## 7) Риски и ограничения

1. **False positives** — pattern-based detection может блокировать легитимные academic вопросы. Mitigation: `audit_only` mode для начала, tuning на real data
2. **Latency** — guardrail chain добавляет 2-10ms per request. Acceptable для chat-based AI
3. **Bypass via encoding** — UTF-8 tricks, homoglyphs. Mitigation: normalize input перед detection
4. **Provider output quality** — мы не контролируем что вернёт LLM. Post-guardrails — best-effort
5. **No external moderation API** — всё on-premise. При масштабировании — рассмотреть OpenAI Moderation API / Perspective API

## 8) Definition of Done (для перехода #56 из HARDENING → EXISTS)

- [x] Standalone guardrail module (`ai_guardrails/`)
- [x] Prompt injection detector (pattern + heuristic)
- [x] Content moderation filter (deny-list + categories)
- [x] PII detector (regex, ≥5 patterns)
- [x] GuardrailEngine integrated в AI Gateway
- [x] Guardrail metrics в Prometheus
- [x] Audit trail для guardrail decisions (`blocked_by_guardrail` outcome в usage log)
- [x] Tenant policy override mechanism
- [x] Regression: все AI Gateway тесты green
- [x] Coverage: ≥80% на новый код (96–100% по всем файлам ai_guardrails)
