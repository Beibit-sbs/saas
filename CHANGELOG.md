# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows semantic-style commit grouping.

## [Unreleased]

### Added
- PgBouncer integration in docker-compose with backend runtime routed through connection pooling.
- Backend CI type-check step with mypy and baseline configuration for package-bases mode.
- Coverage gate in pytest defaults (`--cov=app --cov-fail-under=80`).
- Worker graceful shutdown entrypoint (`backend/scripts/run_worker.py`) with SIGTERM handling.
- Role portal shell tests and additional frontend security/runtime route tests.

### Changed
- Billing enforcement expanded across courses/enrollments/scheduling write paths.
- Billing service switched to fail-closed DB-only mode guard for subscription store availability.
- Auth cookie flow unified around `app_access_token` with backward-compatible legacy fallback.
- Admissions service import structure cleaned up (removed lazy imports, preserved patchability).

### Security
- Nginx hardening headers extended with Content-Security-Policy, Referrer-Policy, and Permissions-Policy.
- AI provider secret/env propagation standardized in runtime compose environment.
