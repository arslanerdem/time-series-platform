-- Script to create and configure the time series database in TimescaleDB

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create sensor_data table
CREATE TABLE sensor_data (
  time TIMESTAMPTZ NOT NULL,
  tl DOUBLE PRECISION,
  pl DOUBLE PRECISION,
  ul DOUBLE PRECISION,
  tr DOUBLE PRECISION,
  pr DOUBLE PRECISION,
  ur DOUBLE PRECISION,
  LeftLeak DOUBLE PRECISION,
  RightLeak DOUBLE PRECISION,
  Leak DOUBLE PRECISION,
  AverageLL DOUBLE PRECISION,
  AverageRL DOUBLE PRECISION,
  AverageLeak DOUBLE PRECISION,
  leakloc DOUBLE PRECISION,
  PRIMARY KEY (time)
);

-- Convert to hypertable
SELECT create_hypertable('sensor_data', 'time');

-- Enable compression
ALTER TABLE sensor_data SET (
  timescaledb.compress
);
SELECT add_compression_policy('sensor_data', INTERVAL '7 days');

-- Set retention policy
SELECT add_retention_policy('sensor_data', INTERVAL '6 months');
