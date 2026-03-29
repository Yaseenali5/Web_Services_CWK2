"""Tests for persistence helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.crawler import CrawledPage
from src.indexer import build_inverted_index
from src.search import load_index, save_index


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
