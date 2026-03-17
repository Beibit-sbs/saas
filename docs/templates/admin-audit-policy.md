# Admin Audit Policy

## What To Log
- Admin login/logout
- Permission changes
- Data create/update/delete actions
- Export/download actions with sensitive data

## Required Fields
- actor_id
- action
- target_type
- target_id
- timestamp_utc
- source_ip
- request_id

## Retention
- Keep logs for at least 180 days by default.
- Restrict read access to authorized roles only.
