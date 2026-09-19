import asyncio
import time
from types import SimpleNamespace

import app.services.diagnosis as diagnosis
from app.schemas.domain import ChatRequest, GeneratedDiagnosis


class SlowGenerator:
    async def generate(self, request, evidence):
        del request, evidence
        await asyncio.sleep(1)
        return GeneratedDiagnosis(answer="too late", confidence="sufficient")

    def stream(self, request, evidence):
        del request, evidence

        async def events():
            await asyncio.sleep(1)
            yield "too late"
            yield GeneratedDiagnosis(answer="too late", confidence="sufficient")

        return events()


def _evidence():
    return SimpleNamespace(
        document=SimpleNamespace(filename="manual.pdf"),
        chunk=SimpleNamespace(section="Safety", page=1),
        score=0.8,
    )


def _set_tiny_budget(monkeypatch, evidence) -> None:
    monkeypatch.setattr(
        diagnosis,
        "get_settings",
        lambda: SimpleNamespace(assistant_response_timeout_seconds=0.01),
    )
    monkeypatch.setattr(diagnosis, "_retrieve_evidence", lambda request: evidence)


def test_chat_returns_safe_fallback_when_generation_exceeds_budget(monkeypatch) -> None:
    _set_tiny_budget(monkeypatch, [_evidence()])

    started = time.monotonic()
    result = asyncio.run(
        diagnosis.diagnose(ChatRequest(message="เครื่องมีเสียงผิดปกติ"), SlowGenerator())
    )
    elapsed = time.monotonic() - started

    assert elapsed < 0.25
    assert result.confidence == "insufficient"
    assert "ครบเวลาที่กำหนด" in result.answer
    assert "too late" not in result.answer


def test_stream_finishes_with_fallback_when_generation_exceeds_budget(monkeypatch) -> None:
    _set_tiny_budget(monkeypatch, [_evidence()])

    async def collect():
        return [
            event
            async for event in diagnosis.diagnose_stream(
                ChatRequest(message="abnormal vibration"), SlowGenerator()
            )
        ]

    started = time.monotonic()
    events = asyncio.run(collect())
    elapsed = time.monotonic() - started

    assert elapsed < 0.25
    assert len(events) == 1
    assert events[0].confidence == "insufficient"
    assert "response deadline" in events[0].answer
