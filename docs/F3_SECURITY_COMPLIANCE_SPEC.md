# F3.6 Security & Compliance Specification

**Version:** v1.0  
**Status:** Spec Ready (implementation unfrozen after 2026-04-21)  
**Target Implementation:** 2026-05-10 (after F3.4 frontend completion)  
**Compliance Framework:** FERPA, GDPR, institutional data governance

---

## Overview

F3 processes and stores sensitive intervention effectiveness data (student identifiers indirectly via cohort size, outcome metrics). This spec ensures F3 meets institutional security, privacy, compliance, and audit requirements.

---

## Data Classification

### Data Handled by F3

| Data | Classification | Examples | Retention | Access |
|------|----------------|----------|-----------|--------|
| Cohort metadata | Internal (low sensitivity) | cohort_name, playbook_id, treated_count, control_count | 7 years (audit trail) | Institution admin only |
| Outcome metrics | Internal (low sensitivity) | uplift_percent, dropout_rate, GPA improvement | 7 years | Institution admin only |
| Student identifiers (indirect) | Restricted (FERPA-sensitive) | Via cohort membership, outcome linkage to academic records | 7 years (regulatory) | Institutional Research only |
| Analyst audit trail | Internal | finalized_by, analyzed_at, actor | Forever (audit trail) | Ops/Compliance only |

### Data NOT Handled by F3

- Individual student names, IDs, PII (F3 sees only cohort aggregates)
- Specific intervention content or curriculum (F2 domain)
- External user data from third-party systems

---

## Compliance Requirements

### FERPA (Family Educational Rights and Privacy Act)

**Requirement:** Prevent re-identification of individual students through outcome data.

**F3 Safeguards:**
- **Aggregate threshold:** Do not report outcomes for cohorts < 20 students (re-identification risk)
  - Test: `test_f3_security_minimum_cohort_size.py`
- **No student-level drilldown:** API `/outcomes` endpoint returns only cohort-level aggregates, never individual student records
  - Test: `test_f3_api_no_individual_student_exposure.py`
- **Audit logging:** Log all analyst queries to outcomes (for access review)
  - Test: `test_f3_audit_trail_completeness.py`

### GDPR (General Data Protection Regulation) — EU Pilots Only

**Requirement:** Right to erasure, data minimization, consent.

**F3 Safeguards:**
- **Data retention policy:** Outcome data deleted after 7 years (configurable per regulatory requirement)
  - Implementation: `backend/app/modules/interventions/gdpr_retention_service.py`
- **Consent tracking:** F3 assumes institution has obtained student consent for academic outcome tracking (outside F3 scope)
- **Data export:** Provide institutional research team ability to export anonymized cohort analysis for DPIA
  - Endpoint: `GET /api/admin/interventions/cohorts/{cohort_id}/export?format=json|csv`

### Institutional Data Governance

**Requirement:** Align F3 data handling with institutional policy (Data Stewardship Model, DMP, etc.).

**F3 Safeguards:**
- **Data stewardship:** Institutional Research = data steward for F3 outcomes
  - Role RBAC: `institutional_research` scope required for export
- **Classification labels:** Mark F3 outcomes as "Institutional Research — Confidential" in audit logs
- **Incident response:** F3 includes incident response playbook for data breach scenario
  - Runbook: `docs/runbooks/F3_DATA_BREACH_RESPONSE.md`

---

## RBAC & Access Control

### Required Scopes

| Scope | Operations | Users |
|-------|-----------|-------|
| `effectiveness.read` | View cohorts, list outcomes, read analysis | Program manager, dean, admin |
| `effectiveness.write` | Create/finalize cohorts | Program manager, admin |
| `effectiveness.export` | Export analysis to PDF/CSV | Institutional research, compliance officer |
| `effectiveness.admin` | Delete cohorts (after hold period), adjust guardrails | Platform admin only |

### Tenant Isolation

**Requirement:** A user from tenant A cannot access tenant B's cohorts.

**F3 Safeguards:**
- **Middleware:** All F3 endpoints require `X-Tenant-ID` header + validation
  - Test: `test_f3_tenant_isolation.py`
- **Query filtering:** SQL WHERE clause always includes `tenant_id = current_tenant_id`
  - Test: `test_f3_cross_tenant_access_denied.py`
- **Audit log:** All cross-tenant access attempts logged + alerted
  - Prometheus metric: `f3_unauthorized_cross_tenant_attempts_total`

---

## Data Protection

### Encryption at Rest

**Requirement:** Outcome data encrypted in database.

**Implementation:**
- **PostgreSQL encryption:** Use pgcrypto extension + column-level encryption for sensitive fields
  - Fields: `outcome_data` (JSON blob containing uplift, CI bounds)
  - SQL: `CREATE EXTENSION pgcrypto; ALTER TABLE app_intervention_cohorts_outcomes ADD COLUMN outcome_data_encrypted bytea;`
- **Key rotation:** Master key rotated annually
  - Test: `test_f3_encryption_key_rotation.py`

### Encryption in Transit

**Requirement:** HTTPS + TLS 1.2+ for all F3 API calls.

**Implementation:**
- **Nginx reverse proxy:** Force HTTPS + HSTS header (`Strict-Transport-Security: max-age=31536000`)
  - Config: `infra/nginx/f3-effectiveness-locations.conf`
- **TLS 1.2+ only:** Disable TLS 1.0, 1.1
- **Test:** `test_f3_api_tls_enforcement.py`

---

## Input Validation & Injection Prevention

### Input Validation

**Requirement:** Prevent malformed input from breaking analysis or exposing vulnerabilities.

**F3 Safeguards:**

| Input | Validation |
|-------|-----------|
| `cohort_name` | Max 256 chars, alphanumeric + spaces + hyphens only, no SQL |
| `analysis_window_start` | ISO 8601 date, must be before `analysis_window_end` |
| `treated_count` | Integer, 20–10000 (FERPA threshold + practical limit) |
| `control_count` | Integer, 20–10000 |
| `comparison_type` | ENUM: `dropout_rate` \| `gpa_improvement` (whitelist) |

**Implementation:**
- Pydantic schema validation in `effectiveness_schemas.py`
- Test: `test_f3_input_validation_comprehensive.py` (40+ cases)

### SQL Injection Prevention

**Requirement:** No SQL injection via user input.

**F3 Safeguards:**
- **Parametrized queries:** SQLAlchemy ORM (not raw SQL)
  - Example: `session.query(InterventionCohortModel).filter_by(tenant_id=tenant_id).all()`
  - NOT: `session.execute(f"SELECT * FROM cohorts WHERE tenant_id = {tenant_id}")`
- **Test:** `test_f3_sql_injection_attempts.py` (pen-test style)

---

## Audit Logging & Forensics

### Audit Trail

**Requirement:** Record all F3 operations for forensic investigation.

**F3 Safeguards:**

| Operation | Logged fields |
|-----------|--------------|
| Finalize cohort | tenant_id, cohort_id, actor, timestamp, result (success/error) |
| Analyze cohort | tenant_id, cohort_id, actor, outcomes count, guardrails pass/fail |
| View cohort | tenant_id, cohort_id, user_id, timestamp |
| Export cohort | tenant_id, cohort_id, user_id, format, timestamp, bytes_exported |
| Delete cohort | tenant_id, cohort_id, actor, reason, timestamp |

**Log format:** JSON structured logs (Loguru)

**Example:**
```json
{
  "timestamp": "2026-05-10T14:32:15.123Z",
  "operation": "finalize_cohort",
  "tenant_id": 1,
  "cohort_id": 999,
  "actor": "program_mgr_001",
  "result": "success",
  "ip_address": "10.0.1.20",
  "user_agent": "Mozilla/5.0...",
  "duration_ms": 145
}
```

**Retention:** 7 years (FERPA requirement for educational records)

**Access:** Only auditor + compliance officer roles

---

## Secrets Management

### API Keys & Credentials

**Requirement:** Secrets never stored plaintext in code or config.

**F3 Safeguards:**
- **Environment variables:** All secrets loaded from `.env` (not in git)
- **Key rotation:** Master keys rotated quarterly
  - Kubernetes secret: `f3-encryption-master-key`
- **Audit:** All secret access logged (Vault or K8s audit log)

### JWT/Tokens

**Requirement:** F3 REST API secured with OAuth2 bearer tokens.

**Implementation:**
- **Token validation:** All requests must include `Authorization: Bearer <jwt>`
- **Scope validation:** JWT must include `effectiveness.read` or `effectiveness.write` claim
- **Token expiry:** 1 hour (short-lived), refresh tokens valid 7 days
- **Test:** `test_f3_api_token_validation.py`

---

## Incident Response

### Data Breach

**Scenario:** Unauthorized disclosure of cohort outcome data.

**Response steps:**
1. Immediately disable affected cohort exports (set status = `BREACH_HOLD`)
2. Notify compliance officer + institutional research team
3. Audit all recent exports + access logs
4. File incident report + notify regulatory body if required (GDPR)
5. Document timeline + remediation in `/logs/incidents/`

**Runbook:** `docs/runbooks/F3_DATA_BREACH_RESPONSE.md`

### Service Unavailability

**Scenario:** F3 API becomes inaccessible during critical analysis window.

**Runbook:** `docs/runbooks/F3_OUTAGE_RESPONSE.md`

**Response:**
- Alert on-call SRE
- Check database connectivity + perform failover if needed
- Restore from backup if data corruption
- Notify PMs/admins of ETA via institutional status page

**Runbook:** `docs/runbooks/F3_OUTAGE_RESPONSE.md`

---

## Compliance Tests (CI/CD)

**File:** `backend/tests/security/test_f3_compliance.py`

```python
# FERPA tests
- test_cohort_minimum_size_enforcement (cohort < 20 raises error)
- test_no_individual_student_exposure (API returns only aggregates)
- test_audit_trail_completeness (all ops logged)

# GDPR tests (EU tenants only)
- test_data_retention_policy_enforcement (7-year retention)
- test_user_export_right (export data in machine-readable format)
- test_erasure_workflow (delete student records when requested)

# RBAC tests
- test_tenant_isolation (cross-tenant access denied)
- test_scope_validation (only scoped users can access)
- test_unauthorized_export (non-research users cannot export)

# Data protection tests
- test_encryption_at_rest (columns encrypted)
- test_tls_enforcement (TLS 1.2+ only)
- test_sql_injection_attempts (parametrized queries hold)
- test_input_validation_comprehensive (all fields validated)
```

**CI gate:** All compliance tests must pass before merge to main.

---

## Monitoring & Alerting

### Security Metrics

| Metric | Alert threshold |
|--------|-----------------|
| Failed auth attempts (per user) | > 10 in 1 hour → account lockout |
| Cross-tenant access attempts | > 0 → instant alert + log review |
| Unauthorized export attempts | > 0 → instant alert |
| Encryption key rotation overdue | > 365 days → warning |
| Audit log retention < 90 days | → warning |

### Log Aggregation

**Centralize:** ELK stack (Elasticsearch + Kibana)

**Dashboards:**
- `F3 Security & Compliance` — audit trail, failed attempts, cross-tenant alerts
- `F3 Data Access` — who accessed what, when, why

---

## Documentation Requirements

| Artifact | Owner | Deadline |
|----------|-------|----------|
| F3 Security Runbook | Compliance | 2026-05-10 |
| Data Breach Response Plan | Ops | 2026-05-10 |
| FERPA Compliance Checklist | Compliance | 2026-05-10 |
| Encryption Key Rotation SOP | DevOps | 2026-05-10 |
| Pen-test report (external) | Security team | 2026-05-12 |

---

## Success Criteria

F3.6 Security & Compliance is **complete** when:

- [ ] All FERPA safeguards implemented + tested
- [ ] Encryption at rest + in transit enabled + validated
- [ ] RBAC + tenant isolation verified by pen-test
- [ ] Audit logging complete + 7-year retention enabled
- [ ] All compliance tests in CI passing
- [ ] Security runbooks written + validated by ops
- [ ] External pen-test performed + findings remediated (if any)
- [ ] FERPA compliance checklist signed by compliance officer

---

## References

- **FERPA:** [US Department of Education — FERPA](https://www2.ed.gov/policy/gen/guid/fpco/ferpa/)
- **GDPR:** [EU GDPR Regulation 2016/679](https://gdpr-info.eu/)
- **Institutional Policy:** Data Stewardship Model (provided by institution)
- **Backend API:** [F3_EXECUTION_PLAN.md](F3_EXECUTION_PLAN.md)
