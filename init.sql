CREATE TABLE IF NOT EXISTS user_sessions (
    user_id BIGINT PRIMARY KEY,
    history JSONB
);