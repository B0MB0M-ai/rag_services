from fastapi.testclient import TestClient

from app.main import app
from app.repositories.catalog import (
    DOCUMENT_CHUNKS,
    DOCUMENT_CONTENT,
    KNOWLEDGE_DOCUMENTS,
    SERVICE_CASES,
    load_persistent_state,
    persist_documents,
    persist_service_cases,
)

client = TestClient(app)


def _clear_persistent_state() -> None:
    KNOWLEDGE_DOCUMENTS.clear()
    DOCUMENT_CONTENT.clear()
    DOCUMENT_CHUNKS.clear()
    SERVICE_CASES.clear()
    persist_documents()
    persist_service_cases()


def test_uploaded_rag_data_and_service_conversation_survive_process_restart() -> None:
    _clear_persistent_state()
    upload = client.post(
        "/data/upload",
        data={"product_name": "Persistent Pump"},
        files={
            "product_image": ("pump.png", b"persistent image", "image/png"),
            "manual": (
                "pump.txt",
                b"Persistent Pump: stop and inspect the shaft seal when oil leaks.",
                "text/plain",
            ),
        },
    )
    assert upload.status_code == 200

    chat = client.post("/api/v1/chat", json={"message": "How do I check an oil leak?"})
    assert chat.status_code == 200
    expected_answer = chat.json()["data"]["answer"]
    document_ids = {document.id for document in KNOWLEDGE_DOCUMENTS}

    KNOWLEDGE_DOCUMENTS.clear()
    DOCUMENT_CONTENT.clear()
    DOCUMENT_CHUNKS.clear()
    SERVICE_CASES.clear()
    load_persistent_state()

    assert {document.id for document in KNOWLEDGE_DOCUMENTS} == document_ids
    assert all(document_id in DOCUMENT_CONTENT for document_id in document_ids)
    assert all(document_id in DOCUMENT_CHUNKS for document_id in document_ids)
    assert len(SERVICE_CASES) == 1
    assert SERVICE_CASES[0].question == "How do I check an oil leak?"
    assert SERVICE_CASES[0].answer == expected_answer

    data_page = client.get("/data")
    assert "Persistent Pump" in data_page.text
    cases_page = client.get("/cases")
    assert "Questions and answers" in cases_page.text
    assert "How do I check an oil leak?" in cases_page.text
    assert expected_answer in cases_page.text

    _clear_persistent_state()
