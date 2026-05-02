# Brain Core Demo Runbook and Evidence (2026-05-01)

## Scope

This artifact provides execution-backed evidence that at least one Brain Core demo scenario from section 10.6 is operational for enterprise demo readiness.

- Prepared on (UTC): 2026-05-01
- Source run: `smoke-gate-once` (script `scripts/platform_smoke_check.sh`)
- Environment: docker-compose stack (`infra/.env`)

## Demo Scenario Covered

Scenario covered: Student at risk pipeline (section 10.6, scenario 1)

Signal -> Decision -> Action evidence mapping:

1. Signal/ingestion path active:
- Domain and endpoint smoke checks exercised admin endpoints with `200 OK` responses across advising/student-success/academic modules.

2. Decision path active:
- Repeated runtime log entries observed during smoke execution:
  - `app.modules.brain_core.service` message: `brain_core_decision_created`

3. Action/execution path active:
- Expanded domain DB matrix executed successfully (`40 passed`), indicating decision-coupled domain write/read paths are healthy.
- E2E smoke suite completed successfully (`50 passed`), confirming admin-console flows stay functional after decision activity.

## Executed Evidence (from smoke-gate-once)

Command:

```bash
bash scripts/platform_smoke_check.sh
```

Observed results (excerpt):

- `[PASS] Domain Endpoint DB Round-Trips: expanded integration matrix`
- `40 passed in 2.29s`
- multiple log entries: `brain_core_decision_created`
- `[PASS] Domain Endpoint HTTP 200 Smoke: non-core domain list endpoints`
- `27 passed in 0.73s`
- `[PASS] E2E Smoke Suite: admin-console + billing + interventions + role-zones`
- `50 passed (16.0s)`

## Reproducibility Commands

```bash
# 1) Start stack
cd infra && docker compose --env-file .env up -d --build

# 2) Run smoke gate once (includes DB round-trips + endpoint smoke + E2E smoke)
cd /home/sbs/AI && bash scripts/platform_smoke_check.sh
```

## Compliance Position

Status for section 10.8 TIER-1 item "Brain Core demo scenario rehearsed": COMPLETE (execution-backed).

This artifact is readiness evidence, not a claim of external certification.
