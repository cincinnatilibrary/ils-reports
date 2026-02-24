#!/usr/bin/env bash
# Run the collection_analysis pipeline.
set -e

# Credentials are read from environment variables.
# For local development, copy .env.sample to .env and fill in your values.
# A .env file in the project root is loaded automatically.
uv run collection-analysis "$@"
