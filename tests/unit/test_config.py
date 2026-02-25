"""Unit tests for collection_analysis.config — no external dependencies."""

import json

import pytest

from collection_analysis import config

_REQUIRED_VARS = ("PG_HOST", "PG_PORT", "PG_DBNAME", "PG_USERNAME", "PG_PASSWORD", "OUTPUT_DIR")


@pytest.fixture(autouse=True)
def no_dotenv(monkeypatch):
    """Prevent load_dotenv() from reading the real .env during config tests."""
    monkeypatch.setattr("collection_analysis.config.load_dotenv", lambda *a, **kw: None)

_VALID_JSON = {
    "pg_host": "localhost",
    "pg_port": 1032,
    "pg_dbname": "iii",
    "pg_username": "testuser",
    "pg_password": "testpass",
    "output_dir": "/tmp/out",
}


class TestLoadValidConfig:
    def test_load_valid_config(self, valid_config):
        result = config.load()
        assert result["pg_host"] == "localhost"
        assert result["pg_port"] == 1032  # int, not string
        assert result["pg_dbname"] == "iii"

    def test_load_defaults_applied(self, valid_config):
        result = config.load()
        assert result["pg_sslmode"] == "require"
        assert result["pg_itersize"] == 15000

    def test_load_defaults_not_clobbered(self, valid_config, monkeypatch):
        monkeypatch.setenv("PG_SSLMODE", "prefer")
        monkeypatch.setenv("PG_ITERSIZE", "50000")
        result = config.load()
        assert result["pg_sslmode"] == "prefer"
        assert result["pg_itersize"] == 50000

    def test_port_coerced_to_int(self, valid_config):
        result = config.load()
        assert isinstance(result["pg_port"], int)

    def test_itersize_coerced_to_int(self, valid_config, monkeypatch):
        monkeypatch.setenv("PG_ITERSIZE", "10000")
        result = config.load()
        assert result["pg_itersize"] == 10000
        assert isinstance(result["pg_itersize"], int)

    def test_log_level_default(self, valid_config):
        result = config.load()
        assert result["log_level"] == "INFO"

    def test_log_file_default_none(self, valid_config):
        result = config.load()
        assert result["log_file"] is None

    def test_log_level_override(self, valid_config, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        result = config.load()
        assert result["log_level"] == "DEBUG"

    def test_log_file_override(self, valid_config, monkeypatch, tmp_path):
        log_path = str(tmp_path / "pipeline.log")
        monkeypatch.setenv("LOG_FILE", log_path)
        result = config.load()
        assert result["log_file"] == log_path


class TestLoadErrors:
    def test_load_missing_required_env_var(self, monkeypatch):
        for var in _REQUIRED_VARS:
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(ValueError, match="PG_HOST"):
            config.load()

    @pytest.mark.parametrize("missing_var", _REQUIRED_VARS)
    def test_load_missing_one_required_var(self, valid_config, monkeypatch, missing_var):
        monkeypatch.delenv(missing_var)
        with pytest.raises(ValueError, match=missing_var):
            config.load()

    def test_load_invalid_port(self, valid_config, monkeypatch):
        monkeypatch.setenv("PG_PORT", "not_an_int")
        with pytest.raises(ValueError):
            config.load()

    def test_explicit_path_missing_file(self, monkeypatch, tmp_path):
        for var in _REQUIRED_VARS:
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(FileNotFoundError):
            config.load(str(tmp_path / "nonexistent.json"))


class TestDeprecationWarnings:
    def test_config_json_warns(self, monkeypatch, tmp_path):
        for var in _REQUIRED_VARS:
            monkeypatch.delenv(var, raising=False)
        (tmp_path / "config.json").write_text(json.dumps(_VALID_JSON))
        monkeypatch.chdir(tmp_path)
        with pytest.warns(DeprecationWarning, match="deprecated"):
            config.load()

    def test_explicit_config_path_warns(self, monkeypatch, tmp_path):
        for var in _REQUIRED_VARS:
            monkeypatch.delenv(var, raising=False)
        p = tmp_path / "custom.json"
        p.write_text(json.dumps(_VALID_JSON))
        with pytest.warns(DeprecationWarning, match="deprecated"):
            config.load(str(p))

    def test_config_path_with_env_vars_warns(self, valid_config, monkeypatch, tmp_path):
        """--config with all env vars already set also warns (file is ignored)."""
        p = tmp_path / "custom.json"
        p.write_text(json.dumps(_VALID_JSON))
        with pytest.warns(DeprecationWarning):
            config.load(str(p))

    def test_env_vars_alone_no_warning(self, valid_config):
        """No DeprecationWarning when all required vars are set via env."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            config.load()  # must not raise


class TestSleepBetweenTables:
    def test_default_is_zero(self, valid_config):
        result = config.load()
        assert result["pg_sleep_between_tables"] == 0.0

    def test_float_value(self, valid_config, monkeypatch):
        monkeypatch.setenv("PG_SLEEP_BETWEEN_TABLES", "1.5")
        result = config.load()
        assert result["pg_sleep_between_tables"] == 1.5

    def test_integer_string_coerced_to_float(self, valid_config, monkeypatch):
        monkeypatch.setenv("PG_SLEEP_BETWEEN_TABLES", "2")
        result = config.load()
        assert result["pg_sleep_between_tables"] == 2.0
        assert isinstance(result["pg_sleep_between_tables"], float)

    def test_invalid_value_raises(self, valid_config, monkeypatch):
        monkeypatch.setenv("PG_SLEEP_BETWEEN_TABLES", "not_a_number")
        with pytest.raises(ValueError, match="PG_SLEEP_BETWEEN_TABLES"):
            config.load()


class TestPgConnectionString:
    def test_pg_connection_string_format(self, valid_config):
        cfg = config.load()
        url = config.pg_connection_string(cfg)
        assert url.startswith("postgresql+psycopg://")

    def test_pg_connection_string_sslmode(self, valid_config):
        cfg = config.load()
        url = config.pg_connection_string(cfg)
        assert "sslmode=require" in url

    def test_pg_connection_string_contains_host_and_db(self, valid_config):
        cfg = config.load()
        url = config.pg_connection_string(cfg)
        assert "localhost" in url
        assert "iii" in url
