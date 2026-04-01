"""Tests for the command-line shell behavior."""

from __future__ import annotations

from pathlib import Path

import src.main as main_module
from src.crawler import CrawledPage
from src.main import SearchShell
from src.search import SearchResult


def test_run_command_reports_unknown_command(tmp_path: Path, capsys) -> None:
    shell = SearchShell(index_path=tmp_path / "index.json")

    keep_running = shell.run_command("unknown")

    captured = capsys.readouterr()
    assert keep_running is True
    assert "Unknown command: unknown" in captured.out


def test_load_reports_missing_saved_index(tmp_path: Path, capsys) -> None:
    shell = SearchShell(index_path=tmp_path / "missing.json")

    shell.run_command("load")

    captured = capsys.readouterr()
    assert "No saved index found" in captured.out


def test_build_command_uses_crawler_indexer_and_persistence(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    crawl_calls: list[float] = []
    indexed_pages: list[list[CrawledPage]] = []
    saved_payloads: list[tuple[dict, Path]] = []
    crawled_pages = [
        CrawledPage(
            url="https://quotes.toscrape.com/",
            title="Quotes to Scrape",
            page_type="quote_listing",
            content="good friends",
        )
    ]
    built_index = {
        "metadata": {"page_count": 1, "term_count": 2},
        "pages": {},
        "index": {},
    }

    class FakeCrawler:
        def __init__(self, politeness_window: float) -> None:
            crawl_calls.append(politeness_window)

        def crawl(self) -> list[CrawledPage]:
            return crawled_pages

    def fake_build_inverted_index(pages: list[CrawledPage]) -> dict:
        indexed_pages.append(pages)
        return built_index

    def fake_save_index(index_data: dict, destination: Path) -> None:
        saved_payloads.append((index_data, destination))

    monkeypatch.setattr(main_module, "WebsiteCrawler", FakeCrawler)
    monkeypatch.setattr(main_module, "build_inverted_index", fake_build_inverted_index)
    monkeypatch.setattr(main_module, "save_index", fake_save_index)

    index_path = tmp_path / "index.json"
    shell = SearchShell(index_path=index_path)

    shell.run_command("build")

    captured = capsys.readouterr()
    assert crawl_calls == [6.0]
    assert indexed_pages == [crawled_pages]
    assert saved_payloads == [(built_index, index_path)]
    assert shell.index_data == built_index
    assert "Index built successfully: 1 pages, 2 unique terms" in captured.out


def test_print_command_formats_matching_postings(tmp_path: Path, capsys) -> None:
    shell = SearchShell(index_path=tmp_path / "index.json")
    shell.index_data = {
        "pages": {
            "https://quotes.toscrape.com/": {
                "title": "Quotes to Scrape",
            }
        },
        "index": {
            "good": {
                "https://quotes.toscrape.com/": {
                    "frequency": 2,
                    "positions": [0, 2],
                }
            }
        },
    }

    shell.run_command("print good")

    captured = capsys.readouterr()
    assert "Inverted index for 'good':" in captured.out
    assert "frequency=2" in captured.out
    assert "positions=[0, 2]" in captured.out


def test_find_command_formats_ranked_results(tmp_path: Path, monkeypatch, capsys) -> None:
    shell = SearchShell(index_path=tmp_path / "index.json")
    shell.index_data = {"pages": {}, "index": {}}

    def fake_find_pages(index_data: dict, query: str) -> list[SearchResult]:
        assert query == "good friends"
        assert index_data == shell.index_data
        return [
            SearchResult(
                url="https://quotes.toscrape.com/",
                title="Quotes to Scrape",
                score=3.5,
                total_frequency=3,
                matched_terms=["good", "friends"],
                proximity_span=1,
            )
        ]

    monkeypatch.setattr(main_module, "find_pages", fake_find_pages)

    shell.run_command("find good friends")

    captured = capsys.readouterr()
    assert "Found 1 matching page(s):" in captured.out
    assert "score=3.500" in captured.out
    assert "proximity span=1" in captured.out
