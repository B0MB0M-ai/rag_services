from app.schemas.domain import ChatRequest, ChatResult, Citation

WARNING = (
    "This is a preliminary assessment. It must be reviewed and confirmed by a "
    "qualified technician before work begins."
)


def diagnose(request: ChatRequest) -> ChatResult:
    """Deterministic mock RAG provider for safe, zero-cost demonstrations."""
    normalized = f"{request.message} {request.fault_code or ''}".lower()
    oil_terms = ("oil", "leak", "น้ำมัน", "รั่ว", "e-hyd-04")
    if any(term in normalized for term in oil_terms):
        return ChatResult(
            answer=(
                "Stop the machine and perform lockout/tagout. Then inspect the pressure, "
                "connections, hoses, and hydraulic cylinder seals. Clean the affected area "
                "before locating the leak. Never use your hands to search for a leak while "
                "the system is pressurized."
            ),
            confidence="sufficient",
            citations=[
                Citation(
                    document="HP-500 Maintenance Manual (synthetic data)",
                    section="Hydraulic System §4.2",
                    score=0.91,
                )
            ],
            suggested_part_ids=["p-seal-hp500", "p-filter-h46"],
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
