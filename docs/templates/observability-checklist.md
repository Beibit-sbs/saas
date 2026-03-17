# Observability Checklist

## Logging
- Structured logs enabled.
- Request or correlation ID included in each log line.
- Error logs include code path and operation context.

## Metrics
- `/metrics` endpoint available.
- Request count and latency metrics collected.
- AI gateway request and error metrics collected.

## Tracing
- Trace context propagated across services.
- External integration calls wrapped with spans.

## Alerting
- Basic alerts defined for:
  - high error rate
  - high latency
  - service unavailable

## Dashboard
- Service health dashboard exists.
- AI gateway usage and error panels exist.
- Audit throughput panel exists.
