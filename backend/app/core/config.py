from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings."""

    app_env: str = "development"
    mock_ai: bool = True
    openai_api_key: SecretStr | None = None
    openai_response_model: str = "gpt-5-mini"
    cors_origins: str = "http://localhost:8000"
    rag_min_evidence_score: float = 0.35
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    rag_vector_results: int = 12
    rag_keyword_results: int = 12
    rag_final_context_count: int = 6
    max_upload_size_mb: int = 20

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
