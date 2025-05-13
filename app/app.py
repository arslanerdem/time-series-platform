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
    except Exception a
