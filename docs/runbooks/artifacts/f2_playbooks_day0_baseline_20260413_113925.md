# F2 Playbooks Post-Release Day-0 Baseline

- Captured at (UTC): 2026-04-13T11:39:29Z
- Scope: F2.9 day-0 baseline capture
- Feature flag: interventions.auto_playbooks

## Verification Snapshot

### Backend playbook checks

```text
...........                                                              [100%]
==================================== PASSES ====================================
_________________________ test_create_playbook_success _________________________
----------------------------- Captured stderr call -----------------------------
{"timestamp": "2026-04-13T11:39:28.231583+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "9facb521-08a3-4967-bfd5-e2877c92cf3b", "trace_id": "5a35f521-5cf8-4ce2-90eb-071850966b11", "actor_id": "owner@example.com", "user_id": "owner@example.com", "tenant_id": "1", "institution_id": "-", "logger": "app.request", "message": "http_request", "endpoint": "/api/admin/interventions/playbooks", "path": "/api/admin/interventions/playbooks", "method": "POST", "status_code": 201, "duration_ms": 7.13}
{"timestamp": "2026-04-13T11:39:28.233526+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "-", "trace_id": "-", "actor_id": "-", "user_id": "-", "tenant_id": "-", "institution_id": "-", "logger": "httpx", "message": "HTTP Request: POST http://testserver/api/admin/interventions/playbooks \"HTTP/1.1 201 Created\""}
------------------------------ Captured log call -------------------------------
INFO     app.request:main.py:588 http_request
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/api/admin/interventions/playbooks "HTTP/1.1 201 Created"
_________________________ test_start_execution_success _________________________
----------------------------- Captured stderr call -----------------------------
{"timestamp": "2026-04-13T11:39:28.243851+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "da837352-21db-4a4a-afe3-e4ca08a299a1", "trace_id": "7344163b-074c-4e5f-845f-39f2af94ce63", "actor_id": "owner@example.com", "user_id": "owner@example.com", "tenant_id": "1", "institution_id": "-", "logger": "app.request", "message": "http_request", "endpoint": "/api/admin/interventions/playbooks/executions", "path": "/api/admin/interventions/playbooks/executions", "method": "POST", "status_code": 201, "duration_ms": 6.41}
{"timestamp": "2026-04-13T11:39:28.245278+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "-", "trace_id": "-", "actor_id": "-", "user_id": "-", "tenant_id": "-", "institution_id": "-", "logger": "httpx", "message": "HTTP Request: POST http://testserver/api/admin/interventions/playbooks/executions \"HTTP/1.1 201 Created\""}
------------------------------ Captured log call -------------------------------
INFO     app.request:main.py:588 http_request
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/api/admin/interventions/playbooks/executions "HTTP/1.1 201 Created"
___________________ test_playbook_write_requires_permission ____________________
----------------------------- Captured stderr call -----------------------------
{"timestamp": "2026-04-13T11:39:28.249506+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "5eb4848f-1df6-4bb1-8dc5-67cc9c948754", "trace_id": "24c8b8ee-dbbe-4e96-a877-4bfa08f43944", "actor_id": "student.no.jobs@example.com", "user_id": "student.no.jobs@example.com", "tenant_id": "1", "institution_id": "-", "logger": "app.audit", "message": "admin_action user=student.no.jobs@example.com action=security.access.denied entity=security path=/api/admin/interventions/playbooks ip=testclient result=denied correlation_id=5eb4848f-1df6-4bb1-8dc5-67cc9c948754"}
{"timestamp": "2026-04-13T11:39:28.249726+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "5eb4848f-1df6-4bb1-8dc5-67cc9c948754", "trace_id": "24c8b8ee-dbbe-4e96-a877-4bfa08f43944", "actor_id": "student.no.jobs@example.com", "user_id": "student.no.jobs@example.com", "tenant_id": "1", "institution_id": "-", "logger": "app.request", "message": "http_request", "endpoint": "/api/admin/interventions/playbooks", "path": "/api/admin/interventions/playbooks", "method": "POST", "status_code": 403, "duration_ms": 1.52}
{"timestamp": "2026-04-13T11:39:28.250942+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "-", "trace_id": "-", "actor_id": "-", "user_id": "-", "tenant_id": "-", "institution_id": "-", "logger": "httpx", "message": "HTTP Request: POST http://testserver/api/admin/interventions/playbooks \"HTTP/1.1 403 Forbidden\""}
------------------------------ Captured log call -------------------------------
INFO     app.audit:service.py:421 admin_action user=student.no.jobs@example.com action=security.access.denied entity=security path=/api/admin/interventions/playbooks ip=testclient result=denied correlation_id=5eb4848f-1df6-4bb1-8dc5-67cc9c948754
INFO     app.request:main.py:588 http_request
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/api/admin/interventions/playbooks "HTTP/1.1 403 Forbidden"
____________ test_create_playbook_returns_403_when_feature_disabled ____________
----------------------------- Captured stderr call -----------------------------
{"timestamp": "2026-04-13T11:39:28.259603+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "b5b89939-bf5a-4bb5-ae6a-a1519e833bd1", "trace_id": "3c9e9eac-f495-462d-b639-f39b65e7f47f", "actor_id": "owner@example.com", "user_id": "owner@example.com", "tenant_id": "1", "institution_id": "-", "logger": "app.request", "message": "http_request", "endpoint": "/api/admin/interventions/playbooks", "path": "/api/admin/interventions/playbooks", "method": "POST", "status_code": 403, "duration_ms": 5.24}
{"timestamp": "2026-04-13T11:39:28.261031+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "-", "trace_id": "-", "actor_id": "-", "user_id": "-", "tenant_id": "-", "institution_id": "-", "logger": "httpx", "message": "HTTP Request: POST http://testserver/api/admin/interventions/playbooks \"HTTP/1.1 403 Forbidden\""}
------------------------------ Captured log call -------------------------------
INFO     app.request:main.py:588 http_request
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/api/admin/interventions/playbooks "HTTP/1.1 403 Forbidden"
__________ test_list_playbooks_allows_read_only_when_feature_disabled __________
----------------------------- Captured stderr call -----------------------------
{"timestamp": "2026-04-13T11:39:28.267364+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "0f8f4986-6a47-45f1-b40e-39c7cdb542ba", "trace_id": "2e37221d-97a1-4bb5-94a0-61ab68addb95", "actor_id": "owner@example.com", "user_id": "owner@example.com", "tenant_id": "1", "institution_id": "-", "logger": "app.request", "message": "http_request", "endpoint": "/api/admin/interventions/playbooks", "path": "/api/admin/interventions/playbooks", "method": "GET", "status_code": 200, "duration_ms": 3.16}
{"timestamp": "2026-04-13T11:39:28.268999+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "-", "trace_id": "-", "actor_id": "-", "user_id": "-", "tenant_id": "-", "institution_id": "-", "logger": "httpx", "message": "HTTP Request: GET http://testserver/api/admin/interventions/playbooks \"HTTP/1.1 200 OK\""}
------------------------------ Captured log call -------------------------------
INFO     app.request:main.py:588 http_request
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/api/admin/interventions/playbooks "HTTP/1.1 200 OK"
=========================== short test summary info ============================
PASSED tests/modules/interventions/test_router_playbooks_phase2.py::test_create_playbook_success
PASSED tests/modules/interventions/test_router_playbooks_phase2.py::test_start_execution_success
PASSED tests/modules/interventions/test_router_playbooks_phase2.py::test_playbook_write_requires_permission
PASSED tests/modules/interventions/test_router_playbooks_phase2.py::test_create_playbook_returns_403_when_feature_disabled
PASSED tests/modules/interventions/test_router_playbooks_phase2.py::test_list_playbooks_allows_read_only_when_feature_disabled
PASSED tests/modules/interventions/test_playbook_security_guards.py::test_create_playbook_rejects_duplicate_step_order
PASSED tests/modules/interventions/test_playbook_security_guards.py::test_start_execution_rejects_student_fanout_limit
PASSED tests/modules/interventions/test_risk_observability_metrics.py::test_render_metrics_contains_risk_observability_series
PASSED tests/modules/interventions/test_risk_observability_metrics.py::test_recompute_scores_records_success_metrics
PASSED tests/modules/interventions/test_risk_observability_metrics.py::test_acknowledge_recommendation_records_error_metric
PASSED tests/modules/interventions/test_risk_observability_metrics.py::test_render_metrics_contains_playbook_observability_series
11 passed in 0.13s
```

### Prometheus rules validation

```text
Checking /etc/prometheus/alerts.yml
  SUCCESS: 23 rules found
```

## Review Schedule

- Day 7 review due: 2026-04-20
- Day 14 review due: 2026-04-27
- Day 30 review due: 2026-05-13

## KPI Tracking Checklist

- [ ] intervention_conversion_rate baseline recorded
- [ ] playbook_execution_latency_p95 baseline recorded
- [ ] auto_playbook_trigger_precision baseline recorded
- [ ] playbook_abandonment_rate baseline recorded
- [ ] PlaybookExecutionLatencyP95High alert noise reviewed
- [ ] PlaybookAbandonmentRateHigh alert noise reviewed
- [ ] Feature flag rollout phase (0/1/2/3) documented

## Notes

- This baseline is generated by scripts/f2_playbooks_post_release_day0.sh.
- Keep this artifact immutable; append follow-up findings in day-7/day-14/day-30 artifacts.
- Rollout runbook: docs/runbooks/F2_PLAYBOOKS_RELEASE_ROLLBACK.md
