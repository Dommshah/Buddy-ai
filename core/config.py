from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    """Central configuration for the AI agent."""

    # LLM settings
    api_key: str = ""
    model: str = "gemini-2.0-flash"
    base_url: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.7

    # Agent settings
    system_prompt: str = ""
    max_iterations: int = 15
    verbose: bool = True

    # Memory settings
    memory_dir: Path = field(default_factory=lambda: Path("./data/memory"))
    max_memory_items: int = 500

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_env(cls, env_path: str | None = None) -> Config:
        """Load config from environment variables."""
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()

        return cls(
            api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
            model=os.getenv("MODEL_NAME", "gemini-2.0-flash"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            memory_dir=Path(os.getenv("MEMORY_DIR", "./data/memory")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    def validate(self) -> list[str]:
        """Return list of validation errors."""
        errors = []
        if not self.api_key:
            errors.append("GEMINI_API_KEY is required. Set it in .env or environment.")
        if self.temperature < 0 or self.temperature > 2:
            errors.append("Temperature must be between 0 and 2.")
        if self.max_tokens < 1:
            errors.append("max_tokens must be positive.")
        return errors
