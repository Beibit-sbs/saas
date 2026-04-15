# F3.2 Data Contract — Schema Review Guide

**Target Deadline:** 2026-04-17  
**Reviewer:** Backend Engineering Team Lead  
**Approval Required Before:** F3.3 unfreeze (2026-04-21)

---

## Context

F3 (Intervention Effectiveness Lab) introduces 3 new database tables to track cohort-level analysis of intervention outcomes. This guide helps the backend team review the data contract for correctness, performance, and consistency with platform architecture.

---

## Tables to Review

### Table 1: `app_intervention_cohorts`

**Purpose:** Core cohort record (group of students analyzed together)

**Structure:**
```sql
CREATE TABLE app_intervention_cohorts (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  playbook_execution_id INTEGER NOT NULL,
  cohort_name VARCHAR(255) NOT NULL,
  cohort_size INTEGER NOT NULL CHECK (cohort_size >= 20),
  treatment_group_size INTEGER NOT NULL,
  control_group_size INTEGER NOT NULL,
  outcome_type VARCHAR(50) NOT NULL,
  analysis_window_start DATE NOT NULL,
  analysis_window_end DATE NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, finalized, analyzed
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Foreign keys
  FOREIGN KEY (tenant_id) REFERENCES app_tenants(id),
  FOREIGN KEY (playbook_execution_id) REFERENCES app_intervention_playbook_executions(id),
  
  -- Constraints
  CONSTRAINT chk_cohort_sizes CHECK (treatment_group_size + control_group_size = cohort_size),
  CONSTRAINT chk_dates CHECK (analysis_window_start < analysis_window_end),
  UNIQUE(tenant_id, playbook_execution_id) -- One cohort per playbook execution
);
```

**Review Checklist:**
- [ ] **FK to playbook_executions:** Does FK exist? Check exact table/column name (should be `app_intervention_playbook_executions.id`)
- [ ] **Cohort size >= 20:** FERPA compliance requirement — constraint correct? ✓
- [ ] **Status enum:** `draft→finalized→analyzed` flow matches F3 product contract? ✓
- [ ] **Unique constraint:** Why one cohort per playbook execution? Confirm with product → **CORRECT** (each execution → one analysis cohort)
- [ ] **Indexes needed:**
  - `(tenant_id)` — filtering by tenant (required for RBAC)
  - `(playbook_execution_id)` — lookup by playbook
  - `(status, created_at)` — list cohorts by status, newest first (common query)
  - `(tenant_id, created_at)` — compound index for filter + sort
- [ ] **Partition strategy:** For large-scale (1M+ cohorts), consider partitioning by `created_at` (monthly)? → **FUTURE (not for MVP)**

**Questions for Backend:**
1. Can `playbook_execution_id` be NULL (e.g., manual cohort creation)? → **NO, always from playbook**
2. Should `cohort_name` be UNIQUE per tenant? → **No, allow duplicates (names are UX hint)**
3. Are `analysis_window_start/end` indexed? → **Recommended: ADD INDEX**

---

### Table 2: `app_intervention_cohort_outcomes`

**Purpose:** Analysis results (guardrail pass/fail, uplift metrics, confidence bands)

**Structure:**
```sql
CREATE TABLE app_intervention_cohort_outcomes (
  id SERIAL PRIMARY KEY,
  cohort_id INTEGER NOT NULL,
  outcome_name VARCHAR(255) NOT NULL,
  outcome_type VARCHAR(50) NOT NULL, -- dropout_rate, gpa, enrollment, etc.
  
  -- Metrics
  treatment_metric NUMERIC(10,4) NOT NULL,
  control_metric NUMERIC(10,4) NOT NULL,
  uplift_percent NUMERIC(10,4) NOT NULL,
  
  -- Confidence band (95% CI)
  confidence_lower NUMERIC(10,4) NOT NULL,
  confidence_upper NUMERIC(10,4) NOT NULL,
  confidence_width_pp NUMERIC(10,4) NOT NULL,
  
  -- Guardrails (PASS/FAIL)
  guardrail_confidence_band_pass BOOLEAN NOT NULL,
  guardrail_uniformity_pass BOOLEAN NOT NULL,
  guardrail_completeness_pass BOOLEAN NOT NULL,
  all_guardrails_pass BOOLEAN NOT NULL,
  
  -- Encrypted outcome details (JSON)
  outcome_data_encrypted BYTEA NOT NULL, -- pgcrypto encrypted
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Foreign key
  FOREIGN KEY (cohort_id) REFERENCES app_intervention_cohorts(id) ON DELETE CASCADE,
  
  -- Constraints
  CONSTRAINT chk_confidence_width CHECK (confidence_width_pp <= 8),
  CONSTRAINT chk_completeness CHECK (/* ≥ 90% per group */),
  UNIQUE(cohort_id, outcome_type)
);
```

**Review Checklist:**
- [ ] **FK cascade:** ON DELETE CASCADE for outcomes when cohort deleted? ✓ (correct — clean up by cohort)
- [ ] **Encryption field:** `outcome_data_encrypted BYTEA` — is this correct type for pgcrypto? Check if `pgcrypto` extension loaded
  ```sql
  CREATE EXTENSION IF NOT EXISTS pgcrypto;
  ```
- [ ] **Indexes needed:**
  - `(cohort_id)` — eager load outcomes for a cohort
  - `(all_guardrails_pass)` — filter "all pass" outcomes
  - `(created_at DESC)` — list newest outcomes first
- [ ] **Numeric precision:** NUMERIC(10,4) allows values up to 99.9999 — sufficient for percentages? ✓
- [ ] **UNIQUE constraint:** One outcome per cohort+type → prevents duplicates? ✓
- [ ] **Guardrail boolean logic:** all_guardrails_pass = (confidence_band AND uniformity AND completeness)? Need trigger?

**Questions for Backend:**
1. Should `outcome_data_encrypted` be decrypted in application layer only? → **YES, never in SQL**
2. Are guardrail evaluations done in Python or SQL? → **Python (effectiveness_service.analyze_cohort)**
3. How to query "pass rate %"? Example:
   ```sql
   SELECT 
     (COUNT(*) FILTER (WHERE all_guardrails_pass))::FLOAT / COUNT(*) * 100 as pass_rate
   FROM app_intervention_cohort_outcomes
   WHERE cohort_id IN (SELECT id FROM app_intervention_cohorts WHERE tenant_id = 1);
   ```

---

### Table 3: `app_intervention_cohort_members`

**Purpose:** Individual student-level membership (for audit trail, not for analysis)

**Structure:**
```sql
CREATE TABLE app_intervention_cohort_members (
  id SERIAL PRIMARY KEY,
  cohort_id INTEGER NOT NULL,
  student_id INTEGER NOT NULL,
  group_type VARCHAR(50) NOT NULL, -- treatment, control
  
  created_at TIMESTAMP DEFAULT NOW(),
  
  -- Foreign key
  FOREIGN KEY (cohort_id) REFERENCES app_intervention_cohorts(id) ON DELETE CASCADE,
  
  -- Constraint
  UNIQUE(cohort_id, student_id),
  CONSTRAINT chk_group_type CHECK (group_type IN ('treatment', 'control'))
);
```

**Review Checklist:**
- [ ] **Purpose:** Why store individual members? Audit trail + verification of group composition? ✓
- [ ] **Indexes needed:**
  - `(cohort_id)` — fetch all members for a cohort
  - `(student_id)` — reverse lookup: "which cohorts is student in?"
  - Compound `(cohort_id, group_type)` — count treatment vs control
- [ ] **Constraints:** student_id is PII-adjacent — ensure encrypted/audited? → **DEFER TO TEAM**
- [ ] **Retention:** Members table grows with each cohort. Cleanup policy? → **7-year retention (GDPR)**

**Questions for Backend:**
1. Can one student be in multiple cohorts (overlapping groups)? → **YES, allowed (different playbooks)**
2. Should `student_id` refer to `app_users(id)` FK? → **Possibly, check architecture**
3. How to efficiently fetch "all students in control group for cohort X"?
   ```sql
   SELECT student_id FROM app_intervention_cohort_members 
   WHERE cohort_id = 123 AND group_type = 'control';
   ```

---

## Cross-Table Relationships

**Diagram:**
```
app_intervention_playbook_executions
            ↓ (1:1)
app_intervention_cohorts
    ├─ (1:M) → app_intervention_cohort_outcomes
    └─ (1:M) → app_intervention_cohort_members

app_tenants
    ↓ (1:M)
app_intervention_cohorts
```

**Verification:**
- [ ] Are all FK relationships correct in schema definition?
- [ ] Does schema align with F2 tables (no conflicts on `playbook_execution_id`)?
  - F2 table: `app_intervention_playbook_executions` ← already exists ✓
  - F3 table: `app_intervention_cohorts` → FK to F2 table ✓

---

## F3-Specific Schema Considerations

### 1. FERPA Compliance
- [ ] Minimum cohort size = 20? ✓ (CHECK constraint)
- [ ] No PII exposure (student_id OK in members audit log, but protected by RBAC)
- [ ] Are student names/emails stored? → **NO (by product design)**

### 2. GDPR Compliance
- [ ] 7-year retention: Data auto-deleted? → **Future: migration script cleanup by created_at**
- [ ] Data export capability: Can we SELECT * → JSON? → **Yes, outcomes_encrypted needs decryption**

### 3. Multi-Tenancy & Isolation
- [ ] All 3 tables have `tenant_id` filter? → **Only app_intervention_cohorts; outcomes/members filtered via cohort_id FK**
- [ ] Are queries guaranteed to filter by tenant? → **Yes, through cohort_id JOIN chain**

### 4. Performance & Scalability
- [ ] Expected row counts per table?
  - cohorts: ~10K per year (100 institutions × 100 cohorts)
  - outcomes: ~100K per year (10K cohorts × 10 outcome types avg)
  - members: ~1M+ (10K cohorts × 100 students avg)
- [ ] Indexes sufficient for expected queries? → **Review above**
- [ ] Archive strategy for old data? → **Future: consider partitioning by year**

---

## Recommended Index Additions

```sql
-- app_intervention_cohorts
CREATE INDEX idx_cohorts_tenant_id ON app_intervention_cohorts(tenant_id);
CREATE INDEX idx_cohorts_playbook_exec_id ON app_intervention_cohorts(playbook_execution_id);
CREATE INDEX idx_cohorts_status_created ON app_intervention_cohorts(status, created_at DESC);
CREATE INDEX idx_cohorts_tenant_created ON app_intervention_cohorts(tenant_id, created_at DESC);

-- app_intervention_cohort_outcomes
CREATE INDEX idx_outcomes_cohort_id ON app_intervention_cohort_outcomes(cohort_id);
CREATE INDEX idx_outcomes_guardrail_pass ON app_intervention_cohort_outcomes(all_guardrails_pass);
CREATE INDEX idx_outcomes_created ON app_intervention_cohort_outcomes(created_at DESC);

-- app_intervention_cohort_members
CREATE INDEX idx_members_cohort_id ON app_intervention_cohort_members(cohort_id);
CREATE INDEX idx_members_student_id ON app_intervention_cohort_members(student_id);
CREATE INDEX idx_members_cohort_group ON app_intervention_cohort_members(cohort_id, group_type);
```

---

## Sign-Off Checklist

**Before 2026-04-17 EOD, confirm:**

- [ ] **Schema correctness:** All tables created, FKs valid, constraints working
- [ ] **Performance:** Indexes created, query plans reviewed (no full table scans on large queries)
- [ ] **Compliance:** FERPA/GDPR checks passed
- [ ] **Integration:** No conflicts with existing F2 schema
- [ ] **Alembic migration:** Migration script reviewed + tested locally
- [ ] **Documentation:** Any custom notes on deployment or schema quirks?

**Sign-off template:**
```
✅ APPROVED (Backend Engineering Lead, date)
   - Schema reviewed: OK
   - Performance acceptable: OK
   - No concerns: None
   
   Notes: [optional]
```

---

## References

- **F3 Product Contract:** `docs/F3_PRODUCT_CONTRACT.md` (clarify semantics: uplift %, confidence band, guardrails)
- **F3 Data Contract Diagram:** [TBD — SBS can provide ER diagram if needed]
- **Alembic Migration:** `backend/alembic/versions/*_f3_schema.py`
- **F3 Wiring Checklist:** `docs/runbooks/artifacts/f3_wiring_checklist_20260421.md` (Step 4: run migration)

---

## Q&A Session Schedule

**Optional:** If backend team has questions, schedule 30-min Q&A before 2026-04-17:
- **When:** 2026-04-16 or 2026-04-17 morning
- **Attendees:** Backend Lead, SBS (product/architecture)
- **Topics:** Performance, compliance, integration gaps

**Contact:** [TBD — product owner email]
