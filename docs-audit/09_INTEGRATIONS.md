# 09 — Полный аудит интеграций

[← 08 Workflows](08_WORKFLOWS.md) · [Индекс](README.md) · Далее: [10 Feature Flags →](10_FEATURE_FLAGS.md)

Источники: `app/modules/*_integration`, `app/platform/events`, `webhooks`, `notifications`, `app/platform/router_developer_api.py`, `router_mcp.py`.

---

## 10.1 Внешние интеграции (country‑adapter, 10 модулей)

Все на уровне **L2 contract‑ready** (флаги `no_provider_call=True`, `no_credential_use=True`, `no_live_integration_claim=True`). Живой адаптер — KZ; заявлены планы SA/AE/QA/OM/BH/KW.

| Модуль | Тип | Страна | Статус |
|--------|-----|--------|--------|
| `finance_erp_integration` | Finance/ERP | KZ (+планы) | L2 Contract‑Ready |
| `hr_payroll_integration` | HR/Payroll | KZ (+SA) | L2 Contract‑Ready |
| `payment_gateway_integration` | Payments | KZ (+SA) | L2 Contract‑Ready |
| `sso_saml` | Identity/SSO | KZ (+SA) | L2 Contract‑Ready |
| `identity_provider_integration` | Identity/IdP | KZ | L2 Contract‑Ready |
| `learning_management_system_integration` | LMS | KZ (+SA) | L2 Contract‑Ready |
| `student_information_system_integration` | SIS | KZ | L2 Contract‑Ready |
| `government_services_integration` | Government | KZ | L2 Contract‑Ready |
| `regulatory_reporting_integration` | Compliance | KZ | L2 Contract‑Ready |
| `notification_gateway_integration` | Notifications | KZ | L2 Contract‑Ready |

> **Важно:** «L2 contract‑ready» означает контракт и границы готовы, но **живых вызовов провайдеров нет**. Перед продакшеном требуется реализация адаптеров и настройка секретов.

---

## 10.2 Gateway‑модули (доставка)

| Модуль | Назначение |
|--------|-----------|
| `email_gateway_integration` | Email‑доставка |
| `mobile_push_gateway` | Push‑уведомления (device_tokens, push_notifications) |
| `notification_center` | In‑app уведомления (read/unread) |
| `integrations` | Управление провайдерами (LDAP, AI‑провайдеры), шифрование настроек (`INTEGRATIONS_ENCRYPTION_KEY`) |

---

## 10.3 Внутренние интеграции (события/шина)

- **Event bus (Outbox):** `app/platform/events/` — `EXACT_EVENT_REGISTRY` (232 события) + prefix‑реестр. Publish → `OutboxEventModel` → worker → webhooks/аналитика.
- **Webhooks:** `app/platform/webhooks/dispatcher.py` — доставка событий платформенным подписчикам и developer‑app подпискам; retry (`retry_failed_deliveries`).
- **Event ingestion (аналитика):** `app/platform/event_ingestion/` — fire‑and‑forget лог для аналитики (`ANALYTICS_EVENT_READ`, `KPI_REFRESH_EXECUTED` и т.п.).
- **Brain‑интеграция:** `brain_core/signal_listener.py` подписан на доменные события; middleware эмитит `platform.module.activity.logged`.

Полный список событий по доменам — [11_BACKGROUND_JOBS.md](11_BACKGROUND_JOBS.md) §12.5 и ниже.

---

## 10.4 Очереди / уведомления

- **Notifications** (`app/platform/notifications/`): каналы `email`, `in_app`, `webhook`; outbox‑паттерн (персист перед доставкой); `NotificationDispatchService` ретраит каждые 10 минут.
- **Jobs‑очередь** (`app/modules/jobs/`): статусы queued/running/succeeded/failed/cancelled, до 3 ретраев, fallback in‑memory.

---

## 10.5 Developer / партнёрские интеграции

- **Developer API** (`router_developer_api`, `/api/dev`): аутентификация `X‑App‑Key`/`X‑App‑Secret`; доступ к analytics, KPI, students/grades; подписки на webhooks (`developer_repository`).
- **Semantic layer** (`router_semantic`, `/api/v2/semantic`): entities/metrics/dimensions/queries.
- **MCP server** (`router_mcp`, `/api/v1/internal/mcp`): интроспекция схемы БД, агрегированная статистика для AI‑copilot с redaction PII.

---

## 10.6 AI‑провайдеры (через AI Gateway)

`ai_gateway`: реестр моделей + адаптеры провайдеров: **OpenAI, Gemini, Anthropic, custom** (в т.ч. Ollama/deepseek‑r1 опционально). Единый `POST /api/ai/chat`, usage‑логирование, audit‑hooks, частично RLS на tenant‑таблицах. Управление ключами: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `AI_CUSTOM_PROVIDER_URL/API_KEY`.

Сопутствующие: `ai_routing_control`, `ai_cost_governance`, `ai_guardrails`, `ai_copilot_ops`, `model_evaluation`, `prompt_management`, `knowledge_retrieval`.

---

## 10.7 Аутентификационные интеграции

LDAP/AD (`ldap`), OIDC (`identity`), SAML 2.0 (`sso_saml`, федерация с Okta/AD/Keycloak), 2FA/TOTP. См. [03_ROLES_AND_RBAC.md](03_ROLES_AND_RBAC.md) §4.6.

---

## 10.8 Проблемы (аудит)

- **Нет живых интеграций:** все country‑адаптеры — L2 (контракт без реальных вызовов). Продакшен требует реализации.
- **`innovation_commercialization`** и **`admissions_crm`** — код не закоммичен (риск целостности).
- Полный RLS‑аудит внешних интеграций не проводился.
