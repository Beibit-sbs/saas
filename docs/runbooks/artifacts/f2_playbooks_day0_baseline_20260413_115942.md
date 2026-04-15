# F2 Playbooks Post-Release Day-0 Baseline

- Captured at (UTC): 2026-04-13T11:59:47Z
- Scope: F2.9 day-0 baseline capture
- Feature flag: interventions.auto_playbooks
- Mode: pre-pilot 1/3/7-day validation (not 7/14/30)

## Verification Snapshot

### Backend playbook checks

```text
...........                                                              [100%]
==================================== PASSES ====================================
_________________________ test_create_playbook_success _________________________
----------------------------- Captured stderr call -----------------------------
{"timestamp": "2026-04-13T11:59:45.597129+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "afed6da8-5f75-401d-9285-fec9fdf75b1f", "trace_id": "74c04c90-00db-4373-8ac2-55c45ce638f3", "actor_id": "owner@example.com", "user_id": "owner@example.com", "tenant_id": "1", "institution_id": "-", "logger": "app.request", "message": "http_request", "endpoint": "/api/admin/interventions/playbooks", "path": "/api/admin/interventions/playbooks", "method": "POST", "status_code": 201, "duration_ms": 8.02}
{"timestamp": "2026-04-13T11:59:45.599132+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "-", "trace_id": "-", "actor_id": "-", "user_id": "-", "tenant_id": "-", "institution_id": "-", "logger": "httpx", "message": "HTTP Request: POST http://testserver/api/admin/interventions/playbooks \"HTTP/1.1 201 Created\""}
------------------------------ Captured log call -------------------------------
INFO     app.request:main.py:588 http_request
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/api/admin/interventions/playbooks "HTTP/1.1 201 Created"
_________________________ test_start_execution_success _________________________
----------------------------- Captured stderr call -----------------------------
{"timestamp": "2026-04-13T11:59:45.611169+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "1885513c-2cb2-4ffc-a1fb-33d07c693fe2", "trace_id": "0e7054d3-99a1-4b67-934d-43c2ed690686", "actor_id": "owner@example.com", "user_id": "owner@example.com", "tenant_id": "1", "institution_id": "-", "logger": "app.request", "message": "http_request", "endpoint": "/api/admin/interventions/playbooks/executions", "path": "/api/admin/interventions/playbooks/executions", "method": "POST", "status_code": 201, "duration_ms": 7.22}
{"timestamp": "2026-04-13T11:59:45.613137+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "-", "trace_id": "-", "actor_id": "-", "user_id": "-", "tenant_id": "-", "institution_id": "-", "logger": "httpx", "message": "HTTP Request: POST http://testserver/api/admin/interventions/playbooks/executions \"HTTP/1.1 201 Created\""}
------------------------------ Captured log call -------------------------------
INFO     app.request:main.py:588 http_request
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/api/admin/interventions/playbooks/executions "HTTP/1.1 201 Created"
___________________ test_playbook_write_requires_permission ____________________
----------------------------- Captured stderr call -----------------------------
{"timestamp": "2026-04-13T11:59:45.617552+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "e04d6da2-c909-4de6-b2d2-3e10c9d33177", "trace_id": "18dd4d4e-b76c-4923-bd20-61f254baf90c", "actor_id": "student.no.jobs@example.com", "user_id": "student.no.jobs@example.com", "tenant_id": "1", "institution_id": "-", "logger": "app.audit", "message": "admin_action user=student.no.jobs@example.com action=security.access.denied entity=security path=/api/admin/interventions/playbooks ip=testclient result=denied correlation_id=e04d6da2-c909-4de6-b2d2-3e10c9d33177"}
{"timestamp": "2026-04-13T11:59:45.617763+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "e04d6da2-c909-4de6-b2d2-3e10c9d33177", "trace_id": "18dd4d4e-b76c-4923-bd20-61f254baf90c", "actor_id": "student.no.jobs@example.com", "user_id": "student.no.jobs@example.com", "tenant_id": "1", "institution_id": "-", "logger": "app.request", "message": "http_request", "endpoint": "/api/admin/interventions/playbooks", "path": "/api/admin/interventions/playbooks", "method": "POST", "status_code": 403, "duration_ms": 1.54}
{"timestamp": "2026-04-13T11:59:45.619200+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "-", "trace_id": "-", "actor_id": "-", "user_id": "-", "tenant_id": "-", "institution_id": "-", "logger": "httpx", "message": "HTTP Request: POST http://testserver/api/admin/interventions/playbooks \"HTTP/1.1 403 Forbidden\""}
------------------------------ Captured log call -------------------------------
INFO     app.audit:service.py:421 admin_action user=student.no.jobs@example.com action=security.access.denied entity=security path=/api/admin/interventions/playbooks ip=testclient result=denied correlation_id=e04d6da2-c909-4de6-b2d2-3e10c9d33177
INFO     app.request:main.py:588 http_request
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/api/admin/interventions/playbooks "HTTP/1.1 403 Forbidden"
____________ test_create_playbook_returns_403_when_feature_disabled ____________
----------------------------- Captured stderr call -----------------------------
{"timestamp": "2026-04-13T11:59:45.625906+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "20e2d576-da50-448e-877c-e4c011c5e90e", "trace_id": "067c7543-59f3-4e02-984b-b351a5fb5c81", "actor_id": "owner@example.com", "user_id": "owner@example.com", "tenant_id": "1", "institution_id": "-", "logger": "app.request", "message": "http_request", "endpoint": "/api/admin/interventions/playbooks", "path": "/api/admin/interventions/playbooks", "method": "POST", "status_code": 403, "duration_ms": 3.68}
{"timestamp": "2026-04-13T11:59:45.627246+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "-", "trace_id": "-", "actor_id": "-", "user_id": "-", "tenant_id": "-", "institution_id": "-", "logger": "httpx", "message": "HTTP Request: POST http://testserver/api/admin/interventions/playbooks \"HTTP/1.1 403 Forbidden\""}
------------------------------ Captured log call -------------------------------
INFO     app.request:main.py:588 http_request
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/api/admin/interventions/playbooks "HTTP/1.1 403 Forbidden"
__________ test_list_playbooks_allows_read_only_when_feature_disabled __________
----------------------------- Captured stderr call -----------------------------
{"timestamp": "2026-04-13T11:59:45.632690+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "63c419d7-1ef8-4281-9aa9-c82e8ac1559e", "trace_id": "85417f36-7522-4920-a606-61df1eca263a", "actor_id": "owner@example.com", "user_id": "owner@example.com", "tenant_id": "1", "institution_id": "-", "logger": "app.request", "message": "http_request", "endpoint": "/api/admin/interventions/playbooks", "path": "/api/admin/interventions/playbooks", "method": "GET", "status_code": 200, "duration_ms": 2.67}
{"timestamp": "2026-04-13T11:59:45.634159+00:00", "level": "INFO", "service": "ai-platform", "environment": "development", "request_id": "-", "trace_id": "-", "actor_id": "-", "user_id": "-", "tenant_id": "-", "institution_id": "-", "logger": "httpx", "message": "HTTP Request: GET http://testserver/api/admin/interventions/playbooks \"HTTP/1.1 200 OK\""}
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
11 passed in 0.12s
```

### Prometheus rules validation

```text
Checking /etc/prometheus/alerts.yml
  SUCCESS: 23 rules found
```

## Review Schedule

- Day 1 review due: 2026-04-14
- Day 3 review due: 2026-04-16
- Day 7 review due: 2026-04-20

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
