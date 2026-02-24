#!/usr/bin/env bash
# Auto-fix Python and SQL formatting.
set -e

uv run ruff format collection_analysis/ tests/
uv run ruff check --fix collection_analysis/ tests/
uv run sqlfluff fix --force sql/
