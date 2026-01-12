# TechPulse

A full-stack monorepo for data-driven applications.

## Quick Start

```bash
# Install all dependencies
make setup

# Start all services
make dev
```

## Services

| Service | URL | Description |
| :--- | :--- | :--- |
| **FastAPI** | `http://localhost:8000/docs` | REST API |
| **Dagster** | `http://localhost:3000` | Data Orchestration |
| **Next.js** | `http://localhost:3001` | Web UI |

## Commands

* `make setup` - Install all dependencies
* `make dev` - Start all services
* `make api` - Start FastAPI only
* `make dagster` - Start Dagster only
* `make ui` - Start Next.js only
* `make lint` - Run linters
* `make clean` - Remove generated files
