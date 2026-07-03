# Модуль: Student Success (Успех студента)

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `backend/app/modules/student_success_runtime/`, `student_success_analytics/`, `interventions/`, `student_risk_signal_registry/`
Frontend: `frontend/modules/student-success/`, `frontend/modules/interventions/`
Вертикаль: **V02/Student Success** · Brain: [Student Success Brain](../brains/student-success.md)

## Назначение
Раннее выявление рисков студентов (посещаемость, успеваемость, удержание, wellbeing) и управление интервенциями до негативного исхода.

## Бизнес‑функции
Реестр студентов · retention‑риски · academic/attendance risk · intervention‑кейсы и playbooks · advisor‑рекомендации · сигналы · дашборд успеха.

## Пользователи (роли)
advisor, faculty, `student_lifecycle_admin`, student success team; `auditor`.

## Страницы / Runtime Shell / Dashboard
- `/console/student-success/*` (~11: interventions, cohorts, signals, dashboard, runtime-shell, attendance-risk, academic-risk, advisors, student-registry, student-retention).
- `/console/interventions/*` (playbooks, executions, cohorts, create-cohort).
- **Runtime Shell:** `StudentSuccessRuntimeShellPage` → `/api/v1/student-success/runtime-shell`.
- **Dashboard:** `student_success_dashboard_runtime`.

## Backend
- **Router:** `student_success_runtime/runtime_shell_router.py` + 8 под‑роутеров (student_registry, student_retention, student_academic_risk, student_attendance_risk, student_intervention, student_advisor, success_signals, success_dashboard). `interventions/router.py` + playbook/risk/effectiveness роутеры.
- **Services/Models/DTO:** по каждому под‑домену; `interventions/models.py`.

## Database
`university_cohort_risk_snapshots`, `university_auto_triggered_interventions`, intervention‑кейсы, `attendance_risk_records`. Alert‑таблицы риска.

## API
`/api/v1/student-success` (runtime), `/api/admin/student-success`, `/api/admin/interventions/*`. Permission `student_success.summary.read`.

## Связанные модули
`attendance`, `grades`, `enrollments`, `advising`, `student_lifecycle`, `counseling`, `brain_core`.

## Workflow
Раннее предупреждение → интервенция ([../08_WORKFLOWS.md](../08_WORKFLOWS.md) §9.3).

## Brain / AI
Brain‑вертикаль Student Success. Сигналы `academic.attendance_risk.detected`, `academic.grade_risk.detected`, `enrollments.dropout_risk.detected`, `student_life.wellbeing.at_risk`; решения `student_risk`, `student_support_bridge`, `advanced_student_life`, `enrollment_dropout_risk`. Reasoning: composite risk scorer. Сигнальный реестр `student_risk_signal_registry` (UCE‑049).

## Background Jobs
`composite_early_warning_sweep` (24ч, score>55 → Brain), `academic_risk_detection` (24ч).

## Feature Flags
`early_warning_auto_intervention` (вероятный).

## Проблемы / Рекомендации
- Дубль `student_success_runtime` vs `student_success_analytics`. **Рекомендация:** консолидировать; закрыть тест‑долг по advisor/attendance‑risk путям.
