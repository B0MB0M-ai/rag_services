from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi.testclient import TestClient

from app.main import app
from app.rag.indexing import chunk_text, embed_text
from app.repositories.catalog import DOCUMENT_CHUNKS, DOCUMENT_CONTENT, KNOWLEDGE_DOCUMENTS

client = TestClient(app)


def setup_function() -> None:
    KNOWLEDGE_DOCUMENTS.clear()
    DOCUMENT_CONTENT.clear()
    DOCUMENT_CHUNKS.clear()


def _docx(text: str) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="urn:test"><w:body><w:p><w:r>'
            f"<w:t>{text}</w:t></w:r></w:p></w:body></w:document>",
        )
    return output.getvalue()


def test_chunking_is_deterministic_and_overlaps() -> None:
    chunks = chunk_text("one two three four five six", size=15, overlap=4)
    assert chunks == chunk_text("one two three four five six", size=15, overlap=4)
    assert len(chunks) > 1
    assert embed_text("hydraulic leak") == embed_text("hydraulic leak")


def test_docx_is_extracted_indexed_and_retrieved_with_source() -> None:
    response = client.post(
        "/api/v1/documents",
        data={"category": "manual"},
        files={
            "file": (
                "pump.docx",
                _docx("E-PUMP-9 cavitation requires checking the suction filter"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    document = response.json()["data"]
    assert document["status"] == "indexed"
    assert document["chunk_count"] == 1

    answer = client.post(
        "/api/v1/chat", json={"message": "cavitation suction filter", "fault_code": "E-PUMP-9"}
    ).json()["data"]
    assert answer["confidence"] == "sufficient"
    assert answer["citations"][0]["document"] == "pump.docx"
    assert answer["suggested_part_ids"] == []


def test_invalid_docx_has_observable_failed_state_and_can_be_reindexed() -> None:
    response = client.post(
        "/api/v1/documents",
        data={"category": "manual"},
        files={
            "file": (
                "broken.docx",
                b"not a zip",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    document = response.json()["data"]
    assert document["status"] == "failed"
    assert "Unable to extract" in document["indexing_error"]
    assert document["id"] not in DOCUMENT_CHUNKS

    reindexed = client.post(f"/api/v1/documents/{document['id']}/index")
    assert reindexed.status_code == 200
    assert reindexed.json()["data"]["status"] == "failed"
    assert client.post("/api/v1/documents/missing/index").status_code == 404
