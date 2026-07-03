# Кластер таблиц: Alert / Risk (раннее предупреждение)

[← Каталог таблиц](README.md) · Brain: [../brains/brain-core.md](../brains/brain-core.md)

~40 таблиц вида `*_alerts` / `*_risk_alerts` — материализация раннего предупреждения. Питают Brain Core сигналы и Runtime Shell safety‑секции.

## Примеры (по доменам)

| Домен | Alert‑таблицы |
|-------|---------------|
| Academic | `university_academic_withdrawal_alerts`, `university_advising_support_alerts`, `university_advising_no_show_risk_alerts`, `university_program_sunset_alerts`, `university_course_retirement_alerts` |
| Student services | `university_student_service_sla_alerts`, `university_student_service_unresolved_alerts`, `university_housing_maintenance_risk_alerts` |
| Financial aid / finance | `university_financial_aid_disbursement_risk_alerts`, `university_delinquency_legal_escalation_alerts`, `finance_expense_budget_exceeded_alerts`, `budget_overrun_alerts`, `payment_failure_alerts` |
| Career / alumni | `university_career_stalled_opportunity_alerts`, `university_alumni_disengagement_risk_alerts` |
| Faculty / HR | `university_faculty_kpi_low_performance_alerts`, `university_faculty_contract_termination_alerts`, `university_hr_offboarding_alerts`, `university_hr_payroll_cycle_risk_alerts` |
| Facilities / asset / procurement | `university_facilities_overdue_work_order_alerts`, `university_asset_condemned_risk_alerts`, `university_procurement_risk_alerts` |
| Student life | `university_student_life_alert_records`, `university_student_life_disciplinary_escalation_alerts` |
| Research / ethics | `university_research_grant_delay_alerts`, `ethics_alert_records` |
| Accreditation / thesis | `accreditation_risk_alerts`, `thesis_overdue_alerts`, `thesis_rejection_risk_alerts` |
| Campus / SLA / transport / dining | `campus_sla_breach_risk_alerts`, `dining_capacity_alert_records` |
| Integrity / exams / equipment / scholarship | `integrity_escalation_alerts`, `exam_proctoring_alerts`, `equipment_booking_overdue_alerts`, `scholarship_revocation_alerts` |
| Cohort | `university_cohort_risk_snapshots`, `university_auto_triggered_interventions`, `attendance_risk_records` |

## Общие поля (типовые)
`tenant_id` (FK), `alert_status` (pending/acknowledged/resolved/critical), `alert_level` (low/medium/high/critical), `created_at`, метаданные (JSONB).

## Роль
Промежуточный слой между доменными событиями и Brain Core: событие риска → alert‑запись → сигнал Brain → решение (human‑gated) → интервенция/уведомление.
