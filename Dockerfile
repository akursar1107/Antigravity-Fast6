# Fast6 — NFL First TD Prediction Platform
# Multi-stage build: Node (frontend) + Python (backend)
#
# DEPLOYMENT: This image runs FastAPI only. The Next.js frontend is built but
# NOT served by this container. For production:
#   - Option A: Deploy Next.js separately (Vercel, Railway, etc.) and set
#     NEXT_PUBLIC_API_BASE_URL to this backend's URL.
#   - Option B: Use two containers: one for FastAPI (this), one for Next.js.
# See docs/plans/NEXTJS_DEPLOYMENT.md for frontend deployment.

# ── Stage 1: Build Next.js frontend ──────────────────────────────
FROM node:20-slim AS frontend-build

WORKDIR /build
COPY web/package.json web/package-lock.json ./
RUN npm ci --ignore-scripts
COPY web/ .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ── Stage 2: Production image (FastAPI + static frontend) ────────
FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ backend/

# Copy built frontend (for potential future static serving; not used by CMD)
COPY --from=frontend-build /build/.next/standalone web/
COPY --from=frontend-build /build/.next/static web/.next/static
COPY --from=frontend-build /build/public web/public

# Data directory for SQLite
RUN mkdir -p /app/data

# Expose FastAPI port
EXPOSE 8000

# Health check against FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run FastAPI
CMD ["uvicorn", "backend.api.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
