# Support And Rollback Plan

## Support Channels

- pilot owner coordination channel
- internal issue triage channel
- engineering escalation path
- product review path

## Issue Severity Levels

- Sev 1: pilot-blocking route or access failure
- Sev 2: major workflow gap with workaround
- Sev 3: documentation or usability gap
- Sev 4: cosmetic or follow-up improvement

## Triage Flow

1. Capture issue summary and route.
2. Classify severity.
3. Assign owner.
4. Decide workaround, defer, or rollback.
5. Record outcome in post-pilot review.

## Pilot Owner Responsibilities

- coordinate demo readiness
- confirm placeholder-only pilot participants
- confirm limitations are stated clearly
- confirm no production-ready claim or sales-ready claim

## Rollback Conditions

- critical route unavailable
- role-based access fails in a blocking way
- misleading visibility that risks fake KPI interpretation
- environment instability that invalidates pilot trust

## Rollback Steps

1. Stop the pilot session.
2. Revert to the last trusted environment snapshot.
3. Preserve logs and screenshots.
4. Communicate issue status and next review time.

## Data Safety Rules

- no real personal data
- no credentials
- no DB seed execution from this package
- no live dispatch

## Backup Expectations

- backup/restore dry-run proof should exist before broader pilot use
- request_id and logs should remain available for issue tracing

## Communication Plan

- notify pilot owner first
- notify internal stakeholders with limitation summary
- avoid any external sales framing

## Post-Pilot Review

- summarize issues by severity
- record acceptance status against checklist
- update limitations and next hardening steps
