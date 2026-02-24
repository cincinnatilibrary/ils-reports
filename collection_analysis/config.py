"""
config.py — Load and validate pipeline configuration from environment variables.

Environment variables (primary, preferred):
    PG_HOST        Sierra PostgreSQL hostname or IP  (required)
    PG_PORT        Port, typically 1032              (required)
    PG_DBNAME      Database name, typically 'iii'    (required)
    PG_USERNAME    PostgreSQL username               (required)
    PG_PASSWORD    PostgreSQL password               (required)
    OUTPUT_DIR     Directory for output databases    (required)
    PG_SSLMODE     SSL mode (default 'require')      (optional)
    PG_ITERSIZE    Cursor fetch size (default 5000)  (optional)
    LOG_LEVEL      DEBUG | INFO | WARNING            (optional, default 'INFO')
    LOG_FILE       Path to log file; unset disables  (optional)

For local development, copy .env.sample to .env — it is loaded automatically.

Legacy: config.json is still accepted but deprecated.  A DeprecationWarning is
raised whenever a JSON file is used so that callers can migrate to env vars.
"""

import json
import os
import warnings
from pathlib import Path

from dotenv import load_dotenv

# Mapping from env-var name to internal (lowercase) config key.
_ENV_VARS: list[tuple[str, str]] = [
    ("PG_HOST", "pg_host"),
    ("PG_PORT", "pg_port"),
    ("PG_DBNAME", "pg_dbname"),
    ("PG_USERNAME", "pg_username"),
    ("PG_PASSWORD", "pg_password"),
    ("OUTPUT_DIR", "output_dir"),
    ("PG_SSLMODE", "pg_sslmode"),
    ("PG_ITERSIZE", "pg_itersize"),
    ("LOG_LEVEL", "log_level"),
    ("LOG_FILE", "log_file"),
]

_REQUIRED_KEYS = {"pg_host", "pg_port", "pg_dbname", "pg_username", "pg_password", "output_dir"}


def load(config_path: str | None = None) -> dict:
    """Load and return the pipeline configuration.

    Priority order (highest wins):
    1. Environment variables (including those loaded from .env)
    2. config.json (deprecated fallback)

    Args:
        config_path: Optional path to a legacy config.json file.  Providing
            this argument emits a DeprecationWarning.

    Returns:
        Validated configuration dict with lowercase keys.

    Raises:
        FileNotFoundError: If *config_path* is given but the file does not exist.
        ValueError: If required configuration is missing after all sources are tried.
    """
    # Silently load .env if present; no-op if the file does not exist.
    load_dotenv()

    cfg: dict = {}

    # Read every known env var into cfg.
    for env_var, key in _ENV_VARS:
        val = os.environ.get(env_var)
        if val is not None:
            cfg[key] = val

    # Determine whether we still need to fall back to a JSON file.
    missing_required = _REQUIRED_KEYS - cfg.keys()

    if missing_required:
        # Resolve which JSON path to try.
        json_path: Path | None = None
        if config_path is not None:
            json_path = Path(config_path)
            if not json_path.exists():
                raise FileNotFoundError(
                    f"Config file not found: {json_path.resolve()}\n"
                    f"Set the required environment variables or copy .env.sample to .env."
                )
        elif Path("config.json").exists():
            json_path = Path("config.json")

        if json_path is not None:
            warnings.warn(
                f"{json_path} is deprecated as a configuration source. "
                f"Set environment variables (or use a .env file) instead. "
                f"See .env.sample for the full list.",
                DeprecationWarning,
                stacklevel=2,
            )
            with json_path.open() as f:
                json_cfg = json.load(f)
            # env vars keep priority — only fill in what is still missing.
            for key, val in json_cfg.items():
                cfg.setdefault(key, val)

    elif config_path is not None:
        # All required vars are already set via env, but caller passed --config.
        warnings.warn(
            f"--config / config_path is deprecated; environment variables are already set. "
            f"The file {config_path!r} will be ignored.",
            DeprecationWarning,
            stacklevel=2,
        )

    # Final check for required keys.
    missing_required = _REQUIRED_KEYS - cfg.keys()
    if missing_required:
        env_names = ", ".join(
            env_var for env_var, key in _ENV_VARS if key in missing_required
        )
        raise ValueError(
            f"Missing required configuration: {env_names}. "
            f"Set these environment variables or copy .env.sample to .env."
        )

    # Type coercions — work whether values came from env (str) or JSON (int/str).
    try:
        cfg["pg_port"] = int(cfg["pg_port"])
    except (ValueError, TypeError) as exc:
        raise ValueError(f"PG_PORT must be an integer, got {cfg['pg_port']!r}") from exc

    try:
        cfg["pg_itersize"] = int(cfg.get("pg_itersize", 5000))
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"PG_ITERSIZE must be an integer, got {cfg.get('pg_itersize')!r}"
        ) from exc

    cfg.setdefault("pg_sslmode", "require")
    cfg.setdefault("pg_itersize", 5000)
    cfg.setdefault("log_level", "INFO")
    cfg.setdefault("log_file", None)

    return cfg


def pg_connection_string(cfg: dict) -> str:
    """Build a SQLAlchemy-compatible PostgreSQL connection URL from config."""
    return (
        f"postgresql+psycopg://{cfg['pg_username']}:{cfg['pg_password']}"
        f"@{cfg['pg_host']}:{cfg['pg_port']}/{cfg['pg_dbname']}"
        f"?sslmode={cfg['pg_sslmode']}"
    )
