# F3.5 Observability Specification — Metrics, Logs, Alerts

**Version:** v1.0  
**Status:** Spec Ready for Implementation (post-unfreeze)  
**Target Implementation:** 2026-05-05 (after F3.3 unfreeze 2026-04-21)  
**Alignment:** F3.1 Product Contract + Release Gate requirements

---

## Overview

This spec defines operational observability for the Intervention Effectiveness Lab (F3):
- **What to measure:** Key F3 business and technical metrics
- **How to instrument:** Log patterns, OpenTelemetry spans, Prometheus metrics
- **When to alert:** SLO/SLI thresholds and escalation runbooks
- **How to debug:** Log aggregation patterns for triage

---

## Tier 1: Business Metrics (Dashboard)

**Audience:** Program Managers, Deans, Ops Leads  
**Update frequency:** Real-time (≤ 5 min lag)  
**Storage:** Prometheus + Grafana dashboard `f3-effectiveness-dashboard`

### Metric 1.1: Cohorts Finalized (counter)

**Name:** `f3_cohorts_finalized_total`

**Attributes:**
- `tenant_id` (label)
- `playbook_id` (label)
- `status` (label): `finalized` | `analyzed` | `error`

**Query:**
```promql
rate(f3_cohorts_finalized_total[5m])  # Finalize rate per 5 min
```

**SLI:**
- Service level: ≥ 99.5% finalize operations complete without error
- Definition: `(total_successful / total_attempted) ≥ 0.995`

### Metric 1.2: Outcomes Analyzed (counter)

**Name:** `f3_outcomes_analyzed_total`

**Attributes:**
- `tenant_id`, `outcome_type` (labels): `dropout_rate` | `gpa_improvement`
- `guardrail_pass` (label): `pass` | `fail`
- `segment_name` (label): `all` | `low_risk` | `high_risk` | ...

**Query:**
```promql
rate(f3_outcomes_analyzed_total{guardrail_pass="pass"}[5m])  # Pass-rate trend
```

**SLI:**
- Guardrail pass rate: ≥ 85% of analyzed outcomes pass all 3 guardrails
- Definition: `(pass_count / total_count) ≥ 0.85`

### Metric 1.3: Analysis Latency (histogram)

**Name:** `f3_analyze_cohort_duration_seconds`

**Attributes:**
- `tenant_id`, `outcome_count` (categorical: `1_to_5` | `5_to_10` | `10_plus`)

**SLI:**
- P95 latency: ≤ 2 seconds
- P99 latency: ≤ 5 seconds
- Definition: `histogram_quantile(0.95, f3_analyze_cohort_duration_seconds) ≤ 2.0`

### Metric 1.4: Cohort Data Quality (gauge)

**Name:** `f3_cohort_data_completeness_percent`

**Attributes:**
- `tenant_id`, `cohort_id` (labels)
- `group` (label): `treated` | `control` | `combined`

**Interpretation:**
- ≥ 90%: Green (acceptable for analysis)
- 80–89%: Yellow (degraded; investigate missing data)
- < 80%: Red (analysis cannot proceed; alert)

**Query:**
```promql
avg by (tenant_id) (f3_cohort_data_completeness_percent{group="combined"})
```

---

## Tier 2: Technical Metrics (Ops Dashboard)

**Audience:** Backend ops, platform SRE  
**Update frequency:** 1-min resolution  
**Storage:** Prometheus time-series

### Metric 2.1: API Call Rate by Endpoint

**Name:** `f3_http_requests_total`

**Attributes:**
- `method` (GET | POST)
- `endpoint` (path): `/finalize` | `/analyze` | `/outcomes` | `/latest`
- `status` (HTTP code): 200 | 400 | 404 | 422 | 5xx

**Queries:**
```promql
# Request rate per endpoint
rate(f3_http_requests_total[1m])

# Error rate per endpoint
rate(f3_http_requests_total{status=~"5.."}[1m]) / rate(f3_http_requests_total[1m])
```

### Metric 2.2: Database Query Performance

**Name:** `f3_db_query_duration_seconds`

**Attributes:**
- `query_type` (label): `get_cohort` | `get_outcomes` | `list_cohorts` | `analyze`
- `status` (label): `ok` | `timeout` | `error`

**SLI (database):**
- P95 query time: ≤ 500ms
- Definition: `histogram_quantile(0.95, f3_db_query_duration_seconds) ≤ 0.5`

### Metric 2.3: Service-Level Requests (SLR)

**Name:** `f3_request_success_rate`

**Calculation:**
```
success_rate = (requests_200 + requests_2xx) / (total_requests)
```

**SLI:**
- Minimum: 99.5% of requests return non-error response
- Tracked: `f3_request_success_rate ≥ 0.995` during business hours (8am–6pm institutional timezone)

---

## Tier 3: Error & Debug Logs

**Audience:** Platform engineers, incident response  
**Format:** JSON structured logs  
**Retention:** 30 days (compliance requirement for outcome data audit trail)  
**Search:** ELK stack (Elasticsearch + Kibana)

### Log Pattern 1: Cohort Finalization

```json
{
  "timestamp": "2026-04-21T10:15:32.123Z",
  "level": "INFO",
  "service": "f3-effectiveness-service",
  "operation": "finalize_cohort",
  "tenant_id": 1,
  "cohort_id": 999,
  "cohort": {
    "name": "Academic Coaching Fall 2025",
    "playbook_id": 42,
    "treated_count": 50,
    "control_count": 48,
    "status": "finalized",
    "analysis_window": {
      "start": "2025-08-01",
      "end": "2026-05-15"
    }
  },
  "actor": "program_mgr_001",
  "duration_ms": 142,
  "result": "success"
}
```

**Search queries (Kibana):**
```
# Finalization errors
operation:finalize_cohort AND (result:error OR level:ERROR)

# Slow finalizations (> 500ms)
operation:finalize_cohort AND duration_ms:[500 TO *]

# By tenant
operation:finalize_cohort | stats count by tenant_id
```

### Log Pattern 2: Analysis with Guardrail Results

```json
{
  "timestamp": "2026-04-21T10:16:45.567Z",
  "level": "INFO",
  "service": "f3-effectiveness-service",
  "operation": "analyze_cohort",
  "tenant_id": 1,
  "cohort_id": 999,
  "outcomes": [
    {
      "type": "dropout_rate",
      "segment": "all",
      "treated_rate": 14.0,
      "control_rate": 18.0,
      "uplift_percent": -4.0,
      "confidence": { "lower": -7.0, "upper": -1.0 },
      "guardrails": {
        "confidence_band_valid": true,
        "distribution_uniform": true,
        "data_complete": true,
        "overall_pass": true,
        "fail_reason": null
      }
    }
  ],
  "analysis_summary": {
    "total_outcomes": 2,
    "outcomes_passed": 2,
    "pass_rate": 1.0,
    "report_ready": true
  },
  "duration_ms": 287,
  "result": "success"
}
```

**Search queries (Kibana):**
```
# Analyses with guardrail failures
operation:analyze_cohort AND outcomes.guardrails.overall_pass:false

# High-impact interventions (uplift >= 5pp)
operation:analyze_cohort AND outcomes.uplift_percent:[5 TO *]

# Low confidence (band width > 10pp)
operation:analyze_cohort AND outcomes.confidence_band_width:[10 TO *]
```

### Log Pattern 3: Errors & Validation Failures

```json
{
  "timestamp": "2026-04-21T10:17:00.890Z",
  "level": "ERROR",
  "service": "f3-effectiveness-service",
  "operation": "finalize_cohort",
  "tenant_id": 1,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "cohort_name cannot be empty",
    "details": {
      "field": "payload.cohort_name",
      "constraint": "min_length=1",
      "value": ""
    }
  },
  "http": {
    "status": 400,
    "user_agent": "internal-api-client/1.0"
  },
  "request_id": "req-abc123def456",
  "result": "failure"
}
```

**Search queries (Kibana):**
```
# All errors in F3
service:f3-effectiveness-service AND level:ERROR | stats count by error.code

# Validation errors by field
service:f3-effectiveness-service AND level:ERROR AND error.code:VALIDATION_ERROR | stats count by error.details.field

# Errors per tenant (for ops investigation)
service:f3-effectiveness-service AND level:ERROR | stats count by tenant_id
```

---

## Tier 4: Traces & Distributed Tracing

**Technology:** OpenTelemetry (Python)  
**Exporter:** Jaeger (trace backend)  
**Sampling:** 1% baseline (100% on errors)

### Trace Span: `analyze_cohort`

**Root span attributes:**
```
service.name: f3-effectiveness-service
span.name: analyze_cohort
tenant_id: <int>
cohort_id: <int>
component: cohort_analysis
```

**Child spans:**
1. `db.query::get_cohort` — fetch cohort metadata
2. `db.query::get_outcomes` — fetch outcome records
3. `business_logic::compute_uplift` — calculate uplift + confidence bands
4. `business_logic::check_guardrails` — validate 3 guardrails
5. `db.mutation::update_status` — update cohort status to "analyzed"

**Example trace view (Jaeger):**
```
analyze_cohort [287ms total]
  ├─ db.query::get_cohort [8ms]
  ├─ db.query::get_outcomes [15ms]
  ├─ business_logic::compute_uplift [12ms]
  ├─ business_logic::check_guardrails [240ms]
  │  ├─ check_confidence_band [2ms]
  │  ├─ check_distribution_uniformity [235ms]  ← Slow segment
  │  └─ check_data_completeness [3ms]
  └─ db.mutation::update_status [12ms]
```

---

## Tier 5: Alerting Rules (Prometheus)

**Alert manager:** Prometheus rules + PagerDuty routing

### Alert 1: High Guardrail Failure Rate

**Rule:**
```yaml
alert: F3HighGuardrailFailureRate
expr: |
  (
    rate(f3_outcomes_analyzed_total{guardrail_pass="fail"}[5m])
    /
    rate(f3_outcomes_analyzed_total[5m])
  ) > 0.15
for: 5m
annotations:
  summary: "F3 guardrail failure rate >15% (expected <15%)"
  description: |
    Tenant {{ $labels.tenant_id }}: {{ $value | humanizePercentage }} of analyzed outcomes
    are failing guardrail checks. Investigate outcome data quality or guardrail thresholds.
  runbook: docs/runbooks/F3_GUARDRAIL_FAILURE_INCIDENT.md
severity: warning
```

### Alert 2: Analysis Latency SLO Violation

**Rule:**
```yaml
alert: F3AnalysisLatencySLOViolation
expr: |
  histogram_quantile(0.95, f3_analyze_cohort_duration_seconds) > 2.0
for: 10m
annotations:
  summary: "F3 P95 analysis latency > 2s (SLO violation)"
  description: |
    P95 latency: {{ $value | humanizeDuration }}. Check database performance, query
    plans for outcome computation, and guardrail validation logic.
  runbook: docs/runbooks/F3_LATENCY_INCIDENT.md
severity: warning
```

### Alert 3: API Error Rate Threshold

**Rule:**
```yaml
alert: F3HighAPIErrorRate
expr: |
  rate(f3_http_requests_total{status=~"5.."}[5m])
  /
  rate(f3_http_requests_total[5m])
  > 0.01
for: 2m
annotations:
  summary: "F3 API error rate >1% (expected <0.5%)"
  description: |
    Tenant {{ $labels.tenant_id }}, endpoint {{ $labels.endpoint }}: {{ $value | humanizePercentage }}
    of requests returning 5xx. Check backend logs and database connectivity.
  runbook: docs/runbooks/F3_API_ERROR_INCIDENT.md
severity: critical
```

### Alert 4: Low Data Completeness

**Rule:**
```yaml
alert: F3LowDataCompleteness
expr: f3_cohort_data_completeness_percent < 80
for: 15m
annotations:
  summary: "F3 cohort data completeness <80% (threshold for analysis)"
  description: |
    Cohort {{ $labels.cohort_id }} ({{ $labels.group }}): {{ $value | humanizePercentage }}.
    Cannot proceed with analysis until completeness ≥ 90%. Check outcome tracking
    import jobs and student outcome record updates.
  runbook: docs/runbooks/F3_DATA_COMPLETENESS_INCIDENT.md
severity: warning
```

---

## Dashboard Layout (Grafana)

**Dashboard URL:** `http://prometheus:3000/d/f3-effectiveness-dashboard`

### Row 1: Executive Summary (PM/Dean View)

- **Cohorts finalized this month** (counter)
- **Average uplift across analyzed cohorts** (gauge)
- **Guardrail pass rate** (gauge, green >85%)
- **P95 analysis latency** (gauge)

### Row 2: Outcome Analysis Trends

- **Outcomes by type** (pie chart): Dropout reduction vs GPA improvement
- **Pass/fail by guardrail** (horizontal bar): Counts of confidence_band_valid, distribution_uniform, data_complete
- **Uplift distribution** (histogram): Bucket counts for [negative, 0±2pp, 2–5pp, >5pp]

### Row 3: Technical Metrics (Ops)

- **Request rate & errors** (line + area): Total requests and 5xx error rate
- **Database query latency** (heatmap): Distribution of query times
- **Data completeness by cohort** (table): Tenant, cohort, treated%, control%, combined%

### Row 4: Active Incidents (Alerts)

- **Firing alerts** (status list): Any triggered alert rules with severity
- **Recent error logs** (log search): Last 100 log entries with level=ERROR from Kibana

---

## Implementation Roadmap (post-unfreeze)

| Phase | Task | Owner | Due | Notes |
|-------|------|-------|-----|-------|
| 1 | Add Prometheus instrumentation to `effectiveness_service.py` | Backend | 2026-05-02 | Python `prometheus_client` library; export to Prometheus via `/metrics` endpoint |
| 2 | Instrument database queries (SQLAlchemy hooks + OTel) | Backend | 2026-05-05 | OpenTelemetry SDK for Python; span decorators on service methods |
| 3 | Add structured JSON logging (Loguru or similar) | Backend | 2026-05-05 | Override default logging; include request_id, tenant_id, operation context |
| 4 | Create Grafana dashboard from dashboard JSON spec | DevOps | 2026-05-08 | Build dashboard from Row 1–4 template; link to runbooks |
| 5 | Configure Prometheus alert rules (Alertmanager) | DevOps | 2026-05-08 | Load YAML rules into Prometheus; test with Alertmanager mock |
| 6 | Create runbooks (Guardrail, Latency, Error, Completeness incidents) | Ops | 2026-05-10 | Troubleshooting steps, escalation paths, remediation scripts |
| 7 | Integration test with Prometheus/Jaeger/ELK stack | QA | 2026-05-12 | Verify metrics arrive, alerts fire correctly, logs aggregate properly |

---

## Success Criteria

F3.5 Observability is **complete** when:

- [ ] All Tier 1 metrics (business) are queryable and non-null
- [ ] All Tier 3 log patterns appear in Kibana with correct JSON structure
- [ ] P95 analysis latency ≤ 2 seconds, confirmed in test environment
- [ ] Guardrail pass rate ≥ 85% on test cohorts (normal case)
- [ ] All 4 alert rules fire correctly on synthetic incidents (chaos engineering test)
- [ ] Grafana dashboard renders 4 rows with no data gaps
- [ ] Two runbooks (Guardrail, Latency) are written and validated by ops team

---

## References

- **Business Metrics:** [F3.1 Product Contract](F3_PRODUCT_CONTRACT.md)
- **API Instrumentation:** Prometheus Python client, OpenTelemetry Python SDK
- **Dashboarding:** Grafana 10.0+
- **Alerting:** Prometheus Alertmanager
- **Log Aggregation:** Elasticsearch + Kibana (or ELK stack equivalent)
- **Tracing:** Jaeger backend
