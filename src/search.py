"""Persistence and search helpers for the quote search tool."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import difflib
import json
import math
import re

from src.indexer import tokenise


QUERY_COMPONENT_PATTERN = re.compile(r'"([^"]+)"|(\S+)')


@dataclass(slots=True)
class SearchResult:
    """A ranked search result."""

    url: str
    title: str
    score: float
    total_frequency: int
    matched_terms: list[str]
    proximity_span: int | None


@dataclass(slots=True)
class QueryPlan:
    """Normalised query terms plus any quoted phrases to enforce."""

    terms: list[str]
    phrases: list[tuple[str, ...]]


def save_index(index_data: dict[str, Any], destination: str | Path) -> None:
    """Persist the inverted index as JSON."""

    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text(json.dumps(index_data, indent=2, sort_keys=True), encoding="utf-8")


def load_index(source: str | Path) -> dict[str, Any]:
    """Load a previously saved inverted index from disk."""

    source_path = Path(source)
    return json.loads(source_path.read_text(encoding="utf-8"))


def normalise_single_term(raw_term: str) -> str:
    """Convert user input into exactly one searchable term."""

    terms = tokenise(raw_term)
    if len(terms) != 1:
        raise ValueError("Please provide exactly one searchable word")
    return terms[0]


def get_word_postings(index_data: dict[str, Any], raw_term: str) -> tuple[str, dict[str, Any]]:
    """Return the postings list for a single term."""

    term = normalise_single_term(raw_term)
    postings = index_data.get("index", {}).get(term, {})
    return term, postings


def find_pages(index_data: dict[str, Any], query: str) -> list[SearchResult]:
    """Return ranked pages that contain every term in the query."""

    query_plan = _parse_query(query)
    terms = query_plan.terms
    if not terms:
        raise ValueError("Query cannot be empty")

    term_postings = []
    for term in terms:
        postings = index_data.get("index", {}).get(term, {})
        if not postings:
            return []
        term_postings.append((term, postings))

    matching_urls = set(term_postings[0][1].keys())
    for _, postings in term_postings[1:]:
        # Multi-word queries use AND semantics by intersecting posting lists.
        matching_urls &= set(postings.keys())

    pages = index_data.get("pages", {})
    postings_by_term = dict(term_postings)
    results: list[SearchResult] = []

    for url in matching_urls:
        if not _matches_required_phrases(url, query_plan.phrases, postings_by_term):
            continue

        total_frequency = sum(postings[url]["frequency"] for _, postings in term_postings)
        tf_idf_score = sum(
            _tf_idf_score(
                term_frequency=postings[url]["frequency"],
                document_frequency=len(postings),
                total_pages=len(pages),
            )
            for _, postings in term_postings
        )
        position_lists = [postings[url]["positions"] for _, postings in term_postings]
        proximity_span = _minimum_window_span(position_lists) if len(position_lists) > 1 else None
        proximity_bonus = 0.0 if proximity_span is None else 1.0 / (1.0 + proximity_span)
        score = tf_idf_score + proximity_bonus

        results.append(
            SearchResult(
                url=url,
                title=pages.get(url, {}).get("title", "Untitled page"),
                score=score,
                total_frequency=total_frequency,
                matched_terms=terms,
                proximity_span=proximity_span,
            )
        )

    return sorted(results, key=lambda result: (-result.score, result.title.lower(), result.url))


def suggest_terms(index_data: dict[str, Any], query: str, limit: int = 3) -> list[str]:
    """Suggest close vocabulary terms for query words that are not in the index."""

    if limit <= 0:
        return []

    index = index_data.get("index", {})
    vocabulary = list(index.keys())
    suggestions: list[str] = []

    for term in _parse_query(query).terms:
        if term in index:
            continue

        for suggestion in difflib.get_close_matches(term, vocabulary, n=limit, cutoff=0.90):
            if suggestion not in suggestions:
                suggestions.append(suggestion)
            if len(suggestions) >= limit:
                return suggestions

    return suggestions


def _tf_idf_score(term_frequency: int, document_frequency: int, total_pages: int) -> float:
    """Calculate a smoothed TF-IDF score component."""

    if total_pages <= 0 or document_frequency <= 0:
        return 0.0

    inverse_document_frequency = math.log((1 + total_pages) / (1 + document_frequency)) + 1
    return term_frequency * inverse_document_frequency


def _parse_query(query: str) -> QueryPlan:
    seen_terms: set[str] = set()
    unique_terms: list[str] = []
    phrases: list[tuple[str, ...]] = []

    for match in QUERY_COMPONENT_PATTERN.finditer(query):
        quoted_text = match.group(1)
        component_text = quoted_text if quoted_text is not None else match.group(2)
        component_terms = tokenise(component_text or "")
        if not component_terms:
            continue

        if quoted_text is not None and len(component_terms) > 1:
            phrases.append(tuple(component_terms))

        for term in component_terms:
            if term in seen_terms:
                continue
            seen_terms.add(term)
            unique_terms.append(term)

    return QueryPlan(terms=unique_terms, phrases=phrases)


def _matches_required_phrases(
    url: str,
    phrases: list[tuple[str, ...]],
    postings_by_term: dict[str, dict[str, Any]],
) -> bool:
    for phrase in phrases:
        position_lists = [postings_by_term[term][url]["positions"] for term in phrase]
        if not _contains_exact_phrase(position_lists):
            return False

    return True


def _contains_exact_phrase(position_lists: list[list[int]]) -> bool:
    if not position_lists:
        return False

    candidate_starts = set(position_lists[0])
    for offset, positions in enumerate(position_lists[1:], start=1):
        position_set = set(positions)
        candidate_starts = {start for start in candidate_starts if start + offset in position_set}
        if not candidate_starts:
            return False

    return True


def _minimum_window_span(position_lists: list[list[int]]) -> int | None:
    if not position_lists:
        return None

    pointers = [0 for _ in position_lists]
    best_span: int | None = None

    # Walk the sorted position lists to find the tightest span containing all query terms.
    while True:
        current_positions = [positions[pointer] for positions, pointer in zip(position_lists, pointers)]
        current_min = min(current_positions)
        current_max = max(current_positions)
        span = current_max - current_min

        if best_span is None or span < best_span:
            best_span = span

        list_index = current_positions.index(current_min)
        pointers[list_index] += 1
        if pointers[list_index] >= len(position_lists[list_index]):
            break

    return best_span
