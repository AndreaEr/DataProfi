# Contributing to DataProfi

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

4. Run tests to verify setup:

```bash
pytest
```

## Development Workflow

1. Create a branch for your feature/fix
2. Make your changes
3. Run tests: `pytest`
4. Run linter: `ruff check .`
5. Submit a pull request

## Project Structure

```
dataprofi/
  core/         - Shared types and configuration
  ingest/       - Data loading (CSV, JSON, API)
  profiler/     - Quality scoring, column profiling, timeseries, geo, correlations, schema
  cleaner/      - Cleaning pipeline (missing, duplicates, outliers, types, normalization)
  indexer/      - PostgreSQL index recommendation engine
  api/          - FastAPI server and Pydantic schemas

frontend/
  src/components/  - React components (one per tab)
  src/api/         - API client functions
  src/types/       - TypeScript type definitions

tests/            - pytest test suite
samples/          - Sample datasets for testing
```

## Code Style

- Python: follow ruff defaults, line length 100
- TypeScript: strict mode, no `any` where avoidable
- No emoji or unicode symbols in UI - use lucide-react icons
- Comments only when the WHY is non-obvious - code should be self-documenting
- No unnecessary abstractions - three similar lines beats a premature helper

## Adding a New Profiler Module

1. Create `dataprofi/profiler/your_module.py`
2. Define dataclasses in `dataprofi/core/types.py`
3. Add API endpoint in `dataprofi/api/server.py`
4. Add frontend component in `frontend/src/components/YourView.tsx`
5. Add API client function in `frontend/src/api/client.ts`
6. Register the tab in `frontend/src/App.tsx`
7. Write tests in `tests/test_your_module.py`

## Reporting Issues

Use GitHub Issues. Include:
- What you expected
- What happened instead
- Steps to reproduce
- Sample data (if applicable)
