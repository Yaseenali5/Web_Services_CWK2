"""Tests for persistence and search helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.crawler import CrawledPage
from src.indexer import build_inverted_index
from src.search import find_pages, get_word_postings, load_index, normalise_single_term, save_index


@pytest.fixture
def sample_index() -> dict:
    pages = [
        CrawledPage(
            url="https://quotes.toscrape.com/page/1/",
            title="Quotes to Scrape",
            page_type="quote_listing",
            content="good friends good books",
        ),
        CrawledPage(
            url="https://quotes.toscrape.com/page/2/",
            title="Quotes to Scrape",
            page_type="quote_listing",
            content="good people need friends",
        ),
        CrawledPage(
            url="https://quotes.toscrape.com/page/3/",
            title="Quotes to Scrape",
            page_type="quote_listing",
            content="indifference is painful",
        ),
    ]
    return build_inverted_index(pages)


def test_save_and_load_index_roundtrip(sample_index: dict, tmp_path: Path) -> None:
    destination = tmp_path / "index.json"

    save_index(sample_index, destination)
    loaded_index = load_index(destination)

    assert loaded_index["index"]["good"]["https://quotes.toscrape.com/page/1/"]["frequency"] == 2
    assert loaded_index["metadata"]["page_count"] == 3


def test_save_index_creates_missing_parent_directories(sample_index: dict, tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "path" / "index.json"

    save_index(sample_index, destination)

    assert destination.exists()


def test_get_word_postings_returns_empty_for_missing_word(sample_index: dict) -> None:
    term, postings = get_word_postings(sample_index, "missing")

    assert term == "missing"
    assert postings == {}


def test_normalise_single_term_rejects_multiword_input() -> None:
    with pytest.raises(ValueError, match="exactly one searchable word"):
        normalise_single_term("good friends")


def test_find_pages_uses_and_semantics_for_multiword_queries(sample_index: dict) -> None:
    results = find_pages(sample_index, "good friends")

    assert [result.url for result in results] == [
        "https://quotes.toscrape.com/page/1/",
        "https://quotes.toscrape.com/page/2/",
    ]


def test_find_pages_returns_empty_when_any_term_is_missing(sample_index: dict) -> None:
    assert find_pages(sample_index, "good missing") == []


def test_find_pages_rejects_empty_queries(sample_index: dict) -> None:
    with pytest.raises(ValueError, match="Query cannot be empty"):
        find_pages(sample_index, "   ")
