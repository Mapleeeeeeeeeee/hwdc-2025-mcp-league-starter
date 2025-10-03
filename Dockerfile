# Multi-stage Dockerfile for deploying Backend + Frontend on single Cloud Run instance
# Architecture: Nginx as reverse proxy, Backend on :8080, Frontend on :3000

# ================================
# Stage 1: Build Backend
# ================================
FROM python:3.12.11-slim-bookworm AS backend-builder

WORKDIR /app/backend

# Install uv for faster Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy backend dependency files
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy backend source code
COPY backend/ ./

# ================================
# Stage 2: Build Frontend
# ================================
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Install pnpm
RUN npm install -g pnpm@10.14.0

# Copy package files
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --no-frozen-lockfile

# Copy frontend source code (excluding node_modules to preserve installed packages)
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/next.config.ts frontend/tsconfig.json frontend/postcss.config.mjs frontend/vitest.config.ts ./
COPY frontend/middleware.ts frontend/next-env.d.ts ./
COPY frontend/eslint.config.mjs ./

# Build Next.js with standalone output
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

RUN pnpm build

# ================================
# Stage 3: Runtime - Multi-service
# ================================
FROM nginx:bookworm

# Set shell options for better error handling
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install Python 3.12, Node.js 20, and required system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    curl \
    ca-certificates \
    gnupg \
    libsecret-1-0 \
    supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv in runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create app directories
WORKDIR /app

# Copy backend from builder
COPY --from=backend-builder /app/backend /app/backend

# Copy frontend standalone build from builder
# Next.js standalone output structure: .next/standalone/frontend/*
COPY --from=frontend-builder /app/frontend/.next/standalone/frontend /app/frontend
COPY --from=frontend-builder /app/frontend/.next/static /app/frontend/.next/static
COPY --from=frontend-builder /app/frontend/public /app/frontend/public

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisord.conf

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose Cloud Run port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start all services via supervisor
CMD ["/app/start.sh"]
