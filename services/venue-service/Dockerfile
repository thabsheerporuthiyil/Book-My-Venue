# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

# Prevent Python from writing pyc files and keep stdout unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv for fast dependency resolution and installation
COPY --from=ghcr.io/astral-sh/uv:0.4.10 /uv /uvx /bin/

WORKDIR /monorepo

# Copy dependency files and platform library
COPY services/venue-service/requirements/ services/venue-service/requirements/
COPY libraries/ /libraries/

# Install dependencies into the system python environment
RUN cd services/venue-service && uv pip install --system --no-cache-dir -r requirements/prod.txt

# ==============================================================================

FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /monorepo/services/venue-service

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /libraries /libraries

# Create a non-root user
RUN addgroup --system appgroup && adduser --system --group appuser

# Copy application code
COPY --chown=appuser:appgroup services/venue-service/ .

# Collect static files (requires a dummy secret key to satisfy Django)
RUN DJANGO_SETTINGS_MODULE=config.settings.prod \
    DJANGO_SECRET_KEY=dummy-key-for-build \
    DATABASE_URL=postgres://dummy \
    python manage.py collectstatic --noinput

# Ensure the appuser owns the staticfiles directory
RUN chown -R appuser:appgroup /monorepo/services/venue-service/staticfiles

# Switch to non-root user
USER appuser

EXPOSE 8002

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8002/health/deep/ || exit 1

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8002", "--workers", "1", "--access-logfile", "-", "--error-logfile", "-"]
