import tomllib
from unittest.mock import patch

import pytest

from run import load_config


class TestLoadConfig:
    def test_no_config_file_returns_brave_default(self, tmp_path):
        # Point __file__ to a location where no config.toml exists
        fake_run = tmp_path / "run.py"
        fake_run.touch()
        with patch("run.__file__", str(fake_run)):
            config = load_config()
        assert config == {"backend": "brave"}

    def test_valid_config_brave(self, tmp_path):
        config_path = tmp_path / "config.toml"
        config_path.write_text('backend = "brave"\n')
        fake_run = tmp_path / "run.py"
        fake_run.touch()
        with patch("run.__file__", str(fake_run)):
            config = load_config()
        assert config["backend"] == "brave"

    def test_valid_config_serper(self, tmp_path):
        config_path = tmp_path / "config.toml"
        config_path.write_text('backend = "serper"\n')
        fake_run = tmp_path / "run.py"
        fake_run.touch()
        with patch("run.__file__", str(fake_run)):
            config = load_config()
        assert config["backend"] == "serper"

    def test_unknown_backend_value_loaded(self, tmp_path):
        # load_config just returns the raw dict; validation happens in main()
        config_path = tmp_path / "config.toml"
        config_path.write_text('backend = "duckduckgo"\n')
        fake_run = tmp_path / "run.py"
        fake_run.touch()
        with patch("run.__file__", str(fake_run)):
            config = load_config()
        assert config["backend"] == "duckduckgo"

    def test_extra_keys_loaded(self, tmp_path):
        config_path = tmp_path / "config.toml"
        config_path.write_text('backend = "brave"\nextra_key = "value"\n')
        fake_run = tmp_path / "run.py"
        fake_run.touch()
        with patch("run.__file__", str(fake_run)):
            config = load_config()
        assert config["extra_key"] == "value"


def test_malformed_config_toml_raises(tmp_path):
    """Verify tomllib raises on invalid TOML content."""
    bad = tmp_path / "config.toml"
    bad.write_text("[broken")
    with pytest.raises(tomllib.TOMLDecodeError):
        with open(bad, "rb") as f:
            tomllib.load(f)


def test_load_config_returns_dict():
    """load_config always returns a dict (empty or populated)."""
    result = load_config()
    assert isinstance(result, dict)
    assert "backend" in result  # default or from file
