-- Run only through explicit setup_database; one global worker and rate ledger.
CREATE TABLE IF NOT EXISTS climate_location_fetch_job (
    id SMALLINT PRIMARY KEY CHECK (id = 1),
    state TEXT NOT NULL CHECK (state IN ('running', 'complete', 'failed')),
    sample_lat DOUBLE PRECISION NOT NULL,
    sample_lon DOUBLE PRECISION NOT NULL,
    current_month DATE NOT NULL,
    backend_pid INTEGER NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE climate_location_fetch_job ADD COLUMN IF NOT EXISTS backend_pid INTEGER;

CREATE TABLE IF NOT EXISTS climate_location_fetch_limit (
    id SMALLINT PRIMARY KEY CHECK (id = 1),
    window_start TIMESTAMPTZ NOT NULL,
    starts INTEGER NOT NULL CHECK (starts >= 0)
);
