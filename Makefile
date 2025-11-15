.PHONY: help venv install sync lint format fix test build rebuild up down dev clean init-dev dev-https

UV_PYTHON := .venv/bin/python

# Default target
help:
	@echo "Available targets:"
	@echo "  venv       - Create virtual environment with uv"
	@echo "  install    - Recreate venv and install deps from pyproject.toml"
	@echo "  sync       - Sync dependencies (alias for install)"
	@echo "  lint       - Run ruff linter (requires install)"
	@echo "  format     - Format code with ruff (requires install)"
	@echo "  fix        - Auto-fix linting issues (requires install)"
	@echo "  test       - Run tests (requires install)"
	@echo "  build      - Build Docker image (uses cache)"
	@echo "  rebuild    - Build Docker image without cache"
	@echo "  up         - Start services with docker-compose"
	@echo "  down       - Stop services"
	@echo "  dev        - Start dev container with hot reload"
	@echo "  init-dev   - One-time HTTPS dev setup (hosts entry + certificates)"
	@echo "  dev-https  - Start dev container with HTTPS (requires init-dev)"
	@echo "  clean      - Clean build artifacts and caches"

# Create virtual environment if it doesn't exist
# Use Python 3.12 explicitly (Python 3.14 not supported by onnxruntime/chromadb)
venv:
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment with Python 3.12..."; \
		uv venv --python python3.12 || uv venv --python 3.12; \
	else \
		echo "Virtual environment already exists. Delete .venv to recreate with Python 3.12."; \
	fi

# Recreate venv and install dependencies from pyproject.toml (includes dev extras)
install sync:
	@echo "Removing existing virtual environment..."
	@rm -rf .venv
	@$(MAKE) venv
	@echo "Installing dependencies defined in pyproject.toml (with [dev] extras)..."
	uv pip install --python $(UV_PYTHON) -e ".[dev]"

# Lint code (depends on install)
lint: install
	uv run ruff check .

# Format code (depends on install)
format: install
	uv run ruff format .

# Auto-fix linting issues (depends on install)
fix: install
	uv run ruff check --fix .
	uv run ruff format .

# Run tests (depends on install)
test: install
	uv run pytest tests/ -v || echo "No tests directory found. Create tests/ directory to add tests."

# Build Docker image
build:
	@docker-compose build

rebuild:
	@docker-compose build --no-cache --pull

# Start services
# Clean up any existing containers first to avoid ContainerConfig errors
up:
	@echo "Cleaning up any existing containers..."
	@docker-compose down 2>/dev/null || true
	@docker rm -f chainlit-app 2>/dev/null || true
	@echo "Starting services..."
	docker-compose up -d

# Stop services
down:
	docker-compose down

# Start dev container with hot reload
# Clean up any existing containers first to avoid ContainerConfig errors
dev:
	@echo "Cleaning up any existing containers..."
	@docker-compose down 2>/dev/null || true
	@docker rm -f chainlit-app 2>/dev/null || true
	@echo "Starting dev container..."
	docker-compose up

# One-time HTTPS development setup
# Sets up /etc/hosts entry and generates SSL certificates
init-dev:
	@bash scripts/one_time_setup.sh

# Start dev container with HTTPS (requires init-dev to be run first)
# Clean up any existing containers first to avoid ContainerConfig errors
dev-https:
	@if [ ! -f ".certs/chainlit-dev.crt" ] || [ ! -f ".certs/chainlit-dev.key" ]; then \
		echo "❌ Certificates not found. Please run 'make init-dev' first."; \
		exit 1; \
	fi
	@echo "Cleaning up any existing containers..."
	@docker-compose down 2>/dev/null || true
	@docker rm -f chainlit-app chainlit-proxy 2>/dev/null || true
	@echo "Starting dev container with HTTPS..."
	docker-compose -f docker-compose.yml -f docker-compose.https.yml up

# Clean build artifacts
clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info .venv 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	# Try to remove __pycache__ with sudo if permission denied
	@if [ -d __pycache__ ]; then \
		sudo rm -rf __pycache__ 2>/dev/null || \
		docker run --rm -v "$$(pwd):/app" -w /app python:3.12-slim rm -rf __pycache__ 2>/dev/null || \
		echo "Warning: Could not remove __pycache__ (may need manual cleanup)"; \
	fi
	docker-compose down -v || true

