# Модуль: Quality & Accreditation (Качество и аккредитация)

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `backend/app/modules/quality_accreditation/`, `accreditation/`, `accreditation_compliance/`, `accreditation_dashboard/`
Frontend: `frontend/modules/quality-accreditation/`, `frontend/modules/accreditation/`
Вертикаль: **V05 Quality / Accreditation** · Brain: [Quality Accreditation Brain](../brains/quality-accreditation.md)

## Назначение
Управление качеством и аккредитацией: циклы самооценки, сбор доказательств, аудит‑находки, корректирующие действия, планы улучшений, мониторинг готовности, отчётность.

## Бизнес‑функции
Self‑assessment · accreditation evidence · audit findings · corrective actions · improvement plans · readiness monitoring · реестр аккредитаций · дашборд.

## Пользователи (роли)
`quality_accreditation_admin` (accreditation officer), `rector`/`executive`; `auditor`.

## Страницы / Runtime Shell / Dashboard
- `/console/quality-accreditation/*`, `/console/accreditation-compliance`.
- **Runtime Shell:** `QualityAccreditationRuntimeShellPage` → `getQualityAccreditationRuntimeShell()`.
- **Dashboard:** `dashboard_runtime_router`.

## Backend
- **Router:** `quality_accreditation/router.py` + 8 под‑роутеров: accreditation_evidence, accreditation_registry, audit_findings, corrective_action, dashboard, improvement_plan, readiness_monitoring, self_assessment, + runtime_shell.
- **Services/DTO/Permissions:** `permissions.py` (48+).

## Database
`accreditation_records`, `accreditation_risk_alerts`, QA‑таблицы (миграция `qa38a2rt01_a0382_quality_accreditation_tables`). FK на `app_tenants`.

## API
`/api/admin/quality-accreditation/*`, `/api/admin/accreditation-compliance`. Permissions `self_assessment.*`, `accreditation_evidence.create`, `corrective_action.*`, `audit_findings.read`.

## Связанные модули
`reporting_runtime` (Ministry), `research_ethics`, `document_decree_correspondence` (evidence), `executive_governance`, `brain_core`.

## Workflow
Качество/аккредитация ([../08_WORKFLOWS.md](../08_WORKFLOWS.md) §9.9).

## Brain / AI
Brain‑вертикаль Quality Accreditation. Сигнал `accreditation.status_changed`; решение `accreditation_remediation`. AI — через Brain reasoning/evidence summary (safe agent).

## Интеграции / Jobs / Flags
Интеграции: `regulatory_reporting_integration` (L2). Jobs: KPI‑refresh. Флаги: динамические.

## Проблемы / Рекомендации
- **Дубль‑семейство:** `quality_accreditation` vs `accreditation`×3 (accreditation, accreditation_compliance, accreditation_dashboard).
- FE‑drift маршрутов (19→27) — P2. **Рекомендация:** консолидировать семейство, синхронизировать FE‑контракты.
