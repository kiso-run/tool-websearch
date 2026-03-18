# tool-websearch — Development Plan

## Overview

Web search tool for kiso with Brave and Serper backends. Accepts a query via
stdin (JSON), calls the configured search API, and prints formatted results to
stdout.

## Architecture

- **`run.py`** — single-file tool: `main()`, `load_config()`, `search_brave()`,
  `search_serper()`, `format_results()`.
- **`config.toml`** — backend selection (`brave` or `serper`).
- **httpx** — HTTP client for API calls (timeout 30s).
- Input/output follows the kiso tool protocol (JSON on stdin, text on stdout,
  diagnostics on stderr).

## Capabilities

| Function         | Description                                      |
|------------------|--------------------------------------------------|
| `search_brave`   | Query Brave Search API, return structured results |
| `search_serper`  | Query Google via Serper API, return structured results |
| `format_results` | Render result list as numbered text output        |
| `load_config`    | Read `config.toml` for backend selection          |
| `main`           | Entry point: parse input, route to backend, handle errors |

## Milestones

### M1 — Brave search backend

- [x] `search_brave` with query, max_results, language, country params
- [x] Brave API headers (Accept, Accept-Encoding, X-Subscription-Token)
- [x] Parse `web.results` from response JSON
- [x] HTTP error propagation via `raise_for_status`

### M2 — Serper search backend

- [x] `search_serper` with query, max_results, language, country params
- [x] Serper API headers (Content-Type, X-API-KEY)
- [x] Language/country lowercased for Serper (`hl`, `gl`)
- [x] Parse `organic` results only (ignore knowledgeGraph, etc.)

### M3 — Config + main entry point

- [x] `load_config` reads `config.toml` from tool directory
- [x] Default to `brave` backend when no config file exists
- [x] `main()` reads JSON from stdin, routes to backend
- [x] `max_results` capped at 100
- [x] Missing API key detection with user/debug messages
- [x] Unknown backend error handling
- [x] SIGTERM handler for clean shutdown

### M4 — Test suite

- [x] `test_brave.py` — success, empty, missing web key, HTTP errors, param passing
- [x] `test_serper.py` — success, empty, missing organic key, HTTP errors, param casing
- [x] `test_formatting.py` — numbered output, multiline snippets, special chars, empty
- [x] `test_main.py` — missing API key, unknown backend, max_results capping
- [x] `test_config.py` — default backend, TOML parsing, extra keys

### M5 — Complete test coverage

- [x] `test_error_handling.py` — timeout and network error paths in `main()`
- [x] `test_formatting.py` — snippet with blank lines
- [x] Verify all error paths exit 1 with correct stdout/stderr messages
- [x] Both backends tested for timeout and network errors
