# Модуль: Student Lifecycle (Жизненный цикл студента)

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `backend/app/modules/student_lifecycle/`, `backend/app/modules/students/`, `backend/app/modules/student_portal/`
Frontend: `frontend/modules/student-lifecycle/`
Вертикаль: **V02 Student Lifecycle** · Runtime‑дерево A‑055

## Назначение
Сквозной жизненный цикл студента: абитуриент → студент → зачисление → обучение → выпуск → alumni, включая финансовый мост и hardship‑поддержку.

## Бизнес‑функции
Регистрация абитуриентов/студентов · зачисление и review · апелляции · прикрепление доказательств (evidence) · переходы статусов (в т.ч. graduated/alumni) · финансовый мост студента.

## Пользователи (роли)
`student_lifecycle_admin`, `registrar`, finance officer; `student` (read своего); `auditor`.

## Основной функционал
CRUD абитуриентов/студентов · enrollment.create/read/review · appeals.create/review · evidence.attach · audit.read.

## Страницы / Маршруты / Runtime Shell
- `/console/student-lifecycle` (+ связанные `/console/enrollments`, `/console/degree-progress`, `/console/alumni`).
- Дерево A‑055 (см. отчёты `A-055.*`) реализует пошаговые runtime‑shell'ы (attendance selector, grade entry selector, transcript/GPA readiness, degree progress, graduation eligibility, alumni engagement, finance bridge, hardship).

## Backend
- **Router:** `student_lifecycle/router.py` (`/api/admin/student-lifecycle`).
- **Services:** `service.py`. **Models:** `models.py` (`student_lifecycle_*`). **DTO:** `schemas.py`. **Permissions:** `permissions.py` (50+).

## Database
`student_lifecycle_*`; читает `university_students`, `university_enrollments`, `university_academic_records`, `university_alumni_records`. FK на `app_tenants`.

## API
Префикс `/api/admin/student-lifecycle`. Permissions `student_lifecycle.applicants.*`, `students.*`, `enrollment.*`, `appeals.*`, `evidence.attach`, `audit.read`.

## Связанные модули
`admissions`, `students`, `enrollments`, `grades`, `transcripts`, `degree_progress`, `alumni`, `student_financial_hardship`, `student_services_support`, `finance_procurement_asset` (student‑finance bridge), `brain_core`.

## Workflow
Академический жизненный цикл ([../08_WORKFLOWS.md](../08_WORKFLOWS.md) §9.2) + hardship/referral‑цепочки (`A-055.20…31`).

## Brain / AI
Сигналы `enrollments.dropout_risk.detected`, `degree_progress.graduation_risk.detected`; решения `student_risk`, `enrollment_dropout_risk`, `graduation_degree_progress_risk`, `student_support_bridge`. AI — через Brain.

## Интеграции / Jobs / Flags
События в Brain/KPI. Jobs: `composite_early_warning_sweep`, `academic_risk_detection`. Флаги: динамические.

## Проблемы / Рекомендации
- Пересечение с `students`/`student_portal`. **Рекомендация:** зафиксировать границы владения данными студента; довести A‑055 дерево до полного E2E.
