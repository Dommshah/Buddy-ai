"""Semantic memory for Kaka.ai — FAISS vector search over pretrained MiniLM embeddings."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from core.tools import Tool

_INDEX_DIR = Path("./data/memory/semantic")
_MODEL_NAME = "all-MiniLM-L6-v2"
_model = None  # lazy singleton


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def _passphrase() -> str | None:
    """Encryption passphrase for semantic metadata (when encryption enabled)."""
    from core.config import Config

    cfg = Config.from_env()
    return cfg.data_passphrase if getattr(cfg, "encrypt_data", False) else None


def _load_store() -> tuple[Any, list[dict]]:
    """Load (faiss index, metadata) from disk; build empty ones if absent."""
    import faiss
    import numpy as np

    from core.crypto import read_maybe_encrypted

    _INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index_path = _INDEX_DIR / "index.faiss"
    meta_path = _INDEX_DIR / "meta.json"
    passphrase = _passphrase()

    dim = 384  # all-MiniLM-L6-v2 output dimension
    if index_path.exists() and meta_path.exists():
        index = faiss.read_index(str(index_path))
        try:
            meta = json.loads(read_maybe_encrypted(meta_path, passphrase))
        except ValueError:
            raise ValueError(
                "Semantic memory is encrypted — set DATA_PASSPHRASE to unlock it."
            )
    else:
        index = faiss.IndexFlatIP(dim)
        meta = []
    return index, meta


def _save_store(index: Any, meta: list[dict]) -> None:
    import faiss

    from core.crypto import write_sealed

    write_sealed(_INDEX_DIR / "meta.json", json.dumps(meta, indent=1), _passphrase())
    faiss.write_index(index, str(_INDEX_DIR / "index.faiss"))


def remember_semantic(text: str, tags: str = "") -> str:
    """Store a text memory with semantic embedding for later similarity search."""
    if not text.strip():
        return "Error: empty text."
    import numpy as np

    model = _get_model()
    index, meta = _load_store()
    vec = model.encode([text], normalize_embeddings=True).astype("float32")
    index.add(vec)
    meta.append({
        "text": text[:2000],
        "tags": tags,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    _save_store(index, meta)
    return f"Remembered ({index.ntotal} total semantic memories): {text[:80]}..."


def search_semantic(query: str, k: int = 5) -> str:
    """Find the most semantically similar stored memories to a query."""
    import numpy as np

    model = _get_model()
    index, meta = _load_store()
    if index.ntotal == 0:
        return "Semantic memory is empty. Store something with remember_semantic first."
    k = max(1, min(int(k), index.ntotal))
    qvec = model.encode([query], normalize_embeddings=True).astype("float32")
    scores, ids = index.search(qvec, k)
    lines = []
    for score, idx in zip(scores[0], ids[0]):
        m = meta[int(idx)]
        lines.append(f"[{m['ts']}] ({m.get('tags','')}) {m['text']}  [sim={float(score):.3f}]")
    return "\n".join(lines)


def register(registry: Any) -> None:
    registry.register(Tool(
        name="remember_semantic",
        description="Store a fact, decision, or note in long-term semantic memory (searchable by meaning, not keywords).",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The information to remember"},
                "tags": {"type": "string", "description": "Optional comma-separated tags"},
            },
            "required": ["text"],
        },
        execute=remember_semantic,
    ))
    registry.register(Tool(
        name="search_semantic",
        description="Search long-term semantic memory by meaning. Returns top-k similar memories.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to look for (natural language)"},
                "k": {"type": "integer", "description": "Number of results (default 5)"},
            },
            "required": ["query"],
        },
        execute=search_semantic,
    ))
