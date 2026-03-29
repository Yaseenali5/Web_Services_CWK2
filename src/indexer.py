"""Indexing logic for the coursework search tool."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable
import re
import unicodedata

from src.crawler import CrawledPage


TOKEN_PATTERN = re.compile(r"[^\W_]+(?:'[^\W_]+)*", re.UNICODE)


def normalise_text(text: str) -> str:
    """Normalise text before tokenisation."""

    normalised = unicodedata.normalize("NFKC", text)
    return normalised.replace("’", "'").replace("‘", "'").lower()


def tokenise(text: str) -> list[str]:
    """Split text into searchable terms."""

    return TOKEN_PATTERN.findall(normalise_text(text))


def build_inverted_index(
    pages: Iterable[CrawledPage],
    source_site: str = "https://quotes.toscrape.com/",
) -> dict[str, Any]:
    """Build an inverted index with frequency and positions for each word."""

    index: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    page_metadata: dict[str, dict[str, Any]] = {}
    page_count = 0

    for page in pages:
        tokens = tokenise(page.content)
        page_metadata[page.url] = {
            "title": page.title,
            "page_type": page.page_type,
            "token_count": len(tokens),
        }

        page_term_positions: dict[str, list[int]] = defaultdict(list)
        for position, token in enumerate(tokens):
            page_term_positions[token].append(position)

        for token, positions in page_term_positions.items():
            index[token][page.url] = {
                "frequency": len(positions),
                "positions": positions,
            }

        page_count += 1

    final_index = {term: postings for term, postings in sorted(index.items())}
    metadata = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "page_count": page_count,
        "term_count": len(final_index),
        "source_site": source_site,
    }

    return {
        "metadata": metadata,
        "pages": page_metadata,
        "index": final_index,
    }
