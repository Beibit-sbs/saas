# F3.5 Observability Implementation Guide — Start Post-Unfreeze (2026-04-21)

**Released:** 2026-04-14 (pre-unfreeze preparation)  
**Execution Start:** 2026-04-21 (post F3.3 unfreeze)  
**Target Delivery:** 2026-05-05 (15 days)  
**Owner:** DevOps/SRE Team  
**Status:** Preparation phase (ready to execute on unfreeze day)

---

## Executive Summary

F3.5 delivers observability for intervention effectiveness feature:
- **5 metric tiers** (business/technical/logs/traces/alerts)
- **4 Prometheus alert rules** (latency, error rate, queue depth, garbled conditions)
- **Grafana dashboard** with 8 panels (KPIs, API latency, guardrail pass rate, queue visualization)
- **SLO targets:** P95 latency ≤ 2s, error rate < 0.5%, guardrail pass > 80%
- **OpenTelemetry spans** for distributed tracing (backend → frontend)

**Deliverables by Phase:**
- Phase 1-2: Infrastructure setup (Prometheus metrics, OpenTelemetry)
- Phase 3-4: Grafana dashboard (8 panels, real-time KPI)
- Phase 5-6: Alert rules + testing
- Phase 7: SLO validation + documentation

---

## 7-Phase Implementation Roadmap

### Phase 1: Prometheus Metrics Definition (2026-04-21 to 2026-04-22, 2 days)

**Objective:** Define & instrument metrics in backend for F3

**Files to Create/Update:**
- `backend/app/metrics/f3_metrics.py` (NEW, 60 lines)
- `backend/app/modules/interventions/effectiveness_service.py` — Add metric recording (inline, ~10 lines added)

**Metrics to Instrument (4 primary):**

| Metric | Type | Labels | Example |
|--------|------|--------|---------|
| `f3_cohort_operations_total` | Counter | `operation` (finalize/analyze/fetch), `status` (success/error) | +1 when cohort finalized |
| `f3_cohort_operation_duration_seconds` | Histogram | `operation`, `status` | 0.23s for finalize |
| `f3_guardrails_evaluated_total` | Counter | `guardrail` (confidence/uniformity/completeness), `result` (pass/fail) | +1 when confidence check done |
| `f3_active_cohort_analysis_queue_depth` | Gauge | `queue_name` (analyze_queue), `status` (pending/failed) | 3 pending analyses |

**Implementation Example (Python):**
```python
# backend/app/metrics/f3_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Define metrics (counter = increments, histogram = buckets by time, gauge = current value)
cohort_operations_total = Counter(
    name='f3_cohort_operations_total',
    documentation='Total F3 cohort operations',
    labelnames=['operation', 'status'],
)

cohort_operation_duration_seconds = Histogram(
    name='f3_cohort_operation_duration_seconds',
    documentation='F3 cohort operation latency',
    labelnames=['operation', 'status'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0),  # P95 target: < 2.0s
)

guardrails_evaluated_total = Counter(
    name='f3_guardrails_evaluated_total',
    documentation='F3 guardrails evaluation count',
    labelnames=['guardrail', 'result'],
)

analysis_queue_depth = Gauge(
    name='f3_active_cohort_analysis_queue_depth',
    documentation='Pending analyses in queue',
    labelnames=['queue_name', 'status'],
)
```

**Usage in Service Layer:**
```python
# backend/app/modules/interventions/effectiveness_service.py
def analyze_cohort(self, *, tenant_id: int, cohort_id: int, actor: str, payload):
    import time
    from app.metrics.f3_metrics import cohort_operations_total, cohort_operation_duration_seconds
    
    start = time.time()
    try:
        # ... analysis logic ...
        cohort_operations_total.labels(operation='analyze', status='success').inc()
        cohort_operation_duration_seconds.labels(operation='analyze', status='success').observe(
            time.time() - start
        )
        return result
    except Exception as e:
        cohort_operations_total.labels(operation='analyze', status='error').inc()
        cohort_operation_duration_seconds.labels(operation='analyze', status='error').observe(
            time.time() - start
        )
        raise
```

**Exit Criteria:**
- [ ] All 4 metrics defined in `f3_metrics.py`
- [ ] Service methods record metrics (finalize, analyze, fetch)
- [ ] Prometheus scrape config updated to include new endpoint
- [ ] `curl localhost:9090/metrics | grep f3_` returns 4+ metric lines
- [ ] Ready for Phase 2 (OpenTelemetry spans)

---

### Phase 2: OpenTelemetry Distributed Tracing (2026-04-22 to 2026-04-24, 3 days)

**Objective:** Instrument backend → frontend request tracing for F3 operations

**Files to Create/Update:**
- `backend/app/telemetry/f3_spans.py` (NEW, 50 lines)
- `backend/app/modules/interventions/effectiveness_router.py` — Add span recording (inline, ~5 lines)
- `frontend/shared/telemetry/f3-traces.ts` (NEW, 40 lines)

**Spans to Record (3 top-level):**

| Span Name | Start Point | Attributes | Child Spans |
|-----------|------------|-----------|-------------|
| `f3.finalize_cohort` | Router receives request | `cohort_id`, `tenant_id`, `actor` | db_query, validation, serialization |
| `f3.analyze_cohort` | Router receives request | `cohort_id`, `tenant_id`, `actor` | db_query, statistical_analysis, result_persistence |
| `f3.fetch_outcomes` | Router receives request | `cohort_id`, `tenant_id` | db_query, encryption |

**OpenTelemetry Implementation (Python):**
```python
# backend/app/telemetry/f3_spans.py
from opentelemetry import trace
from opentelemetry.trace import Tracer

tracer = trace.get_tracer(__name__)

def record_cohort_operation(operation_name: str, cohort_id: int, tenant_id: int):
    """Context manager for recording F3 cohort operations."""
    
    with tracer.start_as_current_span(f"f3.{operation_name}") as span:
        span.set_attribute("cohort_id", cohort_id)
        span.set_attribute("tenant_id", tenant_id)
        span.set_attribute("service", "intervention_effectiveness")
        yield span
```

**Usage in Router:**
```python
# backend/app/modules/interventions/effectiveness_router.py
from app.telemetry.f3_spans import record_cohort_operation

def analyze_cohort(...):
    with record_cohort_operation("analyze_cohort", cohort_id, tenant_id) as span:
        result = InterventionEffectivenessService(db).analyze_cohort(...)
        span.set_attribute("result.success", True)
        return result
```

**Frontend Tracing:**
```typescript
// frontend/shared/telemetry/f3-traces.ts
import { trace } from '@opentelemetry/api';

const tracer = trace.getTracer('f3-cohorts');

export async function traceCohortFetch(cohortId: number) {
  const span = tracer.startSpan('f3.fetch_cohort_frontend');
  try {
    span.setAttributes({ cohort_id: cohortId });
    const data = await fetch(`/api/admin/interventions/cohorts/${cohortId}`);
    span.setStatus({ code: SpanStatusCode.OK });
    return data;
  } catch (err) {
    span.setStatus({ code: SpanStatusCode.ERROR, message: err.message });
    throw err;
  } finally {
    span.end();
  }
}
```

**Exit Criteria:**
- [ ] 3 top-level spans defined (finalize, analyze, fetch)
- [ ] All spans have required attributes (cohort_id, tenant_id, etc.)
- [ ] Jaeger UI shows traces for F3 operations (localhost:16686)
- [ ] End-to-end trace (request → backend → db → response) visible
- [ ] Ready for Phase 3 (Grafana dashboard)

---

### Phase 3: Grafana Dashboard — Infrastructure Layer (2026-04-24 to 2026-04-26, 3 days)

**Objective:** Build 8-panel Grafana dashboard with F3 KPIs & operational metrics

**Files to Create:**
- `infra/grafana/dashboards/f3-intervention-effectiveness-dashboard.json` (NEW, 400+ lines)

**8 Dashboard Panels:**

| Panel # | Title | Metric(s) | Visualization | SLO Target |
|---------|-------|-----------|--|-----------|
| 1 | F3 Cohorts Created (7d) | `f3_cohort_operations_total{operation="finalize",status="success"}` | Stat/Counter | N/A |
| 2 | API Latency P95 | `histogram_quantile(0.95, f3_cohort_operation_duration_seconds)` | Gauge | ≤ 2.0s |
| 3 | Error Rate (%) | `(f3_cohort_operations_total{status="error"} / f3_cohort_operations_total) * 100` | Graph | < 0.5% |
| 4 | Guardrail Pass Rate (%) | `(f3_guardrails_evaluated_total{result="pass"} / f3_guardrails_evaluated_total) * 100` | Gauge | > 80% |
| 5 | Analysis Queue Depth | `f3_active_cohort_analysis_queue_depth{status="pending"}` | Graph | Monitor (alert if > 50) |
| 6 | Operation Latency Distribution | `f3_cohort_operation_duration_seconds_bucket` | Heatmap | Visualize 25th/50th/75th percentile |
| 7 | Errors by Operation | `f3_cohort_operations_total{status="error"}` grouped by `operation` | Bar Chart | Alert if any op > 5%  error rate |
| 8 | Trace Sampling (OpenTelemetry) | Jaeger link + span count | Link | Show 1h span volume |

**Dashboard JSON Structure:**
```json
{
  "dashboard": {
    "title": "F3 Intervention Effectiveness",
    "panels": [
      {
        "id": 1,
        "title": "Cohorts Created (7d)",
        "targets": [
          {
            "expr": "increase(f3_cohort_operations_total{operation=\"finalize\",status=\"success\"}[7d])",
            "label": "Finalized Cohorts"
          }
        ],
        "type": "stat",
        "fieldConfig": {
          "defaults": {
            "color": { "mode": "thresholds" },
            "mappings": [],
            "thresholds": {
              "mode": "absolute",
              "steps": [
                { "color": "red", "value": null },
                { "color": "yellow", "value": 100 },
                { "color": "green", "value": 500 }
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "API Latency P95",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, f3_cohort_operation_duration_seconds)",
            "label": "P95 Latency"
          }
        ],
        "type": "gauge",
        "fieldConfig": {
          "defaults": {
            "unit": "s",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                { "color": "red", "value": null },
                { "color": "yellow", "value": 1.5 },
                { "color": "green", "value": 2.0 }
              ]
            }
          }
        }
      }
      // ... 6 more panels
    ]
  }
}
```

**Dashboard Link in Grafana UI:**
- URL: `http://localhost:3000/d/f3-effectiveness/f3-intervention-effectiveness`
- Refresh rate: 30 seconds (auto-refresh enabled)
- Templating: Dropdown for tenant_id filtering (optional)

**Exit Criteria:**
- [ ] Dashboard JSON created and validated
- [ ] All 8 panels render without errors
- [ ] Metrics populate correctly (data shows in graphs)
- [ ] SLO thresholds visualized (color coding: green/yellow/red)
- [ ] Dashboard accessible at `/d/f3-effectiveness/`
- [ ] Ready for Phase 4 (alert rules)

---

### Phase 4: Prometheus Alert Rules (2026-04-26 to 2026-04-27, 2 days)

**Objective:** Define 4 alert rules for SLO violations + operational issues

**Files to Create:**
- `infra/prometheus/f3-alerts.yml` (NEW, 80 lines)

**4 Alert Rules:**

```yaml
# f3-alerts.yml
groups:
  - name: f3_intervention_effectiveness
    interval: 30s
    rules:
      - alert: F3_HighLatency
        expr: histogram_quantile(0.95, f3_cohort_operation_duration_seconds) > 2.0
        for: 5m
        labels:
          severity: warning
          service: f3-effectiveness
        annotations:
          summary: "F3 API latency P95 > 2.0s"
          description: "P95 latency is {{ $value }}s, exceeds SLO target of 2.0s"
      
      - alert: F3_HighErrorRate
        expr: (f3_cohort_operations_total{status="error"} / f3_cohort_operations_total) > 0.005
        for: 5m
        labels:
          severity: critical
          service: f3-effectiveness
        annotations:
          summary: "F3 error rate > 0.5%"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      - alert: F3_LowGuardrailPassRate
        expr: (f3_guardrails_evaluated_total{result="pass"} / f3_guardrails_evaluated_total) < 0.8
        for: 10m
        labels:
          severity: warning
          service: f3-effectiveness
        annotations:
          summary: "F3 guardrail pass rate < 80%"
          description: "Pass rate is {{ $value | humanizePercentage }}"
      
      - alert: F3_AnalysisQueueBacklog
        expr: f3_active_cohort_analysis_queue_depth{status="pending"} > 50
        for: 10m
        labels:
          severity: warning
          service: f3-effectiveness
        annotations:
          summary: "F3 analysis queue > 50 pending"
          description: "Queue depth is {{ $value }}, processing may be slow"
```

**Alert Routing (in Prometheus AlertManager config):**
```yaml
# Add to infra/.env or alertmanager.yml
F3_ALERT_WEBHOOK=https://slack.example.com/hooks/...  # Slack webhook

# Alertmanager routing:
route:
  receiver: 'default'
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  routes:
    - match:
        service: 'f3-effectiveness'
        severity: 'critical'
      receiver: 'f3-critical-slack'
      repeat_interval: 5m  # Re-alert every 5m if still firing
```

**Testing Alerts:**
```bash
# Simulate high latency alert
curl -X POST localhost:9009/insert/prometheus/api/v1/write \
  -d 'f3_cohort_operation_duration_seconds{operation="analyze",status="success",le="5.0"} 2.5 1707000000000'

# Check Prometheus for alert status
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname=="F3_HighLatency")'
```

**Exit Criteria:**
- [ ] All 4 alert rules defined in `f3-alerts.yml`
- [ ] Alert rules pass validation: `promtool check rules f3-alerts.yml`
- [ ] Alerts trigger correctly when metrics exceed thresholds
- [ ] Slack/email notifications configured and tested
- [ ] Ready for Phase 5 (SLO validation)

---

### Phase 5: SLO Targets & Reporting (2026-04-27 to 2026-04-28, 2 days)

**Objective:** Define SLO targets, track error budget, generate SLO reports

**Files to Create:**
- `docs/F3_SLO_TARGETS.md` (NEW, 60 lines)
- `infra/prometheus/f3-slo-recording-rules.yml` (NEW, 40 lines)

**SLO Definitions:**

| SLO | Metric | Target | Window | Error Budget |
|-----|--------|--------|--------|--------------|
| **API Availability** | `f3_cohort_operations_total{status="success"}` | 99.5% | 30 days | 3.6 hours |
| **Latency** | `f3_cohort_operation_duration_seconds{quantile="p95"}` | ≤ 2.0s | 30 days | Monitored |
| **Guardrail Pass Rate** | `f3_guardrails_evaluated_total{result="pass"} / total` | ≥ 80% | 7 days | Monitor weekly |
| **Error Rate** | `(error_total / total) * 100` | < 0.5% | 24 hours | Immediate escalation if > 1% |

**Recording Rules (for efficient SLO queries):**
```yaml
# f3-slo-recording-rules.yml
groups:
  - name: f3_slo
    interval: 1m
    rules:
      - record: f3:slo:api_availability:rate5m
        expr: rate(f3_cohort_operations_total{status="success"}[5m])
      
      - record: f3:slo:latency_p95:rate5m
        expr: histogram_quantile(0.95, rate(f3_cohort_operation_duration_seconds_bucket[5m]))
      
      - record: f3:slo:guardrail_pass_rate:rate5m
        expr: (rate(f3_guardrails_evaluated_total{result="pass"}[5m]) / rate(f3_guardrails_evaluated_total[5m])) * 100
```

**SLO Document Example:**
```markdown
# F3 SLO Targets

## API Availability (99.5%)
- Metric: Success rate of cohort operations
- Target: 99.5% uptime (3.6 hours error budget per month)
- Monitoring: Prometheus alert if < 99% in 5m window

## Latency (P95 ≤ 2.0s)
- Metric: finalize_cohort + analyze_cohort P95 latency
- Target: ≤ 2.0s round-trip
- Monitoring: Grafana dashboard tracks hourly

## Error Budget Tracking
- Month of April 2026: 3.6 hours available
- Used so far: 0h (no outages)
- Remaining: 3.6h (100% available)
```

**Exit Criteria:**
- [ ] All SLO targets documented in `F3_SLO_TARGETS.md`
- [ ] Recording rules configured + validated
- [ ] SLO dashboard shows error budget tracking
- [ ] Ready for Phase 6 (observability testing)

---

### Phase 6: Observability Testing & Validation (2026-04-28 to 2026-05-02, 5 days)

**Objective:** Test metrics, alerts, and dashboard accuracy under load

**Test Scenarios:**

| Scenario | Action | Expected Metrics | Pass Criteria |
|----------|--------|------------------|---------------|
| 1 | Finalize 10 cohorts | `f3_cohort_operations_total{operation="finalize"}.increase() == 10` | Metric increments correctly |
| 2 | Inject 5s latency in DB | `f3_cohort_operation_duration_seconds_bucket{le="5.0"} > 0` | P95 captures outlier |
| 3 | Create 500 analyses | Queue depth graph rises → falls | Breadbox fills then drains |
| 4 | Trigger 10 analysis errors | Error rate & alert fires | Alert triggers at > 0.5% |
| 5 | Run 100 guardrail checks, 20 fail | Pass rate = 80% | Gauge reads 80.0 |
| 6 | Rapid API calls (100/s) | Latency increases, no drop | Metrics handle concurrency |
| 7 | Dashboard refresh 1000x | Zero errors, all panels render | Dashboard scalable |
| 8 | Tracer output to Jaeger | 50+ spans visible | End-to-end tracing works |

**Load Test Script (Python):**
```python
# tests/observability/test_f3_metrics_under_load.py
import concurrent.futures
import requests
from prometheus_client import CollectorRegistry, Counter

def test_finalize_cohort_high_volume():
    """Test metrics under 100 concurrent finalize requests."""
    
    def finalize():
        response = requests.post(
            'http://localhost:8000/api/admin/interventions/cohorts/finalize',
            json={
                'cohort_name': 'Test Cohort',
                'cohort_size': 100,
                'treatment_group_size': 50,
                'outcome_type': 'completion_rate',
            },
            headers={'X-Tenant-ID': '1'},
            timeout=5,
        )
        return response.status_code == 201
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        results = list(executor.map(finalize, range(100)))
    
    # Verify metrics incremented
    success_count = requests.get('http://localhost:9090/api/v1/query',
                                  params={'query': 'f3_cohort_operations_total{status="success"}'})
    assert success_count.json()['data']['result'][0]['value'][1] == '100'  # 100 successes recorded
```

**Exit Criteria:**
- [ ] All 8 test scenarios pass
- [ ] Metrics accurately record operations under load
- [ ] Alerts fire correctly when thresholds exceeded
- [ ] Dashboard renders without lag (< 1s load time)
- [ ] No data loss during high-volume operations
- [ ] Ready for Phase 7 (documentation & SLO review)

---

### Phase 7: Documentation & SLO Review (2026-05-02 to 2026-05-05, 4 days)

**Objective:** Document observability setup, finalize SLOs, prepare for handoff

**Files to Create/Update:**
- `docs/F3_OBSERVABILITY_RUNBOOK.md` (NEW, 100 lines)
- `docs/F3_OBSERVABILITY_SPEC.md` — UPDATE with implementation details
- `docs/F3_SLO_TARGETS.md` — Finalize + sign-off

**Observability Runbook Contents:**

1. **Dashboard Access**
   - URL: http://grafana.example.com/d/f3-effectiveness/
   - Login: [default credentials]
   - Refresh: 30s auto-refresh

2. **Alert Response Playbook**
   ```
   Alert: F3_HighLatency (P95 > 2.0s)
   → Check: SELECT AVG(duration) FROM cohort_operations LIMIT 1000
   → If DB slow: Run VACUUM ANALYZE on cohort tables
   → If network latency: Check PgBouncer connection Pool
   → Escalate if > 5s sustained latency
   ```

3. **Metric Query Examples**
   ```promql
   # Current P95 latency (last 1h)
   histogram_quantile(0.95, rate(f3_cohort_operation_duration_seconds_bucket[1h]))
   
   # Error rate (last 24h)
   (rate(f3_cohort_operations_total{status="error"}[24h]) / rate(f3_cohort_operations_total[24h])) * 100
   
   # Guardrail pass rate (last 7d)
   (rate(f3_guardrails_evaluated_total{result="pass"}[7d]) / rate(f3_guardrails_evaluated_total[7d])) * 100
   ```

4. **Troubleshooting**
   - Q: Dashboard shows "No data" for F3 metrics
     A: Check if F3.3 unfreeze completed & APIs are called. Metrics only appear after first operation.
   - Q: Alert won't silence
     A: Check Alertmanager route config (infra/.env) for correct webhook
   - Q: Latency spikes daily at 3am
     A: Check if backup jobs conflict with F3 operations

**SLO Sign-off Template:**
```
# F3 SLO Review & Approval (2026-05-05)

[ ] API Availability SLO (99.5%): APPROVED
    - Target realistic: YES
    - Error budget tracking: YES
    - Alert thresholds: YES

[ ] Latency SLO (P95 ≤ 2.0s): APPROVED
    - Baseline established: YES
    - Load testing confirmed: YES
    - Seasonal variation: NO (new feature)

[ ] Guardrail Pass Rate SLO (≥ 80%): APPROVED
    - Target aligns with product: YES
    - Weekly review cadence: YES

[ ] Error Rate SLO (< 0.5%): APPROVED
    - Escalation path: YES
    - On-call runbook: YES

Signed: [DevOps Lead] @ 2026-05-05
```

**Exit Criteria:**
- [ ] Runbook completed with alert response procedures
- [ ] All SLO metrics documented + baselined
- [ ] SLO targets sign-off completed
- [ ] Grafana dashboard stable (0 data gaps)
- [ ] Team trained on dashboard + alerts
- [ ] **F3.5 Observability DELIVERY COMPLETE**

---

## Quick Reference: Key Metrics & Targets

```
┌─────────────────────────────────────────────────────────────┐
│             F3 Observability Metrics Summary                │
├─────────────────────────────────────────────────────────────┤
│ Metric                      │ Type     │ Target              │
├─────────────────────────────────────────────────────────────┤
│ Finalize Latency (P95)      │ Histogram│ ≤ 2.0s              │
│ Analyze Latency (P95)       │ Histogram│ ≤ 2.0s              │
│ Error Rate                  │ Gauge    │ < 0.5%              │
│ Guardrail Pass Rate         │ Gauge    │ > 80%               │
│ Queue Depth (Pending)       │ Gauge    │ Monitor (alert > 50)│
│ Availability                │ Rate     │ 99.5% (30d window)  │
│ Trace Sampling Rate         │ Gauge    │ 10% (adjustable)    │
└─────────────────────────────────────────────────────────────┘

Alert Thresholds:
  🔴 Critical: Error rate > 1%, Latency P95 > 5s
  🟡 Warning: Error rate > 0.5%, Latency P95 > 2.0s, Pass rate < 80%
```

---

##Infrastructure Dependencies

- **Prometheus:** Already running (infra/prometheus), scraping backend:8000
- **Grafana:** Already running (infra/grafana), requires API key for programmatic dashboards
- **Jaeger:** Already running (infra backend docker-compose), listening on localhost:16686
- **OpenTelemetry SDK:** Already in `backend/requirements.txt` (v1.22+)

---

## Team Responsibilities

| Phase | Owner | Duration |
|-------|-------|----------|
| 1 | Backend engineer | 2 days |
| 2 | Backend engineer | 3 days |
| 3 | DevOps engineer | 3 days |
| 4 | DevOps engineer | 2 days |
| 5 | DevOps + SRE | 2 days |
| 6 | QA + DevOps | 5 days |
| 7 | DevOps + Backend | 4 days |

**Total Effort:** 21 person-days (21 calendar days with 1-person team)

---

## Post-Implementation Checklist (2026-05-05)

- [ ] All 4 metrics emitted from backend
- [ ] OpenTelemetry spans visible in Jaeger
- [ ] Grafana dashboard accessible + all 8 panels populated
- [ ] Prometheus alert rules deployed + tested
- [ ] SLO targets documented + baselined
- [ ] Load testing (Phase 6) passed all 8 scenarios
- [ ] Runbook completed + team trained
- [ ] Feature-flag ready for F3.8 release (2026-05-15)
- [ ] **F3.5 Observability DELIVERY COMPLETE**

Ready for F3.6 Security delivery (2026-05-10) + F3.8 Release (2026-05-15).
