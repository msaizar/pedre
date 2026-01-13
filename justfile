# Run all QA checks
qa: format check ty

# Run linting checks
check:
    uv run ruff check --fix .

# Format code
format:
    uv run ruff format .

# Run type checking
ty:
    uv run ty check

# Run tests
test:
    uv run pytest

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
