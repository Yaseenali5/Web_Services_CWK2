"""Command-line interface for the coursework search tool."""

from __future__ import annotations

from pathlib import Path
import sys

from src.crawler import WebsiteCrawler
from src.indexer import build_inverted_index
from src.search import find_pages, get_word_postings, load_index, save_index


INDEX_PATH = Path(__file__).resolve().parent.parent / "data" / "index.json"


class SearchShell:
    """Interactive shell for building and querying the index."""

    def __init__(self, index_path: Path = INDEX_PATH) -> None:
        self.index_path = index_path
        self.index_data: dict | None = None

    def run_command(self, raw_command: str) -> bool:
        command_line = raw_command.strip()
        if not command_line:
            print("Please enter a command. Type 'help' to see the available options.")
            return True

        command, _, arguments = command_line.partition(" ")
        command = command.lower()
        arguments = arguments.strip()

        handlers = {
            "build": self.handle_build,
            "load": self.handle_load,
            "print": self.handle_print,
            "find": self.handle_find,
            "help": self.handle_help,
            "exit": self.handle_exit,
            "quit": self.handle_exit,
        }

        handler = handlers.get(command)
        if handler is None:
            print(f"Unknown command: {command}. Type 'help' to see the available options.")
            return True

        return handler(arguments)

    def handle_build(self, _: str) -> bool:
        print("Building the search index. This will take around a minute because of the politeness window.")
        crawler = WebsiteCrawler(politeness_window=6.0)
        pages = crawler.crawl()
        if not pages:
            print(
                "Build failed: no pages were crawled. Check your network connection "
                "or the target website availability."
            )
            return True

        self.index_data = build_inverted_index(pages)
        save_index(self.index_data, self.index_path)

        metadata = self.index_data["metadata"]
        print(
            f"Index built successfully: {metadata['page_count']} pages, "
            f"{metadata['term_count']} unique terms, saved to {self.index_path}"
        )
        return True

    def handle_load(self, _: str) -> bool:
        if not self.index_path.exists():
            print(f"No saved index found at {self.index_path}. Run 'build' first.")
            return True

        self.index_data = load_index(self.index_path)
        metadata = self.index_data["metadata"]
        print(
            f"Index loaded successfully: {metadata['page_count']} pages and "
            f"{metadata['term_count']} unique terms."
        )
        return True

    def handle_print(self, arguments: str) -> bool:
        if not self._ensure_index_loaded():
            return True

        if not arguments:
            print("Usage: print <word>")
            return True

        try:
            term, postings = get_word_postings(self.index_data, arguments)
        except ValueError as error:
            print(error)
            return True

        if not postings:
            print(f"No postings found for '{term}'.")
            return True

        print(f"Inverted index for '{term}':")
        for url, stats in sorted(postings.items()):
            page_title = self.index_data["pages"].get(url, {}).get("title", "Untitled page")
            print(
                f"- {page_title} | {url} | frequency={stats['frequency']} | "
                f"positions={stats['positions']}"
            )

        return True

    def handle_find(self, arguments: str) -> bool:
        if not self._ensure_index_loaded():
            return True

        if not arguments:
            print("Query cannot be empty.")
            return True

        try:
            results = find_pages(self.index_data, arguments)
        except ValueError as error:
            print(error)
            return True

        if not results:
            print("No pages matched that query.")
            return True

        print(f"Found {len(results)} matching page(s):")
        for index, result in enumerate(results, start=1):
            proximity_text = (
                f", proximity span={result.proximity_span}" if result.proximity_span is not None else ""
            )
            print(
                f"{index}. {result.title} | {result.url} | score={result.score:.3f} "
                f"| total frequency={result.total_frequency}{proximity_text}"
            )

        return True

    def handle_help(self, _: str) -> bool:
        print("Available commands:")
        print("- build")
        print("- load")
        print("- print <word>")
        print("- find <query>")
        print("- help")
        print("- exit")
        return True

    def handle_exit(self, _: str) -> bool:
        print("Exiting search tool.")
        return False

    def _ensure_index_loaded(self) -> bool:
        if self.index_data is not None:
            return True

        print("No index is currently loaded. Run 'build' or 'load' first.")
        return False


def run_interactive_shell() -> None:
    shell = SearchShell()
    print("Coursework Search Tool")
    print("Type 'help' to see the available commands.")

    while True:
        try:
            keep_running = shell.run_command(input("> "))
        except KeyboardInterrupt:
            print("\nExiting search tool.")
            break
        except EOFError:
            print("\nExiting search tool.")
            break

        if not keep_running:
            break


def run_single_command(arguments: list[str]) -> int:
    shell = SearchShell()
    shell.run_command(" ".join(arguments))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raise SystemExit(run_single_command(sys.argv[1:]))
    run_interactive_shell()
