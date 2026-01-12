# Hacker News API Client

## Purpose

Provide a synchronous client for the Hacker News Firebase API with retry
logic, typed validation, and structured error reporting.

## Module Structure

- `techpulse.source.hn.client` implements the HTTP client.
- `techpulse.source.hn.models` defines Pydantic data models for API payloads.
- `techpulse.source.hn.errors` defines error types for client failures.

## HackerNewsClient

### Responsibilities

- Manage an `httpx.Client` session as a context manager.
- Execute GET requests with retry and backoff for transient failures.
- Translate HTTP responses into typed `HNItem` and `HNUser` models.

### Core Methods and Contracts

#### `get_item(item_id)`

- Input: integer item ID.
- Output: `HNItem` if the API returns data, `None` if the API returns null.
- Validation: Pydantic model validation of response payload.

#### `get_user(username)`

- Input: string username.
- Output: `HNUser` if the API returns data, `None` if the API returns null.
- Validation: Pydantic model validation of response payload.

#### Story List Methods

- `get_top_stories`, `get_new_stories`, `get_best_stories`
- `get_ask_stories`, `get_show_stories`, `get_job_stories`

Each returns a list of integer IDs from the corresponding endpoint.

#### `get_max_item()`

Returns the current maximum item ID as an integer.

### Retry and Rate Limit Behavior

- Retries on `httpx.ConnectError`, `httpx.ReadTimeout`, and
  `httpx.ConnectTimeout` with exponential jitter, up to 5 attempts.
- For HTTP 429, respects the `Retry-After` header if present. Otherwise waits
  60 seconds and retries by raising a timeout to trigger the retry policy.
- For HTTP 5xx, logs and triggers retry by raising a timeout.
- For other non-200 responses, raises `HackerNewsAPIError` immediately.

### Error Handling

- `HackerNewsNetworkError` for network failures outside the retry loop.
- `HackerNewsMaxRetriesError` when all retry attempts are exhausted.
- `HackerNewsAPIError` for non-200 responses not treated as retryable.
- `HackerNewsDataError` for Pydantic validation failures.
- `RuntimeError` if methods are called outside of context manager.

## Data Models

### `HNItem`

Represents a Hacker News item. Key fields include:

- `id`: int
- `type`: `HNItemType` enum
- `by`: optional string
- `time`: UTC datetime converted from Unix timestamp
- `title`, `text`, `url`: optional strings
- `kids`: list of child item IDs
- `parent`, `score`, `descendants`, `poll`, `parts`: optional fields
- `deleted`, `dead`: booleans

### `HNUser`

Represents a Hacker News user profile. Key fields include:

- `id`: username string
- `created`: UTC datetime converted from Unix timestamp
- `karma`: integer
- `about`: optional string
- `submitted`: list of item IDs

### `HNItemType`

Enum of item types: `story`, `comment`, `job`, `poll`, `pollopt`.

## Integration Points

- External dependency: Hacker News Firebase API at
  `https://hacker-news.firebaseio.com/v0`.
- Used by Dagster assets through `HackerNewsClientResource`.
