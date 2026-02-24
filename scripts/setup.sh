#!/usr/bin/env bash
# Install all dependencies and pre-commit hooks.
set -e

uv sync --all-extras
uv run pre-commit install
