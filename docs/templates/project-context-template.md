# PROJECT_CONTEXT

## Project Identity
- Project name:
- Short description:
- Owner:
- Start date:
- Target release:
- Source template revision/date:
- Confirmed rename targets updated (`README.md`, `docs/project-status.md`, user-facing titles): yes/no

## Scope
- In scope:
- Out of scope:
- Success criteria:

## Users and Roles
- Primary user groups:
- Roles:
- Role responsibilities:

## Domain Modules
- Required modules:
- Optional modules:
- Deferred modules:
- Keep as platform baseline (do not redesign without approval):
- Scaffold modules that need production review before reuse:

## Integrations
- Required integrations:
- External systems:
- API dependencies:
- Selected AI providers from template baseline:

## Data and Security
- Personal data involved (yes/no):
- Data sensitivity level:
- Retention requirements:
- Compliance requirements:
- Production secret handling owner:

## Auth and Access
- Auth mode: local / LDAP-AD / hybrid
- SSO requirements:
- RBAC constraints:
- Admin boundaries:
- LDAP/AD rollout decision from template baseline:

## AI and Automation
- AI provider policy:
- Allowed AI features:
- Restricted AI operations:
- Audit requirements for AI actions:
- Keep template AI gateway as-is / extend / defer:

## Internationalization
- Required languages:
- Optional languages:
- Localization constraints:

## Non-Functional Requirements
- Availability target:
- Performance target:
- Scalability expectations:
- Observability requirements:

## Deployment
- Environments: local / staging / production
- Infrastructure constraints:
- Rollback strategy:
- TLS termination approach for production:
- Backup/restore owner and storage boundary:

## Template Bootstrap Checklist
- `infra/.env.example` reviewed and copied to `infra/.env`
- Required startup variables reviewed: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `JWT_SECRET`, `NEXT_PUBLIC_API_BASE_URL`
- Optional provider/integration variables reviewed for this project
- Template validation command selected and documented
- Platform maturity review completed for scaffold modules

## Runtime Configuration Ownership
- Environment-owned configuration that stays outside admin runtime settings:
- Admin-managed runtime settings to allow in derived project:
- Config domains that must remain read-only in admin UI:

## Delivery Plan
- Current phase:
- Immediate milestones:
- Risks:
- Open questions:
