"""Tests for indexer text normalisation and tokenisation."""

from __future__ import annotations

from src.indexer import normalise_text, tokenise


def test_tokenise_is_case_insensitive_and_handles_apostrophes() -> None:
    tokens = tokenise("Good, good FRIENDS don't hide.")

    assert tokens == ["good", "good", "friends", "don't", "hide"]


def test_normalise_text_handles_unicode_quotes_and_case() -> None:
    normalised = normalise_text("“It’s ONLY Words.”")

    assert normalised == '“it\'s only words.”'
