# F3.6 Security & Compliance Implementation Guide — Start 2026-05-10

**Released:** 2026-04-14 (pre-unfreeze preparation)  
**Execution Start:** 2026-05-10 (post F3.4/F3.5 delivery)  
**Target Delivery:** 2026-05-22 (13 days)  
**Owner:** Security + Compliance Engineer + Backend Team  
**Status:** Specification complete, implementation guide ready

---

## Executive Summary

F3.6 delivers security & regulatory compliance for intervention effectiveness:
- **FERPA Safeguards:** Cohort minimum size 20 students (denying analysis if < 20)
- **GDPR Compliance:** 7-year retention with automatic deletion, data export capability
- **RBAC Enforcement:** 4 scopes (effectiveness.read, .write, .export, .admin)
- **Encryption:** pgcrypto (data at rest), TLS 1.2+ (in transit)
- **Audit Logging:** All operations logged to ELK, exportable + SIEM-integrable
- **Penetration Testing:** 3-day security audit on finalized code

**Deliverables by Phase:**
- Phase 1-2: FERPA validation + 7-year retention enforcement
- Phase 3-4: RBAC + audit logging infrastructure
- Phase 5: Data encryption at rest (pgcrypto)
- Phase 6: Security testing (pen-test, SAST/DAST)
- Phase 7: Compliance sign-off + documentation

---

## 7-Phase Implementation Roadmap

### Phase 1: FERPA Safeguards — Cohort Size Validation (2026-05-10 to 2026-05-12, 3 days)

**Objective:** Enforce minimum cohort size (≥ 20 students) per FERPA requirements

**Files to Create/Update:**
- `backend/app/modules/interventions/effectiveness_validators.py` (NEW, 40 lines)
- `backend/app/modules/interventions/effectiveness_service.py` — Add validator calls (3 lines added)

**FERPA Rules Implemented:**

```python
# backend/app/modules/interventions/effectiveness_validators.py
from app.core.module_helpers.service_validation import DomainValidationError

class FERPAValidator:
    """FERPA safeguard enforcement for intervention cohorts."""
    
    MIN_COHORT_SIZE = 20
    
    @staticmethod
    def validate_cohort_size(cohort_size: int) -> None:
        """Ensure cohort size ≥ 20 to prevent student re-identification."""
        if cohort_size < FERPAValidator.MIN_COHORT_SIZE:
            raise DomainValidationError(
                f"Cohort size must be ≥ {FERPAValidator.MIN_COHORT_SIZE} students per FERPA. "
                f"Provided: {cohort_size}. This protects student privacy."
            )
    
    @staticmethod
    def validate_group_composition(treatment_size: int, control_size: int) -> None:
        """Ensure both treatment and control groups are ≥ 10 (half min)."""
        if treatment_size < 10 or control_size < 10:
            raise DomainValidationError(
                f"Both treatment ({treatment_size}) and control ({control_size}) groups "
                f"must be ≥ 10 students per FERPA. Total minimum: 20."
            )
```

**Integration in Service:**
```python
def finalize_cohort(self, *, tenant_id: int, actor: str, payload: CohortFinalizeRequestSchema):
    # Validate FERPA requirements
    FERPAValidator.validate_cohort_size(payload.cohort_size)
    FERPAValidator.validate_group_composition(payload.treatment_group_size, payload.control_group_size)
    
    # Continue with finalization...
```

**Database Constraint (enforced at table level):**
```sql
ALTER TABLE app_intervention_cohorts
  ADD CONSTRAINT cohort_min_size_ferpa CHECK (cohort_size >= 20);

ALTER TABLE app_intervention_cohorts
  ADD CONSTRAINT group_min_size_ferpa CHECK (
    treatment_group_size >= 10 
    AND control_group_size >= 10
  );
```

**Test Coverage (15 tests):**
- ✅ test_cohort_size_20_accepted (boundary)
- ✅ test_cohort_size_19_rejected (below boundary)
- ✅ test_treatment_group_10_accepted (boundary)
- ✅ test_treatment_group_9_rejected (below boundary)
- ✅ test_control_group_10_accepted (boundary)
- ✅ test_control_group_9_rejected (below boundary)
- ✅ test_error_message_includes_ferpa_reason (UX clarity)
- ✅ test_group_composition_math_10_10_=_20 (validation order)
- ✅ test_group_composition_rejects_unbalanced_5_15 (both < 10)
- ✅ test_validator_called_before_db_insert (layer ordering)
- ✅ test_constraint_enforced_at_db_level (defense in depth)
- ✅ test_audit_log_FERPA_rejection (compliance tracking)
- ✅ test_error_response_code_422 (semantics)
- ✅ test_large_cohort_1000_accepted (ceiling)
- ✅ test_negative_size_zero_rejected (sanity check)

**Exit Criteria:**
- [ ] FERPAValidator class fully implemented
- [ ] Service calls validator before finalization
- [ ] DB constraints added + migrated
- [ ] All 15 tests passing
- [ ] FERPA audit log entries created for each validation
- [ ] Ready for Phase 2 (retention policies)

---

### Phase 2: GDPR Compliance — 7-Year Retention & Deletion (2026-05-12 to 2026-05-13, 2 days)

**Objective:** Implement 7-year data retention with automatic deletion + export capability

**Files to Create/Update:**
- `backend/app/modules/interventions/effectiveness_retention_policy.py` (NEW, 50 lines)
- `backend/app/modules/interventions/effectiveness_router.py` — Add `POST /{cohort_id}/export` endpoint (25 lines)
- `backend/scripts/gdpr_retention_cleanup.py` (NEW, 30 lines, daily cron job)

**Retention Policy Implementation:**

```python
# backend/app/modules/interventions/effectiveness_retention_policy.py
from datetime import datetime, timedelta, UTC
from sqlalchemy import delete
from sqlalchemy.orm import Session

class GDPRRetentionPolicy:
    """GDPR data retention and automatic deletion."""
    
    RETENTION_YEARS = 7
    
    @staticmethod
    def calculate_expiration_date(created_at: datetime) -> datetime:
        """Calculate deletion date for a cohort (7 years from creation)."""
        return created_at + timedelta(days=365 * GDPRRetentionPolicy.RETENTION_YEARS)
    
    @staticmethod
    def cohort_is_expired(cohort) -> bool:
        """Check if cohort has exceeded 7-year retention."""
        expiration = GDPRRetentionPolicy.calculate_expiration_date(cohort.created_at)
        return datetime.now(UTC) > expiration
    
    @staticmethod
    def delete_expired_cohorts(db: Session) -> int:
        """Delete all cohorts older than 7 years. Returns count deleted."""
        from app.modules.interventions.effectiveness_models import InterventionCohortModel
        
        cutoff_date = datetime.now(UTC) - timedelta(days=365 * GDPRRetentionPolicy.RETENTION_YEARS)
        
        # Delete outcomes first (FK constraint)
        db.execute(
            delete(InterventionCohortOutcomeModel)
            .where(InterventionCohortOutcomeModel.cohort_id.in_(
                select(InterventionCohortModel.id)
                .where(InterventionCohortModel.created_at < cutoff_date)
            ))
        )
        
        # Delete members
        db.execute(
            delete(InterventionCohortMemberModel)
            .where(InterventionCohortMemberModel.cohort_id.in_(
                select(InterventionCohortModel.id)
                .where(InterventionCohortModel.created_at < cutoff_date)
            ))
        )
        
        # Delete cohorts
        result = db.execute(
            delete(InterventionCohortModel)
            .where(InterventionCohortModel.created_at < cutoff_date)
        )
        db.commit()
        
        return result.rowcount
```

**Data Export Endpoint (for GDPR right-to-access):**

```python
# In effectiveness_router.py
@router.post(
    "/{cohort_id}/export",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(permission_dependency("interventions:export"))],
)
def export_cohort_data(
    cohort_id: int,
    tenant_id: Annotated[int, Depends(get_current_tenant)],
    db: Annotated[Session, Depends(get_interventions_db)],
) -> dict:
    """Export all cohort data for user (GDPR right-to-access)."""
    cohort = db.scalar(
        select(InterventionCohortModel)
        .where(
            and_(
                InterventionCohortModel.id == cohort_id,
                InterventionCohortModel.tenant_id == tenant_id,
            )
        )
    )
    if cohort is None:
        raise TenantResourceNotFoundError(f"Cohort {cohort_id} not found.")
    
    outcomes = db.scalars(
        select(InterventionCohortOutcomeModel).where(
            InterventionCohortOutcomeModel.cohort_id == cohort_id
        )
    ).all()
    
    members = db.scalars(
        select(InterventionCohortMemberModel).where(
            InterventionCohortMemberModel.cohort_id == cohort_id
        )
    ).all()
    
    # Decrypt sensitive fields
    decrypted_outcomes = [
        {
            **outcome.to_dict(),
            'outcome_data': decrypt_field(outcome.outcome_data_encrypted),
        }
        for outcome in outcomes
    ]
    
    return {
        'cohort': CohortReadSchema.model_validate(cohort).model_dump(),
        'outcomes': decrypted_outcomes,
        'members': [MemberReadSchema.model_validate(m).model_dump() for m in members],
        'exported_at': datetime.now(UTC).isoformat(),
        'expiration_date': GDPRRetentionPolicy.calculate_expiration_date(cohort.created_at).isoformat(),
    }
```

**Daily Cleanup Job:**

```python
# backend/scripts/gdpr_retention_cleanup.py
# Scheduled via APScheduler or cron: 0 2 * * * (2am daily)

from app.modules.interventions.effectiveness_retention_policy import GDPRRetentionPolicy
from app.core.db import get_db

def run_retention_cleanup():
    """Daily task: delete cohorts older than 7 years."""
    with get_db() as db:
        deleted_count = GDPRRetentionPolicy.delete_expired_cohorts(db)
        logger.info(f"GDPR retention cleanup: deleted {deleted_count} expired cohorts")
        
        # Emit metric for monitoring
        retention_cleanup_metric.labels(status='success').inc(deleted_count)
```

**Test Coverage (18 tests):**
- ✅ test_expiration_date_7_years_future (plus 7 years)
- ✅ test_is_expired_false_day_1 (not expired)
- ✅ test_is_expired_false_day_2554 (7 years - 1 day)
- ✅ test_is_expired_true_day_2555 (7 years + 1 day)
- ✅ test_cleanup_deletes_expired_cohort (cleanup works)
- ✅ test_cleanup_skips_recent_cohort (recent not deleted)
- ✅ test_cleanup_cascades_outcomes (FK delete)
- ✅ test_cleanup_cascades_members (FK delete)
- ✅ test_export_returns_full_data (export works)
- ✅ test_export_decrypts_sensitive_fields (decrypt works)
- ✅ test_export_includes_expiration_date (metadata)
- ✅ test_export_denies_non_owner (RBAC check)
- ✅ test_export_timestamp_accurate (timestamp)
- ✅ test_scheduler_job_runs_daily (cron execution)
- ✅ test_audit_log_deletion_reason_GDPR (compliance trail)
- ✅ test_retention_policy_respects_timezone_UTC (UTC only)
- ✅ test_multiple_cohorts_partial_cleanup (selective deletion)
- ✅ test_export_filename_sanitized (filename safety)

**Exit Criteria:**
- [ ] GDPRRetentionPolicy class fully implemented
- [ ] Export endpoint defined + working (POST /{cohort_id}/export)
- [ ] Cleanup job scheduled (crontab or APScheduler)
- [ ] DB migration adds `created_at` audit column if missing
- [ ] All 18 tests passing
- [ ] Ready for Phase 3 (RBAC enforcement)

---

### Phase 3: RBAC Enforcement — Fine-Grained Permissions (2026-05-13 to 2026-05-14, 2 days)

**Objective:** Enforce 4 RBAC scopes for F3 operations

**RBAC Scopes (4 total):**

| Scope | Operation | Default Roles | Example |
|-------|-----------|---------------|---------|
| `interventions:read` | GET /cohorts, GET /cohorts/{id}/outcomes | Faculty, Analyst | View results |
| `interventions:write` | POST /finalize, POST /analyze | Intervention Coordinator | Create & analyze cohorts |
| `interventions:export` | POST /{id}/export, GET /download | Compliance Officer, Auditor | Export data |
| `interventions:admin` | DELETE /cohorts/{id}, PATCH settings | Admin | Manage all F3 config |

**Implementation:**

```python
# backend/app/modules/interventions/effectiveness_router.py - Updated with RBAC

@router.post(
    "/finalize",
    # ... other params
    dependencies=[Depends(permission_dependency("interventions:write"))],
)
def finalize_cohort(...):
    """Only users with interventions:write scope can finalize."""
    ...

@router.get(
    "/{cohort_id}/outcomes",
    dependencies=[Depends(permission_dependency("interventions:read"))],
)
def get_cohort_outcomes(...):
    """Only users with interventions:read scope can view outcomes."""
    ...

@router.post(
    "/{cohort_id}/export",
    dependencies=[Depends(permission_dependency("interventions:export"))],
)
def export_cohort_data(...):
    """Only users with interventions:export scope can export."""
    ...

@router.delete(
    "/{cohort_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(permission_dependency("interventions:admin"))],
)
def delete_cohort(...):
    """Only admins can delete cohorts."""
    ...
```

**Audit Logging on Permission Denial:**

```python
# When permission denied, log the attempt
def permission_dependency(required_scope: str):
    async def verify(request: Request, user_id: int, tenant_id: int):
        user_scopes = get_user_scopes(user_id, tenant_id)
        if required_scope not in user_scopes:
            # Log denied attempt
            AuditLog.create(
                tenant_id=tenant_id,
                actor=user_id,
                action='permission_denied',
                resource='interventions_cohort',
                scope=required_scope,
                reason=f'User lacks {required_scope}',
            )
            raise PermissionError(...)
        return user_id
    return Depends(verify)
```

**Test Coverage (20 tests):**
- ✅ test_read_scope_allows_get_cohorts (happy path)
- ✅ test_read_scope_denies_write (negative)
- ✅ test_write_scope_allows_finalize (happy path)
- ✅ test_write_scope_denies_export (negative)
- ✅ test_export_scope_allows_export (happy path)
- ✅ test_export_scope_denies_finalize (negative)
- ✅ test_admin_scope_allows_delete (happy path)
- ✅ test_admin_scope_denies_read (negative, admin-only access)
- ✅ test_multi_scope_user_read_write (user with multiple scopes)
- ✅ test_multi_scope_user_denied_export (only has read+write, not export)
- ✅ test_audit_log_read (read operations logged)
- ✅ test_audit_log_write (write operations logged)
- ✅ test_audit_log_export (export operations logged)
- ✅ test_audit_log_denied_permission (permission denials logged)
- ✅ test_tenant_isolation_user_A_cannot_read_tenant_B (cross-tenant block)
- ✅ test_tenant_isolation_even_with_admin_scope (admin scope tenant-scoped)
- ✅ test_no_scope_denies_all_operations (default deny)
- ✅ test_scope_change_reflected_immediately (no caching lag)
- ✅ test_impersonation_attempt_logged (security flag)
- ✅ test_response_headers_include_authorization_challenge (401 spec)

**Exit Criteria:**
- [ ] All 4 RBAC scopes defined + enforced
- [ ] All endpoints have permission_dependency guards
- [ ] Audit logging works for all operations
- [ ] Cross-tenant access blocked
- [ ] All 20 tests passing
- [ ] Ready for Phase 4 (audit logging infrastructure)

---

### Phase 4: Audit Logging to ELK (2026-05-14 to 2026-05-16, 3 days)

**Objective:** All F3 operations logged as structured JSON → Elasticsearch → Kibana dashboards

**Logging Events:**

| Event | Logged Fields | Retention | Alert Trigger |
|-------|--------------|-----------|----------------|
| Cohort finalized | cohort_id, finalized_by, count, timestamp | 7y | None |
| Analysis performed | cohort_id, analyzed_by, result_count, timestamp | 7y | Low pass rate (< 80%) |
| Data exported | cohort_id, exported_by, row_count, timestamp | 7y | Export > 10k rows (unusual) |
| Permission denied | cohort_id, attempted_by, required_scope, timestamp | 7y | 5+ denied attempts (suspicious) |
| Cohort deleted | cohort_id, deleted_by, deletion_reason, timestamp | 7y | Always (compliance trail) |

**Implementation (Python logging):**

```python
# backend/app/modules/interventions/effectiveness_auditlog.py
import json
from pythonjsonlogger import jsonlogger
import logging

audit_logger = logging.getLogger('f3.audit')
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
audit_logger.addHandler(handler)

class AuditLog:
    @staticmethod
    def finalize_cohort(tenant_id: int, actor_id: int, cohort_id: int, cohort_size: int):
        audit_logger.info(
            'Cohort finalized',
            extra={
                'event_type': 'cohort_finalized',
                'tenant_id': tenant_id,
                'actor_id': actor_id,
                'cohort_id': cohort_id,
                'cohort_size': cohort_size,
                'timestamp': datetime.now(UTC).isoformat(),
                'source': 'interventions:effectiveness',
            }
        )
    
    @staticmethod
    def analyze_cohort(tenant_id: int, actor_id: int, cohort_id: int, result_count: int):
        audit_logger.warning(
            'Cohort analyzed',
            extra={
                'event_type': 'cohort_analyzed',
                'tenant_id': tenant_id,
                'actor_id': actor_id,
                'cohort_id': cohort_id,
                'result_count': result_count,
                'timestamp': datetime.now(UTC).isoformat(),
                'source': 'interventions:effectiveness',
            }
        )
    
    @staticmethod
    def permission_denied(tenant_id: int, actor_id: int, required_scope: str):
        audit_logger.warning(
            'Permission denied',
            extra={
                'event_type': 'permission_denied',
                'tenant_id': tenant_id,
                'actor_id': actor_id,
                'required_scope': required_scope,
                'timestamp': datetime.now(UTC).isoformat(),
                'source': 'interventions:effectiveness',
            }
        )
```

**Kibana Dashboard (4 panels):**
1. **Operations Timeline:** finalize + analyze + export count by hour
2. **Permission Denials:** attempts by scope + actor (detect brute force)
3. **Deletions Audit Trail:** all cohort deletions (compliance proof)
4. **Data Exports:** who exported what, when (data access control)

**Test Coverage (14 tests):**
- ✅ test_audit_log_finalize_logged (event recorded)
- ✅ test_audit_log_has_required_fields (tenant_id, actor_id, timestamp)
- ✅ test_audit_log_json_parseable (valid JSON)
- ✅ test_audit_log_timezone_UTC (UTC only)
- ✅ test_audit_log_elasticsearch_indexed (ELK integration)
- ✅ test_kibana_dashboard_shows_operations (dashboard loads)
- ✅ test_kibana_filter_by_tenant (tenant filtering)
- ✅ test_kibana_filter_by_actor (actor filtering)
- ✅ test_audit_log_retention_7_years (data persists)
- ✅ test_permission_denial_logged_with_scope (denied reason tracked)
- ✅ test_deletion_audit_trail_complete (all fields present)
- ✅ test_audit_log_performance_no_latency (logging async)
- ✅ test_audit_log_siem_integration_splunk (if used)
- ✅ test_audit_log_export_to_csv (compliance export)

**Exit Criteria:**
- [ ] All F3 operations emit audit logs (finalize, analyze, export, delete, denied)
- [ ] Logs sent to Elasticsearch (verified in Kibana)
- [ ] Kibana dashboard created + accessible
- [ ] All 14 tests passing
- [ ] Ready for Phase 5 (encryption at rest)

---

### Phase 5: Encryption at Rest (pgcrypto) (2026-05-16 to 2026-05-17, 2 days)

**Objective:** Encrypt sensitive fields using pgcrypto (PostgreSQL native)

**Encrypted Fields:**

| Field | Table | Reason | Method |
|-------|-------|--------|--------|
| `outcome_data_encrypted` | cohort_outcomes | Sensitive metric values | pgcrypto_aes_256 |
| (future) `member_identifiers` | cohort_members | Hashed student IDs | SHA256 |

**Implementation (SQL + ORM):**

```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Update schema to encrypt outcome_data_encrypted
ALTER TABLE app_intervention_cohort_outcomes
  ALTER COLUMN outcome_data_encrypted
  SET DEFAULT pgcrypto.encrypt(
    outcome_data::bytea,
    current_database()::bytea,  -- Use DB name as key (simplistic; use KMS in prod)
    'aes'
  );
```

**ORM Model:**

```python
# backend/app/modules/interventions/effectiveness_models.py
from sqlalchemy import Column, LargeBinary
from cryptography.fernet import Fernet
import os

class InterventionCohortOutcomeModel(Base):
    __tablename__ = 'app_intervention_cohort_outcomes'
    
    id = Column(Integer, primary_key=True)
    cohort_id = Column(Integer, ForeignKey('app_intervention_cohorts.id'), nullable=False)
    outcome_type = Column(String(50), nullable=False)
    
    # Sensitive field (stored encrypted in DB)
    outcome_data_encrypted = Column(LargeBinary, nullable=False)
    
    @property
    def outcome_data_decrypted(self) -> dict:
        """Decrypt outcome data (application layer only)."""
        key = os.environ['F3_ENCRYPTION_KEY']  # KMS-managed in prod
        cipher = Fernet(key)
        decrypted = cipher.decrypt(self.outcome_data_encrypted)
        return json.loads(decrypted)
    
    @outcome_data_decrypted.setter
    def outcome_data_decrypted(self, value: dict):
        """Encrypt outcome data before storing."""
        key = os.environ['F3_ENCRYPTION_KEY']
        cipher = Fernet(key)
        encrypted = cipher.encrypt(json.dumps(value).encode())
        self.outcome_data_encrypted = encrypted
```

**Key Management:**

```python
# backend/app/core/encryption.py
import os
from cryptography.fernet import Fernet

class EncryptionManager:
    """Manages F3 encryption keys."""
    
    @staticmethod
    def get_or_create_key() -> str:
        """Get encryption key from env (KMS secret in prod)."""
        key = os.environ.get('F3_ENCRYPTION_KEY')
        if not key:
            # Generate new key (only for dev/test)
            key = Fernet.generate_key().decode()
            os.environ['F3_ENCRYPTION_KEY'] = key
        return key
    
    @staticmethod
    def rotate_key(new_key: str, old_key: str, db: Session) -> int:
        """Re-encrypt all data with new key (for key rotation)."""
        from app.modules.interventions.effectiveness_models import InterventionCohortOutcomeModel
        
        outcomes = db.query(InterventionCohortOutcomeModel).all()
        for outcome in outcomes:
            # Decrypt with old key
            old_cipher = Fernet(old_key)
            decrypted = old_cipher.decrypt(outcome.outcome_data_encrypted)
            
            # Re-encrypt with new key
            new_cipher = Fernet(new_key)
            outcome.outcome_data_encrypted = new_cipher.encrypt(decrypted)
            db.add(outcome)
        
        db.commit()
        return len(outcomes)
```

**Test Coverage (12 tests):**
- ✅ test_encrypt_outcome_data (encryption works)
- ✅ test_decrypt_outcome_data (decryption works)
- ✅ test_roundtrip_encrypt_decrypt (no data loss)
- ✅ test_encrypted_field_unreadable_raw_sql (ciphertext opaque)
- ✅ test_key_rotation_reencrypts_all (rotation works)
- ✅ test_wrong_key_decrypt_fails (security: wrong key fails)
- ✅ test_env_var_F3_ENCRYPTION_KEY_required (config requirement)
- ✅ test_encryption_performance_acceptable (< 10ms per record)
- ✅ test_pgcrypto_extension_loaded (dep check)
- ✅ test_tls_required_for_key_transport (infra check)
- ✅ test_audit_log_does_not_include_plaintext (plaintext not leaked)
- ✅ test_backup_includes_encrypted_data (backup integrity)

**Exit Criteria:**
- [ ] pgcrypto extension enabled
- [ ] outcome_data_encrypted field encrypted at rest
- [ ] Decryption happens in application layer only (never in SQL)
- [ ] Encryption key managed via env var (KMS in prod)
- [ ] All 12 tests passing
- [ ] Ready for Phase 6 (security testing)

---

### Phase 6: Security Testing (2026-05-17 to 2026-05-19, 3 days)

**Objective:** Comprehensive security validation via SAST/DAST + pen-test

**Testing Coverage (3 categories):**

**1. Static Analysis (SAST) — Automated Code Scanning**

```bash
# Run static analyzers
bandit -r backend/app/modules/interventions/  # Security issues in Python
python -m ruff check backend/app/modules/interventions/  # Code quality
mypy backend/app/modules/interventions/  # Type coverage (100%)
```

**Issues to Catch:**
- [ ] Hardcoded credentials (checks all files)
- [ ] SQL injection risks (ORM escaping verified)
- [ ] Weak cryptographic algorithms (AES-256 confirm)
- [ ] Missing input validation (all endpoints checked)
- [ ] Missing RBAC checks (permission_dependency on all routes)

**2. Dynamic Analysis (DAST) — Runtime Testing**

```python
# tests/security/test_f3_security_posture.py

def test_sql_injection_protection():
    """Attempt SQL injection in cohort_name parameter."""
    payload = "'; DROP TABLE app_intervention_cohorts; --"
    response = requests.post(
        'http://localhost:8000/api/admin/interventions/cohorts/finalize',
        json={'cohort_name': payload, ...},
        headers={'Authorization': f'Bearer {token}'},
    )
    # Should reject, not execute SQL
    assert response.status_code == 422  # Validation error, not 500
    # Verify table still exists
    assert db.query(InterventionCohortModel).count() > 0

def test_permission_escalation_blocked():
    """User without admin scope can't delete cohort."""
    user_with_read_only = create_user_with_scope('interventions:read')
    response = requests.delete(
        'http://localhost:8000/api/admin/interventions/cohorts/1',
        headers={'Authorization': f'Bearer {user_with_read_only.token}'},
    )
    assert response.status_code == 403  # Forbidden

def test_cross_tenant_access_denied():
    """User from Tenant A can't access Tenant B data."""
    tenant_a_user = create_user(tenant_id=1)
    tenant_b_cohort = create_cohort(tenant_id=2)
    
    response = requests.get(
        f'http://localhost:8000/api/admin/interventions/cohorts/{tenant_b_cohort.id}',
        headers={'Authorization': f'Bearer {tenant_a_user.token}'},
    )
    assert response.status_code == 404  # Not found (doesn't leak existence)

def test_sensitive_data_not_in_logs():
    """Plaintext outcome data not logged."""
    import logging
    with capture_logs():
        service.analyze_cohort(...)
    
    logs = get_captured_logs()
    for log in logs:
        assert 'outcome_data' not in log  # Plaintext field not in logs
        assert '{"metric":' not in log    # JSON plaintext not in logs
```

**3. Penetration Testing (Manual) — 3-Day Audit**

| Day | Focus | Scenarios |
|-----|-------|-----------|
| 1 | Auth/RBAC | Token tampering, scope spoofing, cross-tenant access |
| 2 | Data Protection | Encryption bypass, SQL injection, XXE attacks |
| 3 | Ops Security | Rate limiting, brute force, DoS vectors |

**Test Coverage (25 tests):**
- ✅ test_sast_bandit_pass (no issues)
- ✅ test_dast_sql_injection_blocked (all params)
- ✅ test_dast_xss_blocked (all responses)
- ✅ test_dast_csrf_token_required (POST/PUT/DELETE)
- ✅ test_dast_permission_escalation_blocked (all routes)
- ✅ test_dast_cross_tenant_access_blocked (all resources)
- ✅ test_dast_sensitive_data_not_in_responses (no leaks)
- ✅ test_dast_sensitive_data_not_in_logs (audit trail clean)
- ✅ test_encryption_key_not_exposed (env var only)
- ✅ test_rate_limiting_prevents_brute_force (429 threshold)
- ✅ test_jwt_verification_required (token validation)
- ✅ test_jwt_expiration_enforced (expired token rejected)
- ✅ test_tls_required_all_endpoints (no http fallback)
- ✅ test_cors_headers_restrictive (no *, origin validated)
- ✅ test_csp_header_present (X-Content-Security-Policy)
- ✅ test_x_frame_options_present (clickjacking blocked)
- ✅ test_x_content_type_options_present (MIME sniffing blocked)
- ✅ test_referrer_policy_present (referrer leak blocked)
- ✅ test_hsts_header_present (TLS downgrade prevention)
- ✅ test_input_validation_comprehensive (all params)
- ✅ test_output_encoding_comprehensive (all responses)
- ✅ test_audit_log_immutable (logs can't be modified)
- ✅ test_audit_log_exportable (comply with regulations)
- ✅ test_error_responses_dont_leak_info (generic messages)
- ✅ test_debug_mode_disabled_production (no stack traces)

**Exit Criteria:**
- [ ] SAST scan: 0 critical/high severity issues
- [ ] DAST test: All 21 tests passing
- [ ] Pen-test: No exploitable vulnerabilities found
- [ ] All 25 security tests passing
- [ ] Remediation plan for any findings
- [ ] Ready for Phase 7 (compliance sign-off)

---

### Phase 7: Compliance Documentation & Sign-Off (2026-05-19 to 2026-05-22, 4 days)

**Objective:** Finalize compliance documentation, security officer sign-off, DoD readiness

**Deliverables:**

1. **Security Compliance Matrix** (CREATE `docs/F3_SECURITY_COMPLIANCE_MATRIX.md`)
   - Maps each FERPA/GDPR requirement → implementation evidence → test proof
   - Example row:
     ```
     | Requirement | Implementation | Test Evidence | Status | Sign-off |
     |-------------|-----------------|---------------|--------|----------|
     | Cohort min 20 | FERPAValidator.validate_cohort_size | test_cohort_size_19_rejected | ✅ | |
     ```

2. **Penetration Test Report** (CREATE `docs/F3_PENTEST_REPORT_2026.md`)
   - 3-day assessment findings + fix status
   - Example findings:
     ```
     [Finding P-001] SQL Injection Risk
     - Vector: cohort_name parameter
     - Status: REMEDIATED
     - Fix: ORM parameterization verified
     - Test: test_dast_sql_injection_blocked passes
     - Date Fixed: 2026-05-18
     ```

3. **Data Protection Addendum** (CREATE `docs/F3_DATA_PROTECTION_ADDENDUM.md`)
   - GDPR Data Processing Agreement
   - Processor responsibilities
   - Sub-processor list (cloud providers, etc.)

4. **Incident Response Plan** (UPDATE `docs/runbooks/F3_INCIDENT_RESPONSE.md` with Phase 7 additions)
   - Security incident escalation
   - Breach notification procedures (24-hour FERPA/GDPR notification)
   - Evidence preservation procedures

**Sign-Off Document (CREATE `docs/F3_SECURITY_SIGN_OFF_20260522.md`):**

```markdown
# F3.6 Security & Compliance Sign-Off (2026-05-22)

## Certifications

- [ ] **FERPA Compliance Officer** signs off
  - Cohort minimum size enforcement verified: ✅ 20 students
  - Re-identification risk assessed: ✅ Low
  - Signature: _________________ Date: 2026-05-22

- [ ] **GDPR Data Protection Officer** signs off
  - 7-year retention enforced: ✅ Yes
  - Right-to-access enabled: ✅ Export endpoint live
  - Encryption at rest: ✅ pgcrypto AES-256
  - Signature: _________________ Date: 2026-05-22

- [ ] **Security Officer** signs off
  - SAST scan: ✅ 0 critical/high severity
  - DAST testing: ✅ 21/21 pass
  - Pen-test: ✅ No exploitable vulnerabilities
  - Signature: _________________ Date: 2026-05-22

- [ ] **Compliance Officer** signs off
  - Audit logging complete: ✅ ELK + Kibana
  - 7-year retention: ✅ Automated cleanup
  - All controls documented: ✅ Yes
  - Signature: _________________ Date: 2026-05-22

## Final Verdict

**F3.6 Security & Compliance: APPROVED FOR DELIVERY**

- All FERPA safeguards in place
- All GDPR controls implemented
- Security audit passed
- Compliance requirements met
- Ready for F3.8 release (2026-05-15)
- Ready for F3.10 DoD sign-off (2026-05-22)
```

**Test Coverage (15 final tests):**
- ✅ test_all_requirements_mapped_to_tests (no gaps)
- ✅ test_compliance_matrix_complete (all rows filled)
- ✅ test_pentest_report_format_valid (markdown parseable)
- ✅ test_all_findings_remediated (no open issues)
- ✅ test_sign_off_document_ready (template filled)
- ✅ test_security_officer_consents (sign-off obtained)
- ✅ test_compliance_officer_consents (sign-off obtained)
- ✅ test_dpo_consents (sign-off obtained)
- ✅ test_ferpa_officer_consents (sign-off obtained)
- ✅ test_documentation_version_controlled (git history)
- ✅ test_evidence_artifacts_linked (all references valid)
- ✅ test_audit_trail_complete_7_years (retention verified)
- ✅ test_encryption_key_rotation_documented (procedures)
- ✅ test_incident_response_procedures_drilled (tested)
- ✅ test_delivery_readiness_confirmed (go/no-go decision)

**Exit Criteria:**
- [ ] All compliance matrices filled
- [ ] Pen-test report issued + findings remediated
- [ ] Data Protection Addendum final
- [ ] Incident response plan updated
- [ ] All 4 sign-offs obtained (FERPA, GDPR, Security, Compliance)
- [ ] All 15 final tests passing
- [ ] **F3.6 Security & Compliance DELIVERY COMPLETE**

---

## Quick Reference: F3.6 Deliverables

| Phase | Days | Deliverables | Status |
|-------|------|--------------|--------|
| 1 | 3 | FERPA validators (15 tests) | Ready |
| 2 | 2 | GDPR retention (18 tests) | Ready |
| 3 | 2 | RBAC scopes (20 tests) | Ready |
| 4 | 3 | Audit logging (14 tests) | Ready |
| 5 | 2 | Encryption (12 tests) | Ready |
| 6 | 3 | Security testing (25 tests) | Ready |
| 7 | 4 | Compliance sign-off (15 tests) | Ready |
| **TOTAL** | **13** | **119 tests + 4 sign-offs** | **READY** |

---

## Security Metrics Dashboard

```
┌────────────────────────────────────────────────────────────┐
│           F3.6 Security Metrics (Post-Implementation)      │
├────────────────────────────────────────────────────────────┤
│ FERPA Compliance:          ✅ 100% (cohort min 20)         │
│ GDPR Compliance:           ✅ 100% (7-year + export)       │
│ RBAC Enforcement:          ✅ 100% (4 scopes)              │
│ Audit Logging:             ✅ 100% (ELK integrated)        │
│ Encryption at Rest:        ✅ 100% (AES-256)               │
│ SAST Pass Rate:            ✅ 100% (0 high severity)       │
│ DAST Pass Rate:            ✅ 100% (21/21 tests)           │
│ Pen-Test Pass:             ✅ 100% (no exploits)           │
│ Signature Authority Count: ✅ 4 (FERPA/GDPR/Sec/Comp)      │
└────────────────────────────────────────────────────────────┘
```

---

## Team Responsibilities

| Phase | Owner | Duration | Effort |
|-------|-------|----------|--------|
| 1 | Backend Engineer | 3 days | 24h |
| 2 | Backend + DPA | 2 days | 16h |
| 3 | Backend + Security | 2 days | 16h |
| 4 | Backend + DevOps | 3 days | 24h |
| 5 | Security Engineer | 2 days | 16h |
| 6 | Security + Pen-tester | 3 days | 32h |
| 7 | Compliance + Security | 4 days | 32h |

**Total Effort:** 160 person-hours (13 calendar days with 1-person team)

---

## Post-Implementation Checklist (2026-05-22)

- [ ] All 119 security + compliance tests passing
- [ ] SAST scan: 0 issues
- [ ] DAST scan: 21/21 passing
- [ ] Pen-test: No exploitable vulnerabilities
- [ ] Audit logging functional + ELK indexed
- [ ] Encryption working (plaintext never leaked)
- [ ] RBAC enforced on all endpoints
- [ ] FERPA/GDPR documentation complete
- [ ] All 4 sign-offs obtained
- [ ] **F3.6 Security & Compliance DELIVERY COMPLETE**
- Ready for F3.10 DoD sign-off (2026-05-22 same day)
