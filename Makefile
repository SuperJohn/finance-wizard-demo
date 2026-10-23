# Finance Lab. `make demo` builds the UI, then serves API + UI on http://127.0.0.1:8765.
# Data: ../finance-lake-demo/lake.duckdb if present (run `make demo` there first), else the built-in synthetic fixture.
LAKE ?= $(abspath ../finance-lake-demo/lake.duckdb)

.PHONY: demo fixture install test build lint screenshots clean
demo: install build
	FW_LAKE_PATH=$(LAKE) ./run.sh
fixture: install build
	FW_FIXTURE=1 ./run.sh
install:
	cd backend && uv sync -q
	cd frontend && npm install --silent
test:
	cd backend && uv run pytest -q
	@if [ -f "$(LAKE)" ]; then cd backend && FW_TEST_LAKE=$(LAKE) uv run pytest -q -k synthetic_lake; fi
build:
	cd frontend && npm run build
screenshots:
	uv run --with playwright python scripts/screenshots.py
clean:
	rm -rf backend/.venv frontend/node_modules frontend/dist data
