from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class Machine(BaseModel):
    id: str
    model: str
    serial_number: str
    location: str
    status: Literal["operational", "maintenance", "offline"]


class Part(BaseModel):
    id: str
    sku: str
    name_th: str
    name_en: str
    unit_price_satang: int = Field(ge=0)
    currency: str = "THB"


class EstimateItem(BaseModel):
    part_id: str
    quantity: int = Field(ge=1)


class EstimateRequest(BaseModel):
    items: list[EstimateItem]
    labor_hours: Decimal = Field(ge=0)
    labor_rate_satang: int = Field(ge=0)
    service_fee_satang: int = Field(default=0, ge=0)
    travel_fee_satang: int = Field(default=0, ge=0)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    vat_percent: Decimal = Field(default=Decimal("7"), ge=0)


class EstimateLine(BaseModel):
    sku: str
    description: str
    quantity: int
    unit_price_satang: int
    total_satang: int


class EstimateResult(BaseModel):
    lines: list[EstimateLine]
    parts_subtotal_satang: int
    labor_satang: int
    fees_satang: int
    subtotal_satang: int
    discount_satang: int
    vat_satang: int
    grand_total_satang: int
    currency: str = "THB"
    preliminary: bool = True


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    machine_id: str | None = None
    fault_code: str | None = None


class Citation(BaseModel):
    document: str
    section: str
    score: float


class ChatResult(BaseModel):
    answer: str
    confidence: Literal["sufficient", "insufficient"]
    citations: list[Citation]
    suggested_part_ids: list[str]
    warning: str
