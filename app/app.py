from fastapi import FastAPI, HTTPException, Query
import psycopg2
from pydantic import BaseModel
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import List

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
    tl: float
    pl: float
    ul: float
    tr: float
    pr: float
    ur: float
    LeftLeak: float
    RightLeak: float
    Leak: float
    AverageLL: float
    AverageRL: float
    AverageLeak: float
    leakloc: float
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
                    INSERT INTO sensor_data (time, tl, pl, ul, tr, pr, ur, LeftLeak, RightLeak, Leak, AverageLL, AverageRL, AverageLeak, leakloc)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (data.time, data.tl, data.pl, data.ul, data.tr, data.pr, data.ur, data.LeftLeak, data.RightLeak, data.Leak, data.AverageLL, data.AverageRL, data.AverageLeak, data.leakloc)
                )
        return {"message": "Data inserted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insert failed: {str(e)}")
    finally:
        conn.close()

# Endpoint to get sensor data given the time range (start time and end time)
@app.get("/sensor-data/")
async def get_sensor_data(start_time: datetime = Query(...), end_time: datetime = Query(...)) -> List[SensorData]:
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT time, tl, pl, ul, tr, pr, ur, LeftLeak, RightLeak, Leak, AverageLL, AverageRL, AverageLeak, leakloc 
                    FROM sensor_data 
                    WHERE time BETWEEN %s AND %s;
                    """,
                    (start_time, end_time)
                )
                rows = cur.fetchall()
                if not rows:
                    raise HTTPException(status_code=404, detail="No data found for the given time range")
                sensor_data_list = [SensorData(
                    time=row[0],
                    tl=row[1],
                    pl=row[2],
                    ul=row[3],
                    tr=row[4],
                    pr=row[5],
                    ur=row[6],
                    LeftLeak=row[7],
                    RightLeak=row[8],
                    Leak=row[9],
                    AverageLL=row[10],
                    AverageRL=row[11],
                    AverageLeak=row[12],
                    leakloc=row[13]
                ) for row in rows]
                return sensor_data_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
    finally:
        conn.close()
