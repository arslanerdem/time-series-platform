import pytest
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
import psycopg2
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

# Load environment variables from .env file in project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

from app import app  # Import the FastAPI app

# Test client for FastAPI
client = TestClient(app)

# Database connection configuration from environment variables
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "timeseries"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

# Validate required environment variables
if not DB_CONFIG["password"]:
    raise ValueError("DB_PASSWORD environment variable is not set in .env file")

@pytest.fixture(scope="function")
def db_connection():
    """Create a database connection for tests."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
        conn.close()
    except Exception as e:
        pytest.fail(f"Failed to connect to database: {str(e)}")

@pytest.fixture(scope="function")
def clean_database(db_connection):
    """Clear sensor_data table before each test."""
    try:
        with db_connection:
            with db_connection.cursor() as cur:
                cur.execute("TRUNCATE TABLE sensor_data RESTART IDENTITY;")
        db_connection.commit()
    except Exception as e:
        pytest.fail(f"Failed to clean database: {str(e)}")

@pytest.mark.asyncio
async def test_insert_sensor_data(clean_database):
    """Test POST /sensor-data/ endpoint."""
    payload = {
        "sensor_id": 1,
        "temperature": 25.0,
        "humidity": 65.0,
        "time": "2025-04-27T12:00:00Z"
    }
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        response = await ac.post("/sensor-data/", json=payload)
    
    if response.status_code != 200:
        print(f"Error response: {response.text}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json() == {"message": "Data inserted successfully"}

    # Verify data in database
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT sensor_id, temperature, humidity, time FROM sensor_data WHERE sensor_id = %s",
                    (1,)
                )
                result = cur.fetchone()
                assert result == (1, 25.0, 65.0, datetime(2025, 4, 27, 12, 0, 0, tzinfo=timezone.utc))
    except Exception as e:
        pytest.fail(f"Database query failed: {str(e)}")

@pytest.mark.asyncio
async def test_get_avg_temperature(clean_database):
    """Test GET /sensor-data/avg-temperature/ endpoint."""
    # Insert sample data
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sensor_data (time, sensor_id, temperature, humidity)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (datetime(2025, 4, 27, 12, 0, 0, tzinfo=timezone.utc), 1, 25.0, 65.0)
                )
            conn.commit()
    except Exception as e:
        pytest.fail(f"Failed to insert sample data: {str(e)}")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        response = await ac.get("/sensor-data/avg-temperature/")
    
    if response.status_code != 200:
        print(f"Error response: {response.text}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert len(data) == 1
    assert data[0]["sensor_id"] == 1
    assert abs(data[0]["avg_temp"] - 25.0) < 0.01
    assert "hour" in data[0]