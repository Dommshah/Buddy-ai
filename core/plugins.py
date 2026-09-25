"""Plugin system for extending the AI agent with custom tools."""
from __future__ import annotations

import importlib
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from core.tools import Tool, ToolRegistry


class Plugin(ABC):
    """Base class for all agent plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Plugin description."""

    @abstractmethod
    def get_tools(self) -> list[Tool]:
        """Return list of tools this plugin provides."""

    def on_load(self) -> None:
        """Called when the plugin is loaded."""

    def on_unload(self) -> None:
        """Called when the plugin is unloaded."""


class PluginManager:
    """Manages loading and registering plugins."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        self._plugins: dict[str, Plugin] = {}
        self.logger = logging.getLogger(__name__)

    def load_plugin(self, plugin: Plugin) -> None:
        """Load a plugin instance."""
        if plugin.name in self._plugins:
            self.logger.warning(f"Plugin '{plugin.name}' already loaded, skipping.")
            return

        tools = plugin.get_tools()
        for tool in tools:
            self.registry.register(tool)

        plugin.on_load()
        self._plugins[plugin.name] = plugin
        self.logger.info(f"Loaded plugin: {plugin.name} ({len(tools)} tools)")

    def load_from_module(self, module_path: str) -> None:
        """Load a plugin from a Python module path (e.g. 'plugins.web')."""
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, "plugin") and isinstance(module.plugin, Plugin):
                self.load_plugin(module.plugin)
            elif hasattr(module, "register"):
                module.register(self.registry)
                self.logger.info(f"Loaded module: {module_path}")
            else:
                self.logger.warning(f"No plugin or register() found in {module_path}")
        except Exception as e:
            self.logger.error(f"Failed to load {module_path}: {e}")

    def load_from_directory(self, directory: str | Path) -> None:
        """Load all plugins from a directory."""
        plugin_dir = Path(directory)
        if not plugin_dir.exists():
            return

        for py_file in plugin_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            module_name = f"plugins.{py_file.stem}"
            self.load_from_module(module_name)

    def unload_plugin(self, name: str) -> None:
        plugin = self._plugins.pop(name, None)
        if plugin:
            plugin.on_unload()
            self.logger.info(f"Unloaded plugin: {name}")

    def list_plugins(self) -> list[dict[str, str]]:
        return [{"name": p.name, "description": p.description} for p in self._plugins.values()]
