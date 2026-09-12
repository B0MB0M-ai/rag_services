from app.core.config import get_settings
from app.rag.retrieval import retrieve
from app.schemas.domain import ChatRequest, ChatResult, Citation
from app.services.generation import DiagnosisGenerator, get_diagnosis_generator

WARNING = (
    "This is a preliminary assessment. It must be reviewed and confirmed by a "
    "qualified technician before work begins."
)


async def diagnose(request: ChatRequest, generator: DiagnosisGenerator | None = None) -> ChatResult:
    """Retrieve indexed evidence and generate grounded technical guidance."""
    query = " ".join(part for part in (request.message, request.fault_code) if part)
    results = retrieve(query, request.machine_id)
    threshold = get_settings().rag_min_evidence_score
    evidence = [result for result in results if result.score >= threshold]
    if not evidence:
        # An imported manual is still useful context when the lightweight local
        # retriever cannot bridge paraphrases or different languages. Prefer its
        # best-ranked chunks rather than acting as though the knowledge base is empty.
        evidence = [result for result in results if result.document.category == "manual"][:3]
    if evidence:
        # Retrieval already applies the configured context limit. Give generation and
        # citations the same evidence set so the model can reconcile all cited excerpts.
        generated = await (generator or get_diagnosis_generator()).generate(request, evidence)
        return ChatResult(
            answer=generated.answer,
            confidence=generated.confidence,
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
