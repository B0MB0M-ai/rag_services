from app.schemas.domain import Machine, Part

MACHINES = [
    Machine(
        id="m-hp500",
        model="HP-500 Hydraulic Press",
        serial_number="HP5-2024-001",
        location="Line A",
        status="maintenance",
    ),
    Machine(
        id="m-cnc200",
        model="CNC-200 Mill",
        serial_number="CNC-2023-014",
        location="Line B",
        status="operational",
    ),
    Machine(
        id="m-ac75",
        model="AC-75 Compressor",
        serial_number="AC75-2022-008",
        location="Utility Room",
        status="operational",
    ),
]

PARTS = [
    Part(
        id="p-seal-hp500",
        sku="SEAL-HP500",
        name_th="ชุดซีลกระบอกไฮดรอลิก",
        name_en="Hydraulic cylinder seal kit",
        unit_price_satang=485000,
    ),
    Part(
        id="p-filter-h46",
        sku="FILTER-H46",
        name_th="ไส้กรองน้ำมันไฮดรอลิก",
        name_en="Hydraulic oil filter",
        unit_price_satang=125000,
    ),
    Part(
        id="p-oil-h46",
        sku="OIL-H46-20L",
        name_th="น้ำมันไฮดรอลิก ISO VG 46 (20 ลิตร)",
        name_en="ISO VG 46 hydraulic oil (20 L)",
        unit_price_satang=320000,
    ),
    Part(
        id="p-bearing-6205",
        sku="BRG-6205",
        name_th="ตลับลูกปืน 6205",
        name_en="6205 bearing",
        unit_price_satang=89000,
    ),
]


def get_part(part_id: str) -> Part | None:
    return next((part for part in PARTS if part.id == part_id), None)
