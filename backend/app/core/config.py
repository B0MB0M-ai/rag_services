from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings."""

    app_env: str = "development"
    # Raw, deterministic evidence output is an explicit offline/testing mode. Normal
    # application runs should use the configured language model to synthesize RAG context.
    mock_ai: bool = False
    openai_api_key: SecretStr | None = None
    openai_response_model: str = "gpt-5-mini"
<<<<<<< HEAD
    openai_max_output_tokens: int = 4000
=======
    openai_max_output_tokens: int = 500
    # Leave enough of the five-second user-facing SLA for HTTP and browser rendering.
    assistant_response_timeout_seconds: float = 4.0
>>>>>>> af2ef1a53b031dbccd51e62486ade5395a217ec5
    cors_origins: str = "http://localhost:8000"
    rag_min_evidence_score: float = 0.35
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    rag_vector_results: int = 12
    rag_keyword_results: int = 12
    rag_final_context_count: int = 4
    max_upload_size_mb: int = 20
    app_data_dir: Path = Path(__file__).resolve().parents[2] / "data"

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
