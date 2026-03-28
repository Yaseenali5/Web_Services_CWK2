"""Indexing logic for the coursework search tool."""

from __future__ import annotations

import re
import unicodedata


TOKEN_PATTERN = re.compile(r"[^\W_]+(?:'[^\W_]+)*", re.UNICODE)


def normalise_text(text: str) -> str:
    """Normalise text before tokenisation."""

    normalised = unicodedata.normalize("NFKC", text)
    return normalised.replace("’", "'").replace("‘", "'").lower()


def tokenise(text: str) -> list[str]:
    """Split text into searchable terms."""

    return TOKEN_PATTERN.findall(normalise_text(text))
