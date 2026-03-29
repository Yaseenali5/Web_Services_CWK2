"""Persistence and single-word lookup helpers for the coursework search tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from src.indexer import tokenise


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
        raise ValueError("Please provide exactly one searchable word.")
    return terms[0]


def get_word_postings(index_data: dict[str, Any], raw_term: str) -> tuple[str, dict[str, Any]]:
    """Return the postings list for a single term."""

    term = normalise_single_term(raw_term)
    postings = index_data.get("index", {}).get(term, {})
    return term, postings
