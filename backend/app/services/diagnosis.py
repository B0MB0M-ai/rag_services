import asyncio
import logging
from collections.abc import AsyncIterator

from app.core.config import get_settings
from app.rag.retrieval import RetrievalResult, retrieve
from app.schemas.domain import ChatRequest, ChatResult, Citation, GeneratedDiagnosis
from app.services.generation import DiagnosisGenerator, get_diagnosis_generator

WARNING = (
    "This is a preliminary assessment. It must be reviewed and confirmed by a "
    "qualified technician before work begins."
)

logger = logging.getLogger(__name__)


async def diagnose(request: ChatRequest, generator: DiagnosisGenerator | None = None) -> ChatResult:
    """Retrieve indexed evidence and generate grounded technical guidance."""
    evidence: list[RetrievalResult] = []
    timeout = get_settings().assistant_response_timeout_seconds
    try:
        async with asyncio.timeout(timeout):
            evidence = await asyncio.to_thread(_retrieve_evidence, request)
            if evidence:
                # Retrieval already applies the configured context limit. Give generation and
                # citations the same evidence set so the model can reconcile all cited excerpts.
                generated = await (generator or get_diagnosis_generator()).generate(
                    request, evidence
                )
                return _chat_result(generated, evidence)
            return _insufficient_result()
    except TimeoutError:
        logger.warning("Service Assistant exceeded its %.1f-second response budget", timeout)
        return _timeout_result(request, evidence)


async def diagnose_stream(
    request: ChatRequest, generator: DiagnosisGenerator | None = None
) -> AsyncIterator[str | ChatResult]:
    """Stream answer text followed by the authoritative, structured result."""
    evidence: list[RetrievalResult] = []
    timeout = get_settings().assistant_response_timeout_seconds
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    try:
        evidence = await asyncio.wait_for(asyncio.to_thread(_retrieve_evidence, request), timeout)
        if not evidence:
            result = _insufficient_result()
            yield result.answer
            yield result
            return

        events = (generator or get_diagnosis_generator()).stream(request, evidence)
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TimeoutError
            try:
                event = await asyncio.wait_for(anext(events), remaining)
            except StopAsyncIteration:
                break
            if isinstance(event, GeneratedDiagnosis):
                yield _chat_result(event, evidence)
            else:
                yield event
    except TimeoutError:
        logger.warning("Service Assistant stream exceeded its %.1f-second response budget", timeout)
        # The final event replaces any partial text already rendered by the browser.
        yield _timeout_result(request, evidence)


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


def _timeout_result(request: ChatRequest, evidence: list[RetrievalResult]) -> ChatResult:
    is_thai = any("\u0e00" <= character <= "\u0e7f" for character in request.message)
    answer = (
        "ระบบหยุดการวิเคราะห์อัตโนมัติเมื่อครบเวลาที่กำหนดเพื่อไม่ให้คุณต้องรอนาน "
        "จึงยังไม่สามารถยืนยันสาเหตุหรือขั้นตอนซ่อมได้ โปรดหยุดเครื่องหากมีความเสี่ยง "
        "และให้ช่างผู้มีคุณสมบัติตรวจสอบ ระบุรุ่นเครื่อง รหัสข้อผิดพลาด และอาการล่าสุด "
        "แล้วลองส่งคำถามอีกครั้ง"
        if is_thai
        else "The automated analysis reached its response deadline, so no cause or repair "
        "procedure can be confirmed yet. Stop the machine if there is a safety risk and have "
        "a qualified technician inspect it. Add the machine model, fault code, and latest "
        "symptoms, then try again."
    )
    return _chat_result(
        GeneratedDiagnosis(answer=answer, confidence="insufficient"),
        evidence,
    )
