# merchants-store — demo Flask store
# Build:  docker build -t mariofix/merchants-store .
# Run:    docker run -p 8000:8000 -v merchants_data:/data -e SECRET_KEY=change-me mariofix/merchants-store

FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# SQLite database lives on a named volume so it survives container restarts
RUN mkdir -p /data
ENV DATABASE_URL=sqlite:////data/store.db

# Non-root user
RUN useradd -m appuser && chown -R appuser /app /data
USER appuser

EXPOSE 8000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60"]
