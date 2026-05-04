# ── Stage 1: Build React frontend ────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python runtime ───────────────────────────────────────────────────
FROM python:3.12-slim AS app
WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Install Python dependencies from pyproject.toml
COPY pyproject.toml ./
RUN uv pip install --system --no-dev -r pyproject.toml 2>/dev/null || \
    uv pip install --system \
        fastapi uvicorn[standard] python-multipart \
        openai "openai-agents>=0.0.19" \
        pydantic python-dotenv rich \
        requests httpx aiohttp asyncio-throttle \
        numpy shapely pyproj tenacity

# Copy Python source
COPY *.py ./

# Copy React build → static/
COPY --from=frontend-builder /app/dist ./static

# HF Spaces runs as non-root user 1000
RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

EXPOSE 7860

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
