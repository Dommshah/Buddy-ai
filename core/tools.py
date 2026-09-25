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

    def execute(self, name: str, **kwargs: Any) -> str:
        """Execute a tool by name with given arguments."""
        tool = self._tools.get(name)
        if not tool:
            return f"Error: Unknown tool '{name}'. Available: {', '.join(self._tools.keys())}"
        if not tool.execute:
            return f"Error: Tool '{name}' has no execute function."

        try:
            result = tool.execute(**kwargs)
            return str(result) if result is not None else "Tool executed successfully."
        except Exception as e:
            self.logger.error(f"Tool '{name}' failed: {e}")
            return f"Error executing tool '{name}': {e}"

    def list_tools(self) -> list[dict[str, str]]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]
