.PHONY: help install test lint format clean coverage docker-build docker-up docker-down docker-logs

# ===========================================
# COLORS
# ===========================================
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# ===========================================
# HELP
# ===========================================
help: ## Show this help message
	@echo "$(BLUE)╔════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║      RecoLab v2 - Make Commands       ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /Development/ {next} /Docker/ {exit} {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Docker:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /Docker/ {found=1} found {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ===========================================
# DEVELOPMENT
# ===========================================
install: ## Install dependencies
	@echo "$(BLUE) Installing dependencies...$(NC)"
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "$(GREEN)✓ Dependencies installed!$(NC)"

install-dev: install ## Install development dependencies
	@echo "$(BLUE) Installing development tools...$(NC)"
	pip install pre-commit
	pre-commit install
	@echo "$(GREEN)✓ Development environment ready!$(NC)"

# ===========================================
# TESTING
# ===========================================
test: ## Run all tests
	@echo "$(BLUE) Running tests...$(NC)"
	pytest tests/ -v
	@echo "$(GREEN)✓ Tests completed!$(NC)"

test-unit: ## Run only unit tests
	@echo "$(BLUE) Running unit tests...$(NC)"
	pytest tests/unit -v -m "not integration"
	@echo "$(GREEN)✓ Unit tests completed!$(NC)"

test-integration: ## Run only integration tests
	@echo "$(BLUE) Running integration tests...$(NC)"
	pytest tests/integration -v -m integration
	@echo "$(GREEN)✓ Integration tests completed!$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE) Running tests in watch mode...$(NC)"
	pytest-watch tests/ -v

coverage: ## Run tests with coverage report
	@echo "$(BLUE) Running tests with coverage...$(NC)"
	pytest tests/ \
		--cov=src \
		--cov-report=html \
		--cov-report=term-missing \
		--cov-report=xml \
		-v
	@echo "$(GREEN)✓ Coverage report generated!$(NC)"
	@echo "$(YELLOW) Open htmlcov/index.html to view report$(NC)"

coverage-open: coverage ## Run coverage and open report
	@echo "$(BLUE) Opening coverage report...$(NC)"
	python -m webbrowser htmlcov/index.html

# ===========================================
# CODE QUALITY
# ===========================================
lint: ## Run all linting checks
	@echo "$(BLUE) Running linting checks...$(NC)"
	@echo "$(YELLOW)→ Checking with flake8...$(NC)"
	flake8 src/ tests/ --count --statistics
	@echo "$(YELLOW)→ Checking import sorting...$(NC)"
	isort --check-only --diff src/ tests/
	@echo "$(YELLOW)→ Checking code formatting...$(NC)"
	black --check --diff src/ tests/
	@echo "$(GREEN) All linting checks passed!$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE) Formatting code...$(NC)"
	@echo "$(YELLOW)→ Sorting imports...$(NC)"
	isort src/ tests/
	@echo "$(YELLOW)→ Formatting with black...$(NC)"
	black src/ tests/
	@echo "$(GREEN) Code formatted!$(NC)"

security: ## Run security checks with bandit
	@echo "$(BLUE) Running security checks...$(NC)"
	bandit -r src/ -f screen
	@echo "$(GREEN) Security scan completed!$(NC)"

# ===========================================
# DATABASE
# ===========================================
db-migrate: ## Run database migrations
	@echo "$(BLUE) Running migrations...$(NC)"
	alembic upgrade head
	@echo "$(GREEN) Migrations completed!$(NC)"

db-rollback: ## Rollback last migration
	@echo "$(YELLOW) Rolling back last migration...$(NC)"
	alembic downgrade -1
	@echo "$(GREEN) Rollback completed!$(NC)"

db-reset: ## Reset database (WARNING: destroys data)
	@echo "$(RED) WARNING: This will destroy all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE) Resetting database...$(NC)"; \
		alembic downgrade base; \
		alembic upgrade head; \
		echo "$(GREEN) Database reset!$(NC)"; \
	fi

db-seed: ## Seed database with sample data
	@echo "$(BLUE) Seeding database...$(NC)"
	python scripts/load_movielens.py
	@echo "$(GREEN) Database seeded!$(NC)"

# ===========================================
# APPLICATION
# ===========================================
run: ## Run the API server
	@echo "$(BLUE) Starting API server...$(NC)"
	python run.py

run-dev: ## Run the API server in development mode
	@echo "$(BLUE) Starting API server (dev mode)...$(NC)"
	uvicorn src.presentation.main:app --reload --host 0.0.0.0 --port 8000

# ===========================================
# DOCKER
# ===========================================
docker-build: ## Docker: Build images
	@echo "$(BLUE) Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN) Images built!$(NC)"

docker-up: ## Docker: Start all services
	@echo "$(BLUE) Starting Docker containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN) Containers started!$(NC)"
	@echo "$(YELLOW) API: http://localhost:8000$(NC)"
	@echo "$(YELLOW) Docs: http://localhost:8000/docs$(NC)"
	@echo "$(YELLOW) PgAdmin: http://localhost:5050$(NC)"
	@echo "$(YELLOW) Redis Commander: http://localhost:8081$(NC)"

docker-down: ## Docker: Stop all services
	@echo "$(BLUE) Stopping Docker containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Containers stopped!$(NC)"

docker-down-volumes: ## Docker: Stop and remove volumes (WARNING: deletes data)
	@echo "$(RED)  WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE) Stopping containers and removing volumes...$(NC)"; \
		docker-compose down -v; \
		echo "$(GREEN)✓ Containers and volumes removed!$(NC)"; \
	fi

docker-logs: ## Docker: Show logs
	@echo "$(BLUE) Showing Docker logs...$(NC)"
	docker-compose logs -f

docker-logs-api: ## Docker: Show API logs only
	@echo "$(BLUE) Showing API logs...$(NC)"
	docker-compose logs -f api

docker-restart: ## Docker: Restart all services
	@echo "$(BLUE) Restarting Docker containers...$(NC)"
	docker-compose restart
	@echo "$(GREEN) Containers restarted!$(NC)"

docker-ps: ## Docker: Show running containers
	@echo "$(BLUE) Running containers:$(NC)"
	docker-compose ps

docker-shell: ## Docker: Open shell in API container
	@echo "$(BLUE) Opening shell in API container...$(NC)"
	docker-compose exec api /bin/bash

docker-db-shell: ## Docker: Open PostgreSQL shell
	@echo "$(BLUE) Opening PostgreSQL shell...$(NC)"
	docker-compose exec postgres psql -U recolab -d recolab

# ===========================================
# CLEANUP
# ===========================================
clean: ## Clean up cache and temporary files
	@echo "$(BLUE) Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf .tox/
	rm -rf coverage.xml
	rm -rf junit.xml
	@echo "$(GREEN) Cleaned up!$(NC)"

clean-docker: ## Clean Docker resources
	@echo "$(BLUE) Cleaning Docker resources...$(NC)"
	docker-compose down --rmi all --volumes --remove-orphans
	@echo "$(GREEN) Docker resources cleaned!$(NC)"

# ===========================================
# CI/CD
# ===========================================
ci: lint test ## Run CI checks locally
	@echo "$(GREEN) All CI checks passed!$(NC)"

ci-full: clean install lint test coverage security ## Run full CI pipeline
	@echo "$(GREEN) Full CI pipeline completed!$(NC)"

# ===========================================
# SETUP & DEPLOYMENT
# ===========================================
setup: install db-migrate ## Setup project (install + migrate)
	@echo "$(BLUE) Setting up project...$(NC)"
	@echo "$(GREEN)Project setup completed!$(NC)"
	@echo "$(YELLOW) Run 'make run' to start the server$(NC)"

setup-docker: ## Setup project with Docker
	@echo "$(BLUE) Setting up project with Docker...$(NC)"
	make docker-build
	make docker-up
	@echo "$(YELLOW) Waiting for services to be ready...$(NC)"
	sleep 10
	docker-compose exec api alembic upgrade head
	@echo "$(GREEN) Project setup completed!$(NC)"
	@echo "$(YELLOW)Access API at http://localhost:8000/docs$(NC)"

# ===========================================
# UTILITIES
# ===========================================
check: ## Check if everything is working
	@echo "$(BLUE) Running health checks...$(NC)"
	@echo "$(YELLOW)→ Python version:$(NC)"
	python --version
	@echo "$(YELLOW)→ Pip version:$(NC)"
	pip --version
	@echo "$(YELLOW)→ Dependencies:$(NC)"
	pip list | grep -E "(fastapi|sqlalchemy|pytest|black)" || echo "Dependencies not installed"
	@echo "$(GREEN)✓ Health checks completed!$(NC)"

info: ## Show project information
	@echo "$(BLUE)╔════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║         RecoLab v2 - Info             ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW) Project Structure:$(NC)"
	@echo "  • src/           - Application code"
	@echo "  • tests/         - Test suite"
	@echo "  • scripts/       - Utility scripts"
	@echo "  • models/        - ML models"
	@echo ""
	@echo "$(YELLOW) Quick Start:$(NC)"
	@echo "  1. make setup         - Setup project"
	@echo "  2. make run          - Start server"
	@echo "  3. Visit http://localhost:8000/docs"
	@echo ""
	@echo "$(YELLOW) Docker Quick Start:$(NC)"
	@echo "  1. make setup-docker - Setup with Docker"
	@echo "  2. Visit http://localhost:8000/docs"

# ===========================================
# ALL-IN-ONE COMMANDS
# ===========================================
all: format lint test coverage ## Run all checks
	@echo "$(GREEN) All checks completed successfully!$(NC)"

dev-setup: install-dev setup db-seed ## Complete development setup
	@echo "$(GREEN) Development environment ready!$(NC)"
	@echo "$(YELLOW) Run 'make run-dev' to start developing$(NC)"