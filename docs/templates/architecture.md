# Architecture Template

Status: starter guidance for derived projects.

This file is not a finished architecture description for the current repository. It captures the platform-template baseline and the sections that a derived project must complete with project-specific scope.

## Platform Baseline

Current baseline architecture in this repository:
- Next.js frontend for user and admin UI
- FastAPI backend for auth, admin services, integrations, and operational APIs
- PostgreSQL for RBAC and language persistence when `DATABASE_URL` is configured
- Docker Compose and Nginx for local/prototype deployment shape

Current platform modules already present:
- auth
- rbac
- audit
- i18n
- ldap
- integrations settings
- backup
- feature_flags (scaffold)
- ai_gateway (provider status/validation baseline, not full chat gateway)
- example_slice (reference-only wiring example)

## What This Document Must Contain In A Derived Project

## 1. Problem and Scope
- business goal
- user roles
- in-scope capabilities
- out-of-scope capabilities

## 2. System Context
- external systems actually used by the project
- deployment boundaries
- data sensitivity constraints

## 3. Modules
- frontend modules added beyond the template baseline
- backend domain modules added beyond the template baseline
- ownership boundaries between platform core and project domain code

## 4. Data Flow
- main user flows
- admin flows
- integration flows
- failure handling expectations

## 5. API Contracts
- domain endpoints added by the project
- auth mode actually used
- permission model and error conventions

## 6. Risks and Mitigations
- scaling risks
- security risks
- operability risks

## 7. Rollout Plan
- migration or bootstrap plan
- operational readiness checklist

Do not treat this file as complete architecture documentation until those project-specific sections are filled in.
