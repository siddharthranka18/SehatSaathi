from fastapi import FastAPI

from app.routers import triage


app = FastAPI(
    title="SehatSaathi API"
)

app.include_router(triage.router, prefix="/api")


@app.get("/")
def root():

    return {
        "message": "SehatSaathi API running"
    }