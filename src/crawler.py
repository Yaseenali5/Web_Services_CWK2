"""Website crawler for the coursework search tool."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urljoin, urlparse, urlunparse
import re
import time

import requests
from bs4 import BeautifulSoup


QUOTE_PAGE_PATTERN = re.compile(r"^/$|^/page/\d+/?$")


@dataclass(slots=True)
class CrawledPage:
    """Structured representation of a crawled page."""

    url: str
    title: str
    page_type: str
    content: str


@dataclass(slots=True)
class ParsedDocument:
    """Parsed page content and the crawlable links found within it."""

    page: CrawledPage | None
    links: list[str]


class WebsiteCrawler:
    """Crawl the target site while respecting the politeness window."""

    def __init__(
        self,
        base_url: str = "https://quotes.toscrape.com/",
        politeness_window: float = 6.0,
        timeout: float = 10.0,
        session: requests.Session | None = None,
        sleep_func: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.base_url = self._canonicalise_url(base_url)
        self.base_domain = urlparse(self.base_url).netloc
        self.politeness_window = politeness_window
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(
            {"User-Agent": "coursework-search-tool/1.0 (+https://quotes.toscrape.com/)"}
        )
        self.sleep_func = sleep_func
        self.clock = clock
        self._last_request_started_at: float | None = None

    def crawl(self, start_url: str | None = None) -> list[CrawledPage]:
        """Crawl the allowed site pages starting from the seed URL."""

        seed_url = self._canonicalise_url(start_url or self.base_url)
        queue: deque[str] = deque([seed_url])
        queued_urls = {seed_url}
        visited_urls: set[str] = set()
        pages: list[CrawledPage] = []

        while queue:
            current_url = queue.popleft()
            queued_urls.discard(current_url)

            if current_url in visited_urls:
                continue

            visited_urls.add(current_url)
            html = self.fetch_html(current_url)
            if html is None:
                continue

            parsed_document = self.parse_document(current_url, html)
            if parsed_document.page is not None:
                pages.append(parsed_document.page)

            for discovered_url in parsed_document.links:
                if discovered_url in visited_urls or discovered_url in queued_urls:
                    continue
                queue.append(discovered_url)
                queued_urls.add(discovered_url)

        return pages

    def fetch_html(self, url: str) -> str | None:
        """Fetch a page while respecting the configured politeness window."""

        self._enforce_politeness_window()
        request_started_at = self.clock()

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException:
            return None
        finally:
            self._last_request_started_at = request_started_at

        return response.text

    def parse_document(self, url: str, html: str) -> ParsedDocument:
        """Parse a page into structured content plus crawlable links."""

        soup = BeautifulSoup(html, "html.parser")
        links = self.extract_links(soup, url)

        if self._is_quote_page(url):
            quote_page = self._parse_quote_page(url, soup)
            return ParsedDocument(page=quote_page, links=links)

        return ParsedDocument(page=None, links=links)

    def extract_links(self, soup: BeautifulSoup, current_url: str) -> list[str]:
        """Collect allowed internal links from the page."""

        discovered_urls: list[str] = []
        for anchor in soup.select("a[href]"):
            href = anchor.get("href")
            if not href:
                continue

            absolute_url = self._canonicalise_url(urljoin(current_url, href))
            if self.is_allowed_url(absolute_url):
                discovered_urls.append(absolute_url)

        return discovered_urls

    def is_allowed_url(self, url: str) -> bool:
        """Return whether the URL is within the allowed crawl scope."""

        parsed_url = urlparse(self._canonicalise_url(url))
        if parsed_url.netloc != self.base_domain:
            return False

        path = parsed_url.path or "/"
        if QUOTE_PAGE_PATTERN.fullmatch(path):
            return True
        return False

    def _parse_quote_page(self, url: str, soup: BeautifulSoup) -> CrawledPage | None:
        quote_blocks: list[str] = []

        for quote in soup.select("div.quote"):
            quote_text = quote.select_one("span.text")
            author = quote.select_one("small.author")
            tags = [tag.get_text(strip=True) for tag in quote.select("div.tags a.tag")]

            parts = []
            if quote_text is not None:
                parts.append(quote_text.get_text(" ", strip=True))
            if author is not None:
                parts.append(author.get_text(" ", strip=True))
            if tags:
                parts.append(" ".join(tags))

            block = " ".join(part for part in parts if part).strip()
            if block:
                quote_blocks.append(block)

        if not quote_blocks:
            return None

        title = self._extract_title(soup)
        content = "\n".join(quote_blocks)
        return CrawledPage(url=url, title=title, page_type="quote_listing", content=content)

    def _extract_title(self, soup: BeautifulSoup) -> str:
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        heading = soup.select_one("h1, h2, h3")
        if heading is not None:
            return heading.get_text(" ", strip=True)

        return "Untitled page"

    def _enforce_politeness_window(self) -> None:
        if self._last_request_started_at is None:
            return

        elapsed = self.clock() - self._last_request_started_at
        remaining = self.politeness_window - elapsed
        if remaining > 0:
            self.sleep_func(remaining)

    def _canonicalise_url(self, url: str) -> str:
        parsed_url = urlparse(url)
        path = parsed_url.path or "/"
        if path in {"/page/1", "/page/1/"}:
            path = "/"
        canonical = parsed_url._replace(query="", fragment="", path=path)
        return urlunparse(canonical)

    def _is_quote_page(self, url: str) -> bool:
        path = urlparse(url).path or "/"
        return QUOTE_PAGE_PATTERN.fullmatch(path) is not None
