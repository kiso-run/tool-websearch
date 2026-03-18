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

### M6 — Functional tests (subprocess contract)

**Problem:** `test_main.py` already has good coverage of error paths via
subprocess (missing API key, unknown backend, max_results capping), and
`test_error_handling.py` covers timeout/network errors. However, no test
exercises a **successful search flow** end-to-end through the subprocess
protocol with mocked HTTP responses.

**Files:** `tests/test_functional.py` (new)

**Change:**

1. **Happy path — brave search:**
   - stdin: `{args: {query: "python async", max_results: 3}, ...}`
   - Mock `httpx.get` to return brave response
   - Assert: stdout contains numbered results, exit code 0

2. **Happy path — serper search:**
   - Set config backend to "serper"
   - Mock `httpx.post` to return serper response
   - Assert: stdout contains numbered results, exit code 0

3. **Happy path — with language/country:**
   - Verify params forwarded correctly in mocked call

4. **Empty results — brave:**
   - Mock returns `{web: {results: []}}`
   - Assert: stdout contains `No results found`, exit code 0

5. **Empty results — serper:**
   - Mock returns `{organic: []}`
   - Assert: stdout contains `No results found`, exit code 0

6. **Malformed input — invalid JSON:**
   - Send `"not json"` on stdin
   - Assert: exit code 1

7. **Malformed input — missing query key:**
   - stdin: `{args: {}}`
   - Assert: exit code 1 (KeyError on `args["query"]`)

- [x] Implement functional test file
- [x] All 7 tests pass
- [x] Total test count verified

---

### M7 — SIGTERM graceful shutdown test

**Problem:** `run.py` registers a SIGTERM handler but no test verifies
the process exits cleanly on SIGTERM during an HTTP request.

**Files:** `tests/test_functional.py` (add)

**Change:**

1. Start `run.py` as subprocess with mock HTTP that delays 10s
2. Send SIGTERM after 0.5s
3. Assert: process exits 0

- [x] Implement SIGTERM test
- [x] Passes on Linux

---

### M8 — Brave response edge cases

**Problem:** Unit tests don't cover all Brave API response shapes:
missing `web` key entirely, `web` without `results` key.

**Files:** `tests/test_brave.py` (add)

**Change:**

1. `search_brave` with response `{}` (no `web` key) → returns empty list
2. `search_brave` with response `{web: {}}` (no `results` key) → returns empty list
3. `search_brave` without language/country → params dict must NOT contain
   `search_lang` or `country` keys

- [x] Add 3 edge case tests
- [x] All tests pass

---

## Milestone Checklist

- [x] **M1** — Brave search backend
- [x] **M2** — Serper search backend
- [x] **M3** — Config + main entry point
- [x] **M4** — Test suite
- [x] **M5** — Complete test coverage
- [x] **M6** — Functional tests (subprocess contract)
- [x] **M7** — SIGTERM graceful shutdown test
- [x] **M8** — Brave response edge cases
- [ ] **M9** — kiso.toml validation test
- [ ] **M10** — Config error handling

### M9 — kiso.toml validation test

**Problem:** No test verifies `kiso.toml` consistency with code.

**Files:** `tests/test_manifest.py` (new)

**Change:**

1. Parse `kiso.toml`, extract declared arg names
2. Verify each appears in `run.py`
3. Verify TOML structure

- [ ] Implement manifest validation test

---

### M10 — Config error handling: malformed TOML

**Problem:** `load_config()` reads config.toml but doesn't test malformed files.

**Files:** `tests/test_config.py` (add)

**Change:**

1. Create malformed config.toml, call `load_config()` — verify it raises or handles gracefully
2. Config with unknown backend key — verify `main()` catches it

- [ ] Implement config error tests
