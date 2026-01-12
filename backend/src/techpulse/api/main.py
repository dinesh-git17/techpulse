from fastapi import FastAPI

app = FastAPI(title="TechPulse API")

@app.get("/health")
def health():
    return {"status": "ok", "system": "TechPulse"}
