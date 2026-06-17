from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.triage import router as triage_router
# from app.routers.voice import router as voice_router  # stage 4
app = FastAPI(title="SehatSaathi API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(triage_router, prefix="/api")
# app.include_router(voice_router, prefix="/api")  # stage 4
@app.get("/health")
def health():
    return {"status": "ok"}