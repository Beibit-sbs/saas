# Страница‑зона: Портал регистратора (`/registrar`)

[← Каталог страниц](README.md)

## URL / Назначение
`/registrar` (`frontend/app/registrar/page.tsx`) — офис регистратора: контроль регистрации/зачисления, верификация, выдача транскриптов, аудит.

## Доступ / Permissions
Роль `registrar`/`academic_operations_admin`. Enforced в `middleware.ts`. Backend: `enrollments.*`, `records.*`, `transcripts.*`, `grades.read`.

## Модуль / Backend API
`enrollments`, `academic_records`, `transcripts`, `academic_operations`, `student_lifecycle`. API `/api/admin/enrollments`, `/api/admin/university/records`, `/api/admin/transcripts`.

## Runtime Shell
Может использовать Academic Operations shell для операционного контроля.

## Компоненты / Таблицы
Shared UI, data-table. Таблицы: `university_enrollments`, `university_academic_records`, `app_transcripts`/`app_transcript_items`.

## Зрелость / Проблемы
По `README.md` — начальная ролевая зона (не полный journey). Рекомендация: развить регистраторские флоу.
