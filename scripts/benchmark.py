"""Small benchmark for loading and querying the saved quote index."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import sys
import time
from typing import TypeVar


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.search import find_pages, load_index


INDEX_PATH = PROJECT_ROOT / "data" / "index.json"
QUERIES = ["indifference", "good friends", "life love", "missing word"]
T = TypeVar("T")


def time_call(function: Callable[..., T], *arguments: object) -> tuple[T, float]:
    """Return a function result together with its elapsed runtime."""

    start = time.perf_counter()
    result = function(*arguments)
    elapsed = time.perf_counter() - start
    return result, elapsed


def main() -> int:
    index_data, load_time = time_call(load_index, INDEX_PATH)
    metadata = index_data["metadata"]

    print("Quote Search Tool benchmark")
    print(f"Index: {metadata['page_count']} pages, {metadata['term_count']} terms")
    print(f"Load time: {load_time:.6f}s")

    for query in QUERIES:
        results, query_time = time_call(find_pages, index_data, query)
        print(f"Query {query!r}: {len(results)} result(s), {query_time:.6f}s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
