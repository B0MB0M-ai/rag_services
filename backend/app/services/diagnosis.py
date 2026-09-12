from app.core.config import get_settings
from app.rag.retrieval import retrieve
from app.schemas.domain import ChatRequest, ChatResult, Citation

WARNING = (
    "This is a preliminary assessment. It must be reviewed and confirmed by a "
    "qualified technician before work begins."
)


def diagnose(request: ChatRequest) -> ChatResult:
    """Retrieve indexed evidence and produce a deterministic, grounded response."""
    query = " ".join(part for part in (request.message, request.fault_code) if part)
    results = retrieve(query, request.machine_id)
    threshold = get_settings().rag_min_evidence_score
    evidence = [result for result in results if result.score >= threshold]
    if evidence:
        excerpts = [result.chunk.content for result in evidence[:3]]
        return ChatResult(
            answer="Based on the imported service documentation:\n\n" + "\n\n".join(excerpts),
            confidence="sufficient",
            citations=[
                Citation(
                    document=result.document.filename,
                    section=result.chunk.section,
                    page=result.chunk.page,
                    score=round(result.score, 4),
                )
                for result in evidence
            ],
            suggested_part_ids=[],
            warning=WARNING,
        )
    return ChatResult(
        answer=(
            "The knowledge base does not contain enough evidence to recommend a procedure "
            "or parts. Record additional symptoms and escalate the case to a qualified "
            "technician."
        ),
        confidence="insufficient",
        citations=[],
        suggested_part_ids=[],
        warning=WARNING,
    )
