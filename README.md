# Coursework Search Tool

This project implements a command-line search tool for `https://quotes.toscrape.com/`. It crawls the paginated quote listing pages of the site, builds a case-insensitive inverted index with per-word statistics, saves that index to disk and supports keyword search through an interactive shell.

# Project Overview

The purpose of the project is to demonstrate the main stages of a small search engine: crawling web pages, extracting text, building an inverted index, storing the index, and querying it from a command-line interface.

The application is split into focused modules:

- `src/crawler.py` crawls quote pages, respects the 6-second politeness window and extracts structured page content
- `src/indexer.py` normalises text and builds the inverted index
- `src/search.py` handles index persistence and query processing
- `src/main.py` provides the command-line shell

The index stores:

- page metadata for each crawled URL
- term frequency for each word on each page
- term positions for each word on each page
- build metadata such as page count and term count

# Features

- Polite crawling with at least 6 seconds between successive requests
- Case-insensitive tokenisation and search
- Inverted index with frequency and position statistics
- JSON save/load support through `data/index.json`
- Single-word lookup with `print <word>`
- Multi-word AND search with deterministic ranking via `find <query>`

# Design Decisions

The crawler focuses on the paginated quote listing pages rather than every internal link on the site. This keeps the searchable corpus focused on the main quote content and avoids indexing duplicate tag pages, login pages or utility pages that would add noise to the search results.

The crawler stores each fetched page as a structured record containing the URL, page title, page type and extracted text. The indexer then tokenises this extracted text and builds a nested dictionary:

```text
term -> page URL -> frequency and positions
```

This structure is efficient for the required commands. `print <word>` can directly look up one term, while `find <query>` can retrieve the posting lists for each query term and intersect the page URLs to implement multi-word AND search.

Search results are ranked using term frequency with a proximity bonus for multi-word queries. Frequency rewards pages where the query terms appear more often, while proximity uses the stored positions to prefer pages where the query words appear close together.

# Complexity Notes

- Crawling is linear in the number of allowed pages visited.
- Index construction is linear in the number of tokens extracted from the crawled pages.
- Single-word lookup is a dictionary lookup for the term plus the cost of printing its postings.
- Multi-word search intersects posting lists for the query terms, so it scales with the size of those postings rather than scanning every page.
- Proximity scoring uses stored word positions, avoiding the need to re-tokenise page text at query time.

# Limitations and Future Improvements

- The crawler is deliberately scoped to quote listing pages to keep the corpus focused and the demo simpler.
- The search does not currently use stemming or lemmatisation, so related forms such as `friend` and `friends` are treated as different terms.
- The query language uses AND semantics for multi-word queries but does not include explicit phrase syntax.
- Future improvements could include TF-IDF ranking, phrase search, query suggestions or a larger benchmark corpus.

# Installation and Setup

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

# Usage

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

Examples for the four required commands:

```text
> build
Index built successfully: 10 pages, 847 unique terms, saved to data/index.json

> load
Index loaded successfully: 10 pages and 847 unique terms.

> print nonsense
Inverted index for 'nonsense':
- Quotes to Scrape | https://quotes.toscrape.com/page/2/ | frequency=1 | positions=[398]

> find good friends
Found 2 matching page(s):
1. Quotes to Scrape | https://quotes.toscrape.com/page/2/ | score=11.500 | total frequency=11, proximity span=1
```

You can also run a single command directly:

```bash
.venv/bin/python -m src.main help
.venv/bin/python -m src.main load
```

# Testing

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

The repository also includes a GitHub Actions workflow that installs the dependencies and runs `pytest` on every push and pull request.

# Benchmarking

Run the lightweight benchmark with:

```bash
.venv/bin/python scripts/benchmark.py
```

The benchmark loads the saved index and times a small set of representative queries. It avoids live crawling so the required 6-second politeness delay does not dominate the timing results.

# Dependencies

Install all dependencies with:

```bash
pip install -r requirements.txt
```

The project uses:

- `requests` for HTTP requests
- `beautifulsoup4` for HTML parsing
- `pytest` for automated testing
