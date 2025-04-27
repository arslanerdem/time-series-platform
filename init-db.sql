-- Script to create and configure the time series database in TimescaleDB

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create sensor_data table
CREATE TABLE sensor_data (
  time TIMESTAMPTZ NOT NULL,
  sensor_id INT NOT NULL,
  temperature DOUBLE PRECISION,
  humidity DOUBLE PRECISION,
  PRIMARY KEY (time, sensor_id)
);

-- Convert to hypertable
SELECT create_hypertable('sensor_data', 'time');

-- Enable compression
ALTER TABLE sensor_data SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'sensor_id'
);
SELECT add_compression_policy('sensor_data', INTERVAL '7 days');

-- Set retention policy
SELECT add_retention_policy('sensor_data', INTERVAL '6 months');

-- Insert sample data
INSERT INTO sensor_data (time, sensor_id, temperature, humidity)
VALUES
  (NOW(), 1, 23.5, 60.2),
  (NOW() - INTERVAL '1 hour', 1, 22.8, 61.0),
  (NOW(), 2, 24.1, 59.8);

-- Test query: Average temperature per hour
SELECT time_bucket('1 hour', time) AS hour,
       sensor_id,
       AVG(temperature) AS avg_temp
FROM sensor_data
WHERE time > NOW() - INTERVAL '1 day'
GROUP BY time_bucket('1 hour', time), sensor_id;
