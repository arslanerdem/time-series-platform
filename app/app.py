from fastapi import FastAPI, HTTPException
import psycopg2
from pydantic import BaseModel
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file in project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = FastAPI()

# Database connection configuration from environment variables
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "timeseries"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "timescaledb"),
    "port": os.getenv("DB_PORT", "5432")
}

# Debug: Log environment variables (remove in production)
print(f"DB_CONFIG: {DB_CONFIG}")

# Validate required environment variables
if not DB_CONFIG["password"]:
    raise ValueError("DB_PASSWORD environment variable is not set")

# Pydantic model for sensor data
class SensorData(BaseModel):
    sensor_id: int
    temperature: float
    humidity: float
    time: datetime

# Connect to database
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Endpoint to insert sensor data
@app.post("/sensor-data/")
async def insert_sensor_data(data: SensorData):
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sensor_data (time, sensor_id, temperature, humidity)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (data.time, data.sensor_id, data.temperature, data.humidity)
                )
        return {"message": "Data inserted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insert failed: {str(e)}")
    finally:
        conn.close()

# Endpoint to query average temperature per hour
@app.get("/sensor-data/avg-temperature/")
async def get_avg_temperature():
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT time_bucket('1 hour', time) AS hour,
                           sensor_id,
                           AVG(temperature) AS avg_temp
                    FROM sensor_data
                    WHERE time > NOW() - INTERVAL '1 day'
                    GROUP BY time_bucket('1 hour', time), sensor_id
                    """
                )
                rows = cur.fetchall()
                return [
                    {"hour": row[0], "sensor_id": row[1], "avg_temp": row[2]}
                    for row in rows
                ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
    finally:
        conn.close()