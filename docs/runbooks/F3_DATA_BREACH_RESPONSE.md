# F3 Data Breach Incident Response

**Severity:** P0 (Critical)  
**Time to Contact SRE:** < 5 min  
**Time to Containment:** < 30 min  
**Runbook Owner:** Compliance Officer, Platform SRE  
**Last Updated:** 2026-04-14

---

## Detection

**Triggers:**

1. **Alert from monitoring:**
   - Prometheus alert: `F3UnauthorizedExportAttempt` fires immediately
   - CloudTrail/audit log shows suspicious cross-tenant cohort access
   - Kibana query returns unexpected `effectiveness.export` by unauthorized user

2. **Manual report:**
   - User reports: "I can see another tenant's cohort analysis"
   - Compliance officer finds unauthorized export in audit log
   - External notification: "We found your institution's outcome data in a leaked database"

3. **Internal discovery:**
   - Automated audit script finds data access pattern anomalies
   - Compliance team reviews monthly access logs, finds inconsistency

---

## Immediate Actions (0–5 minutes)

**Goal:** Stop ongoing access, alert leadership, begin investigation.

```bash
# 1. Fire incident severity escalation
PagerDuty trigger:
  - Severity: P0
  - Title: "F3 Data Breach Detected"
  - Responders: SRE on-call, Compliance Officer, VP Engineering
  - Escalation: VP Engineering (5 min timeout)

# 2. Disable F3 exports immediately (firewall rule)
kubectl set env deployment/backend \
  F3_EXPORT_DISABLED=true \
  --namespace=production

# 3. Revoke all active F3 API tokens (force re-auth)
psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "UPDATE app_api_tokens SET revoked_at=NOW() \
      WHERE scopes LIKE '%effectiveness.export%' \
      AND revoked_at IS NULL;"

# 4. Begin audit log dump (preserve evidence)
BREACH_ID=$(date +%s)_$(openssl rand -hex 4)
mkdir -p /audit/breach_${BREACH_ID}
docker exec ai-db-1 pg_dump -U $DB_USER -d $DB_NAME \
  -t "app_intervention_cohorts*" \
  -t "audit_log" \
  > /audit/breach_${BREACH_ID}/dump_$(date +%Y%m%d_%H%M%S).sql
```

**Notification Script:**
```bash
# Send incident notification to leadership
cat > /tmp/incident_alert.txt << 'EOF'
🚨 INCIDENT: F3 Data Breach Detected
================================================
Time: $(date)
Severity: P0 (Critical)
Incident ID: $BREACH_ID
Affected: Cohort outcome data (potentially)
Action: All F3 exports disabled pending investigation
Next Update: 15 minutes
================================================
EOF

# Send via Slack + Email
slack_webhook_send @sre-on-call @compliance-officer < /tmp/incident_alert.txt
mail -s "INCIDENT P0: F3 Data Breach" vp-engineering@institution.edu < /tmp/incident_alert.txt
```

---

## Investigation (5–30 minutes)

**Goal:** Determine scope, which data was accessed/leaked, by whom.

### Step 1: Determine Access Scope

```bash
# Query: which cohorts were accessed? By whom? When?
psql -U $DB_USER -d $DB_NAME << 'SQL'
SELECT 
  cohort_id, tenant_id, cohort_name,
  actor, accessed_at, 
  operation, http_status, ip_address
FROM audit_log
WHERE service = 'f3-effectiveness' 
  AND operation IN ('analyze_cohort', 'export_cohort')
  AND accessed_at > NOW() - INTERVAL '7 days'
  AND http_status IN (200, 201)
ORDER BY accessed_at DESC;
SQL

# Count affected cohorts per tenant
psql -U $DB_USER -d $DB_NAME << 'SQL'
SELECT tenant_id, COUNT(DISTINCT cohort_id) as cohort_count,
  MIN(accessed_at) as first_access, MAX(accessed_at) as last_access
FROM audit_log
WHERE service = 'f3-effectiveness' 
  AND operation IN ('analyze_cohort', 'export_cohort')
  AND accessed_at > NOW() - INTERVAL '7 days'
GROUP BY tenant_id;
SQL
```

### Step 2: Identify Unauthorized Access

```bash
# Query: who accessed cohorts they shouldn't have?
# (cross-tenant access is always unauthorized)
psql -U $DB_USER -d $DB_NAME << 'SQL'
SELECT 
  al.actor, al.cohort_id, c.tenant_id,
  (SELECT tenant_id FROM app_users WHERE username = al.actor LIMIT 1) as actor_tenant,
  al.accessed_at, al.ip_address
FROM audit_log al
JOIN app_intervention_cohorts c ON al.cohort_id = c.id
WHERE al.service = 'f3-effectiveness'
  AND c.tenant_id != (SELECT tenant_id FROM app_users WHERE username = al.actor LIMIT 1)
ORDER BY al.accessed_at DESC;
SQL
```

### Step 3: Assess Data Exposure

**Assessment criteria:**
- How many cohorts? (e.g., 5 cohorts from tenant A exported)
- How much PII-linked data? (e.g., cohort size + outcome metrics can reveal student subsets)
- To whom? (internal user vs external leak)

```bash
# Determine if data left the system
grep -r "effectiveness" /var/log/nginx/access.log* | \
  grep -E "PUT|POST" | \
  grep -E "s3://|ftp://|http.*external" | \
  wc -l

# Check for outbound traffic anomalies (last 24h)
netstat -tuna | grep ESTABLISHED | \
  grep -E ":(443|80)" | \
  awk '{print $5}' | \
  while read dest; do
    if ! whois $dest | grep -q "institution"; then
      echo "🚨 EXTERNAL: $dest"
    fi
  done
```

---

## Containment (15–30 minutes)

**Goal:** Stop active exfiltration, revoke compromised credentials.

### Step 1: Kill Sessions & Export Tokens

```bash
# Revoke all F3 API tokens
psql -U $DB_USER -d $DB_NAME \
  -c "UPDATE app_api_tokens SET revoked_at=NOW() WHERE service='f3';"

# Terminate active F3 API connections
psql -U $DB_USER -d $DB_NAME \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename='app' AND query LIKE '%cohort%';"
```

### Step 2: Disable Affected Accounts

```bash
# Disable any suspicious user accounts
psql -U $DB_USER -d $DB_NAME << 'SQL'
UPDATE app_users SET is_active=false 
WHERE username IN (
  SELECT DISTINCT actor FROM audit_log 
  WHERE service='f3-effectiveness' 
    AND accessed_at > NOW() - INTERVAL '24h'
    AND (http_status='403' OR ip_address NOT LIKE '10.%')
);
SQL
```

### Step 3: Rotate F3 Encryption Keys

```bash
# Generate new master key for F3 cohort data
openssl rand -hex 32 > /etc/secrets/f3_master_key_new.txt
chmod 600 /etc/secrets/f3_master_key_new.txt

# Re-encrypt all F3 cohort data with new key
docker exec ai-backend-1 python -m scripts.f3_reencrypt_master_key \
  --old-key /etc/secrets/f3_master_key.txt \
  --new-key /etc/secrets/f3_master_key_new.txt \
  --dry-run  # Validate first

# Apply re-encryption (this may take 10–30 min for large datasets)
docker exec ai-backend-1 python -m scripts.f3_reencrypt_master_key \
  --old-key /etc/secrets/f3_master_key.txt \
  --new-key /etc/secrets/f3_master_key_new.txt

# Swap keys
mv /etc/secrets/f3_master_key_new.txt /etc/secrets/f3_master_key.txt
```

---

## Notification & Disclosure (30–60 minutes)

**Goal:** Inform affected parties, comply with regulatory requirements.

### Scope Determination

Based on audit findings:
- **Scenario 1:** Internal unauthorized access, no external leak → Notify institution compliance team
- **Scenario 2:** Data exported to external storage (S3, GitHub, etc.) → FERPA & GDPR notification required
- **Scenario 3:** Data in public breach database → Immediate public disclosure

### Notification Steps

```bash
# 1. Notify compliance officer + legal
send_secure_email_to compliance@institution.edu \
  "Incident Report: F3 Data Breach (ID: $BREACH_ID)" \
  "Scope: $COHORT_COUNT cohorts, Tenants: $(cat /tmp/affected_tenants.txt)" \
  "Exposure: [internal|external|unknown]" \
  "Evidence: /audit/breach_${BREACH_ID}/"

# 2. If FERPA-reportable: notify institution's FERPA administrative office
# (usually Registrar or Compliance)

# 3. If GDPR-reportable (EU tenants): prepare Data Protection Authority notification
# (notification deadline: 72 hours from discovery)

# 4. If data in public leak: send public incident statement
cat > /tmp/public_statement.txt << 'EOF'
We discovered unauthorized access to intervention effectiveness analysis data for
$COHORT_COUNT student cohorts. We have immediately:
- Revoked all access tokens
- Disabled affected user accounts
- Rotated encryption keys
- Preserved full audit trail

We are investigating the scope and notifying affected individuals. 
Updates available at: https://status.institution.edu/incidents/$BREACH_ID
EOF
```

---

## Recovery (60+ minutes)

**Goal:** Restore F3 service, verify integrity.

### Step 1: Verify Data Integrity

```bash
# Re-encrypt verification
docker exec ai-backend-1 python -m scripts.f3_verify_encryption \
  --key /etc/secrets/f3_master_key.txt \
  --sample-cohorts 50

# Run F3 test suite to verify functionality
docker exec ai-backend-1 python -m pytest \
  tests/modules/interventions/test_f3_*.py \
  -v --tb=short

# Verify audit logging is working
docker exec ai-backend-1 python -c \
  "from app.modules.interventions import effectiveness_service; \
   s = effectiveness_service.InterventionEffectivenessService(); \
   s.log_operation('breach_recovery_verification', 'success')"
```

### Step 2: Re-enable F3 Exports (with guardrails)

```bash
# Set export re-enable flag (exports now require explicit approval)
kubectl set env deployment/backend \
  F3_EXPORT_DISABLED=false \
  F3_EXPORT_REQUIRE_APPROVAL=true \
  --namespace=production

# Restart backend to apply new env vars
kubectl rollout restart deployment/backend -n production
kubectl rollout status deployment/backend -n production
```

### Step 3: Cross-tenant Access Prevention Hardening

```bash
# Add additional cross-tenant protection middleware
cat >> /tmp/f3_cross_tenant_audit.py << 'EOF'
# middleware: log + alert on ANY cross-tenant cohort access attempt
@app.middleware("http")
async def f3_cross_tenant_audit(request: Request, call_next):
    if "/api/admin/interventions/cohorts" in request.url.path:
        current_tenant = request.headers.get("X-Tenant-ID")
        
        # Check: if cohort_id in request, verify it belongs to current_tenant
        cohort_id = request.path_params.get("cohort_id")
        if cohort_id:
            actual_tenant = get_cohort_tenant(cohort_id)
            if actual_tenant != current_tenant:
                alert("F3_CROSS_TENANT_ACCESS_ATTEMPT", 
                      user=request.user, 
                      cohort_id=cohort_id,
                      timestamp=now())
                return JSONResponse(status_code=403, detail="Unauthorized")
    
    return await call_next(request)
EOF

# Deploy hardening
docker cp /tmp/f3_cross_tenant_audit.py ai-backend-1:/app/middleware/
docker restart ai-backend-1
```

---

## Post-Incident Review (24–48 hours)

**Timeline:**
- T+0: Incident detected
- T+30 min: Contained
- T+4h: Incident post-mortem meeting scheduled
- T+24h: Root cause analysis complete
- T+48h: Preventive measures deployed

**Post-mortem template:**
```markdown
## F3 Data Breach Post-Mortem (ID: $BREACH_ID)

### Timeline
- T+0: [detection event]
- T+5: [SRE alerted]
- T+15: [contained]
- T+30: [notifications sent]

### Root Cause
- [What system weakness allowed this?]
- [Why wasn't it caught by existing controls?]

### Contributing Factors
- [Insufficient cross-tenant validation in API]
- [Audit logging not real-time]
- [No export approval workflow]

### Preventive Actions
- [ ] Add API-level cross-tenant assertion (code change)
- [ ] Implement export approval workflow (process)
- [ ] Real-time alerting on cross-tenant access (monitoring)
- [ ] Quarterly F3 security audit (process)

### Action Items
- [ ] Deploy hardening within 7 days
- [ ] Update F3 Security Spec with new controls
- [ ] Retrain team on cross-tenant access patterns
- [ ] Review all other inter-tenant APIs for similar gaps
```

---

## Success Criteria

- [ ] Incident detected & SRE contacted within 5 minutes
- [ ] All F3 exports disabled within 10 minutes
- [ ] Access scope determined within 30 minutes
- [ ] All affected users notified within 24 hours
- [ ] Root cause identified within 48 hours
- [ ] Preventive measures deployed within 7 days
- [ ] Post-mortem complete and signed off within 2 weeks

---

## Contacts

| Role | Name | Phone | Email | On-call? |
|------|------|-------|-------|----------|
| SRE On-call | [TBD] | [TBD] | [TBD] | Yes |
| Compliance Officer | [TBD] | [TBD] | [TBD] | Business hours |
| VP Engineering | [TBD] | [TBD] | [TBD] | Escalation only |
| Legal (EU GDPR) | [TBD] | [TBD] | [TBD] | GDPR incidents only |

---

## References

- **F3 Security Spec:** `docs/F3_SECURITY_COMPLIANCE_SPEC.md`
- **Audit Logging:** `docs/INCIDENT_OPS_RUNBOOK.md` → Audit Log Review section
- **FERPA Notification Requirements:** [US Dept of Education FERPA](https://www2.ed.gov/policy/gen/guid/fpco/ferpa/)
- **GDPR Breach Notification:** [GDPR Article 33](https://gdpr-info.eu/art-33-gdpr/)
