#!/usr/bin/env bash
# Build or serve the MkDocs documentation.
#
# Usage:
#   scripts/docs.sh                  Build docs → site/
#   scripts/docs.sh --serve          Serve docs at http://127.0.0.1:8000
#   scripts/docs.sh --with-coverage  Run coverage, copy htmlcov/ → docs/coverage/, build docs
set -e

case "${1:-}" in
  --serve)
    uv run mkdocs serve --dev-addr=127.0.0.1:8000
    ;;
  --with-coverage)
    bash "$(dirname "$0")/test.sh" --cov
    cp -r htmlcov/ docs/coverage/
    uv run mkdocs build --strict
    rm -rf docs/coverage/
    ;;
  "")
    uv run mkdocs build --strict
    ;;
  *)
    echo "Unknown option: $1"
    echo "Usage: $0 [--serve | --with-coverage]"
    exit 1
    ;;
esac
