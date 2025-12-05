.PHONY: help setup install dev clean test lint format check security pre-commit docker-up docker-down migrate

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "$(BLUE)Usage:$(NC)\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup

setup: ## Complete project setup (first time)
	@echo "$(BLUE)🚀 Starting project setup...$(NC)"
	@$(MAKE) -s install
	@$(MAKE) -s setup-env
	@$(MAKE) -s setup-secrets
	@$(MAKE) -s setup-pre-commit
	@$(MAKE) -s setup-db
	@echo "$(GREEN)✅ Setup complete!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Edit .env with your configuration"
	@echo "  2. Run 'make migrate' to apply database migrations"
	@echo "  3. Run 'make dev' to start development server"

setup-env: ## Copy .env.example to .env
	@if [ ! -f .env ]; then \
		echo "$(BLUE)📄 Creating .env from template...$(NC)"; \
		cp .env.example .env; \
		echo "$(YELLOW)⚠️  IMPORTANT: Edit .env and set SECURITY__SECRET_KEY$(NC)"; \
		echo "$(YELLOW)   Generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\"$(NC)"; \
	else \
		echo "$(GREEN)✅ .env already exists$(NC)"; \
	fi

setup-secrets: ## Generate secrets baseline
	@echo "$(BLUE)🔐 Generating secrets baseline...$(NC)"
	@if command -v detect-secrets >/dev/null 2>&1; then \
		detect-secrets scan > .secrets.baseline; \
		echo "$(GREEN)✅ Secrets baseline created$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  detect-secrets not found. Run: pip install detect-secrets$(NC)"; \
	fi

setup-pre-commit: ## Install pre-commit hooks
	@echo "$(BLUE)🪝 Installing pre-commit hooks...$(NC)"
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit install; \
		pre-commit install --hook-type commit-msg; \
		echo "$(GREEN)✅ Pre-commit hooks installed$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  pre-commit not found. Run: pip install pre-commit$(NC)"; \
	fi

setup-db: ## Start database containers
	@echo "$(BLUE)🐘 Starting database containers...$(NC)"
	@docker compose -f deployments/docker/docker-compose.base.yml up -d postgres redis
	@echo "$(GREEN)✅ Databases started$(NC)"

##@ Dependencies

install: ## Install dependencies with uv
	@echo "$(BLUE)📦 Installing dependencies...$(NC)"
	@if command -v uv >/dev/null 2>&1; then \
		uv sync --dev; \
		echo "$(GREEN)✅ Dependencies installed$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  uv not found. Installing with pip...$(NC)"; \
		pip install -e ".[dev]"; \
	fi

dev: ## Install development dependencies
	@uv sync --dev

update: ## Update dependencies
	@echo "$(BLUE)🔄 Updating dependencies...$(NC)"
	@uv sync --upgrade
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

##@ Database

migrate: ## Run database migrations (upgrade)
	@echo "$(BLUE)🔄 Running migrations...$(NC)"
	@uv run alembic upgrade head
	@echo "$(GREEN)✅ Migrations applied$(NC)"

migrate-down: ## Rollback last migration
	@echo "$(YELLOW)⚠️  Rolling back last migration...$(NC)"
	@uv run alembic downgrade -1
	@echo "$(GREEN)✅ Migration rolled back$(NC)"

migrate-create: ## Create new migration (usage: make migrate-create msg="message")
	@if [ -z "$(msg)" ]; then \
		echo "$(RED)❌ Error: msg parameter required$(NC)"; \
		echo "Usage: make migrate-create msg=\"add users table\""; \
		exit 1; \
	fi
	@echo "$(BLUE)📝 Creating migration: $(msg)$(NC)"
	@uv run alembic revision --autogenerate -m "$(msg)"
	@echo "$(GREEN)✅ Migration created$(NC)"

migrate-history: ## Show migration history
	@uv run alembic history

migrate-current: ## Show current migration
	@uv run alembic current

##@ Development

run: ## Run development server
	@echo "$(BLUE)🚀 Starting development server...$(NC)"
	@uv run uvicorn src.interface.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run production server
	@echo "$(BLUE)🚀 Starting production server...$(NC)"
	@uv run uvicorn src.interface.main:app --host 0.0.0.0 --port 8000 --workers 4

shell: ## Open Python REPL with app context
	@uv run python

##@ Testing

test: ## Run all tests
	@echo "$(BLUE)🧪 Running tests...$(NC)"
	@uv run pytest tests/ -v

test-unit: ## Run unit tests only
	@echo "$(BLUE)🧪 Running unit tests...$(NC)"
	@uv run pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "$(BLUE)🧪 Running integration tests...$(NC)"
	@uv run pytest tests/integration/ -v

test-property: ## Run property tests only
	@echo "$(BLUE)🧪 Running property tests...$(NC)"
	@uv run pytest tests/properties/ -v

test-cov: ## Run tests with coverage
	@echo "$(BLUE)📊 Running tests with coverage...$(NC)"
	@uv run pytest tests/ --cov=src --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	@uv run pytest-watch tests/

##@ Code Quality

lint: ## Run linter (ruff)
	@echo "$(BLUE)🔍 Running linter...$(NC)"
	@uv run ruff check .

lint-fix: ## Run linter with auto-fix
	@echo "$(BLUE)🔧 Running linter with auto-fix...$(NC)"
	@uv run ruff check . --fix

format: ## Format code (ruff)
	@echo "$(BLUE)✨ Formatting code...$(NC)"
	@uv run ruff format .

format-check: ## Check code formatting
	@echo "$(BLUE)🔍 Checking code format...$(NC)"
	@uv run ruff format --check .

type-check: ## Run type checker (mypy)
	@echo "$(BLUE)🔍 Running type checker...$(NC)"
	@uv run mypy src/

check: format-check lint type-check ## Run all checks (format, lint, type)
	@echo "$(GREEN)✅ All checks passed!$(NC)"

##@ Security

security: ## Run security scan (bandit)
	@echo "$(BLUE)🔒 Running security scan...$(NC)"
	@uv run bandit -r src/ -ll -c pyproject.toml

security-full: ## Run comprehensive security scan
	@echo "$(BLUE)🔒 Running comprehensive security scan...$(NC)"
	@uv run bandit -r src/ -ll -c pyproject.toml
	@echo "$(BLUE)🔍 Checking for secrets...$(NC)"
	@detect-secrets scan --baseline .secrets.baseline

##@ Pre-commit

pre-commit-run: ## Run pre-commit on all files
	@echo "$(BLUE)🪝 Running pre-commit hooks...$(NC)"
	@pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	@echo "$(BLUE)🔄 Updating pre-commit hooks...$(NC)"
	@pre-commit autoupdate

##@ Docker

docker-up: ## Start all Docker services
	@echo "$(BLUE)🐳 Starting Docker services...$(NC)"
	@docker compose -f deployments/docker/docker-compose.base.yml \
		-f deployments/docker/docker-compose.dev.yml up -d
	@echo "$(GREEN)✅ Services started$(NC)"

docker-up-prod: ## Start production Docker services
	@echo "$(BLUE)🐳 Starting production services...$(NC)"
	@docker compose -f deployments/docker/docker-compose.base.yml \
		-f deployments/docker/docker-compose.production.yml up -d
	@echo "$(GREEN)✅ Production services started$(NC)"

docker-down: ## Stop all Docker services
	@echo "$(YELLOW)⏹️  Stopping Docker services...$(NC)"
	@docker compose -f deployments/docker/docker-compose.base.yml \
		-f deployments/docker/docker-compose.dev.yml down

docker-logs: ## Show Docker logs
	@docker compose -f deployments/docker/docker-compose.base.yml logs -f

docker-ps: ## Show running containers
	@docker compose -f deployments/docker/docker-compose.base.yml ps

docker-rebuild: ## Rebuild Docker images
	@echo "$(BLUE)🔨 Rebuilding Docker images...$(NC)"
	@docker compose -f deployments/docker/docker-compose.base.yml \
		-f deployments/docker/docker-compose.dev.yml build --no-cache

##@ Documentation

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)📚 Serving documentation...$(NC)"
	@uv run mkdocs serve

docs-build: ## Build documentation
	@echo "$(BLUE)📚 Building documentation...$(NC)"
	@uv run mkdocs build

##@ Cleanup

clean: ## Clean temporary files
	@echo "$(BLUE)🧹 Cleaning temporary files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Cleaned!$(NC)"

clean-all: clean ## Clean everything including venv
	@echo "$(YELLOW)⚠️  Cleaning virtual environments...$(NC)"
	@rm -rf .venv venv
	@echo "$(GREEN)✅ Deep clean complete!$(NC)"

##@ Utilities

generate-secret: ## Generate secure secret key
	@echo "$(BLUE)🔑 Generating secure secret key:$(NC)"
	@python -c "import secrets; print(secrets.token_urlsafe(64))"

version: ## Show version information
	@echo "$(BLUE)📌 Version Information:$(NC)"
	@echo "Python: $$(python --version)"
	@if command -v uv >/dev/null 2>&1; then echo "uv: $$(uv --version)"; fi
	@echo "Project: $$(grep '^version = ' pyproject.toml | cut -d'"' -f2)"

health: ## Check system health
	@echo "$(BLUE)🏥 System Health Check:$(NC)"
	@echo "Python: $$(python --version 2>&1)"
	@echo "uv: $$(uv --version 2>&1 || echo 'Not installed')"
	@echo "pre-commit: $$(pre-commit --version 2>&1 || echo 'Not installed')"
	@echo "Docker: $$(docker --version 2>&1 || echo 'Not installed')"
	@echo ""
	@echo "$(BLUE)Database Status:$(NC)"
	@docker compose -f deployments/docker/docker-compose.base.yml ps postgres redis 2>/dev/null || echo "Not running"

validate: ## Validate all configurations
	@echo "$(BLUE)🔍 Running configuration validation...$(NC)"
	@uv run python scripts/validate-config.py

validate-strict: ## Validate configurations (strict mode - fail on warnings)
	@echo "$(BLUE)🔍 Running configuration validation (strict mode)...$(NC)"
	@uv run python scripts/validate-config.py --strict

validate-fix: ## Validate and auto-fix issues
	@echo "$(BLUE)🔧 Running configuration validation with auto-fix...$(NC)"
	@uv run python scripts/validate-config.py --fix

##@ Deployment

build: ## Build production Docker image
	@echo "$(BLUE)🐳 Building production image...$(NC)"
	@docker build -t my-api:latest -f deployments/docker/dockerfiles/Dockerfile.prod .
	@echo "$(GREEN)✅ Image built: my-api:latest$(NC)"

deploy-staging: ## Deploy to staging (placeholder)
	@echo "$(YELLOW)⚠️  Deploy to staging not configured$(NC)"
	@echo "Configure your deployment strategy in this target"

deploy-prod: ## Deploy to production (placeholder)
	@echo "$(YELLOW)⚠️  Deploy to production not configured$(NC)"
	@echo "Configure your deployment strategy in this target"

##@ CI/CD

ci-test: ## Run CI test suite
	@echo "$(BLUE)🔄 Running CI test suite...$(NC)"
	@uv run pytest tests/ -v --cov=src --cov-report=xml --cov-report=term

ci-lint: ## Run CI linting
	@echo "$(BLUE)🔍 Running CI linting...$(NC)"
	@uv run ruff check .
	@uv run ruff format --check .
	@uv run mypy src/

ci-security: ## Run CI security checks
	@echo "$(BLUE)🔒 Running CI security checks...$(NC)"
	@uv run bandit -r src/ -ll -c pyproject.toml
	@detect-secrets scan --baseline .secrets.baseline

ci: validate-strict ci-lint ci-security ci-test ## Run full CI pipeline
	@echo "$(GREEN)✅ CI pipeline complete!$(NC)"

##@ ArgoCD / GitOps

validate-argocd: ## Validate ArgoCD manifests
	@echo "$(BLUE)🔍 Validating ArgoCD manifests...$(NC)"
	@chmod +x scripts/validate-argocd.sh
	@./scripts/validate-argocd.sh

argocd-install-dev: ## Install ArgoCD in dev environment
	@echo "$(BLUE)🚀 Installing ArgoCD (dev)...$(NC)"
	@kubectl apply -k deployments/argocd/overlays/dev
	@echo "$(GREEN)✅ ArgoCD installed$(NC)"
	@echo "$(YELLOW)Run 'make argocd-password' to get admin password$(NC)"

argocd-install-staging: ## Install ArgoCD in staging environment
	@echo "$(BLUE)🚀 Installing ArgoCD (staging)...$(NC)"
	@kubectl apply -k deployments/argocd/overlays/staging
	@echo "$(GREEN)✅ ArgoCD installed$(NC)"

argocd-install-prod: ## Install ArgoCD in production environment
	@echo "$(BLUE)🚀 Installing ArgoCD (prod)...$(NC)"
	@kubectl apply -k deployments/argocd/overlays/prod
	@echo "$(GREEN)✅ ArgoCD installed$(NC)"

argocd-password: ## Get ArgoCD admin password
	@echo "$(BLUE)🔑 ArgoCD Admin Password:$(NC)"
	@kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo

argocd-port-forward: ## Port-forward ArgoCD UI
	@echo "$(BLUE)🌐 Port-forwarding ArgoCD UI to https://localhost:8080$(NC)"
	@kubectl port-forward svc/argocd-server -n argocd 8080:443

argocd-sync: ## Sync all ArgoCD applications
	@echo "$(BLUE)🔄 Syncing all applications...$(NC)"
	@argocd app list -o name | xargs -I {} argocd app sync {}

argocd-sync-dev: ## Sync dev application
	@echo "$(BLUE)🔄 Syncing dev application...$(NC)"
	@argocd app sync python-api-base-dev

argocd-sync-staging: ## Sync staging application
	@echo "$(BLUE)🔄 Syncing staging application...$(NC)"
	@argocd app sync python-api-base-staging

argocd-sync-prod: ## Sync production application (manual)
	@echo "$(YELLOW)⚠️  Syncing production application...$(NC)"
	@argocd app sync python-api-base-prod

argocd-status: ## Show ArgoCD applications status
	@echo "$(BLUE)📊 ArgoCD Applications Status:$(NC)"
	@argocd app list

argocd-diff: ## Show diff for all applications
	@echo "$(BLUE)📝 Application Diffs:$(NC)"
	@argocd app list -o name | xargs -I {} sh -c 'echo "=== {} ===" && argocd app diff {}'

test-argocd: ## Run ArgoCD property tests
	@echo "$(BLUE)🧪 Running ArgoCD property tests...$(NC)"
	@uv run pytest tests/properties/test_argocd_manifests.py -v


##@ gRPC

proto-gen: ## Generate Python code from proto files
	@echo "$(BLUE)🔧 Generating gRPC code from proto files...$(NC)"
	@mkdir -p src/infrastructure/grpc/generated
	@python -m grpc_tools.protoc \
		-I protos \
		-I protos/common \
		--python_out=src/infrastructure/grpc/generated \
		--grpc_python_out=src/infrastructure/grpc/generated \
		--pyi_out=src/infrastructure/grpc/generated \
		protos/common/*.proto protos/examples/*.proto
	@touch src/infrastructure/grpc/generated/__init__.py
	@echo "$(GREEN)✅ gRPC code generated$(NC)"

proto-clean: ## Clean generated proto files
	@echo "$(BLUE)🧹 Cleaning generated proto files...$(NC)"
	@rm -rf src/infrastructure/grpc/generated/*_pb2*.py
	@rm -rf src/infrastructure/grpc/generated/*_pb2*.pyi
	@echo "$(GREEN)✅ Generated files cleaned$(NC)"

proto-lint: ## Lint proto files with buf
	@echo "$(BLUE)🔍 Linting proto files...$(NC)"
	@cd protos && buf lint
	@echo "$(GREEN)✅ Proto files are valid$(NC)"

grpc-run: ## Run gRPC server
	@echo "$(BLUE)🚀 Starting gRPC server...$(NC)"
	@uv run python -m src.infrastructure.grpc.server

test-grpc: ## Run gRPC property tests
	@echo "$(BLUE)🧪 Running gRPC property tests...$(NC)"
	@uv run pytest tests/properties/test_grpc*.py -v


##@ Dapr

dapr-up: ## Start Dapr development environment with Docker Compose
	@echo "$(BLUE)🚀 Starting Dapr development environment...$(NC)"
	@docker compose -f deployments/dapr/docker-compose.dapr.yaml up -d
	@echo "$(GREEN)✅ Dapr environment started$(NC)"
	@echo "$(YELLOW)Services:$(NC)"
	@echo "  - API: http://localhost:8000"
	@echo "  - Dapr Dashboard: http://localhost:8080 (if installed)"
	@echo "  - Jaeger UI: http://localhost:16686"
	@echo "  - Prometheus: http://localhost:9091"

dapr-down: ## Stop Dapr development environment
	@echo "$(YELLOW)⏹️  Stopping Dapr environment...$(NC)"
	@docker compose -f deployments/dapr/docker-compose.dapr.yaml down
	@echo "$(GREEN)✅ Dapr environment stopped$(NC)"

dapr-logs: ## Show Dapr sidecar logs
	@echo "$(BLUE)📋 Dapr sidecar logs:$(NC)"
	@docker compose -f deployments/dapr/docker-compose.dapr.yaml logs -f python-api-dapr

dapr-logs-all: ## Show all Dapr service logs
	@docker compose -f deployments/dapr/docker-compose.dapr.yaml logs -f

dapr-ps: ## Show Dapr running containers
	@docker compose -f deployments/dapr/docker-compose.dapr.yaml ps

dapr-restart: ## Restart Dapr environment
	@echo "$(BLUE)🔄 Restarting Dapr environment...$(NC)"
	@$(MAKE) -s dapr-down
	@$(MAKE) -s dapr-up

dapr-health: ## Check Dapr sidecar health
	@echo "$(BLUE)🏥 Checking Dapr sidecar health...$(NC)"
	@curl -s http://localhost:3500/v1.0/healthz && echo "$(GREEN)✅ Sidecar healthy$(NC)" || echo "$(RED)❌ Sidecar unhealthy$(NC)"

dapr-metadata: ## Show Dapr metadata
	@echo "$(BLUE)📊 Dapr metadata:$(NC)"
	@curl -s http://localhost:3500/v1.0/metadata | python -m json.tool

dapr-components: ## List Dapr components
	@echo "$(BLUE)🧩 Dapr components:$(NC)"
	@curl -s http://localhost:3500/v1.0/metadata | python -c "import sys,json; d=json.load(sys.stdin); [print(f\"  - {c['name']} ({c['type']})\") for c in d.get('components',[])]"

dapr-run: ## Run application with Dapr sidecar (local mode)
	@echo "$(BLUE)🚀 Starting application with Dapr sidecar...$(NC)"
	@dapr run --app-id python-api --app-port 8000 --dapr-http-port 3500 --dapr-grpc-port 50001 \
		--components-path deployments/dapr/components \
		--config deployments/dapr/config/config.yaml \
		-- uv run uvicorn src.main:app --host 0.0.0.0 --port 8000

dapr-run-debug: ## Run application with Dapr in debug mode
	@echo "$(BLUE)🐛 Starting application with Dapr (debug mode)...$(NC)"
	@dapr run --app-id python-api --app-port 8000 --dapr-http-port 3500 --dapr-grpc-port 50001 \
		--components-path deployments/dapr/components \
		--config deployments/dapr/config/config.yaml \
		--log-level debug \
		-- uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

test-dapr: ## Run Dapr property tests
	@echo "$(BLUE)🧪 Running Dapr property tests...$(NC)"
	@uv run pytest tests/properties/dapr/ -v

test-dapr-cov: ## Run Dapr tests with coverage
	@echo "$(BLUE)📊 Running Dapr tests with coverage...$(NC)"
	@uv run pytest tests/properties/dapr/ --cov=src/infrastructure/dapr --cov-report=html --cov-report=term

