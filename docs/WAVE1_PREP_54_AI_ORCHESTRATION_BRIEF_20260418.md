# Wave 1 Prep Design Brief: #54 AI Orchestration (Full Routing)

Дата: 2026-04-18
Task ID: #54
Статус: PREP-OPEN
Owner: AI Platform Team
Reviewers: Backend Lead, Product

## 1) Контекст и цель

AI Gateway (#51) работает в production: 4 provider adapters (OpenAI, Gemini, Anthropic, Custom), tenant-scoped model registry, rate limiting, billing/quota integration. Но маршрутизация статическая: пользователь явно выбирает модель. Нет routing policies, fallback chains, A/B testing, cost-aware routing.

## 2) Текущее состояние (as-is)

### Что EXISTS:
- 4 provider adapters в `ai_gateway/service.py` (~1550 LOC)
- Model registry (DB + in-memory fallback): per-tenant list of enabled models с priority
- Explicit model selection: user → model_key → provider adapter → response
- Degraded fallback: при ошибке провайдера → 503 с детерминированным fallback ответом
- Usage logging: per-call tracking (provider, model, tokens, latency, status)
- Rate limiting: per-provider, per-user, per-role (configurable)

### Что НЕТ:
| Gap | Описание |
|-----|----------|
| **Automatic model selection** | Нет routing policy: "для этого типа запроса используй эту модель" |
| **Fallback chains** | При ошибке модели A нет автоматического retry через модель B |
| **A/B testing** | Нет traffic split между моделями для сравнения quality |
| **Cost-aware routing** | Нет выбора модели по стоимости (cheap vs premium) |
| **Latency-aware routing** | Нет выбора по текущей latency (p95 tracking per model) |
| **Task-type routing** | Нет маршрутизации по типу задачи (chat, classification, embedding, code) |
| **Load balancing** | Нет распределения нагрузки между несколькими instances одного провайдера |
| **Routing policies UI** | Нет admin interface для конфигурации routing rules |

## 3) Архитектура routing layer (draft)

### Текущий flow:
```
User → { model_key: "gpt-4o-mini" } → service.chat() → OpenAIAdapter → response
```

### Целевой flow:
```
User → { model_key: "auto" | explicit } → RoutingEngine
    ├── Policy Evaluator (task_type, cost, latency, A/B)
    │   → select_model() → ModelCandidate
    ├── Fallback Chain (if primary fails)
    │   → next_model() → ModelCandidate
    └── CircuitBreaker per provider
        → is_healthy() → bool
→ ProviderAdapter → response
→ Usage + routing decision logged
```

### Routing Policy Types:
```python
class RoutingPolicy:
    name: str
    strategy: str   # "priority", "cost_optimized", "latency_optimized", "ab_test", "round_robin"
    rules: list[RoutingRule]
    fallback_chain: list[str]   # ordered model_keys
    ab_split: dict[str, float]  # model_key → traffic % (only for ab_test)

class RoutingRule:
    condition: str      # "task_type == 'chat'", "input_length > 4000", "role == 'student'"
    target_model: str   # model_key
    priority: int
```

## 4) Component Design

### 4.1 Routing Engine (`ai_gateway/routing/engine.py`)

```python
class RoutingEngine:
    def select_model(request, tenant_policy) -> ModelCandidate:
        """
        1. If explicit model_key → use it (bypass routing)
        2. Evaluate routing rules in priority order
        3. If A/B test active → weighted random selection
        4. If no rule matches → use default model (highest priority in registry)
        5. Check circuit breaker for selected provider
        6. If unhealthy → fallback chain
        """

    def record_routing_decision(request_id, selected_model, reason, latency):
        """Log routing decision для analytics и A/B comparison."""
```

### 4.2 Fallback Chain Manager (`ai_gateway/routing/fallback.py`)

```python
class FallbackChainManager:
    def execute_with_fallback(request, chain: list[str]) -> response:
        """
        Try models in order. On failure (timeout, 5xx, rate limit):
        → log failure → try next model in chain → if all failed → 503
        Max retries configurable per tenant.
        """
```

### 4.3 Circuit Breaker (`ai_gateway/routing/circuit_breaker.py`)

```python
class ProviderCircuitBreaker:
    """
    States: CLOSED (healthy) → OPEN (unhealthy, reject calls) → HALF_OPEN (test probe)
    Configurable: failure_threshold, recovery_timeout, probe_interval
    Storage: Redis (shared across workers) or in-memory (per-process)
    """
```

### 4.4 A/B Test Manager (`ai_gateway/routing/ab_test.py`)

```python
class ABTestManager:
    def get_assignment(user_id, test_id) -> str:
        """Deterministic assignment (hash-based) для consistent A/B experience."""

    def record_result(test_id, model_key, metrics):
        """Record quality/latency/cost для comparison."""
```

## 5) API Contract (draft)

Prefix: `/api/admin/ai/routing`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/policies` | Список routing policies тенанта |
| `POST` | `/policies` | Создать routing policy |
| `PUT` | `/policies/{id}` | Обновить policy |
| `DELETE` | `/policies/{id}` | Удалить policy |
| `GET` | `/fallback-chains` | Список fallback chains |
| `PUT` | `/fallback-chains` | Обновить default fallback chain |
| `GET` | `/circuit-breaker/status` | Состояние circuit breakers per provider |
| `POST` | `/circuit-breaker/{provider}/reset` | Ручной reset circuit breaker |
| `GET` | `/ab-tests` | Список A/B тестов |
| `POST` | `/ab-tests` | Создать A/B тест |
| `GET` | `/ab-tests/{id}/results` | Результаты A/B теста |
| `GET` | `/decisions/log` | Лог routing decisions для analytics |

## 6) Metrics (Prometheus)

```
ai_routing_decisions_total{strategy="...", target_model="...", reason="..."}
ai_routing_fallback_triggered_total{from_model="...", to_model="..."}
ai_circuit_breaker_state{provider="...", state="closed|open|half_open"}
ai_circuit_breaker_trips_total{provider="..."}
ai_provider_latency_seconds{provider="...", quantile="0.5|0.95|0.99"}
ai_ab_test_requests_total{test_id="...", variant="..."}
```

## 7) Skeleton Test List

Backend:
- `test_explicit_model_bypasses_routing`
- `test_auto_model_uses_priority_from_registry`
- `test_routing_rule_task_type_chat_selects_model`
- `test_routing_rule_input_length_selects_premium`
- `test_fallback_chain_retries_on_provider_error`
- `test_fallback_chain_exhausted_returns_503`
- `test_circuit_breaker_opens_on_threshold`
- `test_circuit_breaker_half_open_probe`
- `test_circuit_breaker_closes_on_success`
- `test_ab_test_deterministic_assignment`
- `test_ab_test_respects_traffic_split`
- `test_cost_aware_routing_selects_cheapest`
- `test_routing_decision_logged`
- `test_routing_degrades_gracefully_without_redis`

Frontend:
- `test_routing_policies_page_renders`
- `test_circuit_breaker_status_dashboard`
- `test_ab_test_results_chart`

## 8) Execution Priority (post-day7)

| Шаг | Компонент | Приоритет | Зависимости |
|-----|-----------|-----------|-------------|
| 1 | Routing Engine (basic: priority + explicit) | P0 | Нет |
| 2 | Fallback Chain Manager | P0 | Шаг 1 |
| 3 | Circuit Breaker (in-memory first) | P0 | Шаг 1 |
| 4 | Routing API endpoints | P1 | Шаг 1-3 |
| 5 | Metrics + routing decision logging | P1 | Шаг 1 |
| 6 | A/B Test Manager | P2 | Шаг 1 |
| 7 | Cost-aware routing | P2 | Usage data from #60 |
| 8 | Admin UI for routing policies | P2 | F3.4 + Шаг 4 |

## 9) Риски и ограничения

1. **Circuit breaker state persistence** — in-memory = per-process, не shared. Для multi-worker → Redis. Начать с in-memory (single worker в Docker).
2. **A/B test bias** — hash-based assignment может быть skewed при малых sample sizes. Not critical for pilot.
3. **Latency overhead** — routing decision adds <1ms. Acceptable.
4. **Provider API changes** — fallback chain эффективен только если все модели в chain совместимы по формату.

## 10) Definition of Done (для перехода #54 из HARDENING → EXISTS)

- [ ] Routing Engine с priority-based selection
- [ ] Fallback Chain Manager (≥2 deep)
- [ ] Circuit Breaker per provider
- [ ] ≥6 API endpoints
- [ ] Routing decision logging
- [ ] Prometheus metrics
- [ ] Regression: AI Gateway тесты green
- [ ] Coverage: ≥80%
