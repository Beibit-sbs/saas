# Модуль: HR / Staff Governance (Кадры)

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `hr_staff_governance/`, `hr_payroll/`, `employee_records/`, `staff_recruitment/`, `staff_onboarding/`, `staff_exit_offboarding/`, `staff_probation_review/`, `performance_appraisal/`, `faculty_attestation/`, `leave_management/`, `timesheet_management/`, `contracts_hr/`, `disciplinary_case_management/`
Frontend: `frontend/modules/hr-staff-governance/`, `hr-payroll/`
Вертикаль: **V06 HR / Staff Governance**

## Назначение
Управление персоналом: найм, онбординг, аттестация, отпуска, дисциплина, офбординг, payroll, кадровые приказы.

## Бизнес‑функции
Recruitment · onboarding · probation review · performance appraisal / faculty attestation · leave · timesheets · disciplinary cases · offboarding · payroll cycles · personnel orders.

## Пользователи (роли)
HR director / `hr_staff_governance` admin, HR‑специалисты, руководители подразделений; `auditor`.

## Страницы
- `/console/hr-staff-governance/*` (~15: payroll, recruitment, onboarding, offboarding, performance, leave, disciplinary, appeals, training, provider-readiness, policy-exceptions, workload-bridge, staff-profiles, requests, faculty-profile, access-lifecycle, limitations).
- `/console/hr-payroll`.

## Backend
- **Router:** `hr_staff_governance/router.py` + `hr_payroll/router.py`.
- **Permissions:** `hr_staff_governance/permissions.py`.

## Database
`university_hr_employees`, `university_hr_payroll_cycles`, `university_hr_payroll_cycle_risk_alerts`, `university_personnel_orders`, `hr_contracts`, `university_hr_offboarding_alerts`, `university_faculty_performance_kpis`.

## API
`/api/admin/hr-staff-governance`, `/api/admin/hr-payroll`. Permissions `hr_staff_governance.*`.

## Связанные модули
`faculty`, `faculty_performance_kpis`, `workload_management` (bridge), `finance_procurement_asset` (payroll), `access_control` (access lifecycle), `brain_core`.

## Workflow
Найм→онбординг→аттестация→офбординг; кадровые приказы (`hr.personnel_order.*`).

## Brain / AI
Сигналы `hr.employee.offboarding_initiated`, `hr.anomaly_detected`, `campus.hr.{offboarding_risk,payroll_cycle_risk}_detected`. Решения через Brain (уведомления/задачи).

## Интеграции / Jobs / Flags
Интеграции: `hr_payroll_integration` (L2). Jobs: KPI‑refresh. Флаги: динамические.

## Проблемы / Рекомендации
- **Дубль‑семейство:** `hr_staff_governance` vs `hr_payroll`×2 (`hr_payroll`, `hr_payroll_integration`). Рекомендация: консолидировать, реализовать живой payroll‑адаптер.
