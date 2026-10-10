from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Effort = Literal["low", "medium", "high", "xhigh", "max"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "agentic-ai-evaluation"
    app_env: str = "development"
    log_level: str = "INFO"
    # Browser origins allowed to call the API (the Next.js frontend).
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    anthropic_api_key: str | None = None
    agent_model: str = "claude-opus-5-5"
    judge_model: str = "claude-opus-5-5"
    agent_effort: Effort = "medium"
    judge_effort: Effort = "medium"
    enable_fallbacks: bool = True
    agent_max_turns: int = 8

    datasets_dir: Path = Path("datasets")
    results_dir: Path = Path("results")


@lru_cache
def get_settings() -> Settings:
    return Settings()
