from fastapi import APIRouter, HTTPException

from app.repositories.catalog import MACHINES, PARTS
from app.schemas.domain import Machine, Part

router = APIRouter()


@router.get("/machines", response_model=dict[str, object])
async def list_machines() -> dict[str, object]:
    return {"success": True, "data": MACHINES, "meta": {"total": len(MACHINES)}}


@router.get("/machines/{machine_id}", response_model=dict[str, object])
async def machine_detail(machine_id: str) -> dict[str, object]:
    machine: Machine | None = next((item for item in MACHINES if item.id == machine_id), None)
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {"success": True, "data": machine}


@router.get("/parts", response_model=dict[str, object])
async def list_parts() -> dict[str, object]:
    parts: list[Part] = PARTS
    return {"success": True, "data": parts, "meta": {"total": len(parts)}}
