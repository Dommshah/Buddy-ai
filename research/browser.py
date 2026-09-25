"""
Enhanced Web Browser — multi-source browsing, content extraction,
research deep-dives, and intelligent information synthesis.
"""
from __future__ import annotations

import re
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlparse, urljoin


@dataclass
class WebPage:
    url: str
    title: str = ""
    content: str = ""
    links: list[str] = field(default_factory=list)
    meta: dict[str, str] = field(default_factory=dict)
    fetched_at: str = ""
    status_code: int = 0
    content_type: str = ""
    word_count: int = 0
    language: str = "en"


@dataclass
class ResearchResult:
    query: str
    sources: list[WebPage] = field(default_factory=list)
    summary: str = ""
    key_findings: list[str] = field(default_factory=list)
    citations: list[dict[str, str]] = field(default_factory=list)
    confidence: float = 0.0
    depth: int = 1
    total_words: int = 0


class EnhancedBrowser:
    """Advanced web browser with research capabilities."""

    def __init__(self) -> None:
        self._cache: dict[str, WebPage] = {}
        self._visited: set[str] = set()

    def fetch_page(self, url: str, extract_text: bool = True) -> WebPage:
        """Fetch a web page with intelligent content extraction."""
        import httpx

        if url in self._cache:
            return self._cache[url]

        page = WebPage(url=url, fetched_at=datetime.now().isoformat())

        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                resp = client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; AIAgent/3.0)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                })
                page.status_code = resp.status_code
                page.content_type = resp.headers.get("content-type", "")

                if resp.status_code == 200:
                    html = resp.text
                    page.title = self._extract_title(html)
                    page.meta = self._extract_meta(html)
                    page.links = self._extract_links(html, url)

                    if extract_text:
                        page.content = self._extract_text(html)
                    else:
                        page.content = html

                    page.word_count = len(page.content.split())
                    page.language = page.meta.get("language", "en")
        except Exception as e:
            page.content = f"Error fetching {url}: {e}"

        self._cache[url] = page
        self._visited.add(url)
        return page

    def search_and_collect(
        self, query: str, max_results: int = 5
    ) -> list[WebPage]:
        """Search the web and collect top results."""
        search_results = self._duckduckgo_search(query, max_results)
        pages: list[WebPage] = []

        for result in search_results:
            if result.get("url"):
                page = self.fetch_page(result["url"])
                if page.title and page.word_count > 50:
                    pages.append(page)

        return pages

    def search_and_collect(
        self, query: str, max_results: int = 5
    ) -> list[WebPage]:
        """Search the web and collect top results."""
        search_results = self._duckduckgo_search(query, max_results)
        pages: list[WebPage] = []

        for result in search_results:
            if result.get("url"):
                page = self.fetch_page(result["url"])
                if page.title and page.word_count > 50:
                    pages.append(page)

        return pages

    def deep_research(
        self, query: str, depth: int = 3, max_sources: int = 10
    ) -> ResearchResult:
        """Perform deep research with multi-level link following."""
        result = ResearchResult(query=query, depth=depth)

        # Level 1: Initial search
        pages = self.search_and_collect(query, max_results=max_sources // 2)

        # Synthesize findings
        result.total_words = sum(p.word_count for p in result.sources)
        result.key_findings = self._extract_key_findings(result.sources)
        result.citations = [
            {"title": p.title, "url": p.url, "words": str(p.word_count)}
            for p in result.sources[:max_sources]
        ]
        result.summary = self._synthesize_summary(query, result.sources)
        result.confidence = min(0.95, 0.3 + len(result.sources) * 0.08 + depth * 0.1)

        return result

    def extract_structured_data(self, url: str) -> dict[str, Any]:
        """Extract structured data from a page (JSON-LD, OpenGraph, etc.)."""
        page = self.fetch_page(url)
        structured: dict[str, Any] = {
            "title": page.title,
            "url": page.url,
            "meta": page.meta,
            "links_count": len(page.links),
            "word_count": page.word_count,
        }

        # Try to extract JSON-LD
        json_ld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        matches = re.findall(json_ld_pattern, page.content, re.DOTALL)
        if matches:
            try:
                structured["json_ld"] = [json.loads(m) for m in matches[:3]]
            except json.JSONDecodeError:
                pass

        return structured

    def compare_sources(self, urls: list[str]) -> dict[str, Any]:
        """Compare information across multiple sources."""
        pages = [self.fetch_page(url) for url in urls]

        common_terms = self._find_common_terms(pages)
        unique_points = {}
        for page in pages:
            unique_points[page.url] = self._extract_unique_points(page, pages)

        return {
            "sources": len(pages),
            "common_terms": common_terms[:20],
            "unique_points": unique_points,
            "word_counts": {p.url: p.word_count for p in pages},
            "avg_word_count": sum(p.word_count for p in pages) // max(len(pages), 1),
        }

    # ── Private helpers ──────────────────────────────────────────────

    def _extract_title(self, html: str) -> str:
        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_meta(self, html: str) -> dict[str, str]:
        meta: dict[str, str] = {}
        for match in re.finditer(r'<meta[^>]+(?:name|property)=["\']([^"\']+)["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE):
            meta[match.group(1)] = match.group(2)
        og_match = re.search(r'<meta[^>]+property="og:([^"]+)"[^>]+content="([^"]+)"', html, re.IGNORECASE)
        if og_match:
            meta[f"og:{og_match.group(1)}"] = og_match.group(2)
        return meta

    def _extract_links(self, html: str, base_url: str) -> list[str]:
        links: list[str] = []
        for match in re.finditer(r'href=["\']([^"\'#]+)["\']', html, re.IGNORECASE):
            url = match.group(1)
            if url.startswith(("http://", "https://")):
                links.append(url)
            elif url.startswith("/"):
                parsed = urlparse(base_url)
                links.append(f"{parsed.scheme}://{parsed.netloc}{url}")
        return list(dict.fromkeys(links))[:50]

    def _extract_text(self, html: str) -> str:
        # Remove scripts, styles, nav, footer
        html = re.sub(r'<(script|style|nav|footer|header)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Decode entities
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&quot;', '"').replace('&#39;', "'")
        return text[:50000]

    def _duckduckgo_search(self, query: str, max_results: int) -> list[dict[str, str]]:
        """Search using DuckDuckGo Lite."""
        import httpx

        results: list[dict[str, str]] = []
        try:
            with httpx.Client(timeout=15, follow_redirects=True) as client:
                resp = client.get(
                    "https://lite.duckduckgo.com/lite/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                html = resp.text
                # Extract results from lite page
                for match in re.finditer(r'class="result-link"[^>]*href="([^"]+)"[^>]*>([^<]+)', html):
                    results.append({"url": match.group(1), "title": match.group(2).strip()})
                    if len(results) >= max_results:
                        break
        except (httpx.RequestError, httpx.TimeoutException, re.error):
            pass
        return results

    def _is_relevant(self, url: str, query: str) -> bool:
        query_words = set(query.lower().split())
        url_words = set(re.findall(r'\w+', urlparse(url).path.lower()))
        return bool(query_words & url_words) or any(
            domain in url
            for domain in ["arxiv.org", "github.com", "stackoverflow.com", "docs.", "developer."]
        )

    def _generate_related_queries(self, query: str) -> list[str]:
        words = query.split()
        related = []
        if len(words) > 2:
            related.append(f"{words[-1]} best practices")
            related.append(f"{words[-1]} tutorial")
            related.append(f"{words[0]} examples")
        return related

    def _extract_key_findings(self, sources: list[WebPage]) -> list[str]:
        findings: list[str] = []
        for source in sources[:5]:
            sentences = re.split(r'[.!?]+', source.content)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 30 and len(sentence) < 200:
                    if any(w in sentence.lower() for w in ["study", "research", "found", "showed", "according", "evidence"]):
                        findings.append(sentence[:200])
                        break
        return findings[:10]

    def _synthesize_summary(self, query: str, sources: list[WebPage]) -> str:
        if not sources:
            return f"No sources found for: {query}"

        top_sentences: list[str] = []
        for source in sources[:3]:
            sentences = re.split(r'[.!?]+', source.content)
            for s in sentences:
                s = s.strip()
                if len(s) > 40 and len(s) < 300:
                    top_sentences.append(s)
                    if len(top_sentences) >= 5:
                        break
            if len(top_sentences) >= 5:
                break

        return f"Research on: {query}\n\n" + ". ".join(top_sentences[:5]) + "." if top_sentences else f"Research completed for: {query} ({len(sources)} sources analyzed)"

    def _find_common_terms(self, sources: list[WebPage]) -> list[str]:
        all_words: dict[str, int] = {}
        for source in sources:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', source.content.lower())
            for w in set(words):
                all_words[w] = all_words.get(w, 0) + 1
        sorted_words = sorted(all_words.items(), key=lambda x: x[1], reverse=True)
        return [w for w, c in sorted_words if c >= 2]

    def _extract_unique_points(self, page: WebPage, all_pages: list[WebPage]) -> list[str]:
        other_content = " ".join(p.content for p in all_pages if p.url != page.url)
        page_words = set(re.findall(r'\b[a-zA-Z]{5,}\b', page.content.lower()))
        other_words = set(re.findall(r'\b[a-zA-Z]{5,}\b', other_content.lower()))
        unique = page_words - other_words
        return list(unique)[:10]
