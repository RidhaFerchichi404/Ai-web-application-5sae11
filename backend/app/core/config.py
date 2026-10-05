from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    """Runtime settings. Secrets come from the environment, not from code defaults."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.is_file() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(min_length=1)
    database_url: str = Field(min_length=1)
    ollama_base_url: str = Field(min_length=1)
    ollama_chat_model: str = Field(min_length=1)
    ollama_embedding_model: str = Field(min_length=1)
    max_file_size_mb: int = Field(gt=0)
    upload_directory: str = Field(min_length=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
