from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


PROVIDER_DEFAULT_MODELS = {
    "gemini": "gemini-3.6-flash",
    "openrouter": "z-ai/glm-5.2:free",
    "openai": "gpt-4o-mini",
    "ollama": "qwen2.5:3b",
}

PROVIDER_BASE_URLS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "ollama": "http://localhost:11434/v1",
}

PROVIDER_KEY_VARS = {
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "openrouter": ("OPENROUTER_API_KEY",),
    "openai": ("OPENAI_API_KEY",),
    "ollama": (),
}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass
class Config:
    """Central configuration for the AI agent."""

    # LLM settings
    api_key: str = ""
    model: str = ""
    base_url: str | None = None
    provider: str = "gemini"
    max_tokens: int = 4096
    temperature: float = 0.7

    # Agent settings
    system_prompt: str = ""
    max_iterations: int = 40
    verbose: bool = True
    fallback_models: list[str] = field(default_factory=list)
    vision_model: str = "google/gemma-4-31b-it:free"
    context_compact_chars: int = 120_000  # ~30K tokens before compaction kicks in

    # Privacy settings
    privacy_mode: bool = False      # strict: no persistence of conversations
    proxy_url: str | None = None    # route LLM traffic via HTTP/SOCKS proxy
    scrub_secrets: bool = True      # redact key-shaped strings before they leave

    # Encryption-at-rest settings
    encrypt_data: bool = False      # seal memories/conversations with AES (Fernet)
    data_passphrase: str | None = None  # from DATA_PASSPHRASE or interactive prompt

    # Memory settings
    memory_dir: Path = field(default_factory=lambda: Path("./data/memory"))
    max_memory_items: int = 500

    # Logging
    log_level: str = "INFO"

    @classmethod
    def detect_provider(cls) -> str:
        """Auto-detect provider from available API keys (or PROVIDER env var)."""
        explicit = os.getenv("PROVIDER", "").strip().lower()
        if explicit:
            return explicit
        if os.getenv("OPENROUTER_API_KEY"):
            return "openrouter"
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        return "gemini"

    @classmethod
    def resolve_api_key(cls, provider: str) -> str:
        """Return the API key for the given provider, checking its env vars."""
        for var in PROVIDER_KEY_VARS.get(provider, ()):
            value = os.getenv(var, "")
            if value:
                return value
        return ""

    @classmethod
    def from_env(cls, env_path: str | None = None) -> Config:
        """Load config from environment variables."""
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()

        provider = cls.detect_provider()
        default_model = PROVIDER_DEFAULT_MODELS.get(provider, "gemini-3.6-flash")
        # Offline override: OLLAMA_BASE_URL / OFFLINE_MODEL env takes precedence for ollama
        _ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        if provider == "ollama":
            base_url = _ollama_base
            # Allow OFFLINE_MODEL override
            _off_m = os.getenv("OFFLINE_MODEL", "").strip()
            if _off_m:
                default_model = _off_m
        else:
            base_url = os.getenv("OPENAI_BASE_URL") or PROVIDER_BASE_URLS.get(provider)
        fallbacks = [
            m.strip() for m in os.getenv("FALLBACK_MODELS", "").split(",") if m.strip()
        ]

        _api_key = cls.resolve_api_key(provider)
        if provider == "ollama" and not _api_key:
            _api_key = "ollama"
        # For ollama, prioritize OFFLINE_MODEL over MODEL_NAME
        if provider == "ollama":
            _off_final = os.getenv("OFFLINE_MODEL", "").strip()
            _model_name = _off_final or os.getenv("MODEL_NAME", default_model)
        else:
            _model_name = os.getenv("MODEL_NAME", default_model)
        return cls(
            provider=provider,
            api_key=_api_key,
            model=_model_name,
            base_url=base_url,
            fallback_models=fallbacks,
            vision_model=os.getenv(
                "VISION_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
            ),
            context_compact_chars=_env_int("CONTEXT_COMPACT_CHARS", 120_000),
            max_tokens=_env_int("MAX_TOKENS", 4096),
            temperature=_env_float("TEMPERATURE", 0.7),
            memory_dir=Path(os.getenv("MEMORY_DIR", "./data/memory")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            privacy_mode=os.getenv("PRIVACY_MODE", "").strip().lower() in {"1", "true", "strict", "yes"},
            proxy_url=(os.getenv("PROXY_URL") or None),
            scrub_secrets=os.getenv("SECRET_SCRUB", "true").strip().lower() not in {"0", "false", "off"},
            encrypt_data=os.getenv("ENCRYPT_DATA", "").strip().lower() in {"1", "true", "yes"},
            data_passphrase=(os.getenv("DATA_PASSPHRASE") or None),
        )

    def validate(self) -> list[str]:
        """Return list of validation errors."""
        errors = []
        # ollama is local — no API key needed (offline qwen2.5:3b)
        if self.provider == "ollama":
            pass
        else:
            required_var = PROVIDER_KEY_VARS.get(self.provider, ("API_KEY",))[0] if PROVIDER_KEY_VARS.get(self.provider) else "API_KEY"
            if not self.api_key:
                errors.append(
                    f"{required_var} is required for provider '{self.provider}'. "
                    "Set it in .env or environment."
                )
        if self.temperature < 0 or self.temperature > 2:
            errors.append("Temperature must be between 0 and 2.")
        if self.max_tokens < 1:
            errors.append("max_tokens must be positive.")
        return errors
