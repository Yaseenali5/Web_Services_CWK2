"""Persistence helpers for the coursework search tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def save_index(index_data: dict[str, Any], destination: str | Path) -> None:
    """Persist the inverted index as JSON."""

    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text(json.dumps(index_data, indent=2, sort_keys=True), encoding="utf-8")


def load_index(source: str | Path) -> dict[str, Any]:
    """Load a previously saved inverted index from disk."""

    source_path = Path(source)
    return json.loads(source_path.read_text(encoding="utf-8"))
