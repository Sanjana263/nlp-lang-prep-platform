from fastapi import FastAPI

app = FastAPI(title="Cadence API")


@app.get("/health")
def health():
    return {"status": "ok"}