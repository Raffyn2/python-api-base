<p align="center">
  <img src="logo.png" alt="Base API Logo" width="200" />
</p>

<h1 align="center">Base API - Python Version</h1>

<p align="center">
  <strong>Framework REST API genérico e pronto para produção, construído com FastAPI e Clean Architecture</strong>
</p>

<p align="center">
  <a href="https://github.com/example/my-api/actions/workflows/ci.yml"><img src="https://github.com/example/my-api/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

---

## Visão Geral

Base API é um framework REST API reutilizável projetado para acelerar o desenvolvimento backend com Python. Fornece uma base sólida baseada nos princípios de Clean Architecture, aproveitando Python Generics para maximizar reuso de código e minimizar boilerplate.

O framework inclui tudo necessário para produção: operações CRUD genéricas type-safe, injeção de dependência, logging estruturado, middlewares de segurança, migrations de banco de dados e infraestrutura completa de testes com property-based tests.

### Principais Destaques

- **CRUD Zero Boilerplate** - Crie endpoints REST completos com apenas 3 arquivos: entidade, use case e router
- **Generics Type-Safe** - `IRepository[T]`, `BaseUseCase[T]`, `GenericCRUDRouter[T]` com suporte completo de IDE
- **Pronto para Produção** - Rate limiting, headers de segurança, request tracing, health checks inclusos
- **Padrões de Resiliência** - Circuit breaker, retry com backoff exponencial, domain events
- **Geração de Código** - Scaffold de novas entidades com `python scripts/generate_entity.py`
- **148+ Testes** - Testes unitários, integração e property-based com Hypothesis

## Arquitetura

```
src/my_api/
├── core/           # Configuração, container DI, exceções
├── shared/         # Classes base genéricas (Repository, UseCase, Router, DTOs)
├── domain/         # Entidades, value objects, interfaces de repositório
├── application/    # Use cases, mappers, DTOs
├── adapters/       # Rotas API, middleware, implementações de repositório
└── infrastructure/ # Database, logging, serviços externos
```

O projeto segue Clean Architecture com quatro camadas principais:
- **Domain** - Entidades de negócio e interfaces de repositório
- **Application** - Use cases orquestrando lógica de negócio
- **Adapters** - Rotas API, middleware, implementações concretas de repositório
- **Infrastructure** - Sessões de banco, configuração de logging, integrações externas

## Início Rápido

### Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recomendado) ou pip
- Docker & Docker Compose

### Instalação

```bash
git clone https://github.com/example/my-api.git
cd my-api

# Instalar com uv
uv sync --dev

# Ou com pip
pip install -e ".[dev]"
```

### Configuração

```bash
cp .env.example .env
# Edite .env - Obrigatório: SECURITY__SECRET_KEY (mín 32 chars)
```

### Executando

```bash
# Iniciar banco de dados
docker-compose up -d postgres redis

# Executar migrations
python scripts/migrate.py upgrade head

# Iniciar API
uv run uvicorn my_api.main:app --reload
```

### Pontos de Acesso

| Endpoint | Descrição |
|----------|-----------|
| http://localhost:8000 | Base da API |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/health/live | Health Check |

## Criando uma Nova Entidade

1. **Entidade** (`domain/entities/product.py`):
```python
class Product(SQLModel, table=True):
    id: str = Field(default_factory=generate_ulid, primary_key=True)
    name: str
    price: float
```

2. **Use Case** (`application/use_cases/product_use_case.py`):
```python
class ProductUseCase(BaseUseCase[Product, ProductCreate, ProductUpdate, ProductResponse]):
    pass
```

3. **Router** (`adapters/api/routes/products.py`):
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

Ou use o gerador: `python scripts/generate_entity.py Product name:str price:float`

## Testes

```bash
# Todos os testes
uv run pytest

# Com cobertura
uv run pytest --cov=src/my_api --cov-report=html

# Por tipo
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/properties/
```

## Desenvolvimento

```bash
uv run ruff check .      # Lint
uv run ruff format .     # Formatação
uv run mypy src/         # Type check
uv run pre-commit run --all-files  # Todas as verificações
```

## Stack Tecnológica

| Categoria | Tecnologias |
|-----------|-------------|
| Framework | FastAPI, Pydantic v2, SQLModel |
| Banco de Dados | PostgreSQL, SQLAlchemy 2.0, Alembic |
| DI | dependency-injector |
| Observabilidade | structlog, OpenTelemetry |
| Testes | pytest, Hypothesis, polyfactory |
| Segurança | slowapi, passlib, python-jose |

## Documentação

- [Arquitetura](docs/architecture.md) - Documentação detalhada da arquitetura
- [Resumo de Melhorias](docs/improvements-summary.md) - Melhorias e mudanças recentes

## Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.
