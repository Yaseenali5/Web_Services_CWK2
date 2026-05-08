"""Tests for the crawler module."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.crawler import WebsiteCrawler


HOME_URL = "https://quotes.toscrape.com/"
PAGE_2_URL = "https://quotes.toscrape.com/page/2/"
PAGE_1_ALIAS_URL = "https://quotes.toscrape.com/page/1/"
AUTHOR_URL = "https://quotes.toscrape.com/author/Albert-Einstein"

HOME_HTML = """
<html>
  <head><title>Quotes to Scrape</title></head>
  <body>
    <div class="quote">
      <span class="text">“Good friends, good books.”</span>
      <small class="author">Mark Twain</small>
      <div class="tags"><a class="tag">friends</a><a class="tag">books</a></div>
    </div>
    <a href="/page/2/">Next</a>
    <a href="/author/Mark-Twain">about</a>
    <a href="/tag/friends/">friends</a>
  </body>
</html>
"""

PAGE_2_HTML = """
<html>
  <head><title>Quotes to Scrape</title></head>
  <body>
    <div class="quote">
      <span class="text">“I like nonsense.”</span>
      <small class="author">Dr. Seuss</small>
      <div class="tags"><a class="tag">fantasy</a></div>
    </div>
    <a href="/">Previous</a>
  </body>
</html>
"""


@dataclass
class FakeResponse:
    text: str
    status_code: int = 200

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses: dict[str, FakeResponse | Exception]) -> None:
        self.responses = responses
        self.headers: dict[str, str] = {}
        self.requested_urls: list[str] = []

    def get(self, url: str, timeout: float) -> FakeResponse:
        self.requested_urls.append(url)
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return response


class FakeClock:
    def __init__(self) -> None:
        self.current = 0.0
        self.sleep_calls: list[float] = []

    def now(self) -> float:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.sleep_calls.append(seconds)
        self.current += seconds


def test_is_allowed_url_limits_crawl_scope() -> None:
    crawler = WebsiteCrawler()

    assert crawler.is_allowed_url(HOME_URL)
    assert crawler.is_allowed_url(PAGE_2_URL)
    assert not crawler.is_allowed_url("https://quotes.toscrape.com/tag/friends/")
    assert not crawler.is_allowed_url(AUTHOR_URL)


def test_parse_document_extracts_quote_text_and_allowed_links() -> None:
    crawler = WebsiteCrawler()

    parsed_document = crawler.parse_document(HOME_URL, HOME_HTML)

    assert parsed_document.page is not None
    assert parsed_document.page.page_type == "quote_listing"
    assert "mark twain" in parsed_document.page.content.lower()
    assert "friends books" in parsed_document.page.content.lower()
    assert parsed_document.links == [PAGE_2_URL]


def test_page_one_alias_canonicalises_to_home_url() -> None:
    crawler = WebsiteCrawler()

    assert crawler._canonicalise_url(PAGE_1_ALIAS_URL) == HOME_URL


def test_fetch_html_respects_politeness_window() -> None:
    fake_clock = FakeClock()
    fake_session = FakeSession(
        {
            HOME_URL: FakeResponse(HOME_HTML),
            PAGE_2_URL: FakeResponse(PAGE_2_HTML),
        }
    )
    crawler = WebsiteCrawler(
        session=fake_session,
        sleep_func=fake_clock.sleep,
        clock=fake_clock.now,
    )

    first_html = crawler.fetch_html(HOME_URL)
    second_html = crawler.fetch_html(PAGE_2_URL)

    assert first_html is not None
    assert second_html is not None
    assert fake_clock.sleep_calls == [6.0]


def test_fetch_html_handles_request_failure_gracefully() -> None:
    fake_session = FakeSession({HOME_URL: requests.RequestException("boom")})
    crawler = WebsiteCrawler(session=fake_session)

    assert crawler.fetch_html(HOME_URL) is None


def test_failed_requests_still_count_for_politeness_window() -> None:
    fake_clock = FakeClock()
    fake_session = FakeSession(
        {
            HOME_URL: requests.RequestException("boom"),
            PAGE_2_URL: FakeResponse(PAGE_2_HTML),
        }
    )
    crawler = WebsiteCrawler(
        session=fake_session,
        sleep_func=fake_clock.sleep,
        clock=fake_clock.now,
    )

    failed_html = crawler.fetch_html(HOME_URL)
    successful_html = crawler.fetch_html(PAGE_2_URL)

    assert failed_html is None
    assert successful_html is not None
    assert fake_clock.sleep_calls == [6.0]


def test_crawl_visits_each_allowed_page_once() -> None:
    fake_session = FakeSession(
        {
            HOME_URL: FakeResponse(HOME_HTML),
            PAGE_2_URL: FakeResponse(PAGE_2_HTML),
        }
    )
    crawler = WebsiteCrawler(
        session=fake_session,
        politeness_window=0.0,
    )

    pages = crawler.crawl()

    assert [page.url for page in pages] == [HOME_URL, PAGE_2_URL]
    assert fake_session.requested_urls == [HOME_URL, PAGE_2_URL]
