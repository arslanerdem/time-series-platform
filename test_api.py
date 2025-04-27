import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import psycopg2
from datetime import datetime

from app import app  # Import the FastAPI app

# Test client for FastAPI
client = TestClient(app)

# Database connection configuration (matches docker-compose.yml)
DB_CONFIG = {
    "dbname": "timeseries",
    "user": "postgres",
    "password": "your_secure_password",  # Replace with .env password
    "host": "localhost",  # Use 'timescaledb' in Docker, 'localhost' for local
    "port": "5432"
}

@pytest.fixture(scope="function")
def db_connection():
    """Create a database connection for tests."""
    conn = psycopg2.connect(**DB_CONFIG)
    yield conn
    conn.close()

@pytest.fixture(scope="function")
def clean_database(db_connection):
    """Clear sensor_data table before each test."""
    with db_connection:
        with db_connection.cursor() as cur:
            cur.execute("TRUNCATE TABLE sensor_data RESTART IDENTITY;")
    db_connection.commit()

@pytest.mark.asyncio
async def test_insert_sensor_data(clean_database):
    """Test POST /sensor-data/ endpoint."""
    payload = {
        "sensor_id": 1,
        "temperature": 25.0,
        "humidity": 65.0,
        "time": "2025-04-27T12:00:00Z"
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/sensor-data/", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {"message": "Data inserted successfully"}

    # Verify data in database
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT sensor_id, temperature, humidity, time FROM sensor_data WHERE sensor_id = %s",
                (1,)
            )
            result = cur.fetchone()
            assert result == (1, 25.0, 65.0, datetime(2025, 4, 27, 12, 0, 0))

@pytest.mark.asyncio
async def test_get_avg_temperature(clean_database):
    """Test GET /sensor-data/avg-temperature/ endpoint."""
    # Insert sample data
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sensor_data (time, sensor_id, temperature, humidity)
                VALUES (%s, %s, %s, %s)
                """,
                (datetime(2025, 4, 27, 12, 0, 0), 1, 25.0, 65.0)
            )
        conn.commit()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/sensor-data/avg-temperature/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["sensor_id"] == 1
    assert abs(data[0]["avg_temp"] - 25.0) < 0.01
    assert "hour" in data[0]