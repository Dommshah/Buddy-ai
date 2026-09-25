
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Tool:
    """A callable tool that the agent can invoke."""

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    execute: Callable[..., Any] | None = None
    required_permissions: list[str] = field(default_factory=list)

    def to_schema(self) -> dict[str, Any]:
        """Convert tool to OpenAI function-calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


_MAX_TOOL_STRING_CHARS = 200_000  # per-argument DoS guard


def _validate_tool_args(tool_name: str, parameters: dict[str, Any], args: dict[str, Any]) -> str | None:
    """Lenient JSON-schema-style check. Returns error string or None.

    - Missing ``required`` params → error.
    - Wrong primitive types → error, except safely coercible values
      (digit strings for integers, numbers for strings) which pass.
    - Oversized strings (>200k chars) → error to bound resource use.
    """
    if not isinstance(parameters, dict):
        return None
    props = parameters.get("properties", {})
    if not isinstance(props, dict):
        return None
    for req in parameters.get("required", []) or []:
        if req not in args or args[req] is None or (isinstance(args[req], str) and not args[req].strip()):
            return f"Error: Tool '{tool_name}' missing required argument '{req}'."
    for key, value in args.items():
        spec = props.get(key, {})
        if not isinstance(spec, dict):
            continue
        want = spec.get("type")
        if isinstance(value, str) and len(value) > _MAX_TOOL_STRING_CHARS:
            return (
                f"Error: Tool '{tool_name}' argument '{key}' too large "
                f"({len(value)} chars, max {_MAX_TOOL_STRING_CHARS})."
            )
        if want == "string":
            if not isinstance(value, (str, int, float, bool)):
                return f"Error: Tool '{tool_name}' argument '{key}' must be a string."
        elif want == "integer":
            if isinstance(value, bool) or (
                not isinstance(value, int)
                and not (isinstance(value, str) and value.strip().lstrip("-").isdigit())
            ):
                return f"Error: Tool '{tool_name}' argument '{key}' must be an integer."
        elif want == "number":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                try:
                    float(value)
                except (TypeError, ValueError):
                    return f"Error: Tool '{tool_name}' argument '{key}' must be a number."
        elif want == "boolean":
            if not isinstance(value, bool):
                return f"Error: Tool '{tool_name}' argument '{key}' must be true/false."
        elif want == "array":
            if not isinstance(value, list):
                return f"Error: Tool '{tool_name}' argument '{key}' must be an array."
        elif want == "object":
            if not isinstance(value, dict):
                return f"Error: Tool '{tool_name}' argument '{key}' must be an object."
        if spec.get("enum") and value not in spec["enum"]:
            return (
                f"Error: Tool '{tool_name}' argument '{key}' must be one of "
                f"{spec['enum']}."
            )
    return None


class ToolRegistry:
    """Registry for all available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self.logger = logging.getLogger(__name__)

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        self.logger.debug(f"Registered tool: {tool.name}")

    def register_function(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        parameters: dict[str, Any] | None = None,
    ) -> None:
        """Register a plain function as a tool."""
        self.register(
            Tool(
                name=name,
                description=description,
                parameters=parameters or {"type": "object", "properties": {}},
                execute=func,
            )
        )

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get_schemas(self) -> list[dict[str, Any]]:
        """Get all tool schemas for the LLM."""
        return [tool.to_schema() for tool in self._tools.values()]

    def execute(self, tool_name: str, /, **kwargs: Any) -> str:
        """Execute a tool by name with given arguments.

        ``tool_name`` is positional-only so that tools may freely define
        their own parameters called 'name' or 'tool_name'.
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return f"Error: Unknown tool '{tool_name}'. Available: {', '.join(self._tools.keys())}"
        if not tool.execute:
            return f"Error: Tool '{tool_name}' has no execute function."

        try:
            # Drop arguments the tool's schema does not declare. LLMs
            # occasionally emit extra/hallucinated keys; calling with them
            # used to raise TypeError and fail the whole tool call.
            props = (tool.parameters or {}).get("properties", {})
            filtered = {k: v for k, v in kwargs.items() if k in props}
            # Lenient schema check (no new deps): required presence + basic
            # types. Coercible values pass (e.g. "30" for an integer timeout)
            # so valid LLM output is never rejected; garbage is.
            _arg_error = _validate_tool_args(tool_name, tool.parameters or {}, filtered)
            if _arg_error:
                return _arg_error
            result = tool.execute(**filtered)
            return str(result) if result is not None else "Tool executed successfully."
        except Exception as e:
            self.logger.error(f"Tool '{tool_name}' failed: {e}")
            return f"Error executing tool '{tool_name}': {e}"

    def list_tools(self) -> list[dict[str, str]]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]