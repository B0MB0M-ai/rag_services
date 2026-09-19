import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse

from app.repositories.catalog import save_service_case
from app.schemas.domain import ChatRequest, ChatResult, EstimateRequest, ServiceCase
from app.services.diagnosis import diagnose, diagnose_stream
from app.services.generation import GenerationError
from app.services.pricing import calculate_estimate

router = APIRouter()


@router.post("/chat", response_model=dict[str, object])
async def chat(request: ChatRequest, background_tasks: BackgroundTasks) -> dict[str, object]:
    try:
        result = await diagnose(request)
    except GenerationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    background_tasks.add_task(save_service_case, _service_case(request, result))
    return {"success": True, "data": result}


@router.post("/chat/stream", response_class=StreamingResponse)
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    completed: dict[str, ServiceCase] = {}

    async def events():
        try:
            async for event in diagnose_stream(request):
                if isinstance(event, ChatResult):
                    completed["case"] = _service_case(request, event)
                    yield _ndjson({"type": "done", "data": event.model_dump(mode="json")})
                else:
                    yield _ndjson({"type": "delta", "text": event})
        except GenerationError as error:
            yield _ndjson({"type": "error", "detail": str(error)})

    def persist_completed_case() -> None:
        if service_case := completed.get("case"):
            save_service_case(service_case)

    return StreamingResponse(
        events(),
        media_type="application/x-ndjson",
        background=BackgroundTask(persist_completed_case),
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _service_case(request: ChatRequest, result: ChatResult) -> ServiceCase:
    return ServiceCase(
        id=str(uuid4()),
        question=request.message,
        answer=result.answer,
        confidence=result.confidence,
        citations=result.citations,
        created_at=datetime.now(UTC),
    )


def _ndjson(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


@router.post("/estimates/calculate", response_model=dict[str, object])
async def estimate(request: EstimateRequest) -> dict[str, object]:
    try:
        result = calculate_estimate(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"success": True, "data": result}
