# Модуль: Research & Science / Innovation (Исследования и инновации)

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `research_science/`, `research/`, `research_projects/`, `research_ethics/`, `research_grants/`, `innovation_commercialization/`, `ip_management/`, `patents/`, `publications/`
Frontend: `frontend/modules/research-science/`, `research-brain/`, `research-ethics/`, `research-grants/`, `innovation-commercialization/`
Вертикаль: **V04 Research / Science** · Brain: [Research Science Brain](../brains/research-science.md)

## Назначение
Управление исследовательской деятельностью: проекты, гранты, публикации, этика, лаборатории, наукометрия, IP и коммерциализация.

## Бизнес‑функции
Реестр исследователей · проекты · гранты (дедлайны, pipeline) · публикации/наукометрия · этические заявки · IP/патенты · коммерциализация/лицензии.

## Пользователи (роли)
`research_science_admin` (research director), исследователи, ethics‑комитет; `auditor`.

## Страницы / Runtime Shell / Dashboard
- `/console/research-science/*` (~7), `/console/research-brain`, `/console/research-ethics`, `/console/innovation-commercialization`.
- **Runtime Shells:** `ResearchBrainRuntimeShellPage` (researchers, scientometrics, risk, dashboard); `InnovationCommercializationRuntimeShellPage`.

## Backend
- **Router:** `research_science/router.py` + `runtime_shell_router.py`; `research/router.py`; `research_ethics/router.py`; `innovation_commercialization/router.py`.
- **Services/Models/DTO:** по под‑доменам; `permissions.py` (40+).

## Database
`university_research_grants`, `university_research_publications`, `university_research_labs`, `university_research_ip_assets`, `university_research_experiments`, `ip_assets`, `ip_licensing_records`, `patents`, `publications`, `citations`, `ethics_reviews`. Alert‑таблицы (grant_delay, ethics).

## API
`/api/admin/research-science`, `/api/admin/research`, `/api/admin/research-ethics`, `/api/admin/innovation-commercialization`. Permissions `projects.*`, `publications.*`, `ethics.*`, `grants.*`, `supervision.*`.

## Связанные модули
`quality_accreditation`, `executive_governance`, `document_decree_correspondence`, `brain_core`, `knowledge_retrieval`.

## Workflow
Исследовательская этика ([../08_WORKFLOWS.md](../08_WORKFLOWS.md) §9.8).

## Brain / AI
Brain‑вертикаль Research Science. Сигналы `research.grant_deadline.approaching`, `research.publication_stagnant`, `research.lab_utilization.low`, `research_ethics.*`; решения `research_innovation`, `research_ethics_compliance`.

## Проблемы / Рекомендации
- **`innovation_commercialization` не закоммичен** (P1, DEPRECATED/UNTRACKED — расширение над Research).
- Семейство research (`research`, `research_projects`, `research_science`) — пересечение. **Рекомендация:** реконсилировать git, консолидировать семейство (см. `A-047.2`).
