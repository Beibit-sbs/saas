# Brain: Student Success

[← Каталог Brain](README.md) · Модуль: [../modules/student-success.md](../modules/student-success.md)

Модуль: `backend/app/modules/student_success_runtime/` · Prefix `/api/v1/student-success`

## Назначение
Brain‑вертикаль раннего выявления рисков студентов и управления интервенциями.

## Функции
Реестр студентов · retention‑риски · academic risk · attendance risk · intervention‑кейсы · advisor‑рекомендации · агрегация сигналов · дашборд.

## Под‑роутеры (8)
`student_registry`, `student_retention`, `student_academic_risk`, `student_attendance_risk`, `student_intervention`, `student_advisor`, `success_signals`, `success_dashboard` + `runtime_shell_router`.

## Входные данные
Сигналы `academic.attendance_risk.detected`, `academic.grade_risk.detected`, `enrollments.dropout_risk.detected`, `student_life.wellbeing.at_risk`; данные attendance/grades/enrollments.

## Выходные данные
Решения `student_risk`, `student_support_bridge`, `advanced_student_life`, `enrollment_dropout_risk`; intervention‑кейсы, уведомления advisor/faculty; retention‑риски; дашборд.

## Reasoning / данные
composite_risk_scorer (score>55 → high‑risk). Таблицы `university_cohort_risk_snapshots`, `university_auto_triggered_interventions`, `attendance_risk_records`. Сигнальный реестр `student_risk_signal_registry` (UCE‑049).

## Связанный Runtime Shell
`StudentSuccessRuntimeShellPage` (`/console/student-success/runtime-shell`), секции: overview, interventions, signals, retention_risks, safety.

## Background Jobs
`composite_early_warning_sweep` (24ч), `academic_risk_detection` (24ч). Human‑gated.
