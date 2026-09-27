CREATE TABLE IF NOT EXISTS climate_import_job (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    window_name TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('running', 'complete', 'failed')),
    processed INTEGER NOT NULL DEFAULT 0,
    total INTEGER NOT NULL,
    current_month DATE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
