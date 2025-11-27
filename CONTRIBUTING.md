# Contributing

Thank you for your interest in contributing to this project!

## Development Setup

1. Fork and clone the repository
2. Install dependencies: `uv sync --dev`
3. Install pre-commit hooks: `uv run pre-commit install`
4. Create a branch: `git checkout -b feature/your-feature`

## Code Standards

- **Python 3.12+** required
- **Type hints** on all functions
- **Docstrings** for public APIs
- **Tests** for new functionality

### Linting & Formatting

```bash
uv run ruff check .      # Lint
uv run ruff format .     # Format
uv run mypy src/         # Type check
```

### Testing

```bash
uv run pytest                    # All tests
uv run pytest tests/unit/        # Unit tests
uv run pytest tests/properties/  # Property tests
uv run pytest --cov=src/my_api   # With coverage
```

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new features
4. Follow conventional commits: `feat:`, `fix:`, `docs:`, `test:`

## Architecture Guidelines

- Follow Clean Architecture layers
- Use generics for reusable components
- Keep domain logic free of framework dependencies
- Write property-based tests for core logic

## Questions?

Open an issue for discussion before large changes.
