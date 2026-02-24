#!/usr/bin/env bash
# Run all linters: Python (ruff), SQL (sqlfluff), templates (djlint), CSS (tinycss2).
set -eo pipefail

uv run ruff check collection_analysis/ tests/
uv run sqlfluff lint sql/
uv run djlint datasette/templates/ --lint
uv run python -c "
import tinycss2, pathlib, sys
errs = [
    (f, n)
    for f in pathlib.Path('datasette/static').glob('*.css')
    for n in tinycss2.parse_stylesheet_bytes(f.read_bytes())[0]
    if n.type == 'error'
]
for f, n in errs:
    print(f'CSS error in {f}: {n}')
sys.exit(bool(errs))
"
