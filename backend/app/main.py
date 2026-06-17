from fastapi import FastAPI

from app.routers import triage


app = FastAPI(
    title="SehatSaathi API"
)


app.include_router(
    triage.router
)


@app.get("/")
def root():
    return {
        "message": "API running"
    }