import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import Settings
from app.schemas.domain import ChatRequest, DocumentChunk, GeneratedDiagnosis, KnowledgeDocument
from app.services.generation import GenerationError, OpenAIDiagnosisGenerator


def _evidence() -> SimpleNamespace:
    document = KnowledgeDocument(
        id="doc-1",
        filename="pump.pdf",
        category="manual",
        product_name="Hydraulic Pump",
        size_bytes=100,
        content_type="application/pdf",
        status="indexed",
        chunk_count=1,
        uploaded_at="2026-01-01T00:00:00Z",
    )
    chunk = DocumentChunk(
        id="chunk-1",
        document_id=document.id,
        content="Inspect the suction filter when cavitation is present.",
        section="Troubleshooting",
        page=4,
        ordinal=0,
        embedding=[1.0],
    )
    return SimpleNamespace(chunk=chunk, document=document)


def test_openai_generator_sends_retrieved_evidence_for_structured_generation() -> None:
    parsed = GeneratedDiagnosis(
        answer="ตรวจสอบไส้กรองทางดูดก่อน แล้วให้ช่างยืนยันผล", confidence="sufficient"
    )
    parse = AsyncMock(return_value=SimpleNamespace(output_parsed=parsed))
    client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    settings = Settings(
        mock_ai=False, openai_api_key="test-key", openai_response_model="gpt-5-mini"
    )
    generator = OpenAIDiagnosisGenerator(settings, client=client)

    result = asyncio.run(
        generator.generate(
            ChatRequest(message="ปั๊มมีเสียง cavitation", fault_code="E-PUMP-9"), [_evidence()]
        )
    )

    assert result == parsed
    request = parse.await_args.kwargs
    assert request["model"] == "gpt-5-mini"
    assert request["text_format"] is GeneratedDiagnosis
    assert "pump.pdf" in request["input"]
    assert "Inspect the suction filter" in request["input"]
    assert "E-PUMP-9" in request["input"]
    assert "prices" in request["instructions"]
    assert "test-key" not in str(request)


def test_openai_generator_requires_server_side_api_key() -> None:
    with pytest.raises(GenerationError, match="OPENAI_API_KEY"):
        OpenAIDiagnosisGenerator(Settings(mock_ai=False, openai_api_key=None))
