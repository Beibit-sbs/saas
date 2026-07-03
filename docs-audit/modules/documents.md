# Модуль: Document / Decree / Correspondence (Документы, приказы, корреспонденция)

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `document_decree_correspondence/`, `document_workflow_os/`, `document_workflow/`, `document_template_library/`, `digital_documents/`, `digital_certificates/`, `digital_signature_integration/`, `order_decree_registry/`, `incoming_outgoing_correspondence/`, `records_hub/`, `archive_retention_management/`, `blockchain_diploma/`, `contracts_legal_repository/`
Frontend: `frontend/modules/document-decree-correspondence/`, `document-workflow/`, `contracts-legal-repository/`
Вертикаль: **V08 Document / Decree / Correspondence**

## Назначение
Управление официальными документами: приказы/декреты, входящая/исходящая корреспонденция, маршрутизация, ЭЦП, исполнение, архив, SLA.

## Бизнес‑функции
Реестр документов/приказов · маршрутизация и согласование · signature readiness (ЭЦП) · execution control · корреспонденция (in/out) · шаблоны · архив/хранение · rector‑resolutions · committee decisions · SLA‑дедлайны · evidence.

## Пользователи (роли)
document‑admin, `rector` (резолюции), исполнители, канцелярия; `auditor`.

## Страницы
`/console/document-decree-correspondence/*` (~20: documents, decrees, correspondence, routing, signature-readiness, delivery-readiness, decree-drafts, incoming, outgoing, execution-control, evidence, bridges, committee-decisions, attachments, archive, intake, sla-deadlines, templates, audit, assignments, rector-resolutions); `/console/documents/*`.

## Backend
- **Router:** `document_decree_correspondence/router.py`, `document_workflow_os/router.py` (`/api/admin/documents`).
- **Permissions:** `document_decree_correspondence/permissions.py`, `document_workflow_os/permissions.py`.

## Database
Таблицы document/decree/correspondence (миграция `bs57uv69wx70_a0321_document_workflow_os_tables`), `digital_documents`, `certificates`, `order_decree_registry`, archive/retention, `blockchain_diploma`.

## API
`/api/admin/document-decree-correspondence`, `/api/admin/documents`. Permissions по `permissions.py`.

## Связанные модули
`workflows` (движок), `rector_assignment_workflow`, `executive_governance`, `digital_signature_integration`, `notification_center`, `brain_core`.

## Workflow
Документы/приказы/корреспонденция ([../08_WORKFLOWS.md](../08_WORKFLOWS.md) §9.10).

## Brain / AI
Сигналы `document.signed`, `order.{created,signed,executed}`. Safe evidence summary agent (UCE‑145) может формировать сводки. Human‑gated.

## Интеграции / Jobs / Flags
Интеграции: `digital_signature_integration` (ЭЦП). Jobs: SLA‑мониторинг (через события). Флаги: динамические.

## Проблемы / Рекомендации
- Множество близких модулей (document_workflow / document_workflow_os / document_decree_correspondence / records_hub). FE testid `ddc-audit-timeline` отсутствует — P2. **Рекомендация:** консолидировать документные модули, добавить недостающие testid.
