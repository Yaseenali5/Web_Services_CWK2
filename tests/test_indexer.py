"""Tests for indexer text normalisation and tokenisation."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.crawler import CrawledPage
from src.indexer import build_inverted_index, normalise_text, tokenise


def test_tokenise_is_case_insensitive_and_handles_apostrophes() -> None:
    tokens = tokenise("Good, good FRIENDS don't hide.")

    assert tokens == ["good", "good", "friends", "don't", "hide"]


def test_normalise_text_handles_unicode_quotes_and_case() -> None:
    normalised = normalise_text("“It’s ONLY Words.”")

    assert normalised == '“it\'s only words.”'


def test_build_inverted_index_records_frequency_and_positions() -> None:
    pages = [
        CrawledPage(
            url="https://quotes.toscrape.com/",
            title="Quotes to Scrape",
            page_type="quote_listing",
            content="Good friends good books",
        )
    ]

    index_data = build_inverted_index(pages)
    postings = index_data["index"]["good"]["https://quotes.toscrape.com/"]

    assert postings["frequency"] == 2
    assert postings["positions"] == [0, 2]
    assert index_data["pages"]["https://quotes.toscrape.com/"]["token_count"] == 4


def test_build_inverted_index_adds_metadata() -> None:
    pages = [
        CrawledPage(
            url="https://quotes.toscrape.com/",
            title="Quotes to Scrape",
            page_type="quote_listing",
            content="Good friends",
        ),
        CrawledPage(
            url="https://quotes.toscrape.com/page/2/",
            title="Quotes to Scrape",
            page_type="quote_listing",
            content="Indifference",
        ),
    ]

    index_data = build_inverted_index(pages)

    assert index_data["metadata"]["page_count"] == 2
    assert index_data["metadata"]["term_count"] == 3
    assert index_data["metadata"]["source_site"] == "https://quotes.toscrape.com/"
