#!/usr/bin/env bash
# dev-datasette.sh — Build and run the CHPL Datasette container locally with Podman.
#
# Usage:
#   ./scripts/dev-datasette.sh [options]
#
# Options:
#   --db PATH       Path to SQLite DB to mount (default: test.db in project root).
#                   Creates a test DB at that path if it does not exist.
#   --no-rebuild    Skip rebuilding the container image.
#   --port PORT     Host port to bind (default: 8001).
#   -h, --help      Show this help.
#
# Templates and static files are bind-mounted so edits take effect on
# browser refresh without rebuilding the image.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ── Defaults ────────────────────────────────────────────────────────────────
DB_PATH="${PROJECT_ROOT}/test.db"
IMAGE_NAME="chpl-datasette"
PORT=8001
REBUILD=true

# ── Argument parsing ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --db)        DB_PATH="$(realpath "$2")"; shift 2 ;;
        --no-rebuild) REBUILD=false; shift ;;
        --port)      PORT="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,/^set /p' "$0" | grep '^#' | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# ── Prerequisites ────────────────────────────────────────────────────────────
if ! command -v podman &>/dev/null; then
    echo "ERROR: podman is not installed or not in PATH." >&2
    exit 1
fi

if ! command -v uv &>/dev/null; then
    echo "ERROR: uv is not installed. See https://docs.astral.sh/uv/" >&2
    exit 1
fi

# ── Test database ────────────────────────────────────────────────────────────
if [[ ! -f "$DB_PATH" ]]; then
    echo "==> Creating test database at $DB_PATH"
    uv run --project "$PROJECT_ROOT" python "$SCRIPT_DIR/create-test-db.py" "$DB_PATH"
else
    echo "==> Using existing database: $DB_PATH"
fi

# ── Build ────────────────────────────────────────────────────────────────────
if [[ "$REBUILD" == true ]]; then
    echo "==> Building container image: $IMAGE_NAME"
    podman build --tag "$IMAGE_NAME" "$PROJECT_ROOT/datasette/"
else
    echo "==> Skipping image rebuild (--no-rebuild)"
    if ! podman image exists "$IMAGE_NAME"; then
        echo "ERROR: image '$IMAGE_NAME' does not exist. Run without --no-rebuild first." >&2
        exit 1
    fi
fi

# ── Run ──────────────────────────────────────────────────────────────────────
echo ""
echo "==> Starting Datasette"
echo "    DB:        $DB_PATH"
echo "    Templates: $PROJECT_ROOT/datasette/templates/"
echo "    Static:    $PROJECT_ROOT/datasette/static/"
echo "    URL:       http://localhost:$PORT"
echo ""
echo "    Templates and static files are live-mounted — edit and refresh."
echo "    Press Ctrl-C to stop."
echo ""

exec podman run --rm \
    --name "$IMAGE_NAME" \
    -p "${PORT}:8001" \
    -v "${DB_PATH}:/data/current_collection.db:ro,Z" \
    -v "${PROJECT_ROOT}/datasette/templates:/app/templates:ro,Z" \
    -v "${PROJECT_ROOT}/datasette/static:/app/static:ro,Z" \
    "$IMAGE_NAME"
