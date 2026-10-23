#!/usr/bin/env bash
# One-command start: builds UI if needed, then serves API + UI on http://127.0.0.1:${FW_PORT:-8765}
set -euo pipefail
cd "$(dirname "$0")"
command -v uv >/dev/null || { echo "Install uv: brew install uv"; exit 1; }
(cd backend && uv sync -q)
if [ ! -d frontend/dist ] || [ "${REBUILD:-0}" = "1" ]; then (cd frontend && npm install --silent && npm run build); fi
echo "Finance Lab → http://127.0.0.1:${FW_PORT:-8765}"
cd backend && exec uv run python -c "from fw.main import serve; serve()"
