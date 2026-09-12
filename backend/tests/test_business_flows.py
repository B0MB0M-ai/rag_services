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
    from app.repositories.catalog import DOCUMENT_CHUNKS, DOCUMENT_CONTENT, KNOWLEDGE_DOCUMENTS

    KNOWLEDGE_DOCUMENTS.clear()
    DOCUMENT_CONTENT.clear()
    DOCUMENT_CHUNKS.clear()
    upload = client.post(
        "/api/v1/documents",
        data={"category": "manual"},
        files={
            "file": (
                "hp-500.txt",
                b"HP-500 oil leak E-HYD-04: stop the machine and inspect hydraulic hoses.",
                "text/plain",
            )
        },
    )
    assert upload.json()["data"]["status"] == "indexed"
    response = client.post(
        "/api/v1/chat",
        json={"message": "HP-500 น้ำมันรั่ว", "fault_code": "E-HYD-04"},
    )
    data = response.json()["data"]
    assert response.status_code == 200
    assert data["confidence"] == "sufficient"
    assert data["citations"][0]["document"] == "hp-500.txt"
    assert data["citations"][0]["score"] >= 0.35
    assert "inspect hydraulic hoses" in data["answer"]
    assert "preliminary assessment" in data["warning"]


def test_chat_escalates_when_evidence_is_insufficient() -> None:
    from app.repositories.catalog import DOCUMENT_CHUNKS, DOCUMENT_CONTENT, KNOWLEDGE_DOCUMENTS

    KNOWLEDGE_DOCUMENTS.clear()
    DOCUMENT_CONTENT.clear()
    DOCUMENT_CHUNKS.clear()
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
    assert "Analysis is not available yet" in page.text
    assert "How can we get your" in page.text
    assert "Hydraulic oil leak" in page.text
    assert ':placeholder="typingPlaceholder"' in page.text
    assert "animatePlaceholder" in page.text
    assert "prefers-reduced-motion: reduce" in page.text
    assert "language: 'en'" in page.text
    assert "Use English" in page.text
    assert "ใช้ภาษาไทย" in page.text
    assert "เราจะช่วยให้เครื่องจักรของคุณ" in page.text
    assert "setLanguage('th')" in page.text
    assert 'action="/api/v1/chat"' not in page.text
    assert "fetch('/api/v1/chat'" in page.text
    assert "HP-500" not in page.text


def test_data_upload_page_and_document_api() -> None:
    from app.repositories.catalog import DOCUMENT_CONTENT, KNOWLEDGE_DOCUMENTS

    KNOWLEDGE_DOCUMENTS.clear()
    DOCUMENT_CONTENT.clear()
    page = client.get("/data")
    assert page.status_code == 200
    assert "Import Data for RAG" in page.text
    assert "Product name" in page.text
    assert "Product image" in page.text
    assert "PDF, DOCX, or TXT" in page.text

    response = client.post(
        "/api/v1/documents",
        data={"category": "manual"},
        files={"file": ("safety.pdf", b"sample manual", "application/pdf")},
    )
    assert response.status_code == 201
    document = response.json()["data"]
    assert document["filename"] == "safety.pdf"
    assert document["status"] == "indexed"
    assert document["chunk_count"] == 1
    assert DOCUMENT_CONTENT[document["id"]] == b"sample manual"
    assert client.get("/api/v1/documents").json()["meta"]["total"] == 1


def test_navigation_contains_only_requested_destinations() -> None:
    page = client.get("/")

    assert page.status_code == 200
    assert page.text.count('class="nav-item ') == 4
    assert "Overview" in page.text
    assert "Service Assistant" in page.text
    assert "Import Data" in page.text
    assert "Case Information" in page.text
    assert ">Estimates<" not in page.text
    assert ">Machinery<" not in page.text
    assert ">Knowledge &amp; API<" not in page.text
    assert ">Parts &amp; Pricing<" not in page.text
    assert "navigationCollapsed" in page.text


def test_case_information_page_marks_navigation_item_active() -> None:
    page = client.get("/cases")

    assert page.status_code == 200
    assert "Case Information" in page.text
    assert 'nav-item nav-item--active" href="/cases"' in page.text


def test_product_upload_stores_image_and_manual_for_rag() -> None:
    from app.repositories.catalog import DOCUMENT_CONTENT, KNOWLEDGE_DOCUMENTS

    KNOWLEDGE_DOCUMENTS.clear()
    DOCUMENT_CONTENT.clear()
    response = client.post(
        "/data/upload",
        data={"product_name": "Hydraulic Pump HP-500"},
        files={
            "product_image": ("hp-500.png", b"product image", "image/png"),
            "manual": ("hp-500.pdf", b"product manual", "application/pdf"),
        },
    )

    assert response.status_code == 200
    assert "Hydraulic Pump HP-500 added successfully" in response.text
    assert [document.category for document in KNOWLEDGE_DOCUMENTS] == [
        "manual",
        "product_image",
    ]
    assert all(document.product_name == "Hydraulic Pump HP-500" for document in KNOWLEDGE_DOCUMENTS)


def test_product_upload_does_not_keep_incomplete_product_data() -> None:
    from app.repositories.catalog import DOCUMENT_CONTENT, KNOWLEDGE_DOCUMENTS

    KNOWLEDGE_DOCUMENTS.clear()
    DOCUMENT_CONTENT.clear()
    response = client.post(
        "/data/upload",
        data={"product_name": "Incomplete product"},
        files={
            "product_image": ("product.png", b"product image", "image/png"),
            "manual": ("manual.exe", b"invalid manual", "application/octet-stream"),
        },
    )

    assert response.status_code == 200
    assert "Upload failed" in response.text
    assert KNOWLEDGE_DOCUMENTS == []
    assert DOCUMENT_CONTENT == {}


def test_document_upload_rejects_wrong_type_and_empty_files() -> None:
    wrong_type = client.post(
        "/api/v1/documents",
        data={"category": "manual"},
        files={"file": ("manual.exe", b"unsafe", "application/octet-stream")},
    )
    assert wrong_type.status_code == 422
    assert "Unsupported file type" in wrong_type.json()["detail"]

    empty = client.post(
        "/api/v1/documents",
        data={"category": "machine"},
        files={"file": ("machines.csv", b"", "text/csv")},
    )
    assert empty.status_code == 422
    assert "file is empty" in empty.json()["detail"]
