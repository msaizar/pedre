# Run all QA checks
qa:
    just lint format-check ty

qa-fix:
    just lint-fix format ty

# Lint (no autofix, CI-safe)
lint:
    uv run ruff check .

# Format check only (no changes)
format-check:
    uv run ruff format --check .

# Type checking
ty:
    uv run ty check

# Tests
test:
    uv run pytest

# Auto-fix lint issues
lint-fix:
    uv run ruff check --fix .

# Auto-format code
format:
    uv run ruff format .

# Run tests with coverage report
coverage:
    uv run coverage run -m pytest
    uv run coverage report

# Run tests with coverage and generate HTML report
coverage-html:
    uv run coverage run -m pytest
    uv run coverage html
    @echo "Coverage report generated in htmlcov/index.html"

# Install dependencies
install:
    uv sync

# Serve documentation locally
docs-serve:
    uv run --group docs zensical serve

# Build documentation
docs-build:
    uv run --group docs zensical build
