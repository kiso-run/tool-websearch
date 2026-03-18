"""Functional tests: full main() pipeline with mocked httpx.

Tests exercise the complete code path (stdin → config → backend → format → stdout)
in-process, with httpx mocked to avoid network calls.
"""

import io
import json
import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

import run

ROOT = Path(__file__).parent.parent


def _make_stdin(query="python async", max_results=3, language=None, country=None):
    args = {"query": query, "max_results": max_results}
    if language:
        args["language"] = language
    if country:
        args["country"] = country
    return json.dumps({
        "args": args,
        "session": "test-session",
        "workspace": "/tmp/test-workspace",
        "session_secrets": {},
        "plan_outputs": [],
    })


def _mock_response(data, status_code=200):
    mock = MagicMock(spec=httpx.Response)
    mock.status_code = status_code
    mock.json.return_value = data
    mock.raise_for_status.return_value = None
    return mock


# ---------------------------------------------------------------------------
# M6 — Happy path: Brave
# ---------------------------------------------------------------------------


class TestFunctionalBraveHappy:
    def test_brave_happy_path_returns_numbered_results(self, capsys, brave_response_ok):
        stdin = _make_stdin("python async", max_results=3)
        with patch("sys.stdin", io.StringIO(stdin)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "test-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}), \
             patch("httpx.get", return_value=_mock_response(brave_response_ok)):
            run.main()

        captured = capsys.readouterr()
        assert "1. Python Async Patterns" in captured.out
        assert "2. Asyncio Documentation" in captured.out
        assert "https://example.com/python-async" in captured.out

    def test_brave_happy_path_exit_code_0(self, brave_response_ok):
        stdin = _make_stdin("python async")
        with patch("sys.stdin", io.StringIO(stdin)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "test-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}), \
             patch("httpx.get", return_value=_mock_response(brave_response_ok)):
            # main() should return normally (no SystemExit)
            run.main()


# ---------------------------------------------------------------------------
# M6 — Happy path: Serper
# ---------------------------------------------------------------------------


class TestFunctionalSerperHappy:
    def test_serper_happy_path_returns_numbered_results(self, capsys, serper_response_ok):
        stdin = _make_stdin("python async", max_results=3)
        with patch("sys.stdin", io.StringIO(stdin)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "test-key"}), \
             patch("run.load_config", return_value={"backend": "serper"}), \
             patch("httpx.post", return_value=_mock_response(serper_response_ok)):
            run.main()

        captured = capsys.readouterr()
        assert "1. Python Async Patterns" in captured.out
        assert "2. Asyncio Documentation" in captured.out
        assert "https://example.com/python-async" in captured.out

    def test_serper_happy_path_exit_code_0(self, serper_response_ok):
        stdin = _make_stdin("python async")
        with patch("sys.stdin", io.StringIO(stdin)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "test-key"}), \
             patch("run.load_config", return_value={"backend": "serper"}), \
             patch("httpx.post", return_value=_mock_response(serper_response_ok)):
            run.main()


# ---------------------------------------------------------------------------
# M6 — Happy path with language/country params
# ---------------------------------------------------------------------------


class TestFunctionalWithParams:
    def test_brave_forwards_language_and_country(self, brave_response_ok):
        stdin = _make_stdin("query", language="it", country="IT")
        with patch("sys.stdin", io.StringIO(stdin)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "test-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}), \
             patch("httpx.get", return_value=_mock_response(brave_response_ok)) as mock_get:
            run.main()

        params = mock_get.call_args[1]["params"]
        assert params["search_lang"] == "it"
        assert params["country"] == "IT"

    def test_serper_forwards_language_and_country_lowercased(self, serper_response_ok):
        stdin = _make_stdin("query", language="IT", country="IT")
        with patch("sys.stdin", io.StringIO(stdin)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "test-key"}), \
             patch("run.load_config", return_value={"backend": "serper"}), \
             patch("httpx.post", return_value=_mock_response(serper_response_ok)) as mock_post:
            run.main()

        body = mock_post.call_args[1]["json"]
        assert body["hl"] == "it"
        assert body["gl"] == "it"


# ---------------------------------------------------------------------------
# M6 — Empty results
# ---------------------------------------------------------------------------


class TestFunctionalEmptyResults:
    def test_brave_empty_results(self, capsys, brave_response_empty):
        stdin = _make_stdin("nothing here")
        with patch("sys.stdin", io.StringIO(stdin)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "test-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}), \
             patch("httpx.get", return_value=_mock_response(brave_response_empty)):
            run.main()

        captured = capsys.readouterr()
        assert "No results found" in captured.out

    def test_serper_empty_results(self, capsys, serper_response_empty):
        stdin = _make_stdin("nothing here")
        with patch("sys.stdin", io.StringIO(stdin)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "test-key"}), \
             patch("run.load_config", return_value={"backend": "serper"}), \
             patch("httpx.post", return_value=_mock_response(serper_response_empty)):
            run.main()

        captured = capsys.readouterr()
        assert "No results found" in captured.out


# ---------------------------------------------------------------------------
# M6 — Malformed input
# ---------------------------------------------------------------------------


class TestFunctionalMalformedInput:
    def test_invalid_json_exits_nonzero(self):
        with patch("sys.stdin", io.StringIO("not json at all")):
            with pytest.raises((json.JSONDecodeError, SystemExit)):
                run.main()

    def test_missing_query_key_exits_nonzero(self):
        stdin = json.dumps({
            "args": {},
            "session": "s",
            "workspace": "/tmp",
            "session_secrets": {},
            "plan_outputs": [],
        })
        with patch("sys.stdin", io.StringIO(stdin)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "test-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}):
            with pytest.raises(KeyError):
                run.main()


# ---------------------------------------------------------------------------
# M7 — SIGTERM graceful shutdown
# ---------------------------------------------------------------------------


class TestSIGTERM:
    @pytest.mark.skipif(sys.platform == "win32", reason="SIGTERM not available on Windows")
    def test_sigterm_during_http_exits_cleanly(self):
        """Start run.py as subprocess with a slow mock, send SIGTERM, verify exit 0."""
        # Helper script that patches httpx to block, then runs main()
        helper = textwrap.dedent("""\
            import json, os, sys, time, signal
            from unittest.mock import patch, MagicMock
            import httpx

            # Re-register SIGTERM handler (inherited from run.py module load)
            sys.path.insert(0, os.environ["TOOL_ROOT"])
            import run

            def slow_get(*args, **kwargs):
                time.sleep(30)  # Will be interrupted by SIGTERM
                mock = MagicMock(spec=httpx.Response)
                mock.raise_for_status.return_value = None
                mock.json.return_value = {"web": {"results": []}}
                return mock

            stdin_data = json.dumps({
                "args": {"query": "test"},
                "session": "s",
                "workspace": "/tmp",
                "session_secrets": {},
                "plan_outputs": [],
            })

            with patch("sys.stdin", __import__("io").StringIO(stdin_data)), \\
                 patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "fake-key"}), \\
                 patch("run.load_config", return_value={"backend": "brave"}), \\
                 patch("httpx.get", side_effect=slow_get):
                run.main()
        """)

        proc = subprocess.Popen(
            [sys.executable, "-c", helper],
            env={
                "PATH": os.environ.get("PATH", ""),
                "TOOL_ROOT": str(ROOT),
                "PYTHONPATH": str(ROOT),
            },
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Give it time to start and enter the slow_get
        time.sleep(0.5)
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=5)
        assert proc.returncode == 0
