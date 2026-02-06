# Contributing to Pedre

Thank you for your interest in contributing to Pedre! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Be respectful and constructive in all interactions. We aim to maintain a welcoming and inclusive community.

## Getting Started

### Prerequisites

- Python 3.14 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- [just](https://github.com/casey/just) command runner (optional but recommended)

### Setting Up Your Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:

   ```bash
   git clone https://github.com/msaizar/pedre.git
   cd pedre
   ```

3. Install dependencies:

   ```bash
   uv sync
   ```

4. Create a new branch for your feature or fix:

   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Code Quality

This project uses modern Python tooling for code quality:

- **ruff** - Linting and formatting
- **ty** - Type checking
- **pytest** - Testing framework
- **coverage** - Code coverage reporting

### Running Quality Checks

Run all quality checks at once:

```bash
just qa-fix
```

Or run individual checks:

```bash
just lint-fix    # Lint with ruff
just format   # Format code with ruff
just ty       # Type check with ty
```

### Running Tests

Run the test suite:

```bash
just test
```

Run tests with coverage:

```bash
just coverage
```

### Code Style Guidelines

- Follow PEP 8 style guidelines (enforced by ruff)
- Use Google-style docstrings for all public functions, classes, and modules
- Add type hints to all function signatures
- Keep functions focused and single-purpose
- Avoid deep nesting (max 3-4 levels)
- Write descriptive variable and function names

### Testing Guidelines

- Write tests for all new features and bug fixes
- Maintain or improve code coverage
- Use descriptive test names that explain what is being tested
- Follow the Arrange-Act-Assert pattern in tests
- Place tests in the `tests/` directory mirroring the source structure

## Submitting Changes

### Pull Request Process

1. Ensure all tests pass and quality checks succeed:

   ```bash
   just qa-fix
   just test
   ```

2. Update documentation if you've changed APIs or added features

3. Commit your changes with clear, descriptive commit messages:

   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

4. Push to your fork:

   ```bash
   git push origin feature/your-feature-name
   ```

5. Open a Pull Request on GitHub with:
   - Clear title describing the change
   - Description of what changed and why
   - Reference to any related issues
   - Screenshots if applicable (for UI changes)

### Commit Message Format

Use conventional commit format:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:

```text
feat: add particle effect plugin for interactions
fix: correct NPC pathfinding edge case
docs: update Tiled integration guide
refactor: simplify dialog plugin state handling
```

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- Python version
- Operating system
- Pedre version
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Error messages or stack traces
- Minimal code example if applicable

### Feature Requests

For feature requests, please describe:

- The problem you're trying to solve
- Your proposed solution
- Alternative solutions you've considered
- How this benefits other users

## Development Tips

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Documentation

- Update relevant documentation in the `docs/` directory
- Keep the README.md examples current
- Add docstrings to all public APIs
- Include usage examples in docstrings

## Questions?

If you have questions about contributing:

- Open a GitHub Discussion
- Check existing issues and pull requests
- Review the documentation in the `docs/` directory

## License

By contributing to Pedre, you agree that your contributions will be licensed under the BSD 3-Clause License.
