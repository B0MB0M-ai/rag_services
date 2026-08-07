from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.catalog import PARTS
from app.schemas.domain import EstimateItem, EstimateRequest, Part
from app.services.pricing import calculate_estimate

client = TestClient(app)


@pytest.fixture
def priced_filter() -> None:
    PARTS.append(
        Part(
            id="p-filter-h46",
            sku="FILTER-H46",
            name_th="ไส้กรองทดสอบ",
            name_en="Test filter",
            unit_price_satang=125000,
        )
    )
    yield
    PARTS.clear()


def test_pricing_covers_quantities_decimal_hours_discount_vat_and_rounding(
    priced_filter: None,
) -> None:
    result = calculate_estimate(
        EstimateRequest(
            items=[EstimateItem(part_id="p-filter-h46", quantity=2)],
            labor_hours=Decimal("1.25"),
            labor_rate_satang=80001,
            travel_fee_satang=0,
            service_fee_satang=999,
            discount_percent=Decimal("10"),
            vat_percent=Decimal("7"),
        )
    )

    assert result.parts_subtotal_satang == 250000
    assert result.labor_satang == 100001
    assert result.subtotal_satang == 351000
    assert result.discount_satang == 35100
    assert result.vat_satang == 22113
    assert result.grand_total_satang == 338013


def test_unknown_part_is_rejected_instead_of_accepting_model_price() -> None:
    request = EstimateRequest(
        items=[EstimateItem(part_id="invented", quantity=1)],
        labor_hours=Decimal("0"),
        labor_rate_satang=0,
    )
    with pytest.raises(ValueError, match="Unknown part"):
        calculate_estimate(request)


def test_chat_returns_citation_and_mandatory_warning() -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "HP-500 น้ำมันรั่ว", "fault_code": "E-HYD-04"},
    )
    data = response.json()["data"]
    assert response.status_code == 200
    assert data["confidence"] == "sufficient"
    assert data["citations"][0]["score"] == 0.91
    assert "เบื้องต้น" in data["warning"]


def test_chat_escalates_when_evidence_is_insufficient() -> None:
    response = client.post("/api/v1/chat", json={"message": "อาการที่ไม่เคยพบ xyz"})
    data = response.json()["data"]
    assert data["confidence"] == "insufficient"
    assert data["citations"] == []
    assert data["suggested_part_ids"] == []


def test_catalog_and_assistant_page_are_available() -> None:
    assert client.get("/api/v1/machines").json()["meta"]["total"] == 0
    assert client.get("/api/v1/parts").json()["meta"]["total"] == 0
    page = client.get("/assistant")
    assert page.status_code == 200
    assert "ยังไม่สามารถเริ่มวิเคราะห์ได้" in page.text
    assert "HP-500" not in page.text
