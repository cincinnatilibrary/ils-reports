#!/usr/bin/env bash
# Serve current_collection.db locally via Datasette (direct uv run, no container).
# For a containerised dev environment use scripts/dev-datasette.sh instead.
#
# Usage:
#   scripts/datasette.sh               Serve on port 8001
#   scripts/datasette.sh --dev         Serve with --reload
#   scripts/datasette.sh --db PATH     Serve a custom DB path
set -e

DB_PATH="current_collection.db"
EXTRA_FLAGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dev)
      EXTRA_FLAGS+=(--reload)
      shift
      ;;
    --db)
      DB_PATH="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--dev] [--db PATH]"
      exit 1
      ;;
  esac
done

if [[ ! -f "$DB_PATH" ]]; then
  echo "ERROR: $DB_PATH not found. Run the pipeline first."
  exit 1
fi

uv run datasette serve "$DB_PATH" \
    --metadata datasette/metadata.yml \
    --config datasette/datasette.yml \
    --template-dir datasette/templates/ \
    --static static:datasette/static/ \
    --port 8001 \
    "${EXTRA_FLAGS[@]}"
