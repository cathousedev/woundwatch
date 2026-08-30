# WoundWatch service image.
# Python slim base; install deps, run uvicorn.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install deps first for layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as non-root (container runs the service only; the DB is a separate
# existing instance on the homelab).
RUN useradd --create-home appuser
USER appuser

# The app exposes :8000; Caddy fronts woundwatch.cathousedev.com.
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
