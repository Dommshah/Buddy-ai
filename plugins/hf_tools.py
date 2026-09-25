"""Hugging Face open-source pretrained models — secure local inference via transformers pipelines."""
from __future__ import annotations

import re
from typing import Any

from core.tools import Tool

# ── Security: allowlist of task types and model ID validation ──────────
_ALLOWED_TASKS = {
    "sentiment-analysis",
    "summarization",
    "translation",
    "question-answering",
    "zero-shot-classification",
    "text-classification",
    "feature-extraction",
}

# Valid HF model ID: namespace/model-name, alphanumeric + . _ - /
_MODEL_RE = re.compile(r"^[a-zA-Z0-9._/-]{3,120}$")
_MAX_INPUT_CHARS = 8000
_DEFAULT_MODELS = {
    "sentiment-analysis": "distilbert-base-uncased-finetuned-sst-2-english",
    "summarization": "sshleifer/distilbart-cnn-6-6",
    "translation": "Helsinki-NLP/opus-mt-en-de",
    "question-answering": "distilbert-base-cased-distilled-squad",
}

def _validate_model_id(model_id: str) -> str | None:
    if not _MODEL_RE.match(model_id):
        return "Invalid model ID format."
    if ".." in model_id or model_id.startswith("/") or "//" in model_id:
        return "Model ID may not contain '..' or absolute paths."
    if "/" not in model_id:
        return "Model ID must be 'namespace/model-name'."
    return None

def _run_pipeline(task: str, model_id: str, inputs: dict[str, Any]) -> str:
    err = _validate_model_id(model_id)
    if err:
        return f"Error: {err}"
    if task not in _ALLOWED_TASKS:
        return f"Error: task '{task}' not allowed. Allowed: {', '.join(sorted(_ALLOWED_TASKS))}"

    try:
        from transformers import pipeline
    except ImportError:
        return "Error: transformers not installed."

    # Input size guard
    for v in inputs.values():
        if isinstance(v, str) and len(v) > _MAX_INPUT_CHARS:
            return f"Error: input too large ({len(v)} chars, max {_MAX_INPUT_CHARS})."

    try:
        # trust_remote_code=False is the secure default; never enable for untrusted models
        nlp = pipeline(task, model=model_id, trust_remote_code=False, device=-1)  # CPU
        # Route to correct call signature
        if task == "question-answering":
            result = nlp(question=inputs.get("question", ""), context=inputs.get("context", ""))
        elif task == "zero-shot-classification":
            result = nlp(inputs.get("text", ""), candidate_labels=inputs.get("labels", []))
        elif task == "translation":
            result = nlp(inputs.get("text", ""))
        else:
            # sentiment, summarization, classification, etc. — single text input
            text = inputs.get("text") or inputs.get("inputs") or ""
            result = nlp(text)

        # Truncate large outputs
        out = str(result)
        if len(out) > 6000:
            out = out[:6000] + "… (truncated)"
        return out
    except Exception as e:
        return f"Error running {model_id} ({task}): {str(e)[:300]}"


def hf_sentiment(text: str, model_id: str = "") -> str:
    """Sentiment analysis on text."""
    mid = model_id.strip() or _DEFAULT_MODELS["sentiment-analysis"]
    return _run_pipeline("sentiment-analysis", mid, {"text": text})

def hf_summarize(text: str, model_id: str = "") -> str:
    """Summarize long text."""
    mid = model_id.strip() or _DEFAULT_MODELS["summarization"]
    return _run_pipeline("summarization", mid, {"text": text})

def hf_translate(text: str, model_id: str = "") -> str:
    """Translate text (default en→de)."""
    mid = model_id.strip() or _DEFAULT_MODELS["translation"]
    return _run_pipeline("translation", mid, {"text": text})

def hf_qa(question: str, context: str, model_id: str = "") -> str:
    """Question-answering over a context passage."""
    mid = model_id.strip() or _DEFAULT_MODELS["question-answering"]
    return _run_pipeline("question-answering", mid, {"question": question, "context": context})

def hf_classify(text: str, labels: str = "", model_id: str = "") -> str:
    """Zero-shot classification against comma-separated labels."""
    # Use a dedicated zero-shot model by default
    mid = model_id.strip() or "facebook/bart-large-mnli"
    lab_list = [l.strip() for l in labels.split(",") if l.strip()]
    if not lab_list:
        return "Error: provide labels as comma-separated list."
    return _run_pipeline("zero-shot-classification", mid, {"text": text, "labels": lab_list})

def hf_search(query: str, limit: int = 5) -> str:
    """Search Hugging Face Hub for models (no download)."""
    if not query.strip():
        return "Error: query required."
    limit = max(1, min(int(limit), 10))
    try:
        import httpx
        from core.builtins import _validate_public_url
        url = f"https://huggingface.co/api/models?search={query.strip()}&limit={limit}&sort=downloads&direction=-1"
        # HF API is public HTTPS — allowed
        guard = _validate_public_url(url)
        if guard:
            return f"Blocked: {guard}"
        with httpx.Client(timeout=20) as client:
            resp = client.get(url, headers={"User-Agent": "Kaka.ai"})
            if resp.status_code != 200:
                return f"HF search failed: HTTP {resp.status_code}"
            data = resp.json()
            if not data:
                return "No models found."
            lines = []
            for m in data[:limit]:
                mid = m.get("modelId", "?")
                dl = m.get("downloads", 0)
                pipeline = m.get("pipeline_tag", "—")
                lines.append(f"• {mid}  [{pipeline}]  ↓{dl:,}")
            return "\n".join(lines)
    except Exception as e:
        return f"Error searching HF: {str(e)[:200]}"

def register(registry: Any) -> None:
    registry.register(Tool(
        name="hf_sentiment",
        description="Sentiment analysis via Hugging Face pretrained model (default: distilbert SST-2, CPU).",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to analyze"},
                "model_id": {"type": "string", "description": "Optional HF model ID override"},
            },
            "required": ["text"],
        },
        execute=hf_sentiment,
    ))
    registry.register(Tool(
        name="hf_summarize",
        description="Summarize long text via Hugging Face pretrained model (default: distilbart-cnn-6-6, CPU).",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to summarize (max 8000 chars)"},
                "model_id": {"type": "string", "description": "Optional HF model ID"},
            },
            "required": ["text"],
        },
        execute=hf_summarize,
    ))
    registry.register(Tool(
        name="hf_translate",
        description="Translate text via Hugging Face pretrained model (default: en→de).",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to translate"},
                "model_id": {"type": "string", "description": "HF translation model ID"},
            },
            "required": ["text"],
        },
        execute=hf_translate,
    ))
    registry.register(Tool(
        name="hf_qa",
        description="Question-answering over a context passage via HF pretrained model.",
        parameters={
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Question"},
                "context": {"type": "string", "description": "Context passage"},
                "model_id": {"type": "string", "description": "Optional HF model ID"},
            },
            "required": ["question", "context"],
        },
        execute=hf_qa,
    ))
    registry.register(Tool(
        name="hf_classify",
        description="Zero-shot classify text against labels via HF model (default: bart-large-mnli).",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to classify"},
                "labels": {"type": "string", "description": "Comma-separated candidate labels"},
                "model_id": {"type": "string", "description": "Optional HF model ID"},
            },
            "required": ["text", "labels"],
        },
        execute=hf_classify,
    ))
    registry.register(Tool(
        name="hf_search",
        description="Search Hugging Face Hub for pretrained models (no download, ranked by downloads).",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (e.g., sentiment, summarization)"},
                "limit": {"type": "integer", "description": "Max results (default 5, max 10)"},
            },
            "required": ["query"],
        },
        execute=hf_search,
    ))
