from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Effort = Literal["low", "medium", "high", "xhigh", "max"]

# The backend/ folder. Paths are anchored here so the app works from any working directory.
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

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
    # How many questions run at the same time. Lower it (e.g. 1) on rate-limited free tiers.
    max_concurrency: int = Field(default=5, ge=1)

    # Google Gemini (used by the "gemini" agent, and by llm_judge when judge_provider="gemini")
    gemini_api_key: str | None = None
    gemini_agent_model: str = "gemini-3.5-flash-lite"
    gemini_judge_model: str = "gemini-3.5-flash-lite"
    # Which provider grades answers for the llm_judge evaluator.
    judge_provider: Literal["anthropic", "gemini"] = "anthropic"

    # MongoDB (Atlas). When set, run reports and saved questions live in MongoDB;
    # when empty, they are kept as files in results/ and datasets/.
    mongodb_uri: str | None = None
    mongodb_db: str = "agentic_eval"

    datasets_dir: Path = BASE_DIR / "datasets"
    results_dir: Path = BASE_DIR / "results"

    @field_validator("datasets_dir", "results_dir")
    @classmethod
    def _anchor_relative_paths(cls, value: Path) -> Path:
        # A relative path from .env (e.g. RESULTS_DIR=results) means relative to backend/,
        # not to whatever folder the server happened to be started from.
        return value if value.is_absolute() else BASE_DIR / value


@lru_cache
def get_settings() -> Settings:
    return Settings()
