#!/usr/bin/env bash
# Run tests.
#
# Usage:
#   scripts/test.sh               Unit tests only (default)
#   scripts/test.sh --integration  Integration tests only
#   scripts/test.sh --all          All tests
#   scripts/test.sh --cov          Unit tests + HTML coverage → htmlcov/
set -e

case "${1:-}" in
  --integration)
    uv run pytest tests/ -m integration -v
    ;;
  --all)
    uv run pytest tests/
    ;;
  --cov)
    uv run pytest tests/unit/ --cov=collection_analysis \
        --cov-report=term-missing --cov-report=html
    ;;
  "")
    uv run pytest tests/unit/
    ;;
  *)
    echo "Unknown option: $1"
    echo "Usage: $0 [--integration | --all | --cov]"
    exit 1
    ;;
esac
