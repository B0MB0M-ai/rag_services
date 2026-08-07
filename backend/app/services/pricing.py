from decimal import ROUND_HALF_UP, Decimal

from app.repositories.catalog import get_part
from app.schemas.domain import EstimateLine, EstimateRequest, EstimateResult


def _round_satang(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate_estimate(request: EstimateRequest) -> EstimateResult:
    """Calculate all commercial values deterministically from catalog prices."""
    lines: list[EstimateLine] = []
    for item in request.items:
        part = get_part(item.part_id)
        if part is None:
            raise ValueError(f"Unknown part: {item.part_id}")
        total = part.unit_price_satang * item.quantity
        lines.append(
            EstimateLine(
                sku=part.sku,
                description=part.name_th,
                quantity=item.quantity,
                unit_price_satang=part.unit_price_satang,
                total_satang=total,
            )
        )

    parts = sum(line.total_satang for line in lines)
    labor = _round_satang(request.labor_hours * Decimal(request.labor_rate_satang))
    fees = request.service_fee_satang + request.travel_fee_satang
    subtotal = parts + labor + fees
    discount = _round_satang(Decimal(subtotal) * request.discount_percent / Decimal(100))
    taxable = subtotal - discount
    vat = _round_satang(Decimal(taxable) * request.vat_percent / Decimal(100))
    return EstimateResult(
        lines=lines,
        parts_subtotal_satang=parts,
        labor_satang=labor,
        fees_satang=fees,
        subtotal_satang=subtotal,
        discount_satang=discount,
        vat_satang=vat,
        grand_total_satang=taxable + vat,
    )
