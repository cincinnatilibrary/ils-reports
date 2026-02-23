UV      := uv
DB_PATH := current_collection.db

.PHONY: install-dev lint lint-templates lint-css format test test-integration \
        test-all test-cov docs docs-serve datasette datasette-dev \
        deploy-datasette deploy-db clean

install-dev:
	$(UV) sync --all-extras
	$(UV) run pre-commit install

lint:
	$(UV) run ruff check collection_analysis/ tests/
	$(UV) run sqlfluff lint sql/
	$(MAKE) lint-templates
	$(MAKE) lint-css

lint-templates:
	$(UV) run djlint datasette/templates/ --lint

lint-css:
	$(UV) run python -c "import tinycss2, pathlib, sys; \
	  errs = [(f, n) for f in pathlib.Path('datasette/static').glob('*.css') \
	          for n in tinycss2.parse_stylesheet_bytes(f.read_bytes())[0] \
	          if n.type == 'error']; \
	  [print(f'CSS error in {f}: {n}') for f, n in errs]; sys.exit(bool(errs))"

format:
	$(UV) run ruff format collection_analysis/ tests/
	$(UV) run ruff check --fix collection_analysis/ tests/
	$(UV) run sqlfluff fix --force sql/

test:
	$(UV) run pytest tests/unit/

test-integration:
	$(UV) run pytest tests/ -m integration -v

test-all:
	$(UV) run pytest tests/

test-cov:
	$(UV) run pytest tests/unit/ --cov=collection_analysis \
	    --cov-report=term-missing --cov-report=html

docs:
	$(UV) run mkdocs build --strict

docs-serve:
	$(UV) run mkdocs serve --dev-addr=127.0.0.1:8000

datasette:
	@test -f $(DB_PATH) || (echo "ERROR: $(DB_PATH) not found. Run the pipeline first." && exit 1)
	$(UV) run datasette serve $(DB_PATH) \
	    --metadata datasette/metadata.yml \
	    --config datasette/datasette.yml \
	    --template-dir datasette/templates/ \
	    --static static:datasette/static/ \
	    --port 8001

datasette-dev:
	@test -f $(DB_PATH) || (echo "ERROR: $(DB_PATH) not found. Run the pipeline first." && exit 1)
	$(UV) run datasette serve $(DB_PATH) \
	    --metadata datasette/metadata.yml \
	    --config datasette/datasette.yml \
	    --template-dir datasette/templates/ \
	    --static static:datasette/static/ \
	    --port 8001 --reload

deploy-datasette:
	flyctl deploy --config datasette/fly.toml

deploy-db:
	@test -f $(DB_PATH) || (echo "ERROR: $(DB_PATH) not found." && exit 1)
	flyctl sftp shell --config datasette/fly.toml

clean:
	rm -rf site/ htmlcov/ .coverage .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
