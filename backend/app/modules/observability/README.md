# Observability Scaffold

This module is scaffold-only and not yet connected to runtime.

## Baseline Targets
- Structured logs (JSON-ready fields)
- Correlation/request ID propagation
- Service-level metrics endpoint (Prometheus format)
- Tracing-ready instrumentation points

## Suggested Next Steps
1. Add logging formatter with request_id and actor fields.
2. Add `/metrics` endpoint and minimal counters:
   - http_requests_total
   - http_request_duration_seconds
   - ai_gateway_requests_total
3. Add OpenTelemetry SDK wiring behind a feature flag.
4. Add dashboards and alerts in later phase.

## Safety Rule
Do not switch defaults to strict observability mode until metrics and log exporters are validated in staging.
