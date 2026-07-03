# Страница‑зона: Портал преподавателя (`/faculty`)

[← Каталог страниц](README.md)

## URL / Назначение
`/faculty` (`frontend/app/faculty/page.tsx`) — рабочее место преподавателя: gradebook, ростер группы, расписание, управление курсом, метрики, AI‑copilot.

## Доступ / Permissions
Роль `faculty`/teaching staff. Enforced в `middleware.ts`. Backend: `grades.write` (только свой курс — **ABAC**), `courses.read`, `scheduling.read`, `faculty_performance_kpis.read`.

## Модуль / Backend API
`faculty`, `grades`, `courses`, `scheduling`, `faculty_copilot`, `faculty_performance_kpis`. API `/api/admin/*` с ABAC (инструктор — свои курсы/студенты).

## Runtime Shell
Нет выделенного; faculty‑copilot как AI‑ассистент.

## Компоненты / Таблицы
Shared UI. Таблицы: `university_faculty`, `university_courses`, grades, `office_hours_records`, `university_faculty_performance_kpis`.

## Зрелость / Проблемы
По `README.md` — **не полный production‑journey**. Рекомендация: развить faculty‑портал.
