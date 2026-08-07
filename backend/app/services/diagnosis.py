from app.schemas.domain import ChatRequest, ChatResult, Citation

WARNING = "การประเมินนี้เป็นข้อมูลเบื้องต้น ต้องตรวจสอบและยืนยันโดยช่างผู้มีคุณสมบัติก่อนดำเนินงาน"


def diagnose(request: ChatRequest) -> ChatResult:
    """Deterministic mock RAG provider for safe, zero-cost demonstrations."""
    normalized = f"{request.message} {request.fault_code or ''}".lower()
    oil_terms = ("oil", "leak", "น้ำมัน", "รั่ว", "e-hyd-04")
    if any(term in normalized for term in oil_terms):
        return ChatResult(
            answer=(
                "หยุดเครื่องและทำ lockout/tagout จากนั้นตรวจแรงดัน ข้อต่อ สาย "
                "และซีลกระบอกไฮดรอลิก ทำความสะอาดบริเวณรั่วก่อนระบุตำแหน่ง "
                "ห้ามใช้มือค้นหารอยรั่วขณะระบบมีแรงดัน"
            ),
            confidence="sufficient",
            citations=[
                Citation(
                    document="HP-500 คู่มือบำรุงรักษา (ข้อมูลสังเคราะห์)",
                    section="ระบบไฮดรอลิก §4.2",
                    score=0.91,
                )
            ],
            suggested_part_ids=["p-seal-hp500", "p-filter-h46"],
            warning=WARNING,
        )
    return ChatResult(
        answer=(
            "หลักฐานในฐานความรู้ยังไม่เพียงพอสำหรับแนะนำขั้นตอนหรืออะไหล่ "
            "โปรดบันทึกอาการเพิ่มเติมและส่งต่อให้ช่างผู้มีคุณสมบัติ"
        ),
        confidence="insufficient",
        citations=[],
        suggested_part_ids=[],
        warning=WARNING,
    )
