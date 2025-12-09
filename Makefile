# AI-Ops Platform Makefile
# Useful commands for development and operations

.PHONY: help install dev test lint docker-up docker-down infra-init infra-plan infra-apply clean

# Variables
PYTHON := python3
PIP := pip
DOCKER_COMPOSE := docker compose

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

help: ## Show this help
	@echo ""
	@echo "$(CYAN)🔮 AI-Ops Platform$(RESET)"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ==================== Development ====================

install: ## Install application dependencies
	@echo "$(CYAN)📦 Installing dependencies...$(RESET)"
	cd app && $(PIP) install -r requirements.txt
	cd ai-optimizer && $(PIP) install -r requirements.txt

dev: ## Run application in development mode
	@echo "$(CYAN)🚀 Starting development server...$(RESET)"
	cd app && uvicorn main:app --reload --port 8000

test: ## Run tests
	@echo "$(CYAN)🧪 Running tests...$(RESET)"
	cd app && pytest tests/ -v

test-unit: ## Run unit tests only
	cd app && pytest tests/ -v -m unit

test-integration: ## Run integration tests only
	cd app && pytest tests/ -v -m integration

lint: ## Run linter
	@echo "$(CYAN)🔬 Running linter...$(RESET)"
	ruff check app/ ai-optimizer/

format: ## Format code
	@echo "$(CYAN)✨ Formatting code...$(RESET)"
	ruff format app/ ai-optimizer/

# ==================== Docker ====================

docker-up: ## Start all services with Docker Compose
	@echo "$(CYAN)🐳 Starting services...$(RESET)"
	$(DOCKER_COMPOSE) up -d
	@echo ""
	@echo "$(GREEN)✅ Services started:$(RESET)"
	@echo "  - API:        http://localhost:8000"
	@echo "  - Dashboard:  http://localhost:8080"
	@echo "  - Jaeger:     http://localhost:16686"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Grafana:    http://localhost:3000 (admin/admin)"
	@echo ""

docker-down: ## Stop all services
	@echo "$(CYAN)🛑 Stopping services...$(RESET)"
	$(DOCKER_COMPOSE) down

docker-logs: ## Show service logs
	$(DOCKER_COMPOSE) logs -f

docker-build: ## Rebuild images
	@echo "$(CYAN)🔨 Rebuilding images...$(RESET)"
	$(DOCKER_COMPOSE) build

# ==================== Infrastructure ====================

infra-init: ## Initialize OpenTofu
	@echo "$(CYAN)🌐 Initializing OpenTofu...$(RESET)"
	cd infrastructure && tofu init

infra-plan: ## Show infrastructure plan
	@echo "$(CYAN)📋 Generating plan...$(RESET)"
	cd infrastructure && tofu plan

infra-apply: ## Apply infrastructure changes
	@echo "$(YELLOW)⚠️  Applying infrastructure changes...$(RESET)"
	cd infrastructure && tofu apply

infra-destroy: ## Destroy infrastructure
	@echo "$(YELLOW)⚠️  Destroying infrastructure...$(RESET)"
	cd infrastructure && tofu destroy

infra-fmt: ## Format OpenTofu files
	cd infrastructure && tofu fmt -recursive

infra-validate: ## Validate OpenTofu configuration
	cd infrastructure && tofu validate

# ==================== AI Optimizer ====================

optimize: ## Run pipeline analyzer
	@echo "$(CYAN)🤖 Analyzing pipelines...$(RESET)"
	cd ai-optimizer && $(PYTHON) analyzer.py

optimize-workflow: ## Optimize a specific workflow
	@echo "$(CYAN)🤖 Optimizing workflow...$(RESET)"
	cd ai-optimizer && $(PYTHON) optimizer.py .github/workflows/ci.yml

# ==================== Utilities ====================

clean: ## Clean temporary files
	@echo "$(CYAN)🧹 Cleaning...$(RESET)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .coverage htmlcov/ 2>/dev/null || true

setup-venv: ## Create virtual environment
	@echo "$(CYAN)🐍 Creating virtual environment...$(RESET)"
	$(PYTHON) -m venv .venv
	@echo "$(GREEN)✅ Activate with: source .venv/bin/activate$(RESET)"

check: lint test ## Run linter and tests

all: install check ## Install and verify everything
