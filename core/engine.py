"""Core agent engine - orchestrates LLM calls and tool execution."""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from .config import Config
from .tools import ToolRegistry

TOOL_RE = re.compile(r"USE_TOOL\((\w+)\|(.*?)\)", re.DOTALL)
PARAM_RE = re.compile(r"(\w+)=([^\|;]+)", re.DOTALL)


@dataclass
class Message:
    role: str
    content: str = ""
    tool_calls: list[dict] | None = None
    name: str | None = None
    tool_call_id: str | None = None


class AgentEngine:
    def __init__(self, config: Config = None, tools: ToolRegistry = None, **kw):
        self.config = config or Config.from_env()
        self.tools = tools or ToolRegistry()
        self.messages: list[Message] = []
        self.stream_callback = None
        self._http = httpx.Client(timeout=120.0)

    def reset(self):
        self.messages.clear()

    def _system_prompt(self) -> str:
        tool_lines = []
        for s in (self.tools.get_schemas() or []):
            f = s.get("function", {})
            params = list(f.get("parameters", {}).get("properties", {}).keys())
            param_str = ", ".join(params) if params else "none"
            tool_lines.append(f"  - {f['name']}({param_str}): {f.get('description', '')}")

        tools_section = "\n".join(tool_lines)

        return (
            "You are Kaka.ai, a helpful AI assistant with access to local tools.\n\n"
            "Available tools:\n"
            f"{tools_section}\n\n"
            "To call a tool, write on its own line:\n"
            "USE_TOOL(tool_name|param1=value1 param2=value2)\n\n"
            "Rules:\n"
            "- Call tools when the user asks for file ops, datetime, math, web, etc\n"
            "- After getting tool results, give a final answer\n"
            "- Be concise\n"
        )

    def _to_openai(self) -> list[dict]:
        out = [{"role": "system", "content": self._system_prompt()}]
        for m in self.messages:
            if m.role == "user":
                out.append({"role": "user", "content": m.content})
            elif m.role == "assistant":
                out.append({"role": "assistant", "content": m.content or ""})
            elif m.role == "tool":
                out.append({"role": "user", "content": "[Tool " + (m.name or "") + " result]: " + (m.content or "")})
        return out

    def _call_openrouter(self, messages: list[dict]) -> dict:
        url = (self.config.base_url or "https://openrouter.ai/api/v1") + "/chat/completions"
        resp = self._http.post(url, json={
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }, headers={
            "Authorization": "Bearer " + self.config.api_key,
            "Content-Type": "application/json",
        })
        resp.raise_for_status()
        data = resp.json()
        msg = (data.get("choices") or [{}])[0].get("message") or {}
        return {"content": msg.get("content") or "", "tool_calls": msg.get("tool_calls") or []}

    def _call_gemini(self, messages: list[dict]) -> dict:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.config.api_key)
        contents = []
        sys_text = ""
        for m in messages:
            if m["role"] == "system":
                sys_text = m.get("content", "")
            elif m["role"] == "user":
                contents.append(types.Content(role="user", parts=[types.Part(text=m.get("content", ""))]))
            elif m["role"] == "assistant":
                if m.get("content"):
                    contents.append(types.Content(role="model", parts=[types.Part(text=m["content"])]))

        response = client.models.generate_content(
            model=self.config.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=sys_text,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
            ),
        )
        content = ""
        if response.candidates:
            for part in (response.candidates[0].content.parts or []):
                if part.text:
                    content += part.text
        return {"content": content, "tool_calls": []}

    def _call_llm(self, messages: list[dict]) -> dict:
        if self.config.provider == "gemini":
            return self._call_gemini(messages)
        return self._call_openrouter(messages)

    def _parse_tool_calls(self, text: str) -> list[dict]:
        calls = []
        for m in TOOL_RE.finditer(text):
            name = m.group(1)
            args = {}
            for pm in PARAM_RE.finditer(m.group(2)):
                args[pm.group(1)] = pm.group(2).strip()
            calls.append({
                "id": "call_" + str(len(calls)),
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(args)},
            })
        return calls

    def _execute_tool(self, name: str, args: dict) -> str:
        logging.info("  Tool: %s(%s)", name, json.dumps(args)[:200])
        try:
            return str(self.tools.execute(name, args))[:50000]
        except Exception as e:
            return "Error: " + str(e)

    def chat(self, message: str) -> str:
        self.messages.append(Message(role="user", content=message))

        for attempt in range(3):
            try:
                content = ""
                for _round in range(5):
                    oai = self._to_openai()
                    result = self._call_llm(oai)
                    content = result.get("content", "") or ""

                    tool_calls = self._parse_tool_calls(content)
                    if not tool_calls:
                        tool_calls = result.get("tool_calls", [])

                    if not tool_calls:
                        self.messages.append(Message(role="assistant", content=content))
                        return content

                    self.messages.append(Message(role="assistant", content=content, tool_calls=tool_calls))
                    for tc in tool_calls:
                        fn = tc.get("function", {})
                        name = fn.get("name", "")
                        try:
                            args = json.loads(fn.get("arguments", "{}"))
                        except (json.JSONDecodeError, TypeError):
                            args = {}
                        tr = self._execute_tool(name, args)
                        self.messages.append(Message(role="tool", content=tr, name=name, tool_call_id=tc.get("id", "")))

                self.messages.append(Message(role="assistant", content=content))
                return content

            except Exception as e:
                logging.warning("LLM attempt %d/3 failed: %s", attempt + 1, e)
                if attempt < 2 and self.config.fallback_models:
                    self.config.model = self.config.fallback_models[0]
                    logging.warning("Trying fallback: %s", self.config.model)
                    time.sleep(2 * (attempt + 1))
                elif attempt >= 2:
                    return "Error communicating with AI: " + str(e)[:200]
        return "Error communicating with AI. Please try again."
