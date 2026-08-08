from app.schemas.domain import KnowledgeDocument, Machine, Part

# A new workspace must not imply that customer-owned equipment or commercial data
# already exists. These collections are populated only through an explicit import
# once persistence and ingestion are configured.
MACHINES: list[Machine] = []
PARTS: list[Part] = []
KNOWLEDGE_DOCUMENTS: list[KnowledgeDocument] = []
# Process-local storage keeps uploaded content available to a later extraction/indexing step.
DOCUMENT_CONTENT: dict[str, bytes] = {}


def get_part(part_id: str) -> Part | None:
    return next((part for part in PARTS if part.id == part_id), None)
