# Модуль: Security / Access / Compliance (Безопасность, доступ, соответствие)

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `security_access_compliance/`, `security_operations/`, `access_control/`, `visitor_management/`, `pdpl/`, `consent_management_policy/`, `data_retention_policy_control/`, `third_party_risk_policy/`
Frontend: `frontend/modules/security-access-compliance/`, `security-operations/`, `visitor-management/`, `access-control/`
Вертикаль: **V10 Security / Access / Compliance**

## Назначение
Физическая и цифровая безопасность, контроль доступа, посетители, инциденты, приватность (PDPL), согласия, хранение данных, риски третьих сторон.

## Бизнес‑функции
Access control (карты, логи) · security events/incidents · visitor management (визиты, логи) · compliance reporting · evidence · PDPL/consent/retention policies.

## Пользователи (роли)
`security_access_compliance_admin` (security officer), охрана; `auditor`.

## Страницы
`/console/security-access-compliance`, `/console/security-operations`, `/console/visitor-management`, `/console/access-control`.

## Backend
- **Router:** `security_access_compliance/router.py`, `security_operations/router.py`, `access_control/router.py` (service‑only base), `visitor_management/router.py`.
- **Permissions:** `security_access_compliance/permissions.py` (37+; импортируется в `rbac/service.py`).

## Database
`security_incidents`, `security_incident_escalation_records`, `security_visitors`, `visit_requests`, `visit_logs`, `access_cards`, `access_logs`. Alert‑таблицы.

## API
`/api/admin/security-access-compliance`, `/api/admin/security-operations`, `/api/admin/access-control`, `/api/admin/visitor-management`. Permissions `access_control.read`, `security_event.read`, `compliance_report.read`, `evidence.attach`.

## Связанные модули
`campus_facilities_housing_transport` (access-visitor bridge), `audit`, `hr_staff_governance` (access lifecycle), `brain_core`, `pdpl`.

## Workflow
Инцидент безопасности: `security.incident.{opened,acknowledged,escalated,resolved,dismissed}`; доступ `access.{granted,denied}`, карты `card.*`.

## Brain / AI
Сигналы `campus.security_incident.detected`, `visitor.*`, `security.anomaly`; решения `campus_security`, `visitor_management_ops`, `security_operations_ops` (notify_security_team, create_incident_task, suspend_card, escalate).

## Проблемы / Рекомендации
- FE testid `sac-permission-denied-panel` отсутствует — P2. **Рекомендация:** добавить testid, довести PDPL/consent до полного контракта.
