# Time Series Data Platform with TimescaleDB and FastAPI

This project provides a Dockerized platform for storing and querying time series data using **TimescaleDB** (a PostgreSQL extension optimized for time series) and a **FastAPI** application for data insertion and retrieval. The setup is designed for scalability and ease of use, with a focus on handling large time series datasets, such as sensor data (e.g., temperature and humidity).

## Project Overview

The platform consists of two services:
- **TimescaleDB**: A PostgreSQL-based database with the `timeseries` database and a `sensor_data` hypertable for storing time series data.
- **FastAPI**: A Python API with endpoints to insert sensor data and query average temperature per hour.

The services are orchestrated using **Docker Compose**, ensuring easy setup and replication. Environment variables are managed via a `.env` file for secure configuration.

## Project Structure

```
.
├── .env                    # Environment variables (e.g., database password, not in Git)
├── .gitignore             # Excludes .env, venv, backups, and Python cache files
├── README.md              # Project documentation
├── docker-compose.yml     # Docker Compose configuration for TimescaleDB and FastAPI
├── init-db.sql            # SQL script to initialize the TimescaleDB database
├── app/
│   ├── Dockerfile         # Dockerfile for building the FastAPI container
│   ├── app.py             # FastAPI application code
│   ├── requirements.txt   # Python dependencies for FastAPI and tests
│   ├── pytest.ini         # Pytest configuration for async tests
│   └── tests/             # Test suite for FastAPI endpoints
│       ├── __init__.py
│       └── test_api.py    # Tests for API endpoints
├── .github/
│   └── workflows/
│       └── ci.yml         # GitHub Actions CI workflow
```

- **`.env`**: Stores sensitive data like `POSTGRES_PASSWORD` and `DB_PASSWORD`. Not committed to Git (listed in `.gitignore`).
- **`docker-compose.yml`**: Defines the `timescaledb` and `fastapi` services, including networking, volumes, and environment variables.
- **`init-db.sql`**: Creates the `sensor_data` hypertable, sets up compression and retention policies, and inserts sample data.
- **`app/`**:
  - `Dockerfile`: Builds the FastAPI container with Python 3.9 and dependencies.
  - `app.py`: Implements API endpoints for inserting and querying time series data, using environment variables from `.env` or Docker Compose.
  - `requirements.txt`: Lists Python packages (`fastapi`, `uvicorn`, `psycopg2-binary`, `pytest`, `httpx`, `python-dotenv`, `pytest-asyncio`).
  - `pytest.ini`: Configures `pytest` for async tests.
  - `tests/`: Contains `pytest` tests for API endpoints.
- **`.github/workflows/ci.yml`**: GitHub Actions workflow to run tests automatically.

## Requirements

- **Docker Desktop**: Required to run the Docker Compose services.
- **Git**: To clone and manage the repository.
- **Python 3.8+**: Needed for local development or testing.
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
Create a `.env` file in the project root with the database configuration:
```bash
echo "POSTGRES_PASSWORD=your_secure_password" > .env
echo "DB_PASSWORD=your_secure_password" >> .env
echo "DB_HOST=localhost" >> .env
echo "DB_PORT=5432" >> .env
echo "DB_NAME=timeseries" >> .env
echo "DB_USER=postgres" >> .env
```

- Ensure `POSTGRES_PASSWORD` and `DB_PASSWORD` are identical.
- Use a strong password for production (avoid simple passwords like `344234`).
- `DB_HOST=localhost` is for local testing; Docker uses `timescaledb`.
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

## Testing

The project includes automated tests for the FastAPI endpoints using `pytest`, `httpx`, and `pytest-asyncio`, located in `app/tests/`. Tests verify the `POST /sensor-data/` and `GET /sensor-data/avg-temperature/` endpoints, which are asynchronous.

### Running Tests Locally
1. Ensure the TimescaleDB service is running:
   ```bash
   docker-compose up -d timescaledb
   ```
2. Create and activate a virtual environment:
   ```bash
   cd app
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run tests:
   ```bash
   pytest tests/test_api.py -v
   ```
   Expected output:
   ```
   ============================= test session starts =============================
   collected 2 items

   tests/test_api.py::test_insert_sensor_data PASSED                     [ 50%]
   tests/test_api.py::test_get_avg_temperature PASSED                    [100%]

   ============================== 2 passed in 0.10s ==============================
   ```
5. Deactivate the virtual environment:
   ```bash
   deactivate
   ```

**Notes**:
- The tests load database credentials from the `.env` file in the project root. Ensure `DB_PASSWORD`, `POSTGRES_PASSWORD`, and `DB_HOST=localhost` are set correctly.
- The `pytest-asyncio` plugin is required for async test execution.
- Tests expect timezone-aware UTC datetimes (`timestamptz`) from the database due to TimescaleDB’s handling of the `time` column.
- If tests fail with a 500 error, check:
  - TimescaleDB is running (`docker ps`).
  - `.env` credentials match the database (`DB_PASSWORD` and `POSTGRES_PASSWORD`).
  - The `sensor_data` table exists (`psql -h localhost -p 5432 -U postgres -d timeseries -c "\d sensor_data"`).
  - Logs for errors (`docker logs my-timescaledb`).
  - Run with debug logging for details:
    ```bash
    pytest tests/test_api.py -v --log-cli-level=DEBUG
    ```

## CI/CD

The project uses **GitHub Actions** to automatically run tests on every push or pull request to the `main` branch. The workflow is defined in `.github/workflows/ci.yml` and performs the following:
- Sets up a Python environment and creates a `.env` file with test credentials.
- Starts the `timescaledb` service using Docker Compose.
- Installs dependencies in a virtual environment.
- Runs `pytest` tests against the FastAPI app, connecting to the Dockerized TimescaleDB.
- Cleans up Docker resources after testing.

To view test results:
1. Go to the **Actions** tab on [https://github.com/arslanerdem/time-series-platform](https://github.com/arslanerdem/time-series-platform).
2. Select the latest **CI** workflow run.
3. Check for a green checkmark indicating passing tests or review logs for failures.

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

### Local Development (Optional)
To run `app.py` locally (outside Docker):
```bash
cd app
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
deactivate
```

**Note**: Ensure `.env` has `DB_HOST=localhost` for local runs. The app loads credentials from `.env`.

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
docker volume inspect data_serve_pgdata
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
   echo "DB_HOST=localhost" >> .env
   echo "DB_PORT=5432" >> .env
   echo "DB_NAME=timeseries" >> .env
   echo "DB_USER=postgres" >> .env
   ```
2. Reset the `pgdata` volume:
   ```bash
   docker-compose down
   docker volume rm data_serve_pgdata
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
  - Update `docker-compose.yml` (e.g., `5433:5432`, `8001:8000`) and `DB_PORT` in `.env` if needed.
- **Test Failures**:
  - Ensure TimescaleDB is running and `.env` has correct `DB_PASSWORD` and `DB_HOST=localhost`.
  - Verify virtual environment is activated and dependencies (including `pytest-asyncio`) are installed.
  - Check test logs for errors (e.g., database connection issues).
  - Run `pytest` with `--log-cli-level=DEBUG` for detailed output:
    ```bash
    pytest tests/test_api.py -v --log-cli-level=DEBUG
    ```
- **CI Failures**:
  - Check the **Actions** tab on GitHub for detailed logs.
  - Verify `ci.yml` syntax and `.env` configuration.
  - Ensure TimescaleDB starts correctly in CI (`docker logs my-timescaledb`).
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

MIT License. See `LICENSE` file for details (add a `LICENSE` file if desired).

## Contact

For issues or questions, open an issue on [GitHub](https://github.com/arslanerdem/time-series-platform).