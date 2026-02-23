"""
config.py — Load and validate pipeline configuration from config.json.

Expected config.json fields:
    pg_host       Sierra PostgreSQL host
    pg_port       Sierra PostgreSQL port (typically 1032)
    pg_dbname     Sierra database name (typically 'iii')
    pg_username   PostgreSQL username
    pg_password   PostgreSQL password
    pg_sslmode    SSL mode (typically 'require')
    pg_itersize   Server-side cursor fetch size (default 5000)
    output_dir    Directory where output SQLite databases are written
"""

import json
from pathlib import Path


def load(config_path: str = "config.json") -> dict:
    """Load and return configuration from a JSON file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path.resolve()}\n"
            f"Copy config.json.sample to config.json and fill in your credentials."
        )
    with path.open() as f:
        cfg = json.load(f)

    required = ["pg_host", "pg_port", "pg_dbname", "pg_username", "pg_password", "output_dir"]
    missing = [k for k in required if k not in cfg]
    if missing:
        raise ValueError(f"Missing required config keys: {missing}")

    cfg.setdefault("pg_sslmode", "require")
    cfg.setdefault("pg_itersize", 5000)

    return cfg


def pg_connection_string(cfg: dict) -> str:
    """Build a SQLAlchemy-compatible PostgreSQL connection URL from config."""
    return (
        f"postgresql+psycopg2://{cfg['pg_username']}:{cfg['pg_password']}"
        f"@{cfg['pg_host']}:{cfg['pg_port']}/{cfg['pg_dbname']}"
        f"?sslmode={cfg['pg_sslmode']}"
    )
