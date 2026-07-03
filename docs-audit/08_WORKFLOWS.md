# 08 — Полный аудит Workflow (бизнес‑процессы)

[← 07 Brain‑модули](07_BRAIN_MODULES.md) · [Индекс](README.md) · Далее: [09 Интеграции →](09_INTEGRATIONS.md)

Формат для каждого процесса: начало → шаги → переходы → страницы → API → таблицы → роли.
Движок workflow: `app/modules/workflows/` (`app_workflow_definitions/versions/triggers/steps/assignees/execution_histories`; enum см. [04_DATABASE.md](04_DATABASE.md) §5.5).

---

## 9.1 Приём и зачисление (Admissions)

- **Начало:** создание абитуриента/заявления в `/console/admissions`.
- **Шаги:** applicant → application → этапы (stage history, append‑only) → документы → скоринг (`ai_admissions_scoring`) → решение.
- **Переходы:** `submit` → событие `admissions.application.submitted`; `stage` → `admissions.application.stage_changed`; `decision` → `admissions.application.decision_made` / `workflow_decision_finalized`.
- **Страницы:** `/console/admissions/*` (applications, applicants, leads, workflows, dashboard, audit, settings), `/console/admissions-crm`.
- **API:** `/api/admin/admissions/*`, `/api/admin/admissions-crm/*`.
- **Таблицы:** `ApplicantModel`, `ApplicationModel`, `ApplicationDocumentModel`, `ApplicationStageHistoryModel`, `ApplicationDecisionModel`, `admissions_scorings` (test‑only), `admissions_crm_*`.
- **Роли:** `student_lifecycle_admin`/admissions‑admin, registrar; auditor (read).
- **Brain:** decision `enrollment_dropout_risk`, `admissions.*` сигналы.

## 9.2 Академический жизненный цикл (runtime‑дерево A‑055)

- **Начало:** онбординг tenant‑admin (`/console/platform`) → оргструктура (`/console/org-units`).
- **Шаги:** программы/курсы → зачисление студента → секции/расписание → создание занятий (lessons) → посещаемость → ввод оценок → шкала оценивания → транскрипт/GPA → прогресс по программе → проверка права на выпуск → статус «выпущен» → alumni → финансовый мост студента → receivables → hardship‑поддержка → referral в финансовый офис.
- **Переходы:** событийные (`enrollment.created`, `grade.submitted`, `degree_progress.graduation_risk.detected`, …) + guard'ы (нельзя оценки без посещаемости; нельзя транскрипт без submitted‑оценок).
- **Страницы:** `/console/enrollments`, `/console/scheduling`, `/console/grades`, `/console/transcripts`, `/console/degree-progress`, `/console/alumni`, `/console/finance-procurement-asset/student-finance`.
- **API:** соответствующие `/api/admin/*` + runtime `/api/admin/academic-operations/*`.
- **Роли:** registrar, faculty, `academic_operations_admin`, finance officer, student (read своего).

## 9.3 Раннее предупреждение → интервенция

- **Начало:** доменное событие риска (посещаемость/оценки/финансы/wellbeing) или ночной `composite_early_warning_sweep`.
- **Шаги:** сигнал → Brain context → classify (risk) → reason (composite score) → policy guard → action plan → `create_intervention_case` → notify advisor/faculty → отслеживание исхода → learning.
- **Страницы:** `/console/student-success/*`, `/console/interventions/*` (playbooks, executions, cohorts).
- **API:** `/api/admin/interventions/*`, `/api/admin/student-success`, `/api/admin/brain`.
- **Таблицы:** `university_cohort_risk_snapshots`, `university_auto_triggered_interventions`, intervention‑кейсы, `attendance_risk_records`.
- **Роли:** advisor, faculty, `student_lifecycle_admin`, student success team.

## 9.4 Human‑Approved изменение расписания

- **Начало:** предложение изменения (`timetable_change_proposal`).
- **Шаги:** proposal → симуляция what‑if (`timetable_change_simulation`) → мост рекомендаций аудиторий (`timetable_recommendation_bridge`) → очередь утверждения (`timetable_approval_queue`) → **решение человека** → ручное применение.
- **Переходы:** DRAFT → PENDING_HUMAN_REVIEW → HUMAN_APPROVED / HUMAN_REJECTED / CANCELLED. Запрещены AUTO_APPLY/AUTO_OPTIMIZE.
- **Страницы:** `/console/academic-operations/timetable`, `/console/my-assignments`.
- **API:** `/api/admin/human-approved-timetable-workflow`, `/api/admin/timetable-approval-queue`, `/api/admin/timetable-change-proposal`, `/api/admin/timetable-change-kpi-dashboard`.
- **Роли:** `academic_operations_admin`, scheduling office, утверждающий (human reviewer).
- **Brain:** decision `section_conflict`, `room_allocation_recommendation`.

## 9.5 Финансы: закупка → PO → поставка → актив

- **Начало:** заявка на закупку (`procurement`, `procurement_approval_workflow`).
- **Шаги:** request → approval → PO issued → delivered → asset created → инвентаризация.
- **Переходы:** `procurement.request_submitted` → `approval_required` → `approved` → `po_issued` → `delivered` → `asset_created`.
- **Страницы:** `/console/finance-procurement-asset/*` (purchase-orders, purchase-requests, procurement-reviews, providers, assets…).
- **API:** `/api/admin/finance-procurement-asset/*`, `/api/admin/procurement`.
- **Таблицы:** `university_procurement_*`, `university_asset_inventory_items`, `university_asset_depreciation_records`.
- **Роли:** `finance_procurement_asset_admin`, finance officer.
- **Brain:** `procurement_approval_automation`, `procurement_supply_chain`, `inventory_low_stock`, `finance_operations_health`.

## 9.6 Финансовая задолженность (Delinquency)

- **Начало:** `finance.payment_overdue.detected`.
- **Шаги:** обнаружение → collections case → эскалация (юр.) → recovery.
- **Страницы:** `/console/delinquency-collections`.
- **API:** `/api/admin/delinquency-collections`.
- **Таблицы:** `university_delinquency_records`, `university_collections_agent_records`, `university_delinquency_legal_escalation_alerts`.
- **Brain:** `payment_recovery`.

## 9.7 Академическая честность / экзамен‑прокторинг

- **Начало:** `academic_integrity.violation.detected` / `exam.proctoring.violation_detected` / `plagiarism.similarity.high_detected`.
- **Шаги:** open review case → request evidence → mark ready for human decision → close (dismissed/violation, требует одобрения).
- **Страницы:** `/console/academic-integrity`, `/console/exam-proctoring`, `/console/exam-governance`.
- **API:** `/api/admin/academic-integrity`, `/api/admin/exam-governance`.
- **Brain:** `academic_integrity_violation`, `academic_integrity_case_resolution`, `exam_proctoring_violation`.

## 9.8 Исследовательская этика

- **Начало:** `research_ethics.application.submitted`.
- **Шаги:** request ethics review → request missing documents/consent/data‑privacy → escalate to compliance officer.
- **Страницы:** `/console/research-science/*`, `/console/research-ethics`.
- **API:** `/api/admin/research-ethics`, `/api/admin/research-science`.
- **Brain:** `research_ethics_compliance`, `research_innovation`.

## 9.9 Качество/аккредитация

- **Начало:** цикл самооценки / `accreditation.status_changed`.
- **Шаги:** self‑assessment → сбор доказательств (evidence) → audit findings → corrective actions → improvement plan → readiness monitoring → отчёт министерству.
- **Страницы:** `/console/quality-accreditation/*`, `/console/accreditation-compliance`, `/console/reporting-runtime`.
- **API:** `/api/admin/quality-accreditation/*`, `/api/admin/accreditation-compliance`.
- **Brain:** `accreditation_remediation`.

## 9.10 Документы / приказы / корреспонденция

- **Начало:** intake документа / создание приказа (декрета).
- **Шаги:** draft → routing → signature readiness (ЭЦП) → execution control → delivery → archive; SLA‑дедлайны; evidence.
- **Страницы:** `/console/document-decree-correspondence/*` (~20 страниц), `/console/documents/*`.
- **API:** `/api/admin/document-decree-correspondence`, `/api/admin/documents`.
- **Роли:** document‑admin, rector (rector-resolutions), исполнители.

## 9.11 Governance / поручения (Rector Assignment)

- **Начало:** создание поручения ректором (`rector_assignment_workflow`).
- **Шаги:** assignment → исполнитель → SLA/outbox‑уведомления → отчёт → закрытие.
- **Страницы:** `/console/rector-assignments`, `/console/my-assignments`, `/console/executive-control-tower/*`.
- **API:** `/api/admin/rector-assignments`, `/api/admin/executive-control-tower`.
- **Роли:** `rector`, `executive_control_tower`, исполнители.

---

> **Общая модель workflow:** триггер (manual/event/API) → шаги (start/task/approval/gateway/end) → назначенцы (user/role/group/service_account) → история исполнения (`app_workflow_execution_histories`). Критические шаги требуют approval (human gating).
