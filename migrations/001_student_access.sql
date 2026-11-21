-- Aplicar manualmente en PostgreSQL/Neon de prueba. No ejecutar al arrancar.
BEGIN;

CREATE TABLE IF NOT EXISTS student_demo_profiles (
    id UUID PRIMARY KEY,
    display_name VARCHAR(80) NOT NULL,
    identity_hmac CHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS student_demo_sessions (
    id UUID PRIMARY KEY,
    profile_id UUID NOT NULL REFERENCES student_demo_profiles(id),
    token_hash CHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_student_demo_sessions_expiry
    ON student_demo_sessions(expires_at);

COMMIT;
