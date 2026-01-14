# Getting Started

## Purpose

This document enables a developer to set up and run TechPulse locally from a clean machine. After completing these steps, you will have:

- A working DuckDB database with seed data
- A running FastAPI backend serving trend data
- A running Next.js frontend dashboard

## Prerequisites

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| Python | 3.12+ | https://www.python.org/downloads/ |
| uv | Latest | https://docs.astral.sh/uv/getting-started/installation/ |
| Node.js | 20+ | https://nodejs.org/ |
| pnpm | 9+ | `npm install -g pnpm` |
| Git | Latest | https://git-scm.com/ |

### Verify Prerequisites

```bash
python3 --version   # Should show 3.12.x or higher
uv --version        # Should show version output
node --version      # Should show v20.x or higher
pnpm --version      # Should show 9.x or higher
```

## Repository Setup

### Clone the Repository

```bash
git clone <repository-url>
cd techpulse
```

### Install Dependencies

Run the setup target to install all Python and Node.js dependencies:

```bash
make setup
```

This command performs three operations:

1. Installs Python dependencies via `uv sync`
2. Installs frontend dependencies via `pnpm install`
3. Configures pre-commit hooks for code quality enforcement

## Backend Initialization

The API requires a populated DuckDB database. The database uses a medallion architecture with Bronze, Silver, and Gold layers. For local development, you must initialize the Gold layer tables that the API queries.

### Initialize the Database with dbt

Navigate to the dbt project directory and run seed and transformations:

```bash
cd backend/dbt_project
uv run dbt seed
uv run dbt run
```

The `dbt seed` command loads `tech_taxonomy.csv` into the `dim_technologies` table. The `dbt run` command creates the remaining tables including `mart_monthly_trends`.

### Verify Database Initialization

Confirm the database file exists and contains the expected tables:

```bash
uv run python -c "
import duckdb
conn = duckdb.connect('../data/techpulse.duckdb', read_only=True)
tables = conn.execute('SHOW TABLES').fetchall()
print('Tables:', [t[0] for t in tables])
conn.close()
"
```

Expected output should include: `dim_technologies`, `mart_monthly_trends`, and related tables.

Return to the project root:

```bash
cd ../..
```

## Running the API

### Start the FastAPI Server

```bash
make api
```

The API starts on `http://localhost:8000` with auto-reload enabled for development.

### Verify API Health

In a separate terminal, check the health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","system":"TechPulse","db_connected":true,"cache_connected":false}
```

The `cache_connected: false` is expected when Redis is not configured.

### Verify Core Endpoints

Fetch available technologies:

```bash
curl http://localhost:8000/api/v1/technologies
```

This should return a JSON response containing the technology list from `dim_technologies`.

## Running the Frontend

In a separate terminal:

```bash
make ui
```

The frontend starts on `http://localhost:3001`. Open this URL in a browser to access the dashboard.

## Running All Services

To start all services simultaneously (Dagster, API, and Frontend):

```bash
make dev
```

Services will be available at:

| Service | URL |
|---------|-----|
| Dagster UI | http://localhost:3000 |
| FastAPI | http://localhost:8000 |
| Next.js | http://localhost:3001 |

## Validation Checklist

Confirm the following before proceeding:

- [ ] `make setup` completes without errors
- [ ] `dbt seed` and `dbt run` complete successfully
- [ ] `/health` endpoint returns `db_connected: true`
- [ ] `/api/v1/technologies` returns technology data
- [ ] Frontend loads at `http://localhost:3001`

## Environment Variables

The following environment variables are available for configuration. All use the `TECHPULSE_` prefix.

| Variable | Default | Description |
|----------|---------|-------------|
| `TECHPULSE_DB_PATH` | `data/techpulse.duckdb` | Path to DuckDB database |
| `TECHPULSE_API_HOST` | `0.0.0.0` | API bind address |
| `TECHPULSE_API_PORT` | `8000` | API port |
| `TECHPULSE_LOG_LEVEL` | `INFO` | Log verbosity |
| `TECHPULSE_CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
| `UPSTASH_REDIS_URL` | None | Redis URL for caching (optional) |

## Ingesting Live Data

The database initialized via dbt contains the technology taxonomy but no trend data. To populate trend data from Hacker News:

1. Start Dagster: `make dagster`
2. Open http://localhost:3000
3. Navigate to Assets and materialize `who_is_hiring_thread_id` and `raw_hn_items`
4. Re-run dbt transformations: `cd backend/dbt_project && uv run dbt run`

This process fetches job postings from Hacker News "Who is Hiring" threads and transforms them into trend analytics.

## Next Steps

- [Backend API Documentation](backend/api.md)
- [dbt Project Documentation](backend/dbt_project.md)
- [Orchestration with Dagster](backend/orchestration.md)
- [Backend Architecture Overview](backend/overview.md)
