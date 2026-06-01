CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    nfc_uid TEXT UNIQUE,
    password TEXT,
    face_encoding BYTEA,
    email TEXT,
    phone TEXT,
    address TEXT,
    member_uuid UUID UNIQUE DEFAULT gen_random_uuid()
);

CREATE TABLE IF NOT EXISTS access_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    method TEXT NOT NULL,
    status TEXT NOT NULL,
    snapshot BYTEA
);

CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_status_id ON access_logs(status, id DESC);
CREATE INDEX IF NOT EXISTS idx_access_logs_timestamp ON access_logs(timestamp DESC);

CREATE OR REPLACE VIEW user_access_summary AS
SELECT
    u.id AS user_id,
    u.username,
    u.nfc_uid,
    u.email,
    u.phone,
    u.address,
    u.member_uuid,
    COUNT(l.id) AS total_events,
    COUNT(l.id) FILTER (WHERE l.status = 'FINAL_SUCCESS') AS successful_entries,
    COUNT(l.id) FILTER (WHERE l.status IN ('UNAUTHORIZED', 'FINAL_FAIL')) AS failed_events,
    MAX(l.timestamp) FILTER (WHERE l.status = 'FINAL_SUCCESS') AS last_entry_at,
    MAX(l.timestamp) AS last_event_at
FROM users u
LEFT JOIN access_logs l ON l.user_id = u.id
GROUP BY u.id, u.username, u.nfc_uid, u.email, u.phone, u.address, u.member_uuid;
