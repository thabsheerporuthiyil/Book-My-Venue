# ==========================================
# Build stage
# ==========================================
FROM python:3.12-slim AS builder

# 1. Bring in uv securely from the official Astral image (zero pip overhead)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/prod.txt ./requirements/

# 2. Use uv to create the virtual environment and install dependencies blazingly fast
# --compile-bytecode speeds up container cold starts
RUN uv venv /opt/venv && \
    VIRTUAL_ENV=/opt/venv uv pip install --no-cache-dir --compile-bytecode -r requirements/prod.txt

# ==========================================
# Run stage
# ==========================================
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# 3. Security & Size: Use libpq5 (runtime only) instead of libpq-dev (which contains C headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy codebase
COPY . .

# 4. Django Static Files
# We must collect static files so Swagger UI and Django Admin have their CSS/JS in production.
# We inject dummy environment variables because Django setup requires them just to run collectstatic.
RUN DJANGO_SETTINGS_MODULE="config.settings.prod" \
    DJANGO_SECRET_KEY="dummy-key-for-build" \
    DATABASE_URL="postgres://dummy:dummy@localhost:5432/dummy" \
    python manage.py collectstatic --noinput --clear

# 5. Security Compliance: Principle of Least Privilege
# Create a non-privileged user WITH a home directory (-m)
# Gunicorn and Celery occasionally attempt to write to /home/appuser/.cache or sockets
RUN groupadd -r appgroup && useradd -r -m -g appgroup appuser \
    && mkdir -p /app/staticfiles

# CRITICAL EDGE CASE FIX:
# We DO NOT `chown -R appuser /app` the entire directory!
# If the app is compromised, the hacker could rewrite the Python source code.
# We only give the appuser ownership of the staticfiles folder (and media if it existed).
RUN chown -R appuser:appgroup /app/staticfiles

USER appuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health/ || exit 1

# Start using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "3", "--access-logfile", "-", "config.wsgi:application"]
