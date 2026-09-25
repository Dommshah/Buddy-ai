"""Core agent engine — orchestrates LLM calls and tool execution."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from google import genai
from google.genai import types

from .config import Config
from .memory import MemoryManager
from .tools import ToolRegistry
from .builtins import register_built_in_tools


DEFAULT_SYSTEM_PROMPT = """You are a highly capable personal AI agent v3.0 with autonomous reasoning, deep research, sub-agent orchestration, and universal platform compatibility. You have access to 45+ tools and can think, plan, and act independently.

## Core Capabilities
- Read, write, edit, and search files on the local filesystem
- Execute shell commands and Python code
- Browse the internet, fetch web pages, and perform deep research
- Manage persistent memory and learn from interactions
- Perform calculations and JSON queries
- Access system information across platforms

## Cognitive Abilities
- **Autonomous Reasoning**: Self-directed thinking loop — observe, analyze, hypothesize, decide, reflect
- **8 Reasoning Modes**: Chain-of-thought, tree-of-thought, deductive, inductive, abductive, analogical, critical, reflective
- **Adaptive Learning**: Store patterns, recall past decisions, track skill proficiency
- **Problem-Solving**: Break complex problems into steps, plan autonomously, execute multi-step tasks

## Advanced Capabilities
- **Deep Research**: Multi-source web research with citations, fact-checking, and knowledge synthesis
- **Sub-Agent System**: Spawn specialized agents (researcher, coder, analyst, writer, reviewer) for parallel work
- **Content Creation**: Blog posts, emails, social media, landing pages, video scripts, business proposals
- **Code Analysis**: Complexity analysis, bug detection, refactoring, code generation in multiple languages
- **Security Auditing**: Vulnerability scanning, hardcoded secret detection, dependency checking
- **Pattern Recognition**: Trend detection, sentiment analysis, outlier identification
- **Prediction**: Linear regression, moving average, trend classification, volatility estimation
- **Verification**: Fact-checking, data integrity validation, logical validity checking
- **Creativity**: Brainstorming, SCAMPER, random association, innovation frameworks
- **Voice**: Speech-to-text, text-to-speech, voice command processing
- **Knowledge Base**: Persistent knowledge storage and retrieval from open-source patterns

## Behavior
- Be proactive: use tools when needed, don't just describe what you'd do.
- Always verify your work: check files after writing, confirm commands succeeded.
- Use the autonomous_think tool for complex questions before answering.
- Use deep_research when you need current or comprehensive information.
- Spawn sub-agents for parallel work when handling complex multi-part tasks.
- Be concise in responses but thorough in execution.
- If a task is complex, break it into steps and execute them.
- Never ask permission for routine tasks — just do them.
- If something fails, diagnose and retry with a different approach.
- Maintain context across the conversation; refer back to previous actions.
- Learn from interactions: store patterns, recall past decisions.

## Tool Permission Rules
- Always check tool permissions before execution.
- Ask permission for: write_file, run_command, run_python, scrape_url.
- Never ask for: read_file, list_files, search_files, web_search, fetch_url, calculate.
- Deny: Never expose secrets or execute destructive commands without confirmation.

## Security
- Do NOT execute destructive commands without explicit confirmation (rm -rf, DROP TABLE, etc.).
- Do NOT expose API keys or secrets in output.
- Be cautious with network requests to unknown domains.
- Run security audits on code before deployment.
"""


@dataclass
class Message:
    role: str  # "system", "user", "assistant", "tool"
    content: str = ""
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class AgentEngine:
    """The core agent loop that drives the AI agent."""

    config: Config
    tools: ToolRegistry = field(default_factory=ToolRegistry)
    memory: MemoryManager = field(default_factory=MemoryManager)
    messages: list[Message] = field(default_factory=list)
    _client: genai.Client | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        register_built_in_tools(self.tools)
        self.memory.load()
        self._init_client()
        self._init_messages()

    def _init_client(self) -> None:
        self._client = genai.Client(api_key=self.config.api_key)

    def _init_messages(self) -> None:
        system_prompt = self.config.system_prompt or DEFAULT_SYSTEM_PROMPT
        system_prompt += "\n\n## Memory Context\n" + self.memory.get_context_string()
        self.messages = [Message(role="system", content=system_prompt)]

    def chat(self, user_input: str) -> str:
        """Process a user message and return the agent's response."""
        self.messages.append(Message(role="user", content=user_input))

        for iteration in range(self.config.max_iterations):
            response = self._call_llm()
            self.messages.append(
                Message(role="assistant", content=response.get("content", ""), tool_calls=response.get("tool_calls"))
            )

            if not response.get("tool_calls"):
                final = response.get("content", "")
                self.memory.add_conversation(user_input, final)
                return final

            for tc in response["tool_calls"]:
                fn = tc["function"]
                tool_name = fn["name"]
                try:
                    args = json.loads(fn["arguments"]) if isinstance(fn["arguments"], str) else fn["arguments"]
                except json.JSONDecodeError:
                    args = {}

                if self.config.verbose:
                    logging.info(f"  Tool: {tool_name}({json.dumps(args)[:200]})")

                result = self.tools.execute(tool_name, **args)

                self.messages.append(
                    Message(role="tool", content=str(result), tool_call_id=tc["id"], name=tool_name)
                )

        self.messages.append(
            Message(
                role="user",
                content="You've reached the maximum tool iterations. Please provide your final answer based on everything you've gathered so far.",
            )
        )
        final_response = self._call_llm()
        return final_response.get("content", "I reached the maximum number of steps. Here's what I found so far.")

    def _call_llm(self) -> dict[str, Any]:
        """Make a single LLM API call with tool definitions."""
        schemas = self.tools.get_schemas()

        contents = []
        for msg in self.messages:
            if msg.role == "system":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(text=f"[System Instructions]: {msg.content}")]
                ))
            elif msg.role == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(text=msg.content)]
                ))
            elif msg.role == "assistant":
                if msg.content:
                    contents.append(types.Content(
                        role="model",
                        parts=[types.Part(text=msg.content)]
                    ))
            elif msg.role == "tool":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(text=f"Tool Result ({msg.name}): {msg.content}")]
                ))

        tools = []
        if schemas:
            function_declarations = []
            for schema in schemas:
                func = schema.get("function", {})
                params = func.get("parameters", {}).get("properties", {})
                function_declarations.append(
                    types.FunctionDeclaration(
                        name=func.get("name", ""),
                        description=func.get("description", ""),
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                k: types.Schema(
                                    type=types.Type.STRING,
                                    description=v.get("description", "")
                                )
                                for k, v in params.items()
                            }
                        )
                    )
                )
            tools = [types.Tool(function_declarations=function_declarations)]

        try:
            config = types.GenerateContentConfig(
                system_instruction=self.messages[0].content if self.messages else "",
                tools=tools if tools else None,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
            )

            response = self._client.models.generate_content(
                model=self.config.model,
                contents=contents[1:],
                config=config,
            )

            result: dict[str, Any] = {"content": ""}

            if response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    text_parts = []
                    tool_calls = []

                    for part in candidate.content.parts:
                        if part.text:
                            text_parts.append(part.text)
                        if part.function_call:
                            fc = part.function_call
                            args_dict = dict(fc.args) if fc.args else {}
                            tool_calls.append({
                                "id": f"call_{len(tool_calls)}",
                                "function": {
                                    "name": fc.name,
                                    "arguments": json.dumps(args_dict),
                                },
                            })

                    result["content"] = "\n".join(text_parts)
                    if tool_calls:
                        result["tool_calls"] = tool_calls

            return result

        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            return {"content": f"I encountered an error communicating with the AI: {str(e)}"}

    def reset(self) -> None:
        """Clear conversation history."""
        self._init_messages()

    def get_history(self) -> list[dict[str, str]]:
        """Return conversation history as simple dicts."""
        return [{"role": m.role, "content": m.content} for m in self.messages if m.role != "tool"]
