"""
Shared pytest fixtures for ils-reports test suite.
"""

import sqlite3

import pytest


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Temporary directory for SQLite output files."""
    out = tmp_path / "output"
    out.mkdir()
    return str(out)


@pytest.fixture
def tmp_sql_dir(tmp_path):
    """Temporary directory with views/ and indexes/ subdirectories."""
    sql = tmp_path / "sql"
    (sql / "views").mkdir(parents=True)
    (sql / "indexes").mkdir(parents=True)
    return sql


@pytest.fixture
def empty_db(tmp_path):
    """An open sqlite3.Connection backed by a temp file."""
    conn = sqlite3.connect(tmp_path / "test.db")
    yield conn
    conn.close()


@pytest.fixture
def valid_config(tmp_path, monkeypatch):
    """Minimal valid configuration set via environment variables."""
    cfg = {
        "pg_host": "localhost",
        "pg_port": 1032,
        "pg_dbname": "iii",
        "pg_username": "testuser",
        "pg_password": "testpass",
        "output_dir": str(tmp_path / "output"),
    }
    monkeypatch.setenv("PG_HOST", cfg["pg_host"])
    monkeypatch.setenv("PG_PORT", str(cfg["pg_port"]))
    monkeypatch.setenv("PG_DBNAME", cfg["pg_dbname"])
    monkeypatch.setenv("PG_USERNAME", cfg["pg_username"])
    monkeypatch.setenv("PG_PASSWORD", cfg["pg_password"])
    monkeypatch.setenv("OUTPUT_DIR", cfg["output_dir"])
    return cfg


# ---------------------------------------------------------------------------
# Integration fixtures (require a live PostgreSQL instance via pytest-postgresql)
# These are only activated when the `integration` mark is in use.
# ---------------------------------------------------------------------------

try:
    from pytest_postgresql import factories as pg_factories

    # Session-scoped PostgreSQL process — started once for the whole test run.
    postgresql_proc = pg_factories.postgresql_proc()
    postgresql = pg_factories.postgresql("postgresql_proc")

    @pytest.fixture(scope="session")
    def sierra_db(postgresql_proc):
        """
        Start a PostgreSQL instance, load the Sierra schema and seed data,
        and yield a psycopg2 connection.

        Skipped automatically if pytest-postgresql is not installed or
        PostgreSQL is unavailable.
        """
        from pathlib import Path

        import psycopg2

        fixtures = Path(__file__).parent / "fixtures"

        conn = psycopg2.connect(
            host=postgresql_proc.host,
            port=postgresql_proc.port,
            user="postgres",
            dbname="tests",
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute((fixtures / "sierra_schema.sql").read_text())
        cur.execute((fixtures / "sierra_seed.sql").read_text())
        conn.autocommit = False
        yield conn
        conn.close()

    @pytest.fixture(scope="session")
    def sierra_config(postgresql_proc, tmp_path_factory):
        """Config dict pointing at the test PostgreSQL instance."""
        out = tmp_path_factory.mktemp("output")
        return {
            "pg_host": postgresql_proc.host,
            "pg_port": postgresql_proc.port,
            "pg_dbname": "tests",
            "pg_username": "postgres",
            "pg_password": "",
            "pg_sslmode": "disable",
            "pg_itersize": 100,
            "output_dir": str(out),
        }

except ImportError:
    # pytest-postgresql not installed — integration fixtures will be unavailable.
    pass
