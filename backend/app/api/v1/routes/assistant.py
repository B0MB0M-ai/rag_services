from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.repositories.catalog import SERVICE_CASES, persist_service_cases
from app.schemas.domain import ChatRequest, EstimateRequest, ServiceCase
from app.services.diagnosis import diagnose
from app.services.generation import GenerationError
from app.services.pricing import calculate_estimate

router = APIRouter()


@router.post("/chat", response_model=dict[str, object])
async def chat(request: ChatRequest) -> dict[str, object]:
    try:
        result = await diagnose(request)
    except GenerationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    SERVICE_CASES.insert(
        0,
        ServiceCase(
            id=str(uuid4()),
            question=request.message,
            answer=result.answer,
            confidence=result.confidence,
            citations=result.citations,
            created_at=datetime.now(UTC),
        ),
    )
    persist_service_cases()
    return {"success": True, "data": result}


@router.post("/estimates/calculate", response_model=dict[str, object])
async def estimate(request: EstimateRequest) -> dict[str, object]:
    try:
        result = calculate_estimate(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"success": True, "data": result}
