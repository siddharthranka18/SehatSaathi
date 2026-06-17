from fastapi import APIRouter
from ..models.schemas import TriageRequest, TriageResponse
from ..services.llm_service import run_triage
router = APIRouter()
@router.post("/triage", response_model=TriageResponse)
def triage_endpoint(request: TriageRequest) -> TriageResponse:
    return run_triage(request)