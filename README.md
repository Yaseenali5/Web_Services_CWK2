# Coursework Search Tool

This project implements a command-line search tool for `https://quotes.toscrape.com/`. It crawls the paginated quote listing pages of the site, builds a case-insensitive inverted index with per-word statistics, saves that index to disk, and supports keyword search through an interactive shell.

## Project Overview

The application is split into focused modules:

- `src/crawler.py` crawls quote pages, respects the 6-second politeness window, and extracts structured page content.
- `src/indexer.py` normalises text and builds the inverted index.
- `src/search.py` handles index persistence and query processing.
- `src/main.py` provides the command-line shell.

The index stores:

- page metadata for each crawled URL
- term frequency for each word on each page
- term positions for each word on each page
- build metadata such as page count and term count

## Features

- Polite crawling with at least 6 seconds between successive requests
- Case-insensitive tokenisation and search
- Inverted index with frequency and position statistics
- JSON save/load support through `data/index.json`
- Single-word lookup with `print <word>`
- Multi-word AND search with deterministic ranking via `find <query>`

## Setup

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the interactive shell:

```bash
.venv/bin/python -m src.main
```

Available commands:

- `build` crawls the website, builds the inverted index, and saves it to `data/index.json`
- `load` loads the saved index from disk.
- `print <word>` shows the inverted-index postings for one word
- `find <query>` returns the pages that contain all terms in the query
- `help` lists the available commands
- `exit` closes the shell

Example session:

```text
> build
> print nonsense
> find indifference
> find good friends
> exit
```

You can also run a single command directly:

```bash
.venv/bin/python -m src.main help
.venv/bin/python -m src.main load
```

## Testing

Run the test suite with:

```bash
.venv/bin/pytest
```

The tests cover:

- crawl scope rules
- politeness-window behaviour
- HTML parsing
- inverted-index statistics
- JSON save/load persistence
- single-word lookup
- multi-word query processing
- CLI command behaviour and user-facing error messages

## Dependencies

- `requests`
- `beautifulsoup4`
- `pytest`
