# ==============================================================================
# SettleIQ Multi-Stage Production Dockerfile
# Stage 1: Build the React/TypeScript Frontend Dashboard
# Stage 2: Minimal, Secure Python Runtime
# ==============================================================================

# --- Stage 1: Frontend Build ---
FROM node:20-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Backend Runtime ---
FROM python:3.12-slim AS runtime

# Security: prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python production dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . "psycopg[binary]>=3.1"

# Copy source code
COPY src/ /app/src/

# Copy compiled frontend assets from Stage 1 into the static directory
COPY --from=frontend-builder /app/src/settleiq/static /app/src/settleiq/static

# Create non-root user and assign permissions
RUN useradd -m -u 1000 settleiq && \
    chown -R settleiq:settleiq /app

USER settleiq

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "settleiq.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
