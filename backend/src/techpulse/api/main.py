"""TechPulse API entry point."""

from fastapi import FastAPI

app = FastAPI(title="TechPulse API")


@app.get("/health")
def health() -> dict[str, str]:
    """Return API health status."""
    return {"status": "ok", "system": "TechPulse"}
