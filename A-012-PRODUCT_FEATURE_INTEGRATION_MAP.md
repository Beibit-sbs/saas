# A-012 — PRODUCT FEATURE INTEGRATION MAP

**Date:** 2026-05-04  
**Status:** IN PROGRESS  
**Scope:** Convert SBS UB module base into connected end-to-end product features  
**Next Action:** A-012.1 — Gap analysis + priority ranking

---

## Executive Summary

A-011 security/gate debt closure completed with verdict: **PASS WITH KNOWN DEFERRED INFRA CONDITIONS**.

The SBS UB platform now has a hardened foundation:
- ✅ 15 ACTIVE university_core fallback tables migrated
- ✅ Tenant isolation fail-closed on all critical endpoints (brain_core, billing)
- ✅ KPI metrics suite green (184 tests passed)
- ✅ Audit coverage complete (all module mutations logged)

**A-012 mission:** Transform this foundation into connected, end-to-end product features that deliver visible business value.

**Core principle:** Features must connect ≥2 modules + have frontend UI + create measurable business outcome.

**Mandatory feature groups:** 8 (Student Success, Finance, Academic Ops, Governance, Ministry, Compliance, Procurement, HR, Brain Core)

**Deliverable:** Product feature integration map with 15-25 prioritized features, integration gaps analysis, event map, API/frontend map, brain core decision tree, and recommended build order.

---

## Feature Matrix

### A. STUDENT SUCCESS & RETENTION

#### A-1: Early Warning System (At-Risk Student Detection)

**Feature Name:** Early Warning System  
**Business Problem:** Students at risk of academic failure or withdrawal are not identified early enough for intervention.  
**User Persona:** Academic Advisor, Student Success Coach, Dean of Students  
**Connected Modules:** university_core (enrollments, academic_records), analytics (KPI metrics), brain_core (anomaly detection), audit (advisor actions)  
**Trigger Event:** Daily batch: enrollment + attendance + grade signals analyzed; student falls below risk threshold  
**Brain Core Role:** Anomaly detection + predictive intervention scoring  
**Main Workflow:**
1. Brain Core analyzes student signals (attendance%, GPA, engagement, payment status)
2. Flags high-risk students (score > threshold)
3. Notifies assigned advisor
4. Advisor reviews risk details + recommended actions
5. Advisor initiates intervention (tutoring, meeting, etc.)
6. System tracks intervention outcomes

**Required Backend Endpoints:**
- `GET /api/v1/students/at-risk` (filtered by advisor, tenant)
- `GET /api/v1/students/{student_id}/risk-profile` (full analysis)
- `POST /api/v1/advisors/{advisor_id}/interventions` (create intervention)
- `GET /api/v1/interventions?status=open` (list interventions)
- `POST /api/v1/interventions/{intervention_id}/complete` (mark resolved)

**Required Frontend Screens:**
- At-Risk Dashboard (list, sort by risk score, filter by intervention status)
- Student Risk Profile (detailed signals, advisor notes, intervention history)
- Intervention Workflow (create, update, resolve)

**Required Notifications:**
- Advisor notification when student flagged
- Student notification of intervention (optional opt-in)
- Reminder for overdue intervention follow-ups

**Required Audit Logs:**
- student_risk_flag_created
- advisor_intervention_created / updated / resolved
- advisor_action_taken (time, outcome)

**Required KPI/Dashboard:**
- At-risk student count (by cohort, by risk level)
- Intervention resolution rate (%)
- Student outcome post-intervention (GPA change, retention %)
- Advisor effectiveness (interventions per student, resolution rate)

**Required Tests:**
- Risk scoring logic (unit)
- Advisor notification trigger (integration)
- Intervention CRUD (contract)
- Risk profile details (API response validation)

**Current Readiness:** BACKEND_ONLY (analytics + brain_core + audit + endpoint stubs exist; frontend not started)  
**Priority:** P1 PILOT (core retention feature)

---

#### A-2: Tutoring Assignment & Tracking

**Feature Name:** Tutoring Assignment & Outcome Tracking  
**Business Problem:** At-risk students need tutoring but assignment process is manual; outcomes not tracked against student success.  
**User Persona:** Student, Tutor, Academic Advisor, Retention Manager  
**Connected Modules:** university_core (students, tutor_sessions), billing (tutor cost tracking), analytics (outcome KPIs), audit (session logs)  
**Trigger Event:** Advisor triggers from at-risk student profile OR student self-requests tutoring  
**Brain Core Role:** Match tutor to student (expertise, availability, learning style); predict session effectiveness  
**Main Workflow:**
1. Advisor/student initiates tutoring request (subject, frequency)
2. Brain Core recommends top 3 tutors (match score)
3. Tutor accepts/declines
4. Session scheduled + confirmed
5. Session completed, tutor enters notes + student performance
6. Analytics measure impact on student grade/engagement
7. Feedback loop: tutor rated, brain model improved

**Required Backend Endpoints:**
- `POST /api/v1/tutoring/requests` (initiate)
- `GET /api/v1/tutoring/recommended-tutors?subject=...&student_id=...`
- `POST /api/v1/tutoring/assignments/{tutor_id}/accept`
- `GET /api/v1/tutoring/sessions?tutor_id=...&student_id=...`
- `POST /api/v1/tutoring/sessions/{session_id}/complete` (with notes + grade)
- `GET /api/v1/tutoring/outcomes/{student_id}` (aggregate outcome)

**Required Frontend Screens:**
- Tutoring Request Form (subject, frequency, preferred times)
- Tutor Recommendation List (match score, ratings, availability)
- Session Tracker (upcoming, completed, notes)
- Student Tutoring Impact (grade change, engagement improvement)

**Required Notifications:**
- Tutor notification of assignment request
- Student notification of tutor assignment
- Reminders for upcoming sessions
- Completion confirmation

**Required Audit Logs:**
- tutoring_request_created
- tutor_assignment_accepted / rejected
- session_completed (with tutor notes)
- outcome_analyzed (grade change measurement)

**Required KPI/Dashboard:**
- Tutoring request fulfillment rate (%)
- Session completion rate
- Student grade improvement post-tutoring (%)
- Tutor effectiveness score

**Required Tests:**
- Tutor recommendation logic (unit + integration)
- Session CRUD (contract)
- Outcome calculation (analytics)

**Current Readiness:** PLANNED (sessions table exists; no assignments/recommendations/outcomes logic)  
**Priority:** P2 ENTERPRISE (depends on A-1 maturity)

---

### B. FINANCE & BILLING & DELINQUENCY

#### B-1: Subscription Management & Self-Service

**Feature Name:** Subscription Self-Service Portal  
**Business Problem:** Institutions cannot modify subscription tiers / add seats / manage billing without manual support tickets.  
**User Persona:** Tenant Admin, Finance Manager  
**Connected Modules:** billing (subscriptions, usage), audit (plan changes), notifications (confirmation), rbac (admin.write)  
**Trigger Event:** Admin initiates subscription change (upgrade, downgrade, seat addition)  
**Brain Core Role:** Forecast impact on next bill; recommend plan based on usage trends  
**Main Workflow:**
1. Admin navigates to subscription panel
2. Views current plan, seat count, cost, usage metrics
3. Selects new plan tier or seat count
4. Brain Core shows cost impact + effective date
5. Admin confirms change
6. Billing system applies on next billing cycle
7. Invoice/confirmation sent
8. Audit logged

**Required Backend Endpoints:**
- `GET /api/admin/billing/tenants/{tenant_id}/subscription` (current state)
- `GET /api/admin/billing/plans` (available plans)
- `POST /api/admin/billing/tenants/{tenant_id}/subscription/plan-change` (update plan)
- `POST /api/admin/billing/tenants/{tenant_id}/subscription/seats` (add/remove seats)
- `GET /api/admin/billing/tenants/{tenant_id}/invoice?month=...` (invoice history)

**Required Frontend Screens:**
- Subscription Overview (current plan, seats, costs)
- Plan Selection (available tiers, cost comparison)
- Change Confirmation (cost delta, effective date)
- Invoice History (downloads, payment status)

**Required Notifications:**
- Confirmation of plan change
- Invoice issued notification
- 30-day notice before renewal

**Required Audit Logs:**
- subscription_plan_changed (from → to)
- seats_added / removed
- invoice_generated

**Required KPI/Dashboard:**
- Plan distribution across tenants
- Usage vs. plan limits
- Churn risk (inactive tenants, low usage)
- Revenue by plan tier

**Required Tests:**
- Plan change calculation (contract)
- Billing cycle impact (integration)
- Tenant isolation (cross-tenant test)

**Current Readiness:** PARTIAL (endpoints exist; self-service UI not started)  
**Priority:** P1 PILOT (high customer satisfaction impact)

---

#### B-2: Delinquency Detection & Recovery Workflow

**Feature Name:** Delinquency Detection & Recovery Workflow  
**Business Problem:** Payment delays are not detected early; recovery process is manual and inconsistent.  
**User Persona:** Finance Manager, Collections Officer, Tenant Admin  
**Connected Modules:** billing (usage, subscriptions, delinquency), notifications (escalation), audit (actions), brain_core (risk scoring)  
**Trigger Event:** Invoice unpaid past due date threshold OR usage exceeds contract limits without payment  
**Brain Core Role:** Delinquency risk scoring + churn prediction + recovery action recommendation  
**Main Workflow:**
1. Daily batch: invoice aging analysis
2. Brain Core scores delinquency risk (payment history, usage, contract terms)
3. Escalation policy triggered (reminder → notice → service restriction)
4. Notifications sent to tenant admin + finance contact
5. Finance officer can manually override, apply credits, negotiate payment plan
6. Resolution tracked; churn risk monitored
7. Audit log captures all actions

**Required Backend Endpoints:**
- `GET /api/admin/billing/delinquency` (list at-risk tenants)
- `GET /api/admin/billing/tenants/{tenant_id}/delinquency` (full details)
- `POST /api/admin/billing/tenants/{tenant_id}/delinquency/{record_id}/reminder` (send reminder)
- `POST /api/admin/billing/tenants/{tenant_id}/delinquency/{record_id}/escalate` (apply escalation)
- `POST /api/admin/billing/tenants/{tenant_id}/delinquency/{record_id}/resolve` (mark resolved)
- `PUT /api/admin/billing/tenants/{tenant_id}/delinquency/policy` (update escalation policy)

**Required Frontend Screens:**
- Delinquency Dashboard (list by risk level, action status)
- Delinquency Details (payment history, usage, contact info)
- Recovery Action Panel (send reminder, escalate, apply credit, negotiate)
- Escalation Policy Editor (thresholds, notification templates)

**Required Notifications:**
- Tenant notification of delinquent invoice
- Finance notification of escalation triggers
- Tenant notification of service restriction warning

**Required Audit Logs:**
- invoice_delinquent_flagged
- delinquency_reminder_sent
- delinquency_escalated (action type, reason)
- delinquency_resolved (outcome)

**Required KPI/Dashboard:**
- Delinquency rate (% of active invoices overdue)
- Days sales outstanding (DSO)
- Recovery rate (% resolved within 30/60/90 days)
- Churn due to delinquency (%)

**Required Tests:**
- Risk scoring logic (unit)
- Escalation policy execution (integration)
- Notification triggers (contract)
- Recovery tracking (analytics)

**Current Readiness:** PARTIAL (delinquency module exists; recovery workflow logic partial; frontend in progress)  
**Priority:** P0 DEMO (critical for revenue protection)

---

### C. ACADEMIC OPERATIONS

#### C-1: Course Scheduling & Enrollment Workflow

**Feature Name:** Course Scheduling & Enrollment Management  
**Business Problem:** Course schedules are created manually; enrollment validation is loose; conflicts not detected.  
**User Persona:** Registrar, Department Head, Student, Instructor  
**Connected Modules:** university_core (courses, enrollments, schedules), rbac (registrar role), audit (changes), notifications (enrollment confirmation)  
**Trigger Event:** Registrar publishes course schedule OR student initiates enrollment  
**Brain Core Role:** Conflict detection (room double-booking, student schedule conflicts); recommendation (prerequisite validation, load balancing)  
**Main Workflow:**
1. Registrar defines courses (title, instructor, seats, meeting times, room)
2. Brain Core validates schedule (room availability, instructor availability)
3. Course published to student portal
4. Student enrolls (Brain Core checks prerequisites, detects conflicts)
5. Enrollment confirmed; both parties notified
6. Registrar can modify schedule (with conflict resolution)
7. All changes logged

**Required Backend Endpoints:**
- `POST /api/v1/courses` (create course)
- `PUT /api/v1/courses/{course_id}` (update schedule)
- `GET /api/v1/courses?semester=...&department=...` (list)
- `POST /api/v1/enrollments` (student enrolls)
- `GET /api/v1/students/{student_id}/enrollments` (my schedule)
- `GET /api/v1/courses/{course_id}/conflicts` (check conflicts)

**Required Frontend Screens:**
- Course Schedule Builder (create, edit, conflict detection)
- Student Course Catalog (browse, view prerequisites, check conflicts)
- Enrollment Confirmation (show schedule, confirm, add to calendar)
- My Schedule (view all enrollments, drop course, print schedule)

**Required Notifications:**
- Course published notification
- Enrollment confirmation
- Conflict warning (if student tries to double-book)
- Schedule change notification (if instructor/room changes)

**Required Audit Logs:**
- course_created / updated / deleted
- enrollment_created / dropped
- conflict_detected (type, resolution)
- schedule_conflict_resolved

**Required KPI/Dashboard:**
- Enrollment by course (vs. capacity)
- Student schedule conflicts detected/resolved
- Course utilization rate
- Prerequisite violation rate

**Required Tests:**
- Conflict detection logic (unit)
- Enrollment validation (contract)
- Schedule change impact (integration)

**Current Readiness:** BACKEND_ONLY (tables exist; logic partially implemented; frontend not started)  
**Priority:** P1 PILOT (core operational feature)

---

#### C-2: Grade Management & Transcript Generation

**Feature Name:** Grade Management & Transcript System  
**Business Problem:** Grades are entered manually; transcripts are generated off-system; no audit trail.  
**User Persona:** Instructor, Student, Registrar, Ministry (compliance reporting)  
**Connected Modules:** university_core (academic_records, lms_grades, enrollments), audit (grade changes), notifications (grades posted)  
**Trigger Event:** Instructor submits final grades OR student requests transcript  
**Brain Core Role:** Grade anomaly detection (unusual patterns); academic standing prediction  
**Main Workflow:**
1. Instructor inputs grades (via portal or API batch upload)
2. Brain Core validates (no impossible grades, outlier detection)
3. Registrar reviews/approves grades
4. Grades posted; student notified
5. Student can view grades, GPA impact
6. Transcript requested by student/external party
7. Registrar generates official transcript
8. All changes logged with timestamps + approver

**Required Backend Endpoints:**
- `POST /api/v1/courses/{course_id}/grades` (instructor submits)
- `GET /api/v1/courses/{course_id}/grades` (registrar review)
- `PUT /api/v1/academic-records/{record_id}/grade` (approve)
- `GET /api/v1/students/{student_id}/transcript` (generate)
- `GET /api/v1/students/{student_id}/gpa` (current GPA)
- `GET /api/v1/students/{student_id}/academic-standing` (good standing check)

**Required Frontend Screens:**
- Grade Entry Form (bulk entry, validation, submission)
- Grade Review Panel (approve, flag, request revision)
- Student Grades View (by course, semester, GPA impact)
- Transcript Request Form (order, delivery method)
- Transcript Display (official format, seal/signature)

**Required Notifications:**
- Grades posted notification
- Transcript ready notification
- Academic probation/warning notification

**Required Audit Logs:**
- grade_submitted (instructor, timestamp)
- grade_validated (anomalies detected)
- grade_approved (registrar, timestamp)
- transcript_requested / generated
- grade_changed (reason, approver, timestamp)

**Required KPI/Dashboard:**
- Grade distribution (by course, by semester)
- Average GPA (by cohort, by program)
- Academic standing breakdown (good/probation/suspension)
- Transcript request turnaround time

**Required Tests:**
- Grade validation logic (unit)
- Transcript generation (contract)
- GPA calculation (analytics)
- Audit trail integrity (integration)

**Current Readiness:** PARTIAL (lms_grades table exists; academic_records partial; registrar approval workflow not implemented; frontend not started)  
**Priority:** P1 PILOT (compliance critical)

---

### D. GOVERNANCE & RECTOR DASHBOARD

#### D-1: Executive KPI Dashboard

**Feature Name:** Executive KPI Dashboard (Rector/Provost)  
**Business Problem:** Leadership lacks real-time visibility into institutional health (enrollment, retention, financial, academic).  
**User Persona:** Rector, Provost, Dean, Board Member  
**Connected Modules:** analytics (KPI aggregation), platform.kpi (dashboard builder), audit (data lineage), rbac (governance.read)  
**Trigger Event:** Dashboard load OR scheduled refresh (hourly)  
**Brain Core Role:** Anomaly alerts (KPI deviation from trend); forecasting (enrollment, revenue, churn)  
**Main Workflow:**
1. Rector logs in to governance portal
2. Dashboard displays key metrics (enrollment, retention, revenue, academic standing, delinquency)
3. Brain Core highlights anomalies (red flags, trending concerns)
4. Rector drills into detail (by department, by cohort, by risk level)
5. Exports report (PDF)
6. Shares with board

**Required Backend Endpoints:**
- `GET /api/v1/kpi/executive-dashboard` (aggregated metrics)
- `GET /api/v1/kpi/enrollment-metrics?period=...` (enrollment detail)
- `GET /api/v1/kpi/retention-metrics?period=...`
- `GET /api/v1/kpi/financial-metrics?period=...`
- `GET /api/v1/kpi/academic-metrics?period=...`
- `GET /api/v1/kpi/anomalies` (brain core alerts)

**Required Frontend Screens:**
- Executive Dashboard (4-6 key cards, trend lines, status indicators)
- KPI Detail Drilldown (by department, cohort, risk segment)
- Report Builder (select metrics, date range, format)
- Report History (view/download past reports)

**Required Notifications:**
- Critical KPI alert (anomaly detected)
- Weekly/monthly summary report

**Required Audit Logs:**
- dashboard_accessed
- report_generated / exported
- kpi_anomaly_detected (alert sent)

**Required KPI/Dashboard:**
- Enrollment (total, by program, new vs. returning)
- Retention (year-over-year, by cohort)
- Revenue (by plan tier, by month)
- Academic performance (average GPA, standing distribution)
- Financial health (delinquency rate, DSO, churn rate)
- Operational efficiency (course utilization, advisor workload)

**Required Tests:**
- KPI aggregation logic (unit)
- Anomaly detection (integration)
- Report generation (contract)

**Current Readiness:** PARTIAL (KPI module exists; dashboard templates partial; anomaly detection in progress)  
**Priority:** P0 DEMO (governance requirement)

---

#### D-2: Policy Management & Approval Workflow

**Feature Name:** Policy Management & Approval Workflow  
**Business Problem:** Institution policies are scattered; change requests lack formal approval process.  
**User Persona:** Rector, Policy Officer, Dean, Compliance Officer  
**Connected Modules:** RBAC (governance), audit (policy changes), notifications (approval requests), context (policy engine)  
**Trigger Event:** Policy officer drafts new policy OR requests change to existing policy  
**Brain Core Role:** Policy conflict detection (contradicts existing rules); impact analysis (which processes affected)  
**Main Workflow:**
1. Policy officer creates policy draft (title, text, effective date, scope)
2. Brain Core checks for conflicts with existing policies
3. Route to approval chain (Dean → Provost → Rector)
4. Each approver reviews, comments, approves/rejects
5. If approved, policy published + notified to affected users
6. Policy takes effect on date specified
7. All versions maintained; audit trail complete

**Required Backend Endpoints:**
- `POST /api/v1/policies` (create draft)
- `GET /api/v1/policies?status=draft|approved|active`
- `POST /api/v1/policies/{policy_id}/submit-approval`
- `PUT /api/v1/policies/{policy_id}/approve` (by approver)
- `PUT /api/v1/policies/{policy_id}/reject` (with comment)
- `GET /api/v1/policies/{policy_id}/approvals` (status history)

**Required Frontend Screens:**
- Policy Editor (markdown/rich text)
- Policy Approval Queue (assign to me, review, comment, approve/reject)
- Policy Library (active, historical, searchable)
- Policy Conflict Report (shows related policies)

**Required Notifications:**
- Approval request notification
- Approval reminder (overdue)
- Policy approved/rejected notification
- Policy effective notification

**Required Audit Logs:**
- policy_created / updated (as draft)
- policy_submitted_for_approval
- policy_approved / rejected (by approver, timestamp, comments)
- policy_published (effective date)

**Required KPI/Dashboard:**
- Policies by status (draft, in-review, active)
- Average approval time (days)
- Policies by scope (academic, financial, operational)

**Required Tests:**
- Conflict detection logic (unit)
- Approval workflow (integration)
- Audit trail (contract)

**Current Readiness:** PLANNED (basic infrastructure exists; workflow orchestration not implemented)  
**Priority:** P2 ENTERPRISE (governance maturity requirement)

---

### E. MINISTRY & COMPLIANCE REPORTING

#### E-1: Regulatory Reporting (Annual Ministry Filings)

**Feature Name:** Automated Ministry Reporting  
**Business Problem:** Manual data collection for ministry/regulator filings; prone to errors; compliance risk.  
**User Persona:** Compliance Officer, Institutional Researcher, Ministry Relations Officer  
**Connected Modules:** university_core (students, faculty, academic_records), audit (full data lineage), notifications (deadline alerts), context (report templates)  
**Trigger Event:** Ministry filing deadline OR manual report generation request  
**Brain Core Role:** Data validation (completeness, consistency); gap identification (missing data, inconsistencies)  
**Main Workflow:**
1. Compliance officer initiates report generation (report type, year, format)
2. System pulls data from core entities (enrollments, grades, faculty, degrees)
3. Brain Core validates data quality (flags missing/inconsistent records)
4. Officer reviews validation report, resolves issues
5. Report generated in required format (Excel, XML, API)
6. Signed by authorized officer
7. Submitted to ministry
8. Audit trail captured

**Required Backend Endpoints:**
- `GET /api/compliance/reports?type=...&year=...` (list templates)
- `POST /api/compliance/reports/{report_id}/generate` (initiate)
- `GET /api/compliance/reports/{report_id}/status` (progress)
- `GET /api/compliance/reports/{report_id}/validation-issues` (quality check)
- `POST /api/compliance/reports/{report_id}/sign-and-submit` (final step)
- `GET /api/compliance/reports/{report_id}/download?format=excel|xml`

**Required Frontend Screens:**
- Report Generation Wizard (select type, year, format)
- Data Validation Review (list issues, drill to source record)
- Report Preview (formatted output)
- Signature & Submission (e-signature, confirmation)
- Submission History (track all filed reports)

**Required Notifications:**
- Report ready for review
- Validation issues found (action required)
- Report submitted notification
- Deadline reminder (30 days before)

**Required Audit Logs:**
- report_generated (type, year, count of records)
- validation_issues_identified / resolved
- report_signed (officer, timestamp)
- report_submitted (timestamp, confirmation number)

**Required KPI/Dashboard:**
- Report submission status (on-time, late, pending)
- Data quality score (% records valid)
- Validation issue trends (types, frequency)

**Required Tests:**
- Data extraction logic (unit)
- Validation rules (contract)
- Report formatting (integration)
- Audit trail (contract)

**Current Readiness:** BACKEND_ONLY (data available; report templates partial; submission workflow not implemented; frontend not started)  
**Priority:** P1 PILOT (compliance critical, high penalty risk)

---

### F. PROCUREMENT & ASSETS

#### F-1: Equipment Booking & Maintenance Tracking

**Feature Name:** Equipment Booking & Maintenance System  
**Business Problem:** Equipment reservations are manual; maintenance not tracked; asset utilization invisible.  
**User Persona:** Department Chair, Lab Manager, Facilities Manager, Equipment Owner  
**Connected Modules:** university_core (equipment_booking_action_logs), audit (bookings, maintenance), notifications (availability alerts), analytics (utilization metrics)  
**Trigger Event:** User requests equipment reservation OR maintenance due  
**Brain Core Role:** Conflict detection (double-booking prevention); recommendation (optimize allocation); maintenance prediction (usage-based)  
**Main Workflow:**
1. User searches available equipment (filters: type, location, date range)
2. Brain Core shows availability (conflicts checked)
3. User reserves (date, time, purpose)
4. Equipment owner notified
5. Reservation confirmed; added to user calendar
6. After use, user returns equipment + logs condition/damage
7. System tracks maintenance schedule (usage-based intervals)
8. Facilities manager notified of maintenance due
9. Maintenance logged + equipment status updated
10. Utilization metrics tracked

**Required Backend Endpoints:**
- `GET /api/v1/equipment?category=...&location=...` (inventory)
- `GET /api/v1/equipment/{equipment_id}/availability?date_range=...` (check conflicts)
- `POST /api/v1/equipment/{equipment_id}/bookings` (reserve)
- `GET /api/v1/users/{user_id}/bookings` (my reservations)
- `PUT /api/v1/equipment/{equipment_id}/bookings/{booking_id}/return` (log return + condition)
- `GET /api/v1/equipment/{equipment_id}/maintenance-schedule` (upcoming maintenance)
- `POST /api/v1/equipment/{equipment_id}/maintenance/{maintenance_id}/complete` (log completion)

**Required Frontend Screens:**
- Equipment Catalog (browse, search filters, view photos)
- Availability Calendar (click to reserve)
- Booking Confirmation (review details, add to calendar)
- My Bookings (upcoming, past, cancel)
- Return Log (condition report, damage notes)
- Maintenance Schedule (upcoming maintenance, mark complete)

**Required Notifications:**
- Reservation confirmed
- Equipment available reminder (day before)
- Return overdue (if not returned on time)
- Maintenance due notification (equipment owner + facilities)
- Maintenance complete confirmation

**Required Audit Logs:**
- equipment_booked (user, date, purpose)
- booking_returned (condition notes)
- maintenance_logged (type, cost, date)
- damage_reported / resolved

**Required KPI/Dashboard:**
- Equipment utilization rate (%) by type
- Average booking lead time
- Maintenance frequency (by equipment type)
- Damage/cost trends
- Return on investment (cost vs. usage)

**Required Tests:**
- Conflict detection (unit)
- Booking CRUD (contract)
- Maintenance schedule logic (integration)
- Utilization calculation (analytics)

**Current Readiness:** PLANNED (table exists; booking + return + maintenance logic not implemented; frontend not started)  
**Priority:** P2 ENTERPRISE (operational efficiency)

---

### G. HR & FACULTY MANAGEMENT

#### G-1: Faculty Contract & Performance Management

**Feature Name:** Faculty Contract Lifecycle & Performance Tracking  
**Business Problem:** Faculty contracts are manual; performance reviews scattered; renewal decisions lack data.  
**User Persona:** Department Head, HR Manager, Faculty Member, Rector  
**Connected Modules:** university_core (hr_contracts, faculty), audit (contract changes), notifications (renewal reminders), analytics (performance metrics)  
**Trigger Event:** Contract renewal date approaching OR performance review scheduled  
**Brain Core Role:** Performance prediction; retention risk assessment; contract recommendation (renewal, non-renewal, promotion)  
**Main Workflow:**
1. HR system tracks faculty contracts (start date, end date, terms, salary)
2. Brain Core monitors contract expiration (90 days before renewal decision deadline)
3. Department head notified of upcoming reviews
4. Head conducts performance evaluation (teaching, research, service)
5. Brain Core analyzes evaluation + historical data → retention risk + recommendation
6. Head proposes renewal/non-renewal
7. HR process: contract signed, salary adjusted, notified to faculty
8. All actions logged + faculty notified

**Required Backend Endpoints:**
- `GET /api/v1/faculty/{faculty_id}/contract` (view contract)
- `GET /api/v1/contracts?expiring-within=...` (expiring soon)
- `POST /api/v1/faculty/{faculty_id}/performance-review` (submit evaluation)
- `GET /api/v1/faculty/{faculty_id}/performance-history` (past reviews)
- `PUT /api/v1/faculty/{faculty_id}/contract` (renew/update)
- `GET /api/v1/contracts/renewal-recommendations` (brain core advice)

**Required Frontend Screens:**
- Faculty Contract View (terms, history, renewal status)
- Contract Renewal Dashboard (expiring soon, action required)
- Performance Evaluation Form (rubric-based, comments)
- Performance History (trend over years)
- Renewal Decision Panel (recommend, approve, notify faculty)

**Required Notifications:**
- Renewal decision deadline reminder (60, 30 days before)
- Performance review request
- Contract renewal approved/declined notification
- Salary adjustment notification

**Required Audit Logs:**
- performance_review_submitted (evaluator, date, scores)
- contract_renewal_decision (approved/denied)
- contract_signed (new terms, salary)
- retention_risk_score_calculated

**Required KPI/Dashboard:**
- Faculty renewal rate (% renewed vs. declined)
- Average time to renewal decision
- Performance score distribution (by department, by rank)
- Retention risk breakdown
- Compensation trends (by rank, by performance)

**Required Tests:**
- Performance scoring logic (unit)
- Retention risk model (integration)
- Contract renewal calculation (contract)

**Current Readiness:** PLANNED (table exists; contract + performance logic not implemented; frontend not started)  
**Priority:** P2 ENTERPRISE (HR maturity requirement)

---

### H. BRAIN CORE & AUTOMATION

#### H-1: Student Intervention Orchestration (Cross-Module Automation)

**Feature Name:** Brain Core-Driven Student Intervention Automation  
**Business Problem:** At-risk interventions are reactive + manual; opportunities for proactive, automated actions missed.  
**User Persona:** Student, Advisor, Brain Core Platform Manager  
**Connected Modules:** brain_core (anomaly detection, decision engine), university_core (students, enrollments, academic_records), automation (workflow engine), notifications (multi-channel), audit (all automation decisions)  
**Trigger Event:** Brain Core detects anomaly (grade drop, attendance nosedive, payment late) OR scheduled daily batch  
**Brain Core Role:** **PRIMARY** — Detect, score, recommend, orchestrate, measure outcomes  
**Main Workflow:**
1. Brain Core daily batch: analyzes all student signals (academic, financial, engagement)
2. Anomaly detection: flags students with unexpected changes
3. Decision engine: routes by risk type (academic, financial, engagement)
4. Automation policy: triggered recommendations
   - **Academic risk:** Schedule advisor meeting, recommend tutoring, email study tips
   - **Financial risk:** Email payment reminder, offer payment plan, flag for collections
   - **Engagement risk:** Send motivational message, recommend club/activity, notify mentor
5. Automated actions executed (where safe)
6. Manual approval required for sensitive actions (service restriction, etc.)
7. Outcome tracking: did student recover? did intervention help?
8. Feedback loop: brain core learns from outcomes

**Required Backend Endpoints:**
- `GET /api/v1/brain-core/student-analysis` (batch results)
- `GET /api/v1/brain-core/students/{student_id}/risk-profile` (full analysis)
- `GET /api/v1/brain-core/anomalies?type=...` (filtered anomalies)
- `POST /api/v1/brain-core/students/{student_id}/intervention-recommendations` (trigger decision engine)
- `GET /api/v1/automation/workflows?type=student-intervention` (running workflows)
- `POST /api/v1/automation/workflows/{workflow_id}/execute` (trigger)
- `GET /api/v1/brain-core/intervention-outcomes` (aggregate outcome metrics)

**Required Frontend Screens:**
- Brain Core Student Analysis (anomaly details, risk score, recommended actions)
- Intervention Automation Dashboard (active workflows, executed actions, pending approvals)
- Workflow Orchestration Panel (define rules, thresholds, actions, approval gates)

**Required Notifications:**
- Student: personalized intervention message (tutor offer, payment plan, mentorship)
- Advisor: escalation alert (student needs immediate help)
- System: automation decision log (sent to audit)

**Required Audit Logs:**
- anomaly_detected (type, severity, signals)
- recommendation_generated (action, confidence score)
- automation_action_executed / approved / rejected
- student_outcome_measured (6-week follow-up)

**Required KPI/Dashboard:**
- Anomaly detection rate (students flagged per week)
- Intervention coverage (% of at-risk students reached)
- Automation action success rate (% led to positive outcome)
- Brain Core recommendation accuracy (precision, recall)
- Student recovery rate (post-intervention improvement %)

**Required Tests:**
- Anomaly detection (unit)
- Decision engine policy evaluation (integration)
- Workflow execution (contract)
- Outcome measurement (analytics)

**Current Readiness:** BACKEND_ONLY (brain_core module exists; anomaly + decision engines partial; automation orchestration not implemented; frontend not started)  
**Priority:** P0 DEMO (flagship brain core feature)

---

## Top 10 Demo/Pilot Features (Ranked by Value + Readiness)

| Rank | Feature | Group | Readiness | Why Top 10 |
|---|---|---|---|---|
| 1 | **Early Warning System (A-1)** | Student Success | BACKEND_ONLY | Core retention value + analytics ready |
| 2 | **Delinquency Detection & Recovery (B-2)** | Finance | PARTIAL | Revenue protection + infrastructure exists |
| 3 | **Executive KPI Dashboard (D-1)** | Governance | PARTIAL | Leadership requirement + module ready |
| 4 | **Course Scheduling & Enrollment (C-1)** | Academic Ops | BACKEND_ONLY | Core operational feature + tables exist |
| 5 | **Student Intervention Orchestration (H-1)** | Brain Core | BACKEND_ONLY | Flagship feature + brain_core ready |
| 6 | **Grade Management & Transcripts (C-2)** | Academic Ops | PARTIAL | Compliance critical + tables exist |
| 7 | **Subscription Self-Service (B-1)** | Finance | PARTIAL | Customer satisfaction + logic mostly done |
| 8 | **Regulatory Reporting (E-1)** | Ministry | BACKEND_ONLY | Compliance critical + data available |
| 9 | **Tutoring Assignment & Tracking (A-2)** | Student Success | PLANNED | Depends on A-1 + high impact |
| 10 | **Policy Management & Approval (D-2)** | Governance | PLANNED | Governance maturity + medium complexity |

---

## Integration Gaps

### Gap 1: Brain Core → University Core → Student Success Pipeline

**Problem:** Brain Core anomaly detection → Early Warning System → Intervention Orchestration flow not fully connected.

**Missing:**
- Anomaly detection daily batch scheduler
- Decision engine rule evaluation for student intervention routing
- Automation workflow execution (trigger → action → outcome tracking)

**Impact:** H-1 (Brain Core Orchestration) cannot function without these.

**Effort:** Medium (3-4 endpoints, 2 integration tests)

**Resolution:** Implement in A-013 (IMPLEMENT TOP 3) or A-014.

---

### Gap 2: Billing → Notifications → Student/Tenant Messaging

**Problem:** Billing system can flag delinquency but lacks multi-channel notification (email, SMS, in-app).

**Missing:**
- Notification preference system (opt-in channels)
- Template management (notification text, localization)
- Execution engine (send via chosen channels)

**Impact:** B-1, B-2 cannot complete workflows without user notifications.

**Effort:** Medium (notification service exists; preference + template layer needs work)

**Resolution:** Implement in A-013 or as prerequisite to B-1/B-2.

---

### Gap 3: Academic Operations → Event Bus → KPI/Analytics

**Problem:** Course scheduling, enrollment, grading events are not published to event bus; KPI analytics lag.

**Missing:**
- Event publishing from academic_records, enrollments, lms_grades modules
- Event handler for KPI metrics aggregation
- Real-time KPI recalculation

**Impact:** C-1, C-2 features have data but KPIs stale; D-1 dashboard unreliable.

**Effort:** Low-Medium (event infrastructure exists; mostly wiring)

**Resolution:** Implement in A-013 (prerequisite for all academic features + D-1).

---

### Gap 4: HR/Faculty → Audit/Contract Versioning

**Problem:** Faculty contract lifecycle exists in data but no formal audit trail or version control.

**Missing:**
- Contract document versioning (store PDF versions)
- Signature capture + e-signature integration
- Contract template management

**Impact:** G-1 cannot be production-ready without contract versioning/audit.

**Effort:** Medium (tables need schema update + signature service)

**Resolution:** Implement in A-013 or A-014.

---

### Gap 5: Compliance/Regulatory → Data Lineage & Audit

**Problem:** Ministry reporting requires certified data (audited, signed off) but audit trail not complete.

**Missing:**
- Data lineage tracking (source → transform → report)
- Change audit for all data in compliance scope
- Digital signature/seal for official reports

**Impact:** E-1 cannot be certified without full audit chain.

**Effort:** Medium (audit infrastructure exists; scope expansion + signature service)

**Resolution:** Implement in A-013 (priority for compliance features).

---

### Gap 6: Governance → Policy Engine Integration

**Problem:** Policies can be defined but are not enforced by runtime system.

**Missing:**
- Policy evaluation engine (check: can user action X per policy Y?)
- Policy activation/deactivation workflow
- Policy versioning + historical tracking

**Impact:** D-2 policies exist but are not enforced; governance requirement incomplete.

**Effort:** Medium (requires integration with RBAC decision point)

**Resolution:** Implement in A-014 (lower priority but important for governance maturity).

---

## Event Map

All features depend on a robust event bus. Current events:

**Existing (from audit):**
- `user.created`, `user.deleted`
- `tenant.created`, `tenant.modified`
- `enrollment.created`, `enrollment.dropped`
- `grade.submitted`, `grade.approved`
- `payment.received`, `invoice.delinquent`
- `policy.created`, `policy.approved`, `policy.activated`

**Missing (required for A-012 features):**
- `student.anomaly.detected` (brain core) → triggers A-1, H-1
- `course.scheduled`, `course.conflict.detected` → triggers C-1
- `equipment.booking.requested`, `equipment.returned` → triggers F-1
- `faculty.contract.expiring`, `performance.review.completed` → triggers G-1
- `report.generation.requested`, `report.submitted` → triggers E-1
- `delinquency.escalation.triggered` → triggers B-2
- `intervention.recommended`, `intervention.completed` → triggers all student success features

**Solution:** Define event spec in A-013; implement in parallel with feature endpoints.

---

## API/Frontend Map

### New Endpoints (Summary by Feature)

**A-1: Early Warning System**
- 3 endpoints (risk list, profile, interventions)

**A-2: Tutoring**
- 6 endpoints (requests, recommendations, assignments, sessions, outcomes)

**B-1: Subscription**
- 5 endpoints (view, plan list, change, seat modification, invoices)

**B-2: Delinquency**
- 6 endpoints (list, details, reminder, escalate, resolve, policy)

**C-1: Course Scheduling**
- 6 endpoints (create/update/list courses, enroll, check conflicts)

**C-2: Grade Management**
- 6 endpoints (submit, review, approve, transcript, GPA, standing)

**D-1: KPI Dashboard**
- 5 endpoints (executive dashboard, metric detail, anomalies)

**D-2: Policy Management**
- 5 endpoints (create, list, submit, approve, reject)

**E-1: Regulatory Reporting**
- 6 endpoints (list templates, generate, validate, sign, submit, download)

**F-1: Equipment Booking**
- 7 endpoints (inventory, availability, book, return, maintenance schedule, complete)

**G-1: Faculty Contracts**
- 6 endpoints (view contract, list expiring, submit review, history, renewal decision)

**H-1: Brain Core Orchestration**
- 6 endpoints (student analysis, risk profile, anomalies, recommendations, workflows, outcomes)

**Total: 63 new endpoints**

### New Frontend Screens (Summary)

- 8 major dashboards (at-risk, delinquency, KPI, equipment, faculty, policy, report, intervention automation)
- 12 form workflows (risk intervention, tutoring request, course scheduling, grade entry, policy submission, contract renewal, report generation, etc.)
- 6 library/catalog screens (courses, tutors, equipment, policies, reports, facult

y)
- 4 history/tracking screens (interventions, bookings, grades, contracts)

**Total: 30 new screens**

---

## Brain Core Map

### Decision Tree: Anomaly Detection & Recommendation Routing

```
Daily Batch: Load all students
├─ Calculate signals:
│  ├─ Academic: GPA, grade trend, attendance, course performance
│  ├─ Financial: Invoice aging, payment pattern, usage vs. plan
│  └─ Engagement: LMS activity, event attendance, communication frequency
├─ Detect anomalies:
│  ├─ Academic risk (GPA drop, attendance < 80%, failing grade)
│  ├─ Financial risk (invoice overdue, usage overages)
│  └─ Engagement risk (no LMS activity > 2 weeks, isolated from peers)
├─ Score by risk type + severity (0-100)
├─ Route by policy:
│  ├─ Academic risk (score > 70):
│  │  ├─ Recommend tutoring (Brain Core matches tutor)
│  │  ├─ Schedule advisor meeting
│  │  ├─ Send study tips (automated email)
│  │  └─ Flag for retention program
│  ├─ Financial risk (score > 60):
│  │  ├─ Send payment reminder (automated email)
│  │  ├─ Offer payment plan (automated)
│  │  ├─ Flag for collections officer (if > 30 days late)
│  │  └─ Recommend course restriction if overages (manual approval)
│  └─ Engagement risk (score > 50):
│     ├─ Send motivational message (automated)
│     ├─ Recommend peer mentor match (Brain Core)
│     ├─ Suggest club/activity (aligned to interests)
│     └─ Schedule advisor check-in
└─ Track outcomes:
   ├─ 1-week: Student received notification
   ├─ 2-week: Student took action (enrolled in tutoring, scheduled meeting, etc.)
   ├─ 6-week: Student outcome improved (GPA, attendance, payment, engagement)
   └─ Feedback loop: Update model based on successes/failures
```

### Brain Core APIs (Required for H-1 + dependency for others)

```
POST /api/v1/brain-core/batch/analyze-students
  └─ Input: optional filter (tenant, cohort, risk type)
  └─ Output: list of anomalies + scores + recommendations

GET /api/v1/brain-core/students/{student_id}/risk-profile
  └─ Output: signals, anomaly type, severity, score, recommended actions

POST /api/v1/brain-core/students/{student_id}/intervention-recommendations
  └─ Input: override policy/thresholds (optional)
  └─ Output: prioritized recommendation list (action, confidence, automation allowed)

GET /api/v1/brain-core/anomalies?type=academic|financial|engagement&severity=high
  └─ Output: filtered anomaly list + batch stats

GET /api/v1/brain-core/intervention-outcomes?period=...&success=true
  └─ Output: aggregate outcome metrics (recovery rate, intervention effectiveness)
```

---

## Recommended Build Order

### Phase 1: FOUNDATION (A-012.1 - A-012.2)
**Scope:** Event bus completion, notification infrastructure, brain core APIs

**A-012.1: Event Bus & Notification System**
- Event spec definition (student.anomaly.detected, course.scheduled, etc.)
- Event publisher integration (academic, billing, brain core modules)
- Notification preference system (user opt-in channels)
- Notification template management (email, SMS, in-app)
- Execution engine (multi-channel dispatch)
- Tests: 10 integration tests
- Effort: 2 weeks

**A-012.2: Brain Core APIs (Anomaly + Recommendation)**
- Anomaly detection batch scheduler
- Risk scoring logic (academic, financial, engagement)
- Decision engine rule evaluation
- Recommendation routing
- Outcome tracking schema
- Tests: 12 unit + 8 integration tests
- Effort: 2.5 weeks

### Phase 2: CORE PILOT FEATURES (A-012.3 - A-012.5)
**Scope:** Top 3 highest-impact features with clear business value

**A-012.3: Early Warning System (A-1)**
- Advisors see at-risk student list
- Risk profile details (signals, recommendations)
- Intervention workflow (create, track, resolve)
- Tests: 15 contract tests, 5 integration tests
- Effort: 2 weeks

**A-012.4: Executive KPI Dashboard (D-1)**
- Real-time KPI aggregation (enrollment, retention, financial, academic)
- Anomaly alerts (deviation from trend)
- Drill-down capability (by department, cohort, risk)
- Report export (PDF)
- Tests: 8 contract tests, 4 integration tests
- Effort: 1.5 weeks

**A-012.5: Delinquency Detection & Recovery (B-2)**
- Daily delinquency flagging
- Escalation policy engine (reminder → notice → restriction)
- Recovery action panel (send reminder, escalate, credit, negotiate)
- Audit logging
- Tests: 10 contract tests, 6 integration tests
- Effort: 2 weeks

### Phase 3: EXPANSION (A-013)
**Scope:** Additional high-value features, brain core orchestration

**Features:** Subscription Self-Service (B-1), Brain Core Student Intervention Orchestration (H-1), Course Scheduling (C-1), Grade Management (C-2), Tutoring Assignment (A-2), Regulatory Reporting (E-1)

---

## Next Action

**A-012.1 — FEATURE INTEGRATION GAP ANALYSIS + PRIORITY RANKING**

**Scope:**
1. Validate feature definitions with product team + stakeholders
2. Assess each feature against:
   - Business impact (revenue, retention, compliance, efficiency)
   - Customer feedback (requests, complaints, feature parity)
   - Technical readiness (backend %, frontend %, integration %)
   - Resource effort (dev weeks)
3. Rank by priority + readiness matrix
4. Identify blockers + dependencies

**Output:**
- Validated feature list (15-25 prioritized features)
- Business value scoring (revenue impact, retention impact, operational efficiency, compliance risk)
- Technical readiness assessment (by feature)
- Build order recommendation (phases 1-3)
- Risk register (top 5 risks + mitigation)

**Effort:** 1 week (research + stakeholder interviews + analysis)

---

**Prepared by:** A-011 Closure  
**Status:** READY FOR A-012.1 KICKOFF
