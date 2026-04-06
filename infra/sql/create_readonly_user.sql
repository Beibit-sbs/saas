-- Bootstrap script for a read-only operational DB account.
-- Run manually in controlled environments; do not auto-apply in production pipelines.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ops_readonly') THEN
    CREATE ROLE ops_readonly LOGIN PASSWORD 'change_me_readonly_password';
  END IF;
END
$$;

ALTER ROLE ops_readonly SET default_transaction_read_only = on;

GRANT CONNECT ON DATABASE app TO ops_readonly;
GRANT USAGE ON SCHEMA public TO ops_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ops_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO ops_readonly;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ops_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO ops_readonly;
