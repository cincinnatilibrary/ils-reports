#!/usr/bin/env bash
# build-sample-db.sh — Build a small sample database for local dev/testing.
#
# Usage:
#   scripts/build-sample-db.sh [--limit N] [--output DIR]
#
# Options:
#   --limit N     Maximum rows per table (default: 500)
#   --output DIR  Output directory for sample DB (default: ./sample/)
#   -h, --help    Show this help message
#
# Credentials are read from .env (if present) or the current environment.
# The sample database is written to OUTPUT_DIR/current_collection.db.
#
# WARNING: This is NOT a production build. Do NOT deploy the output.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

LIMIT=500
OUTPUT_DIR="${PROJECT_ROOT}/sample"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --limit)
            LIMIT="$2"
            if ! [[ "$LIMIT" =~ ^[0-9]+$ ]] || [[ "$LIMIT" -le 0 ]]; then
                echo "ERROR: --limit must be a positive integer, got: $2" >&2
                exit 1
            fi
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$(realpath "$2")"
            shift 2
            ;;
        -h|--help)
            grep '^#' "$0" | sed 's/^# \{0,1\}//' | head -20
            exit 0
            ;;
        *)
            echo "Unknown option: $1  (run with --help for usage)" >&2
            exit 1
            ;;
    esac
done

# Load .env credentials into this shell so they're available to uv run.
if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "${PROJECT_ROOT}/.env"
    set +a
fi

mkdir -p "$OUTPUT_DIR"

echo "==> Building sample database"
echo "    Limit:      ${LIMIT} rows/table"
echo "    Output dir: ${OUTPUT_DIR}"
echo ""

EXTRACT_LIMIT="$LIMIT" \
OUTPUT_DIR="$OUTPUT_DIR" \
    uv run --project "$PROJECT_ROOT" collection-analysis

echo ""
echo "==> Done: ${OUTPUT_DIR}/current_collection.db"
echo "    (${LIMIT} rows/table — NOT for production use)"
