from collections.abc import AsyncIterator

from app.core.config import get_settings
from app.rag.retrieval import RetrievalResult, retrieve
from app.schemas.domain import ChatRequest, ChatResult, Citation, GeneratedDiagnosis
from app.services.generation import DiagnosisGenerator, get_diagnosis_generator

WARNING = (
    "This is a preliminary assessment. It must be reviewed and confirmed by a "
    "qualified technician before work begins."
)


async def diagnose(request: ChatRequest, generator: DiagnosisGenerator | None = None) -> ChatResult:
    """Retrieve indexed evidence and generate grounded technical guidance."""
    evidence = _retrieve_evidence(request)
    if evidence:
        # Retrieval already applies the configured context limit. Give generation and
        # citations the same evidence set so the model can reconcile all cited excerpts.
        generated = await (generator or get_diagnosis_generator()).generate(request, evidence)
        return _chat_result(generated, evidence)
    return _insufficient_result()


async def diagnose_stream(
    request: ChatRequest, generator: DiagnosisGenerator | None = None
) -> AsyncIterator[str | ChatResult]:
    """Stream answer text followed by the authoritative, structured result."""
    evidence = _retrieve_evidence(request)
    if not evidence:
        result = _insufficient_result()
        yield result.answer
        yield result
        return

    resolved_generator = generator or get_diagnosis_generator()
    async for event in resolved_generator.stream(request, evidence):
        if isinstance(event, GeneratedDiagnosis):
            yield _chat_result(event, evidence)
        else:
            yield event


def _retrieve_evidence(request: ChatRequest) -> list[RetrievalResult]:
    query = " ".join(part for part in (request.message, request.fault_code) if part)
    results = retrieve(query, request.machine_id)
    threshold = get_settings().rag_min_evidence_score
    evidence = [result for result in results if result.score >= threshold]
    if not evidence:
        # An imported manual is still useful context when the lightweight local
        # retriever cannot bridge paraphrases or different languages. Prefer its
        # best-ranked chunks rather than acting as though the knowledge base is empty.
        evidence = [result for result in results if result.document.category == "manual"][:3]
    return evidence


def _chat_result(generated: GeneratedDiagnosis, evidence: list[RetrievalResult]) -> ChatResult:
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


def _insufficient_result() -> ChatResult:
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
