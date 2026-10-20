from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.writing.router import router as writing_router

app = FastAPI(title="Cadence API")

app.include_router(writing_router)


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok"}