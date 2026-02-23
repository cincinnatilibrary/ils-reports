FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install Datasette and plugins
COPY requirements-datasette.txt .
RUN uv pip install --system --no-cache -r requirements-datasette.txt
RUN datasette install datasette-horizontal-scroll

# Copy Datasette configuration files
COPY metadata.yml .
COPY datasette.yml .
COPY templates/ templates/
COPY static/ static/

# The database is NOT baked into the image — it lives on a mounted volume at /data
# and is updated nightly by the pipeline running on the host or a separate job.
VOLUME ["/data"]

EXPOSE 8001

CMD ["datasette", "serve", "/data/current_collection.db", \
     "--metadata", "/app/metadata.yml", \
     "--config", "/app/datasette.yml", \
     "--template-dir", "/app/templates/", \
     "--static", "static:/app/static/", \
     "--host", "0.0.0.0", \
     "--port", "8001"]
