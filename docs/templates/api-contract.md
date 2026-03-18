# API Contract Template

Status: starter guidance for derived projects.

This file is not a complete API specification for the current repository. It is a fill-in template that should be completed for domain-specific endpoints in derived projects.

## Current Platform Baseline Already In Code

Confirmed patterns already present in the repository:
- backend APIs are exposed under `/api/`
- admin APIs are exposed under `/api/admin/` and nested admin prefixes
- auth uses signed access tokens, bearer auth, and HttpOnly cookie auth
- cookie-authenticated mutations require CSRF token validation
- admin routes require authenticated actor resolution and permission checks
- responses usually return named payload objects instead of raw arrays

Current limitation:
- this repository does not provide a complete endpoint-by-endpoint contract catalog in this file
- AI gateway v1 now includes model registry and unified public chat contract (`POST /api/ai/chat`), but advanced AI flows (streaming, embeddings, tools, RAG) are intentionally out of scope in this phase

## Fill-In Template For Derived Projects

## Endpoint
- Method:
- Path:
- Description:

## Request
- Headers:
- Query params:
- Body schema:

## Response
- Success code and body:
- Error codes and body:

## Security
- Auth required:
- Roles/permissions:

## Notes
- Idempotency:
- Rate limits:

Use `docs/templates/template-contracts.md` for confirmed platform-template contracts that already exist today.
