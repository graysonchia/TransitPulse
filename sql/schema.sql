-- TransitPulse Star Schema
-- ========================

-- Dimension: Date
CREATE TABLE dim_date (
    date_id     SERIAL PRIMARY KEY,
    full_date   DATE NOT NULL UNIQUE,
    year        INT NOT NULL,
    month       INT NOT NULL,
    day         INT NOT NULL,
    weekday     VARCHAR(10) NOT NULL,
    week_num    INT NOT NULL,
    is_weekend  BOOLEAN NOT NULL DEFAULT FALSE,
    is_holiday  BOOLEAN NOT NULL DEFAULT FALSE,
    holiday_name VARCHAR(100)
);

-- Dimension: Time
CREATE TABLE dim_time (
    time_id     SERIAL PRIMARY KEY,
    hour        INT NOT NULL,
    minute      INT NOT NULL,
    period      VARCHAR(20) NOT NULL, -- e.g. 'Morning Peak', 'Off-Peak'
    is_peak_hour BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (hour, minute)
);

-- Dimension: Route
CREATE TABLE dim_route (
    route_id    SERIAL PRIMARY KEY,
    route_code  VARCHAR(20) NOT NULL UNIQUE,
    route_name  VARCHAR(100) NOT NULL,
    route_type  VARCHAR(20) NOT NULL, -- 'LRT', 'MRT', 'BUS', 'KTM', 'Monorail'
    operator    VARCHAR(50) NOT NULL,
    line_color  VARCHAR(20),
    is_express  BOOLEAN NOT NULL DEFAULT FALSE
);

-- Dimension: Stop
CREATE TABLE dim_stop (
    stop_id     SERIAL PRIMARY KEY,
    stop_code   VARCHAR(20) NOT NULL UNIQUE,
    stop_name   VARCHAR(100) NOT NULL,
    latitude    NUMERIC(9,6),
    longitude   NUMERIC(9,6),
    zone        VARCHAR(10),
    is_terminal BOOLEAN NOT NULL DEFAULT FALSE,
    is_interchange BOOLEAN NOT NULL DEFAULT FALSE,
    route_id    INT REFERENCES dim_route(route_id)
);

-- Fact: Ridership
CREATE TABLE fact_ridership (
    ridership_id    BIGSERIAL PRIMARY KEY,
    date_id         INT NOT NULL REFERENCES dim_date(date_id),
    time_id         INT NOT NULL REFERENCES dim_time(time_id),
    route_id        INT NOT NULL REFERENCES dim_route(route_id),
    stop_id         INT NOT NULL REFERENCES dim_stop(stop_id),
    trip_id         VARCHAR(50),
    passenger_count INT NOT NULL DEFAULT 0,
    delay_minutes   NUMERIC(5,2) NOT NULL DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Indexes for analytics query performance
CREATE INDEX idx_fact_date ON fact_ridership(date_id);
CREATE INDEX idx_fact_route ON fact_ridership(route_id);
CREATE INDEX idx_fact_stop ON fact_ridership(stop_id);
CREATE INDEX idx_fact_time ON fact_ridership(time_id);
CREATE INDEX idx_stop_location ON dim_stop(latitude, longitude);
