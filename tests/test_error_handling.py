"""Tests for error paths in main(): timeout and network errors.

These test main() in-process with mocked httpx to verify that timeout and
network exceptions are caught, produce the right stdout/stderr messages,
and exit with code 1.
"""

import io
import json
import os
from unittest.mock import patch

import httpx
import pytest

import run


_STDIN = json.dumps({
    "args": {"query": "test"},
    "session": "s",
    "workspace": "/tmp",
    "session_secrets": {},
    "plan_outputs": [],
})


class TestMainTimeout:
    def test_timeout_exits_1(self):
        with patch("sys.stdin", io.StringIO(_STDIN)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "fake-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}), \
             patch("httpx.get", side_effect=httpx.ReadTimeout("read timed out")):
            with pytest.raises(SystemExit) as exc_info:
                run.main()
        assert exc_info.value.code == 1

    def test_timeout_stdout_says_timed_out(self, capsys):
        with patch("sys.stdin", io.StringIO(_STDIN)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "fake-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}), \
             patch("httpx.get", side_effect=httpx.ReadTimeout("read timed out")):
            with pytest.raises(SystemExit):
                run.main()
        captured = capsys.readouterr()
        assert "timed out" in captured.out

    def test_timeout_stderr_has_detail(self, capsys):
        with patch("sys.stdin", io.StringIO(_STDIN)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "fake-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}), \
             patch("httpx.get", side_effect=httpx.ReadTimeout("read timed out")):
            with pytest.raises(SystemExit):
                run.main()
        captured = capsys.readouterr()
        assert "timeout" in captured.err

    def test_timeout_serper_exits_1(self):
        with patch("sys.stdin", io.StringIO(_STDIN)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "fake-key"}), \
             patch("run.load_config", return_value={"backend": "serper"}), \
             patch("httpx.post", side_effect=httpx.ReadTimeout("read timed out")):
            with pytest.raises(SystemExit) as exc_info:
                run.main()
        assert exc_info.value.code == 1


class TestMainNetworkError:
    def test_network_error_exits_1(self):
        with patch("sys.stdin", io.StringIO(_STDIN)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "fake-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}), \
             patch("httpx.get", side_effect=httpx.ConnectError("connection refused")):
            with pytest.raises(SystemExit) as exc_info:
                run.main()
        assert exc_info.value.code == 1

    def test_network_error_stdout_message(self, capsys):
        with patch("sys.stdin", io.StringIO(_STDIN)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "fake-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}), \
             patch("httpx.get", side_effect=httpx.ConnectError("connection refused")):
            with pytest.raises(SystemExit):
                run.main()
        captured = capsys.readouterr()
        assert "network error" in captured.out

    def test_network_error_stderr_has_detail(self, capsys):
        with patch("sys.stdin", io.StringIO(_STDIN)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "fake-key"}), \
             patch("run.load_config", return_value={"backend": "brave"}), \
             patch("httpx.get", side_effect=httpx.ConnectError("connection refused")):
            with pytest.raises(SystemExit):
                run.main()
        captured = capsys.readouterr()
        assert "network" in captured.err

    def test_network_error_serper_exits_1(self):
        with patch("sys.stdin", io.StringIO(_STDIN)), \
             patch.dict(os.environ, {"KISO_TOOL_WEBSEARCH_API_KEY": "fake-key"}), \
             patch("run.load_config", return_value={"backend": "serper"}), \
             patch("httpx.post", side_effect=httpx.ConnectError("connection refused")):
            with pytest.raises(SystemExit) as exc_info:
                run.main()
        assert exc_info.value.code == 1
