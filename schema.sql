CREATE TABLE IF NOT EXISTS locations (
    loc_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lat DOUBLE PRECISION NOT NULL CHECK (lat BETWEEN -90 AND 90),
    lon DOUBLE PRECISION NOT NULL CHECK (lon BETWEEN -180 AND 180),
    UNIQUE (lat, lon)
);

CREATE TABLE IF NOT EXISTS data (
    loc_id BIGINT NOT NULL REFERENCES locations(loc_id),
    dates DATE NOT NULL,
    temp_mean DOUBLE PRECISION CHECK (temp_mean >= -273.15),
    temp_max DOUBLE PRECISION CHECK (temp_max >= -273.15),
    temp_min DOUBLE PRECISION CHECK (temp_min >= -273.15),
    precip DOUBLE PRECISION CHECK (precip >= 0),
    PRIMARY KEY (loc_id, dates)
);

CREATE INDEX IF NOT EXISTS data_dates_idx ON data (dates);
