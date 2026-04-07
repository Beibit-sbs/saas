# Admin Smoke Checklist

## Goal
Quick confidence check that the admin platform core is working after Docker-side changes or before a release.

## Preconditions
- App stack is running (`make up`) and opens at `http://nginx`.
- Admin session is available (`admin/admin123` in demo mode).
- Backend and frontend checks are green through Docker Compose validation commands.

## Smoke Steps
1. Open `/admin` and confirm tabs load without console/network errors.
2. Check RBAC tab: list roles, create/update one role, assign role to a test user ID.
3. Check Audit tab: load events, filter by action, export CSV.
4. Check Integrations tab: read current LDAP/AI statuses and save a non-secret field.
5. Check I18n tab: add one custom language, disable/enable it, then delete it.
6. Check Backup tab: save profiles, run backup now, verify new history row appears.
7. Check Restore flow: run restore dry-run, then verify restore-now requires confirmation.
8. Check Retention flow: run retention dry-run, then verify apply requires confirmation.
9. Check security behavior: access one admin endpoint without admin headers and verify rejection.

## Expected Results
- No 5xx responses during smoke flow.
- Every admin action creates an audit event.
- Backup jobs include correct `job_type` (`backup`, `restore`, `retention`).
- Destructive actions require explicit confirmation in UI.

## Optional Quick API Spot Checks
- `GET /api/admin/rbac/roles`
- `GET /api/admin/audit/events`
- `GET /api/admin/backups/history`
- `GET /api/admin/backups/restore-candidates?profile_id=<id>`
