-- PayPilot Shield: create the database user and database on local PostgreSQL.
-- Run as the postgres superuser:
--   sudo -u postgres psql -f setup_local_postgres.sql
-- Change the password below before running, and use the same one in your .env.

-- 1. Create the user (role) if it does not exist yet
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'paypilot') THEN
      CREATE ROLE paypilot WITH LOGIN PASSWORD 'paypilot_2026';
   ELSE
      ALTER ROLE paypilot WITH LOGIN PASSWORD 'paypilot_2026';
   END IF;
END
$$;

-- 2. Create the database if it does not exist yet (\gexec runs the generated statement)
SELECT 'CREATE DATABASE paypilot OWNER paypilot ENCODING ''UTF8'''
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'paypilot')
\gexec

-- 3. Make sure the user owns the database and can create tables in it
ALTER DATABASE paypilot OWNER TO paypilot;
GRANT ALL PRIVILEGES ON DATABASE paypilot TO paypilot;

\connect paypilot
GRANT ALL ON SCHEMA public TO paypilot;
ALTER SCHEMA public OWNER TO paypilot;

-- Optional: start from scratch (uncomment to wipe all tables)
-- DROP SCHEMA public CASCADE;
-- CREATE SCHEMA public AUTHORIZATION paypilot;