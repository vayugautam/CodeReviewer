"""
config.py — centralised settings loaded from the .env file.

Why use pydantic-settings instead of os.getenv()?
  pydantic-settings reads the .env file automatically, validates types,
  and raises a clear error at startup if a required variable is missing —
  much better than a cryptic KeyError at runtime.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # GitHub personal access token — optional for public repos
    github_token: str = ""

    # Google Gemini API key — required for LLM review
    gemini_api_key: str = ""

    # Keep externally supplied PR metadata and diffs within predictable bounds.
    max_pr_url_length: int = 2048
    max_review_files: int = 50
    max_total_diff_chars: int = 200_000
    max_llm_diff_chars: int = 40_000
    max_llm_metadata_chars: int = 8_000
    github_timeout_seconds: float = 20.0

    # CORS: which frontend origin is allowed to call this API
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
      env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",          # silently ignore unknown env vars
    )


# Single shared instance — import this everywhere instead of re-reading the file
settings = Settings()
