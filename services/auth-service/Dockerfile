# ==========================================
# Build stage
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/prod.txt ./requirements/

# Install dependencies into virtualenv /opt/venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install uv for blazing fast dependency resolution
RUN pip install uv

# Install dependencies using uv
RUN uv pip install --no-cache-dir -r requirements/prod.txt

# ==========================================
# Run stage
# ==========================================
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies (libpq is needed for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy codebase
COPY . .

# Create a non-privileged user and group for security compliance
RUN groupadd -r appgroup && useradd -r -g appgroup appuser \
    && mkdir -p /app/staticfiles && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health/ || exit 1

# Start using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "3", "--access-logfile", "-", "config.wsgi:application"]
