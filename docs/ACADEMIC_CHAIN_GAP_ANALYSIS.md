# Academic Chain Implementation Gap Analysis

**Date:** 2026-04-05  
**Scope:** Full university academic operating model for pilot v1  
**Strategy:** Pilot-first (test complete chain), then rollout to production  

---

## Executive Summary

The backend has a **solid foundation** for the academic chain. Core entities (students, enrollments, grades, transcripts, intervention cases) are production-ready with full tenant isolation. However, **three critical layers are incomplete** and must be implemented for the operational model to work as designed:

1. **Organizational Structure** (org_unit tree) — Missing entirely
2. **Lesson Execution Reality** (attendance, topics, signals) — 60% complete
3. **Risk Detection & Auto-Intervention** — Structure exists, algorithm missing

**Pilot v1 Readiness:** 60% — can go live for basic academic flow, but need 3-4 weeks to add critical path layers.

---

## 1. CURRENT ACADEMIC CHAIN STATE

### What Already Works (100% Production-Ready)

```
Student Admission
  ↓
StudentProfile (status: admitted → active → standing/probation/dismissed)
  ↓
CohortAssignment (term_year, cohort_number)
  ↓
Enrollment (student → course_section → term)
  ↓
GradeSubmission (versioned, audited)
  ↓
TranscriptRecord (immutable, permanent)
  ↓
ContextEntity + ContextRelation (AI semantic layer)
  ↓
[AI Retrieval Layer] — Can query full academic history
```

**Tenant Isolation:** ✅ Bulletproof
- Composite FKs on all academic tables
- All queries filtered by `tenant_id`
- RLS policies in progress
- Verified safe: no cross-tenant data leakage

**API Endpoints Ready:**
- `POST /api/admin/university/students` — Create student
- `POST /api/admin/university/enrollments` — Enroll in course
- `POST /api/grades/submit` — Submit grade
- `GET /api/transcripts/{student_id}` — View transcript
- `POST /api/admin/interventions/cases` — Create intervention case (manual)
- `PATCH /api/admin/interventions/cases/{id}/status` — Update case status

---

## 2. LAYER 1: ORGANIZATIONAL STRUCTURE — ❌ MISSING

### Current State
- Departments stored as **strings only** in course + student records
- No tree hierarchy
- No governance/responsibility scoping
- No head_person assignments

### What's Needed (From UNIVERSITY_OPERATIONAL_MODEL.md Section 16)

**Database Schema Addition:**

```python
# models/org_structure.py
class OrgUnit(Base):
    __tablename__ = "app_org_org_units"
    
    tenant_id: UUID = Column(UUID, ForeignKey("app_tenants.id"), nullable=False)
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    
    name: str = Column(String(255), nullable=False)
    code: str = Column(String(50), nullable=False)  # Unique within tenant
    unit_type: str = Column(String(50), nullable=False)  # university, school, faculty, department, umo, registrar_office, deans_office, advisory_unit, academic_committee, academic_commission
    
    parent_unit_id: UUID = Column(UUID, ForeignKey("app_org_org_units.id"), nullable=True)  # NULL for root university node
    
    active: bool = Column(Boolean, default=True)
    head_person_id: UUID = Column(UUID, ForeignKey("app_people.id"), nullable=True)
    
    email: str = Column(String(255), nullable=True)
    phone: str = Column(String(20), nullable=True)
    location: str = Column(String(500), nullable=True)
    
    created_at: datetime = Column(DateTime, default=utcnow)
    updated_at: datetime = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'parent_unit_id'], 
                           ['app_org_org_units.tenant_id', 'app_org_org_units.id']),
        UniqueConstraint('tenant_id', 'code'),
        Index('ix_app_org_org_units_tenant_type', 'tenant_id', 'unit_type'),
        Index('ix_app_org_org_units_parent', 'tenant_id', 'parent_unit_id'),
    )
```

**Bootstrap Logic:**
- When tenant is created, auto-create root `OrgUnit(type=university)`
- Admin can then create hierarchy below it

**Integration Points:**
- `Student.org_unit_id` → ForeignKey to OrgUnit (student's registering unit)
- `CourseSection.department_unit_id` → ForeignKey to OrgUnit (which department offers this)
- `InterventionCase.assigned_unit_id` → ForeignKey to OrgUnit (dean/advisor unit)

### Effort: **1 week**
- Model + migration: 2 days
- API endpoints (CRUD + tree query): 2 days
- Tests + tenant isolation audit: 1 day
- Integration with existing student/course/intervention: 2 days

---

## 3. LAYER 2: LESSON EXECUTION REALITY — ⚠️ 60% COMPLETE

### Current State

**What exists:**
- `CourseSection` (section_code, instructor_id, capacity, term_id)
- `SectionSchedule` (section_id, time_slot_id, classroom_id, day_of_week)
- Can retrieve: "CS101 Section A on Monday 10:00 in Room 101"

**What's missing:**
- ❌ No `LessonInstance` (scheduled vs. actual execution)
- ❌ No attendance tracking
- ❌ No lesson topics being taught
- ❌ No materials/assignments binding
- ❌ No assessment signals (quiz scores, lab results)

### What's Needed (From spec: "Lesson Instance as FACT")

**Database Schema Addition:**

```python
# models/academic_execution.py

class Discipline(Base):
    """Subject: Programming, Calculus, etc."""
    __tablename__ = "app_academic_disciplines"
    
    tenant_id: UUID
    id: UUID = primary_key
    
    unique_code: str  # "CS-101"
    title: str  # "Introduction to Programming"
    description: str
    credits: int
    prerequisites: JSON  # List of discipline IDs
    learning_outcomes: JSON  # Array of LOs
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'unique_code'),
    )

class LessonTopic(Base):
    """Topics within a discipline"""
    __tablename__ = "app_academic_lesson_topics"
    
    tenant_id: UUID
    id: UUID = primary_key
    
    discipline_id: UUID = FK(Discipline)
    module_num: int  # Which module in the curriculum
    topic_num: int  # Which topic within module
    title: str  # "Variables and Data Types"
    description: str
    difficulty_level: str  # "beginner", "intermediate", "advanced"
    recommended_materials: JSON  # Array of material IDs
    
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'discipline_id'], ...),
        UniqueConstraint('tenant_id', 'discipline_id', 'module_num', 'topic_num'),
    )

class LessonInstance(Base):
    """ACTUAL EXECUTION of a lesson"""
    __tablename__ = "app_academic_lesson_instances"
    
    tenant_id: UUID
    id: UUID = primary_key
    
    course_section_id: UUID = FK(CourseSection)
    scheduled_date: date  # When was it planned
    actual_date: date = NULL  # When did it actually happen (filled on completion)
    
    instructor_id: UUID = FK(Person)
    status: str  # "planned", "completed", "canceled", "rescheduled"
    
    topic_id: UUID = FK(LessonTopic)  # What was taught
    topic_title_snapshot: str  # "Variables and Data Types" (immutable copy)
    
    materials_attached: JSON  # Array of material references
    notes: str  # What instructor recorded
    
    attendance_captured: bool = False
    attendance_json: JSON = NULL  # {"student_id": "present"/"absent"/"late"}
    
    homework_assigned: bool = False
    homework_json: JSON = NULL  # {"assignment_id", "due_date"}
    
    assessment_signals: JSON = NULL  # Lab results, quiz scores, completion status
    
    created_at: datetime
    updated_at: datetime
    
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'course_section_id'], ...),
        ForeignKeyConstraint(['tenant_id', 'instructor_id'], ...),
        ForeignKeyConstraint(['tenant_id', 'topic_id'], ...),
        Index('ix_lesson_instances_section_date', 'tenant_id', 'course_section_id', 'scheduled_date'),
        Index('ix_lesson_instances_topic_completed', 'tenant_id', 'topic_id', 'status'),
    )

class Attendance(Base):
    """Attendance per lesson per student"""
    __tablename__ = "app_academic_attendance"
    
    tenant_id: UUID
    id: UUID = primary_key
    
    lesson_instance_id: UUID = FK(LessonInstance)
    student_id: UUID = FK(StudentProfile)
    
    status: str  # "present", "absent", "late", "excused"
    marked_at: datetime
    marked_by: UUID = FK(Person)  # Instructor who marked
    
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'lesson_instance_id'], ...),
        ForeignKeyConstraint(['tenant_id', 'student_id'], ...),
        UniqueConstraint('tenant_id', 'lesson_instance_id', 'student_id'),
    )

class StudentTopicProgress(Base):
    """What has student been exposed to"""
    __tablename__ = "app_academic_student_topic_progress"
    
    tenant_id: UUID
    id: UUID = primary_key
    
    student_id: UUID = FK(StudentProfile)
    topic_id: UUID = FK(LessonTopic)
    discipline_id: UUID = FK(Discipline)
    
    first_seen_date: date  # When student first attended lesson on this topic
    last_reviewed_date: date  # When student last reviewed materials
    status: str  # "not_started", "in_progress", "completed"
    
    materials_opened: int  # How many materials were opened
    materials_completed: int
    
    quiz_attempts: int = 0
    quiz_best_score: float = NULL
    
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'student_id'], ...),
        ForeignKeyConstraint(['tenant_id', 'topic_id'], ...),
        UniqueConstraint('tenant_id', 'student_id', 'topic_id'),
    )
```

**Key Rules:**

1. **Only COMPLETED lessons are visible to students**
   - `LessonInstance.status = "completed"`
   - Prevents "spoilers" for future topics

2. **AI Context builds from completed lessons**
   - Can ask: "What have we covered on Variables?"
   - Cannot ask: "What's coming next week?"

3. **Attendance = risk signal**
   - Student absent from 3+ lessons on topic X → flag for intervention

4. **Assessment signals feed risk detection**
   - Low quiz score on topic X → knowledge gap

### Effort: **2 weeks**
- Models + migrations: 3 days
- API: lesson_instance CRUD, attendance marking, topic progress: 4 days
- AI retrieval layer integration (what topics has student completed): 3 days
- Tests: 2 days
- Integration with existing CourseSection: 2 days

---

## 4. LAYER 3: RISK DETECTION & AUTO-INTERVENTION — ⚠️ 30% COMPLETE

### Current State

**What exists:**
- `InterventionCase` model (case_type, severity, status, risk_snapshot_json)
- Manual case creation: `POST /api/admin/interventions/cases`
- Manual status updates

**What's missing:**
- ❌ No risk scoring algorithm
- ❌ No thresholds configuration
- ❌ No automated case creation triggers
- ❌ No outcome tracking

### What's Needed

**Database Schema Additions:**

```python
# models/risk_and_intervention.py

class RiskThreshold(Base):
    """Configurable risk detection thresholds"""
    __tablename__ = "app_risk_thresholds"
    
    tenant_id: UUID
    id: UUID = primary_key
    
    risk_category: str  # "academic_gpa", "attendance", "topic_mastery", "failed_assessment"
    rule_name: str  # "low_cumulative_gpa", "excessive_absence", "quiz_failure"
    
    enabled: bool = True
    
    # Thresholds
    metric: str  # "gpa", "absence_count", "quiz_score", "failed_assignments"
    threshold_value: float  # 2.0, 5 (days), 50 (%)
    comparison: str  # "lte", "gte", "eq"
    
    severity_level: str  # "warning", "concern", "critical"
    
    auto_create_case: bool = True
    escalate_to_roles: JSON  # ["advisor", "dean"]
    
    created_at: datetime
    updated_at: datetime

class RiskSignal(Base):
    """Individual risk detection event"""
    __tablename__ = "app_risk_signals"
    
    tenant_id: UUID
    id: UUID = primary_key
    
    student_id: UUID = FK(StudentProfile)
    threshold_id: UUID = FK(RiskThreshold)
    
    signal_type: str  # "academic_risk", "attendance_risk", "progress_risk", "expulsion_risk"
    detected_at: datetime
    
    current_value: float  # Actual GPA, actual absence days, etc.
    threshold_value: float
    severity: str  # inherited from threshold
    
    signal_data_json: JSON  # Detailed context: which course, which topic, etc.
    
    associated_case_id: UUID = FK(InterventionCase, nullable=True)  # Linked case
    
    __table_args__ = (
        Index('ix_risk_signals_student_detected', 'tenant_id', 'student_id', 'detected_at'),
    )

class InterventionCase(Base):  # EXPANDED from existing
    __tablename__ = "app_intervention_cases"
    
    tenant_id: UUID
    id: UUID = primary_key
    
    student_id: UUID = FK(StudentProfile)
    case_type: str  # "academic_risk_intervention", "attendance_intervention", etc.
    
    severity: str  # "warning", "concern", "critical"
    status: str  # "open", "in_progress", "resolved", "escalated", "closed"
    
    source: str  # "ai_risk_engine", "manual_creation", "advisor_referral"
    
    # Responsibility
    assigned_to_role: str  # "advisor", "dean", "registrar"
    assigned_to_unit_id: UUID = FK(OrgUnit)  # e.g., Dean of Engineering
    assigned_to_person_id: UUID = FK(Person, nullable=True)
    
    # SLA
    created_at: datetime
    due_at: datetime  # SLA deadline
    resolved_at: datetime = NULL
    
    # Data
    risk_snapshot_json: JSON  # Full context at time of creation
    metadata_json: JSON  # Custom fields, audit trail
    
    __table_args__ = (
        Index('ix_intervention_cases_student_open', 'tenant_id', 'student_id', 'status'),
        Index('ix_intervention_cases_due', 'tenant_id', 'due_at'),
    )

class InterventionAction(Base):
    """Specific actions taken within an intervention case"""
    __tablename__ = "app_intervention_actions"
    
    tenant_id: UUID
    id: UUID = primary_key
    
    case_id: UUID = FK(InterventionCase)
    
    action_type: str  # "advisor_meeting", "tutoring_assigned", "course_restriction", "monitoring", "escalate"
    description: str
    
    assigned_responsibility: str  # Who does this?
    due_date: date  # When should this be done?
    
    status: str  # "pending", "in_progress", "completed", "deferred"
    completed_at: datetime = NULL
    completed_by: UUID = FK(Person)
    
    notes: str

class OutcomeTracking(Base):
    """Did the intervention work?"""
    __tablename__ = "app_outcome_tracking"
    
    tenant_id: UUID
    id: UUID = primary_key
    
    case_id: UUID = FK(InterventionCase)
    
    baseline_risk_score: float  # GPA, absence rate, etc. at case creation
    current_risk_score: float  # Most recent measurement
    
    outcome: str  # "improved", "unchanged", "worsened"
    improvement_date: date = NULL
    
    measurement_notes: str  # What metric changed
    outcome_notes: str  # Qualitative assessment
```

**Risk Detection Algorithm (Pseudo-code):**

```python
# workers/risk_detection_job.py

def detect_academic_risks(tenant_id):
    """Daily job: scan for at-risk students"""
    
    thresholds = RiskThreshold.query_enabled(tenant_id)
    
    for threshold in thresholds:
        if threshold.rule_name == "low_cumulative_gpa":
            at_risk = StudentProfile.query(
                tenant_id=tenant_id,
                cumulative_gpa < threshold.threshold_value,  # e.g. 2.0
                status="active"
            )
            
            for student in at_risk:
                existing_case = InterventionCase.find_open(
                    student_id=student.id,
                    case_type=threshold.escalate_to_roles[0]
                )
                
                if not existing_case:
                    signal = RiskSignal.create(
                        student_id=student.id,
                        threshold_id=threshold.id,
                        current_value=student.cumulative_gpa,
                        severity=threshold.severity_level,
                    )
                    
                    if threshold.auto_create_case:
                        case = InterventionCase.create(
                            student_id=student.id,
                            case_type="academic_risk_intervention",
                            severity=threshold.severity_level,
                            source="ai_risk_engine",
                            assigned_to_role=threshold.escalate_to_roles[0],
                            assigned_to_unit_id=student.org_unit_id,  # Advisor unit
                            due_at=utcnow() + timedelta(days=3),  # 3-day SLA
                            risk_snapshot_json={...},  # Current context
                        )
                        signal.associated_case_id = case.id
                        signal.save()
                        
                        emit_event("intervention_case_auto_created", case)
```

**Integration Points:**

1. **Scheduler job runs daily** → checks all thresholds → creates cases
2. **Advisor dashboard** shows assigned open cases
3. **Student dashboard** shows "You're at risk; advisor contacted you"
4. **Outcome query** `GET /api/interventions/outcomes/{case_id}` shows current risk vs. baseline

### Effort: **2 weeks**
- Models + migrations: 2 days
- Threshold configuration UI: 2 days
- Risk detection algorithm + tests: 3 days
- Scheduler job: 1 day
- Outcome tracking + reporting: 2 days
- Integration with case creation: 2 days

---

## 5. IMPLEMENTATION ROADMAP FOR PILOT V1

### Phase A: Foundation (Week 1)
- ✅ org_unit tree model + bootstrap
- ✅ Discipline + LessonTopic models
- ✅ Database migrations
- Tests + tenant isolation audit

**Result:** Can model org structure, can talk about disciplines

### Phase B: Lesson Execution (Week 2-3)
- ✅ LessonInstance + Attendance models
- ✅ StudentTopicProgress tracking
- ✅ API: lesson recording, attendance marking
- ✅ AI retrieval: "what topics has student covered"

**Result:** Faculty can record lessons, AI knows what was taught

### Phase C: Risk & Intervention (Week 3-4)
- ✅ RiskThreshold + RiskSignal models
- ✅ Risk detection algorithm
- ✅ Auto case creation
- ✅ Outcome tracking

**Result:** System automatically detects at-risk students, assigns cases, tracks improvement

### Phase D: Dashboard Integration (Week 4)
- Faculty: My lessons, students at risk
- Advisor: My cases, due dates, outcomes
- Student: My progress, topics covered, support status
- Academic admin: Risk dashboard, outcome metrics

---

## 6. PILOT V1 SUCCESS CRITERIA

**In-scope (MUST HAVE):**
- [ ] Org structure tree fully functional
- [ ] Lesson instances can be recorded with topics + attendance
- [ ] Risk detection runs daily
- [ ] Intervention cases auto-created + can be assigned
- [ ] Student sees only completed lessons
- [ ] AI can answer: "What topics has [student] covered?"
- [ ] Outcome tracking shows improvement trend

**Nice-to-have (Phase 2):**
- Prerequisite enforcement
- Academic standing probation/dismissal
- Remediation plan templates
- Integration with external systems (SIS, LMS)

---

## 7. DATA MIGRATION STRATEGY

**For existing students (if any):**
1. Create default org_unit tree (University → Faculty → Department)
2. Backfill student.org_unit_id from existing department_code
3. Create LessonInstance records from existing CourseSection (status="historical")
4. Backfill attendance from existing attendance records (if any)
5. Audit tenant isolation on each step

---

## 8. ROLLBACK PLAN

If Phase C (risk detection) causes issues:
1. Disable auto case creation (RiskThreshold.auto_create_case = false)
2. Existing cases remain; no data loss
3. Revert to manual case creation
4. Investigate algorithm; deploy fix; re-enable

---

## 9. TEAM EFFORT ESTIMATE

| Phase | Effort | Team |
|-------|--------|------|
| A: Org Structure | 1 week | Backend (1) + DBA (0.5) |
| B: Lesson Execution | 2 weeks | Backend (1), Frontend (0.5) |
| C: Risk Detection | 2 weeks | Backend (1), Data eng (0.5) |
| D: Dashboards | 1 week | Frontend (1), Backend (0.5) |
| **TOTAL** | **6 weeks** | **2 FTE** |

---

## Next Action

Awaiting user confirmation:
1. ✅ Proceed with full implementation (all 4 phases)?
2. 🟡 Start with phases A+B only (org structure + lesson execution)?
3. 🟡 Phase A only (org structure)?

**Recommendation:** Start with **A + B simultaneously** to enable faculty recording by week 3, then add risk detection (Phase C) for full chain.

Should we schedule detailed sprint planning?
