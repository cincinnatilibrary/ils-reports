#!/usr/bin/env bash
# Deploy to Fly.io.
#
# Usage:
#   scripts/deploy.sh       Deploy Datasette app
#   scripts/deploy.sh --db  Open SFTP shell to upload the database
set -e

case "${1:-}" in
  --db)
    flyctl sftp shell --config datasette/fly.toml
    ;;
  "")
    flyctl deploy --config datasette/fly.toml
    ;;
  *)
    echo "Unknown option: $1"
    echo "Usage: $0 [--db]"
    exit 1
    ;;
esac
