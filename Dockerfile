# Multi-stage Dockerfile for Impetus LLM Server
# Optimized for production deployment

# Build stage for frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY impetus-dashboard/package.json impetus-dashboard/pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY impetus-dashboard/ ./

# Build frontend
RUN pnpm build

# Main application stage
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    IMPETUS_ENVIRONMENT=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r impetus && useradd -r -g impetus impetus

# Create application directory
WORKDIR /app

# Copy requirements first for better caching
COPY gerdsen_ai_server/requirements_production.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_production.txt

# Copy application code
COPY gerdsen_ai_server/ ./

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./static/

# Copy configuration files
COPY service/ ./service/
COPY docs/ ./docs/

# Create directories for models and logs
RUN mkdir -p /models /logs && \
    chown -R impetus:impetus /app /models /logs

# Switch to non-root user
USER impetus

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/api/health/live || exit 1

# Use Gunicorn for production
CMD ["gunicorn", "--config", "gunicorn_config.py", "wsgi:application"]