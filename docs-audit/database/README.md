# Каталог таблиц базы данных

[← Индекс аудита](../README.md) · Верхнеуровневый обзор: [../04_DATABASE.md](../04_DATABASE.md)

~250+ таблиц: **211** из реестра `EntityConfig` (`university_core/shared.py`) + ORM‑специфичные (platform/audit/jobs/billing/workflows). ~95% tenant‑scoped (`tenant_id` FK → `app_tenants`).

## Кластерные файлы

| Кластер | Файл |
|---------|------|
| University Core (студенты, ППС, программы, курсы, зачисления) | [university-core-tables.md](university-core-tables.md) |
| Brain Core | [brain-tables.md](brain-tables.md) |
| Platform / Auth / Billing | [platform-tables.md](platform-tables.md) |
| Alert / Risk (раннее предупреждение) | [alert-tables.md](alert-tables.md) |

## Формат (для таблицы)
Название · Описание · Модуль · Поля · Связи · FK · PK · Используется в · CRUD.

> Поштучные файлы на каждую из ~250 таблиц не создавались; таблицы каталогизированы по доменам ниже и по кластерам. Точная схема — в `models.py` модулей и `EntityConfig` (`shared.py`).

## Полный перечень EntityConfig по доменам

### University Core
`university_students`, `university_faculty`, `university_faculty_contracts`, `university_faculty_contract_termination_alerts`, `university_programs`, `university_program_sunset_alerts`, `university_courses`, `university_course_retirement_alerts`, `university_course_prerequisites`.

### Academic Lifecycle
`university_enrollments`, `university_academic_records`, `university_academic_withdrawal_alerts`, `university_advising_sessions`, `university_advising_support_alerts`, `university_advising_no_show_risk_alerts`.

### Student Services
`university_student_service_tickets`, `university_career_opportunities`, `university_career_placement_records`, `university_career_stalled_opportunity_alerts`, `university_financial_aid_records`, `university_financial_aid_disbursements`, `university_financial_aid_disbursement_watches`, `university_financial_aid_disbursement_risk_alerts`, `university_student_service_sla_alerts`, `university_student_service_unresolved_alerts`, `university_housing_requests`, `university_room_assignment_records`, `university_housing_maintenance_risk_alerts`.

### Alumni
`university_alumni_records`, `university_alumni_engagement_events`, `university_alumni_disengagement_risk_alerts`.

### Research / IP
`university_research_grants`, `university_research_grant_delay_alerts`, `university_research_publications`, `university_publication_review_records`, `university_research_labs`, `university_research_ip_assets`, `university_research_experiments`, `patents`, `ip_assets`, `ip_licensing_records`, `publications`, `citations`, `conferences`, `conference_papers`.

### Faculty / HR
`university_faculty_performance_kpis`, `university_faculty_kpi_low_performance_alerts`, `university_hr_employees`, `university_hr_offboarding_alerts`, `university_hr_payroll_cycles`, `university_hr_payroll_cycle_risk_alerts`, `hr_contracts`, `university_personnel_orders`.

### Finance / Collections
`university_delinquency_records`, `university_collections_agent_records`, `university_delinquency_legal_escalation_alerts`, `finance_expense_policy_review_records`, `finance_expense_budget_exceeded_alerts`, `budget_plans`, `budget_allocations`, `budget_overrun_alerts`, `expense_records`, `cost_centers`.

### Facilities / Operations / Procurement
`university_facilities_sla_assignment_records`, `university_facilities_work_orders`, `university_facilities_maintenance_requests`, `university_facilities_overdue_work_order_alerts`, `university_asset_inventory_items`, `university_asset_depreciation_records`, `university_asset_writeoff_records`, `university_asset_condemned_risk_alerts`, `university_operations_facility_issues`, `university_operations_work_orders`, `university_operations_dispatch_records`, `university_operations_cleaning_checks`, `university_operations_room_readiness`, `university_operations_maintenance_assets`, `university_operations_utility_readings`, `university_procurement_vendors`, `university_procurement_contracts`, `university_procurement_assets`, `university_procurement_inventory_items`, `university_procurement_risk_alerts`.

### Student Life / Counseling / Disciplinary
`university_student_life_counseling_cases`, `university_student_life_alert_records`, `university_student_life_wellbeing_checkins`, `university_student_life_accessibility_supports`, `university_student_life_disciplinary_cases`, `university_student_life_disciplinary_escalation_alerts`, `counseling_appointments`, `counseling_cases`, `crisis_reports`.

### Teaching / Ethics / Equipment / Action Logs
`university_teaching_quality_records`, `university_teaching_quality_action_logs`, `university_research_ethics_action_logs`, `university_equipment_booking_action_logs`, `university_ip_asset_action_logs`, `university_scheduling_section_action_logs`, `university_scheduling_section_outcomes`, `university_syllabus_approval_outcomes`.

### Cohort / Intervention
`university_cohort_risk_snapshots`, `university_auto_triggered_interventions`.

### Library
`library_items`, `library_loans`, `library_reservations`, `library_returns`, `library_fines`, `library_overdue_records`.

### Attendance / LMS
`attendance_records`, `attendance_sessions`, `attendance_excuses`, `attendance_risk_records`, `lms_courses`, `lms_lessons`, `lms_lesson_progress`, `lms_submissions`, `lms_grades`, `lms_returned_submissions`, `lms_risk_records`.

### Online Payments
`payment_orders`, `payment_transactions`, `payment_failures`, `payment_refunds`, `payment_processing_log`, `payment_failure_alerts`.

### Feedback / Internship
`feedback_forms`, `feedback_responses`, `feedback_analytics`, `internship_postings`, `internship_applications`, `internship_interviews`, `internship_contracts`.

### Campus (events/rooms/visitor/parking)
`campus_events`, `event_registrations`, `campus_rooms`, `room_bookings`, `visit_requests`, `visit_logs`, `access_cards`, `access_logs`, `parking_lots`, `parking_permits`, `parking_sessions`, `parking_violations`.

### AI / Tutoring
`tutor_sessions`* , `scan_requests`* , `model_eval_runs`, `prompt_templates`, `admissions_scorings`* (`*` = TEST_ONLY_DB_TABLES).

### Security / Transport / Dining / SLA / Ethics
`security_incidents`, `security_incident_escalation_records`, `security_visitors`, `transport_routes`, `transport_bookings`, `transport_disruption_records`, `dining_menus`, `dining_orders`, `dining_capacity_alert_records`, `campus_sla_records`, `campus_sla_breach_risk_alerts`, `ethics_reviews`, `ethics_alert_records`.

### Integrity / Equipment / Scholarships / Communications
`integrity_case`, `integrity_escalation_alerts`, `equipment_items`, `equipment_bookings`, `equipment_booking_overdue_alerts`, `scholarship_applications`, `scholarship_awards`, `scholarship_revocation_alerts`, `communication_messages`, `communication_broadcast_audits`, `communication_broadcast_risk_alerts`.

### Accreditation / Thesis / Syllabi / Exams
`accreditation_records`, `accreditation_risk_alerts`, `thesis_records`, `thesis_overdue_alerts`, `thesis_rejection_risk_alerts`, `syllabi`, `syllabus_review_backlogs`, `syllabus_approval_workflows`, `syllabus_approval_actions`, `exams`, `exam_proctoring_alerts`, `proctoring_sessions`, `proctoring_violations`, `proctoring_records`.

### Auth / Security
`twofa_enrollments`, `twofa_challenges`, `saml_identity_providers`, `saml_sessions`, `saml_attribute_mappings`, `office_hours_records`.

### Misc
`digital_documents`, `certificates`, `student_id_cards`, `card_scans`, `device_tokens`, `push_notifications`.

> Плюс ~120 дополнительных сущностей специализированных доменов и alert‑систем (см. `shared.py`).
