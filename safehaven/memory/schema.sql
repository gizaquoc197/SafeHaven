CREATE TABLE IF NOT EXISTS messages (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    role      TEXT    NOT NULL CHECK (role IN ('user', 'assistant')),
    content   TEXT    NOT NULL,
    timestamp TEXT    NOT NULL,
    emotion   TEXT,
    risk_level INTEGER NOT NULL DEFAULT 1
);
