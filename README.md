# Time Series Data Platform with TimescaleDB and FastAPI

This project provides a Dockerized platform for storing and querying time series data using **TimescaleDB** (a PostgreSQL extension optimized for time series) and a **FastAPI** application for data insertion and retrieval. The setup is designed for scalability and ease of use, with a focus on handling large time series datasets (e.g., sensor data).

## Project Overview

The platform consists of two services:
- **TimescaleDB**: A PostgreSQL-based database with the `timeseries` database and a `sensor_data` hypertable for storing time series data (e.g., temperature and humidity from sensors).
- **FastAPI**: A Python API with endpoints to insert sensor data and query average temperature per hour.

The services are orchestrated using **Docker Compose**, ensuring easy setup and replication. Environment variables are managed via a `.env` file for secure configuration.

## Project Structure

```
.
├── .env                    # Environment variables (e.g., database password)
├── docker-compose.yml      # Docker Compose configuration for TimescaleDB and FastAPI
├── init-db.sql             # SQL script to initialize the TimescaleDB database
├── app/
│   ├── Dockerfile          # Dockerfile for building the FastAPI container
│   ├── app.py              # FastAPI application code
│   └── requirements.txt    # Python dependencies for FastAPI
```

- **`.env`**: Stores sensitive data like `POSTGRES_PASSWORD` and `DB_PASSWORD`. Not committed to Git (listed in `.gitignore`).
- **`docker-compose.yml`**: Defines the `timescaledb` and `fastapi` services, including networking, volumes, and environment variables.
- **`init-db.sql`**: Creates the `sensor_data` hypertable, sets up compression and retention policies, and inserts sample data.
- **`app/`**:
  - `Dockerfile`: Builds the FastAPI container with Python 3.9 and dependencies.
  - `app.py`: Implements API endpoints for inserting and querying time series data.
  - `requirements.txt`: Lists Python packages (`fastapi`, `uvicorn`, `psycopg2-binary`).

## Requirements

- **Docker Desktop**: Required to run the Docker Compose services.
- **Git**: To clone and manage the repository.
- **Python 3.8+** (optional): Only needed for local development outside Docker.
- **psql** (optional): PostgreSQL client for direct database interaction (`brew install postgresql` on macOS).
- **curl** or a similar tool (optional): For testing API endpoints.
- **macOS/Linux/Windows**: Tested on macOS, but should work on other platforms with Docker.

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/arslanerdem/time-series-platform.git
cd time-series-platform
```

### 2. Create the `.env` File
Create a `.env` file in the project root with the database password:
```bash
echo "POSTGRES_PASSWORD=your_secure_password" > .env
echo "DB_PASSWORD=your_secure_password" >> .env
```

- Ensure `POSTGRES_PASSWORD` and `DB_PASSWORD` are identical.
- Use a strong password for production (avoid `344234`).
- The `.env` file is ignored by Git (see `.gitignore`).

### 3. Start the Services
Run Docker Compose to start TimescaleDB and FastAPI:
```bash
docker-compose up -d
```

- The `-d` flag runs containers in detached mode.
- This builds the FastAPI container, starts TimescaleDB, and initializes the database with `init-db.sql`.

### 4. Verify the Setup
Check running containers:
```bash
docker ps
```

Expected output includes:
- `my-timescaledb` (port `5432`)
- `my-fastapi` (port `8000`)

Connect to the database:
```bash
psql -h localhost -p 5432 -U postgres -d timeseries
```
Enter the password from `.env`. Run:
```sql
SELECT * FROM sensor_data;
```

Test FastAPI endpoints:
```bash
curl -X POST "http://localhost:8000/sensor-data/" \
-H "Content-Type: application/json" \
-d '{"sensor_id": 1, "temperature": 25.0, "humidity": 65.0, "time": "2025-04-27T12:00:00Z"}'
```
```bash
curl http://localhost:8000/sensor-data/avg-temperature/
```

## Usage

### API Endpoints
- **POST `/sensor-data/`**: Insert sensor data.
  - Payload example:
    ```json
    {
      "sensor_id": 1,
      "temperature": 25.0,
      "humidity": 65.0,
      "time": "2025-04-27T12:00:00Z"
    }
    ```
  - Response: `{"message": "Data inserted successfully"}`
- **GET `/sensor-data/avg-temperature/`**: Query average temperature per hour for the last 24 hours.
  - Response: JSON array of `{hour, sensor_id, avg_temp}` objects.

### Database Interaction
- Connect via `psql`:
  ```bash
  psql -h localhost -p 5432 -U postgres -d timeseries
  ```
- Query the `sensor_data` hypertable:
  ```sql
  SELECT * FROM sensor_data;
  ```

### Stopping the Services
```bash
docker-compose down
```

To remove data (deletes `pgdata` volume):
```bash
docker-compose down -v
```

## Maintenance

### Backups
Back up the database:
```bash
docker exec my-timescaledb pg_dump -U postgres timeseries > backup_$(date +%F).sql
```

Restore (after copying `backup.sql` to the project directory):
```bash
docker exec -i my-timescaledb psql -U postgres -d timeseries < backup.sql
```

### Volume Management
Check the `pgdata` volume:
```bash
docker volume ls
docker volume inspect database_pgdata
```

Estimate size:
```bash
docker exec my-timescaledb du -sh /var/lib/postgresql/data
```

### Updating Passwords
1. Update `.env`:
   ```bash
   echo "POSTGRES_PASSWORD=new_secure_password" > .env
   echo "DB_PASSWORD=new_secure_password" >> .env
   ```
2. Reset the `pgdata` volume:
   ```bash
   docker-compose down
   docker volume rm database_pgdata
   docker-compose up -d
   ```

## Troubleshooting

- **Authentication Errors**:
  - Ensure `POSTGRES_PASSWORD` and `DB_PASSWORD` in `.env` match.
  - Reset `pgdata` if passwords change (see above).
  - Check logs:
    ```bash
    docker logs my-fastapi
    docker logs my-timescaledb
    ```
- **Port Conflicts**:
  - Check ports:
    ```bash
    lsof -i :5432
    lsof -i :8000
    ```
  - Update `docker-compose.yml` (e.g., `5433:5432`, `8001:8000`) if needed.
- **Container Issues**:
  - Verify services:
    ```bash
    docker ps
    ```
  - Check health:
    ```bash
    docker inspect my-timescaledb --format '{{.State.Health.Status}}'
    ```

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## License

MIT License. See `LICENSE` file for details.

## Contact

For issues or questions, open an issue on GitHub or contact [arslan.erdem@gmail.com].