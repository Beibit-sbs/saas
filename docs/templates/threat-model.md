# Threat Model Template

Status: starter guidance for derived projects.

This file is not a finished project threat model. It records the platform-template baseline that already exists in code and shows what a derived project must complete before production launch.

## Platform Baseline Already Present

Entry points already present in the template:
- browser UI through Next.js frontend
- backend API under `/api/`
- admin routes under `/api/admin/`
- LDAP/AD connectivity when enabled
- AI provider validation endpoints under `/api/admin/ai`

Trust boundaries already present in the template:
- browser to backend
- frontend to backend API
- backend to PostgreSQL
- backend to LDAP/AD
- backend to external AI providers

Sensitive data already present in the template:
- auth cookies and access tokens
- LDAP bind credentials
- AI provider API keys
- local user passwords
- admin audit metadata

## Platform Baseline Threat Areas

Spoofing:
- mitigated by signed access tokens and backend token validation
- legacy identity headers are disabled by default

Tampering:
- mitigated by CSRF protection for cookie-authenticated mutations
- integration secrets are stored encrypted at rest in runtime settings

Repudiation:
- mitigated by admin audit logging conventions and request IDs

Information disclosure:
- partially mitigated by HttpOnly auth cookie flow and secret encryption
- still requires project-specific review for logs, exports, and personal data handling

Denial of service:
- partially mitigated by request rate limiting and AI-provider rate limiting
- still requires deployment-specific capacity planning and perimeter protection

Elevation of privilege:
- mitigated by RBAC permission checks and fail-closed operational behavior when RBAC DB source is unavailable

## What Derived Projects Must Fill In

- project-specific sensitive data classification
- external trust boundaries beyond the template baseline
- abuse scenarios specific to the project domain
- operational controls such as WAF, TLS, secret rotation, backup verification, and incident response
- accepted residual risks and owner approval

Do not treat this file as completed security sign-off. Use it as the starting point for the derived project threat model.
