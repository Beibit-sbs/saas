# Страница‑зона: Портал студента (`/student`)

[← Каталог страниц](README.md)

## URL / Назначение
`/student` (`frontend/app/student/page.tsx`) — самообслуживание студента: расписание, оценки, транскрипт, прогресс по программе, интервенции (read‑only).

## Доступ / Permissions
Аутентифицированный студент (роль `student`). Enforced в `middleware.ts` (gate на `/student/*`). Backend: `enrollments.read`, `profiles.read`, `advising.read` + **ABAC** (только «свои» данные).

## Модуль / Backend API
`student_portal` (backend), `students`, `enrollments`, `grades`, `transcripts`, `degree_progress`. API `/api/admin/*` с ABAC‑ограничением на владельца; `student_portal/service.py` (`build_student_portal_visibility_summary`, `list_requests`).

## Runtime Shell
Нет выделенного; потребляет данные lifecycle/success (read‑only).

## Компоненты / Таблицы
Shared UI. Таблицы: `university_students`, `university_enrollments`, `university_academic_records`, transcripts.

## Зрелость / Проблемы
По `README.md` — **не полный production‑journey** (нет сквозного UX). Рекомендация: развить полноценный студенческий портал.
