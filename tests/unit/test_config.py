"""Unit tests for collection_analysis.config — no external dependencies."""

import json

import pytest

from collection_analysis import config


class TestLoadValidConfig:
    def test_load_valid_config(self, valid_config):
        cfg, path = valid_config
        result = config.load(path)
        assert result["pg_host"] == "localhost"
        assert result["pg_port"] == 1032
        assert result["pg_dbname"] == "iii"

    def test_load_defaults_applied(self, valid_config):
        _, path = valid_config
        result = config.load(path)
        assert result["pg_sslmode"] == "require"
        assert result["pg_itersize"] == 5000

    def test_load_defaults_not_clobbered(self, tmp_path):
        cfg = {
            "pg_host": "host",
            "pg_port": 1032,
            "pg_dbname": "db",
            "pg_username": "u",
            "pg_password": "p",
            "output_dir": str(tmp_path),
            "pg_sslmode": "prefer",
            "pg_itersize": 50000,
        }
        p = tmp_path / "config.json"
        p.write_text(json.dumps(cfg))
        result = config.load(str(p))
        assert result["pg_sslmode"] == "prefer"
        assert result["pg_itersize"] == 50000


class TestLoadErrors:
    def test_load_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            config.load(str(tmp_path / "nonexistent.json"))

    @pytest.mark.parametrize(
        "missing_key",
        ["pg_host", "pg_port", "pg_dbname", "pg_username", "pg_password", "output_dir"],
    )
    def test_load_missing_required_key(self, tmp_path, missing_key):
        cfg = {
            "pg_host": "h",
            "pg_port": 1032,
            "pg_dbname": "db",
            "pg_username": "u",
            "pg_password": "p",
            "output_dir": str(tmp_path),
        }
        del cfg[missing_key]
        p = tmp_path / "config.json"
        p.write_text(json.dumps(cfg))
        with pytest.raises(ValueError, match=missing_key):
            config.load(str(p))

    def test_load_invalid_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{ not valid json }")
        with pytest.raises(json.JSONDecodeError):
            config.load(str(p))


class TestPgConnectionString:
    def test_pg_connection_string_format(self, valid_config):
        _, path = valid_config
        cfg = config.load(path)  # load() applies defaults including pg_sslmode
        url = config.pg_connection_string(cfg)
        assert url.startswith("postgresql+psycopg2://")

    def test_pg_connection_string_sslmode(self, valid_config):
        _, path = valid_config
        cfg = config.load(path)
        url = config.pg_connection_string(cfg)
        assert "sslmode=require" in url

    def test_pg_connection_string_contains_host_and_db(self, valid_config):
        _, path = valid_config
        cfg = config.load(path)
        url = config.pg_connection_string(cfg)
        assert "localhost" in url
        assert "iii" in url
