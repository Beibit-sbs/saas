# Wave 1 Prep Design Brief: #33 Delinquency / Collections

Дата: 2026-04-18
Task ID: #33
Статус: PREP-OPEN
Owner: Finance Domain Team
Reviewers: Backend Lead, Product, Compliance

## 1) Контекст и цель

Billing module (#32) в HARDENING: есть service-layer с subscription lifecycle, plan management, usage tracking. Но нет автоматической обработки неплатежей (dunning), коллекторских workflows, и compliance-событий. Delinquency / Collections — отдельный домен поверх billing.

## 2) Текущее состояние (as-is)

### Что EXISTS в billing:
- `billing/service.py` (~820 LOC) — subscription lifecycle (trial → active → suspended → cancelled)
- `platform/billing/service.py` — plan CRUD, subscription assign, usage increment
- `billing/router.py` — scaffold endpoints (flag-gated `BILLING_MODULE_ROUTER_ENABLED`)
- Subscription states: `trial`, `active`, `suspended`, `cancelled`
- **Нет:** delinquency state, dunning workflow, payment reminders, collections events

### Что можно использовать:
- Существующий `suspended` → расширить как промежуточный dunning-этап
- Event bus (#47) — публиковать billing events (payment_overdue, suspension, collection_started)
- Workflow engine (#46) — оркестрация dunning steps
- Notifications platform — отправка напоминаний

## 3) Dunning Lifecycle (draft)

### Status Machine:
```
active → grace_period (1-7 дней) → overdue (7-30 дней) → suspended (30-60 дней) → collections (60+ дней) → cancelled
               ↓ (payment)            ↓ (payment)           ↓ (payment)              ↓ (payment)
           → active                → active              → active (unsuspend)     → active (special approval)
```

### Этапы:
| Этап | Trigger | Duration | Actions |
|------|---------|----------|---------|
| `grace_period` | invoice not paid by due_date | 1-7 days | Email reminder #1, in-app notice |
| `overdue` | grace_period expired | 7-30 days | Email reminder #2 + #3, admin alert |
| `suspended` | overdue expired | 30-60 days | Disable non-essential features, email warning |
| `collections` | suspended expired | 60+ days | External collection referral, admin escalation |
| `cancelled` | collections failed / manual | terminal | Full disable, data retention start |

### Configurable per Tenant:
```python
class DunningPolicy:
    grace_period_days: int = 7
    overdue_period_days: int = 30
    suspension_period_days: int = 30
    auto_cancel_after_days: int = 90
    reminder_schedule: list[int] = [1, 3, 7, 14, 30]  # days after due_date
    require_approval_for_reactivation: bool = True
```

## 4) Data Model (draft)

### DelinquencyRecord
```sql
CREATE TABLE app_billing_delinquency (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    invoice_id UUID NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'grace_period',
    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_reminder_at TIMESTAMPTZ,
    reminder_count INTEGER DEFAULT 0,
    escalated_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    resolution VARCHAR(32),        -- 'paid', 'waived', 'cancelled', 'written_off'
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### CollectionEvent
```sql
CREATE TABLE app_billing_collection_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delinquency_id UUID NOT NULL REFERENCES app_billing_delinquency(id),
    event_type VARCHAR(64) NOT NULL,  -- 'reminder_sent', 'escalated', 'payment_received', 'suspended', etc.
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## 5) API Contract (draft)

Prefix: `/api/admin/billing/delinquency`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Список delinquency records (filter: status, tenant, date) |
| `GET` | `/{id}` | Детали записи + collection events |
| `POST` | `/{id}/escalate` | Ручная эскалация на следующий этап |
| `POST` | `/{id}/resolve` | Резолюция (paid/waived/written_off) |
| `POST` | `/{id}/reminder` | Ручная отправка напоминания |
| `GET` | `/policy` | Текущая dunning policy тенанта |
| `PUT` | `/policy` | Обновить dunning policy |
| `GET` | `/dashboard` | Summary: count by status, total overdue amount |

## 6) Integration Points

| Система | Тип | Описание |
|---------|-----|----------|
| Billing Service | Dependency | Чтение invoice status, subscription state |
| Event Bus (#47) | Publish | `billing.invoice_overdue`, `billing.suspended`, `billing.collections_started`, `billing.reactivated` |
| Workflow Engine (#46) | Orchestration | Dunning workflow с automatic step transitions |
| Notifications | Side-effect | Email + in-app reminders по расписанию |
| Audit (#50) | Logging | Все escalation/resolution actions |

## 7) Skeleton Test List

Backend:
- `test_grace_period_created_on_unpaid_invoice`
- `test_grace_period_resolves_on_payment`
- `test_overdue_transition_after_grace_period`
- `test_suspension_transition_after_overdue`
- `test_collections_transition_after_suspension`
- `test_manual_escalation_advances_status`
- `test_resolve_paid_clears_delinquency`
- `test_resolve_waived_requires_admin`
- `test_dunning_policy_configurable_per_tenant`
- `test_reminder_count_incremented`
- `test_dashboard_returns_summary_counts`
- `test_events_published_on_status_change`

Frontend:
- `test_delinquency_list_page_renders`
- `test_delinquency_detail_shows_timeline`
- `test_delinquency_resolve_dialog`

## 8) Execution Priority (post-day7)

| Шаг | Компонент | Приоритет | Зависимости |
|-----|-----------|-----------|-------------|
| 1 | Data model + Alembic migration | P0 | #32 billing hardening |
| 2 | Delinquency service + status machine | P0 | Шаг 1 |
| 3 | API endpoints | P0 | Шаг 2 |
| 4 | Scheduler job: auto dunning transitions | P0 | Шаг 2 |
| 5 | Event bus integration | P1 | #47 event bus |
| 6 | Notification integration | P1 | Нет |
| 7 | Dunning policy CRUD | P1 | Шаг 2 |
| 8 | Dashboard (API + UI) | P2 | Шаг 3 |

## 9) Compliance Notes

1. **GDPR**: delinquency records содержат financial PII — retention policy обязательна
2. **Local regulations**: dunning process может быть регулирован (напр. EU consumer protection). Configurable dunning policy per tenant позволяет адаптировать.
3. **Audit trail**: все actions по delinquency обязательно логируются для compliance evidence

## 10) Definition of Done (для перехода #33 из PLANNED → EXISTS)

- [ ] Delinquency status machine (grace → overdue → suspended → collections → cancelled)
- [ ] Configurable dunning policy per tenant
- [ ] ≥8 API endpoints
- [ ] Scheduler auto-transition job
- [ ] Event bus events published
- [ ] Notification integration (≥2 reminder templates)
- [ ] Dashboard summary endpoint
- [ ] Regression: billing тесты green
- [ ] Coverage: ≥80%
