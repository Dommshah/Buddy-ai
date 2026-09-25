"""Web search and scraping plugin."""
from __future__ import annotations

from typing import Any

from core.plugins import Plugin
from core.tools import Tool


class WebSearchPlugin(Plugin):
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Web search and content fetching tools"

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="web_search",
                description="Search the web using DuckDuckGo. Returns top results.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results (default: 5)",
                        },
                    },
                    "required": ["query"],
                },
                execute=self._search,
            ),
            Tool(
                name="scrape_url",
                description="Scrape and extract text content from a URL.",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to scrape"},
                        "selector": {
                            "type": "string",
                            "description": "CSS selector to extract (optional)",
                        },
                    },
                    "required": ["url"],
                },
                execute=self._scrape,
            ),
        ]

    def _search(self, query: str, num_results: int = 5) -> str:
        """Search using DuckDuckGo lite."""
        import httpx
        from html.parser import HTMLParser

        class DDGParser(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.results: list[dict[str, str]] = []
                self._in_result = False
                self._current: dict[str, str] = {}
                self._capture = ""

            def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                attrs_dict = dict(attrs)
                if tag == "a" and "result__a" in attrs_dict.get("class", ""):
                    self._in_result = True
                    self._current["url"] = attrs_dict.get("href", "")
                    self._capture = "title"
                elif tag == "a" and "result__snippet" in attrs_dict.get("class", ""):
                    self._capture = "snippet"

            def handle_data(self, data: str) -> None:
                if self._capture == "title":
                    self._current["title"] = data.strip()
                elif self._capture == "snippet":
                    self._current["snippet"] = data.strip()

            def handle_endtag(self, tag: str) -> None:
                if tag == "a" and self._capture == "title" and self._current.get("title"):
                    pass  # Keep going
                elif tag == "a" and self._capture == "snippet":
                    if self._current.get("title"):
                        self.results.append(self._current)
                    self._current = {}
                    self._capture = ""

        try:
            with httpx.Client(timeout=15, follow_redirects=True) as client:
                resp = client.get(
                    "https://lite.duckduckgo.com/lite/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                parser = DDGParser()
                parser.feed(resp.text)

                if not parser.results:
                    return f"No results found for: {query}"

                output_lines = [f"Search results for: {query}\n"]
                for i, r in enumerate(parser.results[:num_results], 1):
                    title = r.get("title", "No title")
                    url = r.get("url", "")
                    snippet = r.get("snippet", "No description")
                    output_lines.append(f"{i}. {title}\n   {url}\n   {snippet}\n")

                return "\n".join(output_lines)
        except Exception as e:
            return f"Search error: {e}"

    def _scrape(self, url: str, selector: str | None = None) -> str:
        """Scrape URL content."""
        import httpx

        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                resp = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                content_type = resp.headers.get("content-type", "")

                if "html" in content_type:
                    from html.parser import HTMLParser

                    class TextExtractor(HTMLParser):
                        def __init__(self) -> None:
                            super().__init__()
                            self.text_parts: list[str] = []
                            self._skip = False
                            self._skip_tags = {"script", "style", "nav", "footer", "header"}

                        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                            if tag in self._skip_tags:
                                self._skip = True

                        def handle_endtag(self, tag: str) -> None:
                            if tag in self._skip_tags:
                                self._skip = False

                        def handle_data(self, data: str) -> None:
                            if not self._skip:
                                text = data.strip()
                                if text:
                                    self.text_parts.append(text)

                    extractor = TextExtractor()
                    extractor.feed(resp.text)
                    text = "\n".join(extractor.text_parts)
                    if len(text) > 8000:
                        text = text[:8000] + f"\n\n... (truncated from {len(resp.text)} chars)"
                    return f"Content from {url}:\n\n{text}"
                else:
                    return resp.text[:5000]
        except Exception as e:
            return f"Scraping error: {e}"


# Module-level registration
def register(registry: Any) -> None:
    from core.tools import ToolRegistry

    if isinstance(registry, ToolRegistry):
        plugin = WebSearchPlugin()
        for tool in plugin.get_tools():
            registry.register(tool)
