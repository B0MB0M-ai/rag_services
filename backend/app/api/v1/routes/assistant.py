from fastapi import APIRouter, HTTPException

from app.schemas.domain import ChatRequest, EstimateRequest
from app.services.diagnosis import diagnose
from app.services.pricing import calculate_estimate

router = APIRouter()


@router.post("/chat", response_model=dict[str, object])
async def chat(request: ChatRequest) -> dict[str, object]:
    return {"success": True, "data": diagnose(request)}


@router.post("/estimates/calculate", response_model=dict[str, object])
async def estimate(request: EstimateRequest) -> dict[str, object]:
    try:
        result = calculate_estimate(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"success": True, "data": result}
