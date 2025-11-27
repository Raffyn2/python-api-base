# Modern Python API Framework

[![CI](https://github.com/example/my-api/actions/workflows/ci.yml/badge.svg)](https://github.com/example/my-api/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready, reusable REST API framework built with Python 3.12+ and FastAPI, following Clean Architecture principles with maximum code reuse through Generics.

## ✨ Features

- **🏗️ Clean Architecture** - Domain, Application, Adapters, Infrastructure layers
- **🔄 Generic CRUD** - Type-safe, reusable components (`IRepository[T]`, `BaseUseCase[T]`, `GenericCRUDRouter[T]`)
- **⚡ Async Native** - Full async/await support throughout
- **✅ Type Safe** - Strict mypy, Pydantic v2 validation
- **🧪 Well Tested** - 148+ tests including property-based testing with Hypothesis
- **🔒 Secure** - Rate limiting, CORS, security headers, input sanitization
- **📊 Observable** - Structured logging, request tracing, health checks
- **🐳 Docker Ready** - Multi-stage Dockerfile, docker-compose

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker & Docker Compose (for database)

### Installation

```bash
# Clone the repository
git clone https://github.com/example/my-api.git
cd my-api

# Install dependencies with uv
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required: SECURITY__SECRET_KEY (min 32 chars)
```

### Database Migrations

```bash
# Run migrations
python scripts/migrate.py upgrade head

# Create new migration
python scripts/migrate.py revision -m "add new table"

# Show current revision
python scripts/migrate.py current
```

### Running

```bash
# Start database
docker-compose up -d postgres redis

# Run migrations
python scripts/migrate.py upgrade head

# Run the API
uv run uvicorn my_api.main:app --reload

# Or with Docker (production)
docker-compose -f docker-compose.prod.yml up -d
```

### Access

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health**: http://localhost:8000/health/live

## 🏛️ Architecture

```
src/my_api/
├── core/           # Configuration, DI container, exceptions
├── shared/         # Generic base classes (Repository, UseCase, Router, DTOs)
├── domain/         # Entities, value objects, repository interfaces
├── application/    # Use cases, mappers, DTOs
├── adapters/       # API routes, middleware, repository implementations
└── infrastructure/ # Database, external services
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/my_api --cov-report=html

# Run specific test types
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/properties/
```

## 🔧 Development

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy src/

# Pre-commit hooks
uv run pre-commit install
uv run pre-commit run --all-files
```

## 📦 Creating a New Entity

1. **Create Entity** in `domain/entities/`:
```python
class Product(SQLModel, table=True):
    id: str = Field(default_factory=generate_ulid, primary_key=True)
    name: str
    price: float
```

2. **Create Use Case** in `application/use_cases/`:
```python
class ProductUseCase(BaseUseCase[Product, ProductCreate, ProductUpdate, ProductResponse]):
    pass
```

3. **Create Router** in `adapters/api/routes/`:
```python
router = GenericCRUDRouter(
    prefix="/products",
    tags=["Products"],
    response_model=ProductResponse,
    create_model=ProductCreate,
    update_model=ProductUpdate,
    use_case_dependency=get_product_use_case,
)
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
