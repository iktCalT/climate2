CREATE TABLE IF NOT EXISTS locations (
    loc_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lat DOUBLE PRECISION NOT NULL CHECK (lat BETWEEN -90 AND 90),
    lon DOUBLE PRECISION NOT NULL CHECK (lon BETWEEN -180 AND 180),
    UNIQUE (lat, lon)
);

CREATE TABLE IF NOT EXISTS data (
    loc_id BIGINT NOT NULL REFERENCES locations(loc_id),
    dates DATE NOT NULL,
    provider TEXT NOT NULL DEFAULT 'open_meteo_cmip6'
        CONSTRAINT data_provider_format_check CHECK (provider ~ '^[a-z][a-z0-9_]*$'),
    temp_mean DOUBLE PRECISION CHECK (temp_mean >= -273.15),
    temp_max DOUBLE PRECISION CHECK (temp_max >= -273.15),
    temp_min DOUBLE PRECISION CHECK (temp_min >= -273.15),
    precip DOUBLE PRECISION CHECK (precip >= 0),
    PRIMARY KEY (loc_id, dates, provider)
);

ALTER TABLE data ADD COLUMN IF NOT EXISTS provider TEXT;
UPDATE data SET provider = 'open_meteo_cmip6' WHERE provider IS NULL;
ALTER TABLE data ALTER COLUMN provider SET DEFAULT 'open_meteo_cmip6';
ALTER TABLE data ALTER COLUMN provider SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'data'::regclass
          AND conname = 'data_provider_format_check'
    ) THEN
        ALTER TABLE data
            ADD CONSTRAINT data_provider_format_check
            CHECK (provider ~ '^[a-z][a-z0-9_]*$');
    END IF;
END
$$;

ALTER TABLE data DROP CONSTRAINT IF EXISTS data_pkey;
ALTER TABLE data ADD CONSTRAINT data_pkey PRIMARY KEY (loc_id, dates, provider);

CREATE INDEX IF NOT EXISTS data_dates_idx ON data (dates);
CREATE INDEX IF NOT EXISTS data_provider_dates_idx ON data (provider, dates);
