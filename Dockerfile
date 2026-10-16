# Finance Wizard — portable demo image. Synthetic fixture data by default; see README "Docker".
FROM node:22-slim AS ui
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm install --silent
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ ./
RUN uv sync --frozen --no-dev
COPY --from=ui /ui/dist /app/frontend/dist
ENV FW_DATA_DIR=/app/data FW_FIXTURE=1 FW_LAKE_PATH=/lake/lake.duckdb \
    OLLAMA_URL=http://host.docker.internal:11434 PATH=/app/backend/.venv/bin:$PATH
RUN useradd -m fw && mkdir -p /app/data && chown fw /app/data
USER fw
EXPOSE 8765
# 0.0.0.0 inside the container only; compose publishes it on the host's 127.0.0.1.
CMD ["uvicorn", "fw.main:app", "--host", "0.0.0.0", "--port", "8765"]
