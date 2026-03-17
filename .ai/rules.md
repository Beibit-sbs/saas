# AI Engineering Rules

System type: browser-based web applications only.

## Default Stack
- Frontend: Next.js (React, TypeScript)
- Backend: FastAPI (Python 3.12+)
- Database: PostgreSQL 16+
- Infrastructure: Docker, Docker Compose, Nginx, Linux server

## Non-Negotiable Rules
1. No desktop app scope unless explicitly approved.
2. No business logic in frontend; frontend calls backend API only.
3. All data access goes through backend services.
4. All services must be containerized.
5. Secrets are stored only in environment variables or secret manager.
6. DB schema changes only through migrations.
7. Every admin action must be audit logged.
8. Personal data must be minimized and protected.
9. CI must fail on test/lint/security failures.
10. Production configs must avoid default credentials.
11. Every university project must include an admin dashboard.
12. Every university project must support LDAP/AD as an auth mode.
13. Every university project must include API-key based AI provider integration.
14. AI provider access must go through backend gateway adapters.
15. Role-based access control (RBAC) is mandatory.
16. Every university project must include an in-app help assistant for users.
17. Every project UI must support three languages: Kazakh (kk), Russian (ru), English (en), and allow adding extra languages from admin settings.
18. Language selection must change the full user-facing UI consistently on every screen in scope; mixed-language screens are not acceptable.
19. AI gateway must enforce rate limiting and quota policies.
20. Every service must emit structured logs with request or correlation IDs.
21. Platform changes must be backward compatible or guarded by feature flags.
22. Reusable improvements from project repos must be promoted to the master template before starting the next project.
23. Never copy one project directly into another; always create from the master template.
24. Template docs for env/config/contracts must be grounded in confirmed code behavior or existing env examples.
25. Template hardening must document bootstrap flow, maturity, and validation before large decomposition work.
26. Example-only modules must stay explicitly labeled, namespaced, and removable in derived systems.
27. Template validation must have one explicit entrypoint that is easy to run and understand.

## System Boundaries
- Frontend: UI only, no core business logic.
- Backend: business logic, data access, and integration orchestration.
- Platform Core: shared cross-project services (Auth, RBAC, Audit, I18n, AI Gateway, Settings, Feature Flags).
- Infrastructure: deployment and runtime layer (Docker, Nginx, CI/CD, monitoring).

## Platform Philosophy
- Build platform-first, then domain modules.
- Prefer reusable shared services over one-off project shortcuts.
- Keep security and observability as default platform behavior, not optional add-ons.
- Apply changes in small, verifiable steps to avoid breaking the template.

## University Platform Core (Required)
- Admin Dashboard Core: user/role management, integration settings, system controls.
- Auth Core: local auth + LDAP/AD + service/API-key access.
- RBAC Core: platform roles and resource-level permissions.
- Audit Core: immutable audit trail for admin and sensitive actions.
- AI Gateway Core: provider-agnostic adapters (OpenAI, Gemini, Anthropic, custom).
- Help Assistant Core: contextual in-app guidance and Q&A for forms and workflows.
- I18n Core: full interface localization for `kk`, `ru`, `en`.
- Language Behavior Core: when a user changes language, all visible navigation, pages, forms, statuses, and helper UI in scope must update to the same language immediately or after a defined app refresh step.
- Security Core: secret policy, rate limits, and secure headers.
- Backup Core: scheduled backups and restore verification.

## Definition of Done
- Architecture documented and approved.
- API contracts documented.
- Tests for critical paths exist and pass.
- Security checklist completed.
- Docker Compose local run succeeds.
- Deployment runbook exists.

## P1 Safe Roadmap (Template Evolution)
- Alembic migrations are mandatory for schema changes.
- Audit event schema must include: timestamp, actor, action, entity, metadata, ip, result, correlation_id.
- AI gateway must enforce per-user and per-provider request limits.
- Feature Flags module controls risky or partial rollouts.
- Observability baseline is required: structured logs, request IDs, and basic metrics.
