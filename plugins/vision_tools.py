"""Vision & browser tools for Kaka.ai — multimodal analysis and JS-rendered pages."""
from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any

from core.tools import Tool

_SCREENSHOT_DIR = Path("./data/screenshots")
_ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _vision_api_key_and_url() -> tuple[str, str]:
    from core.config import Config

    cfg = Config.from_env()
    return cfg.api_key, cfg.base_url or "https://openrouter.ai/api/v1"


def analyze_image(image_path: str, question: str = "Describe this image in detail.") -> str:
    """Send an image to a vision-capable model and return its analysis."""
    p = Path(image_path).expanduser()
    if not p.exists():
        return f"Error: image not found: {p}"
    if p.suffix.lower() not in _ALLOWED_EXTS:
        return f"Error: unsupported format {p.suffix} (use {', '.join(sorted(_ALLOWED_EXTS))})"
    if p.stat().st_size > 10 * 1024 * 1024:
        return "Error: image larger than 10MB."

    api_key, base_url = _vision_api_key_and_url()
    if not api_key:
        return "Error: no API key configured."

    from core.config import Config

    vision_model = Config.from_env().vision_model
    mime = mimetypes.guess_type(str(p))[0] or "image/png"
    b64 = base64.b64encode(p.read_bytes()).decode()

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                }
            ],
            max_tokens=1200,
        )
        return resp.choices[0].message.content or "(no response)"
    except Exception as e:
        return f"Error: vision analysis failed ({str(e)[:200]}). Check VISION_MODEL supports images."


def browse_page(url: str, wait_seconds: float = 2.0) -> str:
    """Open a URL in a real headless Chromium — handles JavaScript-heavy pages."""
    from core.builtins import _validate_public_url

    guard = _validate_public_url(url, allow_private=False)
    if guard:
        return f"Blocked: {guard}"

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(url, timeout=45_000, wait_until="domcontentloaded")
            page.wait_for_timeout(int(wait_seconds * 1000))
            title = page.title()
            text = page.inner_text("body")

            _SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
            shot = _SCREENSHOT_DIR / f"page_{int(__import__('time').time())}.png"
            page.screenshot(path=str(shot), full_page=False)
            browser.close()

            text = text[:8000]
            return (
                f"Title: {title}\nScreenshot saved: {shot}\n\n{text}"
                + ("\n... (truncated)" if len(text) >= 8000 else "")
            )
    except Exception as e:
        return f"Error browsing '{url}': {str(e)[:200]}"


def register(registry: Any) -> None:
    registry.register(Tool(
        name="analyze_image",
        description="Analyze an image file with a vision AI model. Ask questions about screenshots, photos, diagrams, charts.",
        parameters={
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Path to png/jpg/webp/gif"},
                "question": {"type": "string", "description": "What to analyze or ask about the image"},
            },
            "required": ["image_path"],
        },
        execute=analyze_image,
    ))
    registry.register(Tool(
        name="browse_page",
        description="Open a URL in headless Chromium (renders JavaScript), returning title, visible text, and a screenshot path. Use for SPAs/dynamic pages that fetch_url cannot read.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to open"},
                "wait_seconds": {"type": "number", "description": "Seconds to wait for JS rendering (default 2)"},
            },
            "required": ["url"],
        },
        execute=browse_page,
    ))
