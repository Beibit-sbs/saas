# 06 — Полный аудит Runtime Shells

[← 05 API](05_API.md) · [Индекс](README.md) · Далее: [07 Brain‑модули →](07_BRAIN_MODULES.md)

Отдельные файлы по каждому Runtime Shell: [runtime_shells/README.md](runtime_shells/README.md).

---

## 7.1 Что такое Runtime Shell

**Runtime Shell** — специализированный операционный дашборд (frontend) + агрегирующий read‑эндпоинт (backend `runtime_shell_router.py`), который собирает real‑time картину домена из нескольких под‑сервисов и рендерит секции (overview, метрики, safety‑gates, риски, интервенции). Фронтовый компонент тянет данные через `getRuntimeShell()`.

Это «витрина» Brain‑вертикали: над доменными данными показывается агрегированное состояние + сигналы риска, но **без автономных действий** (safety‑boundary).

---

## 7.2 Реестр Runtime Shells

| # | Runtime Shell | Frontend модуль | Backend | Маршрут |
|---|---------------|-----------------|---------|---------|
| 1 | **Student Success** | `frontend/modules/student-success` | `student_success_runtime` (8 под‑роутеров) | `/console/student-success`, `/…/runtime-shell` |
| 2 | **Academic Operations** | `frontend/modules/academic-operations-runtime` | `academic_operations_runtime` (9 под‑роутеров) | `/console/academic-operations/runtime-shell` |
| 3 | **Executive Governance** | `frontend/modules/executive-governance` | `executive_governance` | `/console/executive-governance` |
| 4 | **Quality Accreditation** | `frontend/modules/quality-accreditation` | `quality_accreditation` (8 под‑роутеров) | `/console/quality-accreditation/runtime-shell` |
| 5 | **Research Brain** | `frontend/modules/research-brain` | `research_science` | `/console/research-brain` |
| 6 | **Reporting Runtime** (Ministry) | `frontend/modules/reporting-runtime` | `reporting_runtime` (8 сервисов) | `/console/reporting-runtime` |
| 7 | **Innovation & Commercialization** | `frontend/modules/innovation-commercialization` | `innovation_commercialization` | `/console/innovation-commercialization` |
| 8 | **Communications** (частично) | `frontend/modules/communications` | `communications` | `/console/communications` |

---

## 7.3 Секции по каждому Shell (сводно)

- **Student Success:** `student_success_overview`, `interventions`, `signals`, `retention_risks`, `safety` (качество данных).
  Под‑роутеры: student_registry, student_retention, student_academic_risk, student_attendance_risk, student_intervention, student_advisor, success_signals, success_dashboard.
- **Academic Operations:** curriculum status, scheduling, enrollment‑метрики, календарь, safety‑gates (metadata‑only, no provider sync).
  Под‑роутеры: academic_registry, assessment, attendance, curriculum, internship, timetable, teaching_load, dashboard, signals.
- **Executive Governance:** стратегические инициативы, KPI, meeting protocols, риски, decision registry, executive assignments.
- **Quality Accreditation:** baseline‑скор аккредитации, комплаенс, evidence, remediation, готовность к отчёту министерству.
  Под‑роутеры: accreditation_evidence, accreditation_registry, audit_findings, corrective_action, dashboard, improvement_plan, readiness_monitoring, self_assessment.
- **Research Brain:** портфель исследований, реестр исследователей, наукометрия, research risk, дашборд.
- **Reporting Runtime:** реестр отчётов, готовность Ministry/NOBD/ranking/regulatory, delivery‑аудит.
- **Innovation & Commercialization:** IP‑портфель, pipeline коммерциализации, лицензии, revenue sharing.
- **Communications:** уведомления, delivery‑аудит, эскалации, предпочтения.

---

## 7.4 Связь Runtime Shell ↔ Brain

Каждый Runtime Shell является пользовательским «окном» соответствующего Brain‑домена (см. [07_BRAIN_MODULES.md](07_BRAIN_MODULES.md)):

| Runtime Shell | Brain‑домен | Основные сигналы |
|---------------|-------------|------------------|
| Student Success | Student Success Brain | `academic.attendance_risk.detected`, `academic.grade_risk.detected`, `enrollments.dropout_risk.detected` |
| Academic Operations | Academic Operations Brain | `faculty.workload_overload.detected`, `scheduling.section.conflict_detected`, `enrollment.capacity_risk.detected` |
| Quality Accreditation | Quality Accreditation Brain | `accreditation.status_changed`, evidence/audit сигналы |
| Research Brain | Research Science Brain | `research.grant_deadline.approaching`, `research.publication_stagnant` |
| Reporting Runtime | Ministry Regulatory Brain | `accreditation.status_changed`, `compliance.review.required` |
| Executive Governance | Executive Governance Brain | высокоуровневые governance‑сигналы всех вертикалей |

---

## 7.5 Permissions

Каждый shell‑эндпоинт защищён permission вида `<domain>.summary.read` (напр. `student_success.summary.read`, `academic_operations.summary.read`). Доступ — доменным `*_admin`‑ролям, `auditor` (read), `rector`/`executive_control_tower` (агрегаты).

---

## 7.6 Проблемы (аудит)

- **Дубли runtime‑пакетов:** `academic_operations` vs `academic_operations_runtime`, `student_success_analytics` vs `student_success_runtime`.
- **Communications shell** — частичный (по инвентарю V15: 0 выделенных backend‑тестов на момент фиксации).
- **Safety‑gates** в ряде shell'ов — metadata‑only индикаторы (нет живой синхронизации с провайдерами), что честно помечено в UI (`boundaryLabels.ts`).
