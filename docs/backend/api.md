# API

## Purpose

Provide a minimal FastAPI application with a health check endpoint.

## Module Structure

- `techpulse.api.main` defines the FastAPI application instance and routes.

## Key Components

### `app`

`FastAPI` application configured with the title "TechPulse API".

### `health()`

`GET /health` endpoint that returns a static health payload.

## Data Contracts

### `GET /health`

- Response: `{"status": "ok", "system": "TechPulse"}`
- Status code: 200

## Control Flow

The endpoint returns a literal dictionary. There are no dependencies or
side effects.

## Error Handling

No explicit error handling. Failures would come from framework-level issues
outside this module.

## Integration Points

None. The API surface does not call into ingestion or storage modules.
