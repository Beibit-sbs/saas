# Wave 1 Prep Design Brief: #60 AI Cost / Performance Governance

Дата: 2026-04-18
Task ID: #60
Статус: PREP-OPEN
Owner: FinOps + AI Platform
Reviewers: Backend Lead, Platform Architecture

## 1) Контекст и цель

AI Gateway логирует usage per call (provider, model, tokens, latency), а billing/usage module отслеживает consumption metrics. Но нет: cost attribution, cost alerts, per-tenant cost caps, cost anomaly detection, performance SLO governance.

## 2) Текущее состояние (as-is)

### Usage Tracking (EXISTS):
- `app_ai_usage_logs` table — per-call: tenant_id, model, provider, input_tokens, output_tokens, latency_ms, status
- `usage/service.py` (~230 LOC) — базовый usage tracking, period-based aggregation
- `billing/service.py` — `assert_quota_with_increment` per request
- Frontend: `/console/billing/usage` — basic usage display

### Что НЕТ:
| Gap | Описание |
|-----|----------|
| **Cost calculation** | Нет mapping token_count → $ per provider/model |
| **Cost attribution** | Нет per-user/per-department cost breakdown |
| **Cost budgets** | Нет tenant/department budget с alerts |
| **Cost anomaly detection** | Нет автоматического обнаружения spike в расходах |
| **Performance SLOs** | Нет p95/p99 latency targets per model |
| **SLO breach alerts** | Нет alerting при нарушении SLO |
| **Cost dashboard** | Нет rich UI с trends, breakdown, projections |
| **Token price catalog** | Нет DB с ценами per model per provider |

## 3) Архитектура cost governance (draft)

### Component Map:
```
AI Usage Logs → Cost Calculator → Cost Store
                    ↑                    ↓
Token Price Catalog          Cost Dashboard API
                                    ↓
                            Budget Manager → Alert Engine
                                    ↓
                            Anomaly Detector → Notifications
```

## 4) Data Model (draft)

### Token Price Catalog:
```sql
CREATE TABLE app_ai_token_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(32) NOT NULL,
    model_key VARCHAR(64) NOT NULL,
    input_price_per_1k NUMERIC(10,6) NOT NULL,   -- $ per 1K input tokens
    output_price_per_1k NUMERIC(10,6) NOT NULL,  -- $ per 1K output tokens
    effective_from DATE NOT NULL,
    effective_to DATE,                             -- NULL = current
    UNIQUE(provider, model_key, effective_from)
);
```

**Примерные цены (2026 data):**
| Provider | Model | Input $/1K | Output $/1K |
|----------|-------|------------|-------------|
| OpenAI | gpt-4o-mini | 0.00015 | 0.00060 |
| OpenAI | gpt-4o | 0.00250 | 0.01000 |
| Anthropic | claude-3-5-haiku | 0.00025 | 0.00125 |
| Google | gemini-1.5-flash | 0.00008 | 0.00030 |

### Cost Aggregation:
```sql
CREATE TABLE app_ai_cost_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    date DATE NOT NULL,
    provider VARCHAR(32) NOT NULL,
    model_key VARCHAR(64) NOT NULL,
    user_id UUID,                    -- NULL = tenant aggregate
    department VARCHAR(128),         -- NULL = tenant aggregate
    request_count INTEGER NOT NULL DEFAULT 0,
    input_tokens BIGINT NOT NULL DEFAULT 0,
    output_tokens BIGINT NOT NULL DEFAULT 0,
    cost_usd NUMERIC(10,4) NOT NULL DEFAULT 0,
    UNIQUE(tenant_id, date, provider, model_key, user_id, department)
);
```

### Budget:
```sql
CREATE TABLE app_ai_budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    scope VARCHAR(32) NOT NULL,       -- 'tenant', 'department', 'user'
    scope_id VARCHAR(128),            -- department name or user_id
    period VARCHAR(16) NOT NULL,      -- 'daily', 'weekly', 'monthly'
    budget_usd NUMERIC(10,2) NOT NULL,
    alert_threshold_pct INTEGER DEFAULT 80,
    hard_cap BOOLEAN DEFAULT FALSE,   -- if true, block requests when exceeded
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

## 5) API Contract (draft)

Prefix: `/api/admin/ai/costs`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/summary?period=daily&from=&to=` | Cost summary с breakdown по model/provider |
| `GET` | `/by-user?from=&to=` | Cost attribution per user |
| `GET` | `/by-department?from=&to=` | Cost attribution per department |
| `GET` | `/trend?days=30` | Cost trend (daily totals) for chart |
| `GET` | `/projection` | Projected cost for current period |
| `GET` | `/anomalies` | Detected cost anomalies |

Prefix: `/api/admin/ai/budgets`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Список бюджетов тенанта |
| `POST` | `/` | Создать бюджет (tenant/department/user scope) |
| `PUT` | `/{id}` | Обновить бюджет |
| `DELETE` | `/{id}` | Удалить бюджет |
| `GET` | `/status` | Текущий % использования по каждому бюджету |

Prefix: `/api/admin/ai/prices`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Token price catalog |
| `PUT` | `/{provider}/{model}` | Обновить цену (idempotent) |

Prefix: `/api/admin/ai/slo`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Performance SLOs |
| `PUT` | `/{model}` | Установить SLO target (p95, error_rate) |
| `GET` | `/compliance` | SLO compliance report |

## 6) Scheduler Jobs

| Job | Interval | Logic |
|-----|----------|-------|
| `ai_cost_daily_aggregation` | 1h | Aggregate usage_logs → cost_daily |
| `ai_budget_check` | 15min | Check budgets, send alerts at threshold |
| `ai_anomaly_detection` | 1h | Compare current window vs rolling avg, flag spikes |
| `ai_slo_compliance_check` | 1h | Compare p95 latency vs SLO targets |

## 7) Anomaly Detection (draft)

**Simple Z-score approach:**
```python
def detect_anomaly(current_daily_cost, rolling_avg_7d, rolling_std_7d) -> bool:
    z_score = (current_daily_cost - rolling_avg_7d) / max(rolling_std_7d, 0.01)
    return z_score > 2.0  # >2σ = anomaly
```

## 8) Metrics (Prometheus)

```
ai_cost_total_usd{tenant_id="...", provider="...", model="...", period="daily"}
ai_budget_utilization_pct{tenant_id="...", scope="...", scope_id="..."}
ai_budget_exceeded_total{tenant_id="...", scope="..."}
ai_cost_anomaly_detected_total{tenant_id="..."}
ai_slo_compliance_pct{model="...", metric="p95_latency|error_rate"}
ai_slo_breach_total{model="...", metric="..."}
```

## 9) Skeleton Test List

Backend:
- `test_cost_calculation_uses_token_prices`
- `test_cost_aggregation_daily_groups_correctly`
- `test_cost_summary_filters_by_period`
- `test_cost_by_user_returns_breakdown`
- `test_cost_by_department_returns_breakdown`
- `test_cost_projection_extrapolates_current_pace`
- `test_budget_alert_at_threshold_pct`
- `test_budget_hard_cap_blocks_requests`
- `test_budget_soft_cap_allows_with_warning`
- `test_anomaly_detection_flags_spike`
- `test_anomaly_detection_ignores_normal`
- `test_slo_compliance_reports_breach`
- `test_token_price_update_idempotent`
- `test_cost_trend_returns_daily_series`

Frontend:
- `test_cost_dashboard_renders_chart`
- `test_budget_management_page_renders`
- `test_anomaly_alert_displays`

## 10) Execution Priority (post-day7)

| Шаг | Компонент | Приоритет | Зависимости |
|-----|-----------|-----------|-------------|
| 1 | Token price catalog (model + API) | P0 | Нет |
| 2 | Cost calculation + daily aggregation | P0 | Шаг 1 |
| 3 | Cost summary + breakdown API | P0 | Шаг 2 |
| 4 | Budget management (CRUD + checks) | P1 | Шаг 2 |
| 5 | Anomaly detection (Z-score) | P1 | Шаг 2 |
| 6 | SLO management | P1 | AI usage logs |
| 7 | Prometheus metrics | P1 | Шаг 2-6 |
| 8 | Frontend dashboard | P2 | F3.4 + Шаг 3 |

## 11) Risks

1. **Price accuracy** — provider prices change frequently. Manual update via admin API. Auto-sync with provider APIs is post-Wave1.
2. **Cost lag** — daily aggregation means cost is 1h behind. For budget hard caps, need inline cost check (slower).
3. **Currency** — initially USD only. Multi-currency is post-Wave2.
4. **Small-scale pilot** — cost governance most valuable at scale. For pilot, budget alerts + basic dashboard sufficient.

## 12) Definition of Done (для перехода #60 из PLANNED → EXISTS)

- [ ] Token price catalog (model + CRUD API)
- [ ] Cost daily aggregation job
- [ ] Cost summary + by-user + by-department APIs
- [ ] Budget management (CRUD + threshold alerts)
- [ ] Anomaly detection (Z-score, basic)
- [ ] SLO compliance tracking
- [ ] Prometheus metrics for cost/budget/SLO
- [ ] Frontend: cost trend chart + budget status
- [ ] Regression: AI Gateway + billing тесты green
- [ ] Coverage: ≥80%
