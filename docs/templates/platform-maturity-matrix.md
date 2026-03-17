# Platform Maturity Matrix

Use these statuses consistently:

- `scaffold`: structure exists, but not safe for direct reuse without significant work.
- `usable`: works for development/internal use, but still has clear operational or functional gaps.
- `production_baseline`: safe reusable baseline for real projects with standard hardening and review.
- `advanced`: materially beyond baseline, with stronger operational maturity and broader reuse confidence.

Current repository assessment:

| Module | Status | Rationale |
| --- | --- | --- |
| auth | production_baseline | Signed access tokens, cookie auth, CSRF, local auth, and LDAP login flow are implemented. |
| rbac | production_baseline | Permissions, DB persistence, assignment sync, and fail-closed operational mode are in place. |
| audit | production_baseline | Admin action logging, filters, export, and DB/memory fallback are implemented. |
| integrations | usable | LDAP and AI provider runtime settings are operational, but broader lifecycle/governance remains project-specific. |
| ai_gateway | usable | Provider status and validation exist, but full provider-agnostic chat/model registry flow is not implemented yet. |
| feature_flags | scaffold | Basic admin management exists, but persistence and rollout maturity are not productionized. |
| backups | usable | Backup profiles, retention, and restore flows exist, but advanced recovery posture is out of scope. |
| i18n | production_baseline | Language registry, protected system languages, admin management, and profile preference are implemented. |
| observability | usable | Structured logs, request IDs, and metrics exist, but operational dashboards/alerting are still light. |
| infra/tls | scaffold | Base stack is HTTP-only and requires production TLS work in derived systems. |

Use this matrix during bootstrap:

1. Keep `production_baseline` modules unless a platform-level change is approved.
2. Treat `usable` modules as opt-in with project-specific review.
3. Treat `scaffold` modules as teaching/reference structure, not production promises.