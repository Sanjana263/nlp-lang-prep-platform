from fastapi import FastAPI
from app.writing.router import router as writing_router   

app = FastAPI(title="Cadence API")

app.include_router(writing_router)                         


@app.get("/health")
def health():
    return {"status": "ok"}