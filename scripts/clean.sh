#!/usr/bin/env bash
# Remove build artifacts: site/, htmlcov/, .coverage, __pycache__ dirs.
set -e

rm -rf site/ htmlcov/ .coverage .pytest_cache/
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
