.PHONY: setup dev api dagster ui lint clean

setup:
	@echo "Installing Python dependencies with uv..."
	uv sync
	@echo "Installing Frontend dependencies..."
	cd frontend && pnpm install

dev:
	@echo "Starting Full Stack (use Ctrl+C to stop)..."
	# Using subshells (&) to run in parallel
	(uv run dagster dev -f backend/src/techpulse/data/definitions.py -p 3000 &)
	(uv run uvicorn techpulse.api.main:app --app-dir backend/src --reload --port 8000 &)
	(cd frontend && pnpm dev --port 3001 &)
	@echo "Services starting..."
	@echo "  Dagster UI: http://localhost:3000"
	@echo "  FastAPI:    http://localhost:8000/docs"
	@echo "  Next.js:    http://localhost:3001"
	wait

api:
	uv run uvicorn techpulse.api.main:app --app-dir backend/src --reload --port 8000

dagster:
	uv run dagster dev -f backend/src/techpulse/data/definitions.py -p 3000

ui:
	cd frontend && pnpm dev --port 3001

lint:
	uv run ruff check .
	cd frontend && pnpm lint

clean:
	rm -rf .venv
	rm -rf frontend/node_modules
	rm -rf backend/dbt_project/*.duckdb
