# Страница‑зона: Админ‑консоль (`/console`)

[← Каталог страниц](README.md)

## URL / Назначение
`/console/*` (~370 страниц) — основная административная и операционная плоскость платформы. Layout: `frontend/app/(admin)/console/`.

## Доступ / Permissions
Требует валидного не‑истёкшего JWT (`app_access_token`/`admin_token`) — enforced в `middleware.ts`. Легаси `/admin` → редирект на `/console/platform`. Конкретные страницы дополнительно проверяют permission через `permission-gate`/backend `permission_dependency`.

## Runtime Shell
Содержит все Runtime Shell'ы (Student Success, Academic Operations, Executive Governance, Quality Accreditation, Research Brain, Reporting, Innovation, Communications) — см. [../runtime_shells/README.md](../runtime_shells/README.md).

## Основные под‑зоны (по доменам)
Platform/Developer · Academic Operations · People/HR · Finance/Procurement · Student Success · Research · Campus/Facilities · Communications · Records/Documents · Executive Governance · Quality/Compliance · AI Services. Полный список групп и маршрутов — [README.md](README.md).

## Backend API
Соответствующие `/api/admin/*` роутеры (см. [../05_API.md](../05_API.md)). Каждый вызов защищён RBAC+ABAC.

## Компоненты / Сервисы / Таблицы
Shared UI (`frontend/shared/ui/*`), доменные `frontend/modules/*/components`. Сервисы — `frontend/modules/*/api.ts` (React Query). Таблицы — соответствующие доменные (см. [../database/README.md](../database/README.md)).

## Зрелость
По `README.md` проекта — админ‑консоль **наиболее зрелая** плоскость (глубже, чем ролевые порталы).
