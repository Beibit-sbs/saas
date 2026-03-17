# Platform Operating Model

## Platform Philosophy
This workspace follows a platform-first architecture.

Instead of building isolated applications, each system is built on a shared platform core and then extended with domain-specific modules.

## System Modules
- Auth
- RBAC
- Audit
- I18n
- Admin
- AI Gateway
- Feature Flags
- Settings
- Backup
- Observability

## System Boundaries
- Frontend: UI only.
- Backend: business logic, API, security enforcement.
- Platform Core: reusable shared services.
- Infrastructure: deployment and runtime operations.

## Development Workflow
Idea
-> Architect design
-> Implementation plan
-> Developer implementation
-> Reviewer validation
-> Security check
-> DevOps packaging
-> Deployment

## Deployment Strategy
- Local: Docker Compose.
- Staging: Docker Compose with staging config.
- Production: production profile + Nginx reverse proxy.

## Security Model
- Authentication: local + LDAP/AD.
- Authorization: RBAC + permissions.
- Data protection: masking and strict access control.
- Audit: all admin actions logged with actor and context.
- Secrets: environment variables for local use, secret manager for production.

## Observability Baseline
- Structured logs for backend services.
- Correlation/request ID propagation.
- Basic service metrics endpoint.
- Optional dashboards with Prometheus/Grafana.

## AI Gateway Model
Use provider abstraction.

AI Gateway
- OpenAI adapter
- Gemini adapter
- Local LLM adapter
- Future provider adapters

Gateway policy should support:
- fallback rules
- quota and rate limits
- provider-level routing policies

## Migration Policy
- DB schema changes only through migrations.
- Direct production schema edits are forbidden.
- Migration scripts must be versioned and reviewed.
