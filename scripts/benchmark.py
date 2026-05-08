"""Small benchmark for loading and querying the saved quote index."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from statistics import mean
import sys
import time
from typing import TypeVar


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.search import find_pages, load_index, suggest_terms


INDEX_PATH = PROJECT_ROOT / "data" / "index.json"
QUERIES = ["indifference", "good friends", '"good friends"', "life love", "frends", "missing word"]
QUERY_RUNS = 100
T = TypeVar("T")


def time_call(function: Callable[..., T], *arguments: object) -> tuple[T, float]:
    """Return a function result together with its elapsed runtime."""

    start = time.perf_counter()
    result = function(*arguments)
    elapsed = time.perf_counter() - start
    return result, elapsed


def time_repeated(function: Callable[..., T], runs: int, *arguments: object) -> tuple[T, list[float]]:
    """Time repeated calls and return the first result plus all timings."""

    timings: list[float] = []
    first_result: T | None = None

    for run_number in range(runs):
        result, elapsed = time_call(function, *arguments)
        timings.append(elapsed)
        if run_number == 0:
            first_result = result

    if first_result is None:
        raise ValueError("runs must be at least 1")

    return first_result, timings


def main() -> int:
    index_data, load_time = time_call(load_index, INDEX_PATH)
    metadata = index_data["metadata"]

    print("Quote Search Tool benchmark")
    print(f"Index: {metadata['page_count']} pages, {metadata['term_count']} terms")
    print(f"Load time: {load_time:.6f}s")
    print(f"Query timings: average/min/max over {QUERY_RUNS} runs")

    for query in QUERIES:
        results, query_timings = time_repeated(find_pages, QUERY_RUNS, index_data, query)
        print(
            f"Query {query!r}: {len(results)} result(s), "
            f"avg={mean(query_timings):.6f}s, min={min(query_timings):.6f}s, "
            f"max={max(query_timings):.6f}s"
        )
        if results:
            print(f"  top result: {results[0].url} score={results[0].score:.3f}")
        else:
            suggestions = suggest_terms(index_data, query)
            if suggestions:
                print(f"  suggestions: {', '.join(suggestions)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
