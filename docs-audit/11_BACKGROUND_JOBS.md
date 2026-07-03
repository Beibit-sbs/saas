# 11 — Полный аудит Background Jobs (Cron / Jobs / Tasks / Events)

[← 10 Feature Flags](10_FEATURE_FLAGS.md) · [Индекс](README.md) · Далее: [12 Статистика →](12_PROJECT_STATISTICS.md)

Источники: `app/platform/jobs/scheduler.py`, `app/modules/jobs/`, `app/platform/events/`, `app/modules/brain_core/early_warning_sweep.py`, `app/platform/runtime_state.py`.

---

## 12.1 Планировщик

- **Реализация:** кастомный `PlatformWorkerScheduler` (**НЕ Celery, НЕ APScheduler**).
- **Модель:** thread‑based, `threading.Lock` для регистрации задач; polling ~5 сек; `run_due_tasks_once()` вызывается повторно; выполнение задач последовательное.
- **Наблюдаемость:** `observe_job_execution(outcome=success|failed)`, heartbeat через `record_scheduler_run(task_name)`; `get_worker_heartbeat()` / `get_scheduler_last_run()` для ops‑дашборда.

---

## 12.2 Периодические задачи (cron, 9)

| Задача | Интервал | Назначение |
|--------|----------|-----------|
| `daily_usage_aggregation` | 24ч | `worker.run_once()` — периодическая обработка |
| `subscription_rollover` | 1ч | `SubscriptionRolloverService.run_rollover_cycle()` |
| `notification_retry_dispatch` | 10м | Ретрай неудачных уведомлений |
| `outbox_event_dispatch` | 1м | Обработка pending‑событий из outbox → webhooks |
| `webhook_retry_dispatch` | 2м | Ретрай неудачных webhook‑доставок (лимит 100/запуск) |
| `kpi_metrics_refresh` | 24ч | `kpi_service.refresh_all_tenants()` |
| `context_rebuild` | 24ч | Перестройка кэша контекста тенантов |
| `academic_risk_detection` | 24ч | `run_daily_detection_for_all_tenants()` (interventions risk) |
| `composite_early_warning_sweep` | 24ч | `run_composite_early_warning_sweep()` (Brain early warning) |

---

## 12.3 Jobs‑очередь (модульная)

`app/modules/jobs/service.py`: статусы `queued/running/succeeded/failed/cancelled`; до 3 ретраев; fallback in‑memory (`JobsMemoryState`) при недоступности БД. API: `/api/admin/jobs` (list/run/retry). UI: `/console/jobs`.

---

## 12.4 Brain‑sweeps (batch)

- **`composite_early_warning_sweep`** — ночной composite‑risk по всем студентам тенанта; score > 55 → Brain signal path; идемпотентно, fail‑closed, изоляция по тенанту.
- **`academic_risk_detection`** — ежедневное детектирование академ‑риска (interventions).

---

## 12.5 События (сводно по доменам)

`EXACT_EVENT_REGISTRY` — **232** типа. Группы (примеры):

| Домен | Примеры |
|-------|---------|
| Core | `tenant.created`, `user.created`, `role.assigned`, `enrollment.created`, `grade.submitted`, `ai.chat.executed` |
| Admissions | `admissions.application.{submitted,stage_changed,decision_made,workflow_decision_finalized}` |
| Academic risk | `academic.{attendance_risk,grade_risk}.detected`, `finance.payment_overdue.detected`, `faculty.{workload_overload,quality_drop}.detected`, `thesis.status_changed` |
| Academic integrity | `academic_integrity.{violation,risk}.detected`, `plagiarism.*`, `exam.proctoring.violation_detected`, `academic_integrity.case.*` |
| Exam proctoring | `exam.proctoring.{suspicious_activity,multiple_faces,face_mismatch,forbidden_app,camera_absent}_detected` |
| Thesis/governance | `thesis.{submission.*,supervisor.*,review.delayed,governance.risk_detected}` |
| Research ethics | `research_ethics.{application.submitted,review.*,missing_consent.detected,conflict_of_interest.detected}` |
| Procurement/asset | `procurement.{request_created,submitted,approval_required,approved,po_issued,delivered,asset_created}`, `inventory.{low_stock.detected,reorder_needed}` |
| Budget | `budget_plan.{created,review_requested,approved,locked,rejected}` |
| Scheduling | `scheduling.section.{created,scheduled,rescheduled,cancelled}`, `scheduling.room_allocation.*`, `enrollment.capacity_risk.detected` |
| Timetable | `scheduling.timetable_{proposal,simulation,approval}.*` |
| Teaching/LMS | `teaching_quality.*`, `lms.{lesson.completed,assignment.submitted,grade.posted}` |
| Equipment | `equipment_booking.booking.{created,confirmed,cancelled,returned,overdue}` |
| HR | `hr.{personnel_order.*,employee.offboarding_initiated,anomaly_detected}` |
| Interventions | `interventions.{case.*,case_outcome.recorded,cohort.analyzed,auto_triggered}` |
| Library | `library.{book.*,reservation.cancelled,item.overdue,fine.calculated}` |
| Attendance | `attendance.{record.marked,absence.*,threshold.breached}` |
| Payments | `payment.{initiated,completed,failed,refunded,failure_pattern}` |
| Events/rooms | `event.*`, `booking.{approved,conflict_detected}`, `room.released` |
| Visitor/access | `visitor.*`, `security.incident.*`, `access.{granted,denied}`, `card.*` |
| Parking | `parking.{permit_issued,violation_recorded,lot_full,capacity_risk}` |
| Publications | `publication.*`, `patent.*`, `conference.*` |
| Auth/security | `twofa.*`, `sso.*` |
| Counseling | `counseling.{appointment_requested,session_completed,high_risk_case_opened,crisis_reported}` |
| Прочие | `blockchain_diploma.*`, `parent_portal.*`, `alumni_donation.*`, `localization.*`, `mobile.*`, `id_card.*` |

Плюс prefix‑реестр (`campus.*`, `automation.*`, и др.) для динамических событий.

---

## 12.6 Проблемы (аудит)

- **Единая точка отказа планировщика:** кастомный in‑memory планировщик, последовательное выполнение — при остановке процесса теряется расписание до перезапуска (heartbeat это отслеживает).
- Нет распределённого брокера очередей (Redis/Celery) — масштабирование фоновых задач ограничено.
- Разночтение количества событий между документами (232 exact в реестре vs 260 в историческом `SBS_UB_PROJECT_CONTEXT_2026.md`) — приведены оба.
