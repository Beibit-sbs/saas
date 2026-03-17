# MCP Read-Only Setup

Goal: allow AI assistants to inspect project files and database schema/data without write privileges.

## 1. Filesystem MCP (read-only)
Use `mcp/servers.example.json` and keep only project folder as allowed path.

## 2. PostgreSQL read-only role
Run once in PostgreSQL:

```sql
CREATE ROLE readonly_user LOGIN PASSWORD 'change_me';
GRANT CONNECT ON DATABASE app TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;
```

## 3. Security Rules
- Never use admin DB credentials in MCP.
- Use separate read-only credentials for each environment.
- Rotate password regularly.
- Restrict network access to DB.
