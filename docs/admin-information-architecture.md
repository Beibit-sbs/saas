# Admin Information Architecture

## 1. Purpose

The admin console is the operational control surface for the platform core.
It centralizes identity-sensitive and privileged tasks while keeping backend as authority.

Route:
- `/admin`

---

## 2. Primary Navigation

Tab order:
1. `overview`
2. `languages`
3. `local-users`
4. `rbac`
5. `integrations`
6. `feature-flags`
7. `backups`
8. `audit`

Design intent:
- Move from global state awareness (`overview`) to concrete control domains.

---

## 3. Tab-Level IA

## Overview

Goal:
- Fast operational snapshot.

Information blocks:
- Backend/API health
- Local user count
- RBAC role and assignment counts
- Language coverage indicators
- LDAP and AI integration readiness
- Last backup and recent audit context

## Languages

Goal:
- Manage language availability without breaking core system languages.

Core actions:
- Add language from catalog
- Enable/disable language
- Delete non-system language

Rules:
- `kk`, `ru`, `en` are protected system languages

## Local Users

Goal:
- Manage local account fallback and controlled non-LDAP users.

Core actions:
- Search/filter users
- Update display name/language/roles
- Reset password
- Delete user

## RBAC

Goal:
- Manage authorization model at role and assignment layers.

Core actions:
- Create/update/delete roles
- Assign role to user
- Revoke assignment
- Filter assignments by user and role

## Integrations

Goal:
- Manage external auth and AI dependencies.

Subdomains:
- LDAP/AD configuration + connection tests
- AI provider credentials and validation endpoints

Security behavior:
- Secrets are not exposed in plain form when existing values are retained.

## Feature Flags

Goal:
- Expose operational feature toggles.

Core actions:
- List feature flags
- Toggle enabled/disabled state

Current state:
- Backed by scaffold/in-memory store

## Backups

Goal:
- Operate backup/restore lifecycle with guardrails.

Core actions:
- Configure backup profiles and active profile
- Run backup
- Manage retention (dry-run/apply)
- List restore candidates
- Execute restore dry-run and restore

Guardrails:
- Profile paths constrained by `BACKUP_ALLOWED_ROOTS`

## Audit

Goal:
- Inspect and export privileged activity.

Core actions:
- Query events
- Export CSV/JSON

Current filters:
- `actor`
- `action`
- `entity`
- `result`
- `correlation_id`
- `since`

---

## 4. Cross-Cutting UX Semantics

- Status line communicates API errors and operation results.
- Tab-specific lazy loading limits unnecessary backend calls.
- Localization is applied across admin labels.
- Operational controls remain in a single-page admin workspace for quick incident response.

---

## 5. Permission and Control Model

- Every write operation is backend-authorized via RBAC dependencies.
- Frontend visibility does not bypass backend authorization.
- Audit domain supports accountability for privileged actions.

---

## 6. Current IA Gaps

- Feature flags do not yet include persistent rollout policy management.
- Dedicated frontend automated tests for admin journeys are not yet part of current repo validation.
