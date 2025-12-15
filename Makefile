.PHONY: help setup install install-dev test test-unit test-integration coverage format lint type-check clean run docker-build docker-up docker-down docker-dev docker-prod

help:
	@echo "Available commands:"
	@echo "  make setup            - Run complete project setup"
	@echo "  make install          - Install production dependencies"
	@echo "  make install-dev      - Install development dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make coverage         - Run tests with coverage report"
	@echo "  make format           - Format code with black and isort"
	@echo "  make lint             - Run flake8 linter"
	@echo "  make type-check       - Run mypy type checker"
	@echo "  make clean            - Remove generated files"
	@echo "  make run              - Run the application locally"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-dev       - Start Docker in development mode"
	@echo "  make docker-prod      - Start Docker in production mode"
	@echo "  make docker-up        - Start Docker containers (alias for docker-dev)"
	@echo "  make docker-down      - Stop Docker containers"
	@echo "  make docker-logs      - View Docker logs"
	@echo "  make all              - Run all checks (format, lint, type-check, tests)"

setup:
	@chmod +x setup.sh
	@./setup.sh

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

coverage:
	pytest --cov=src --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

format:
	black src/ tests/
	isort src/ tests/

lint:
	flake8 src/ tests/

type-check:
	mypy src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -f tasks.db

run:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker-compose build

docker-dev:
	@echo "Starting in DEVELOPMENT mode..."
	docker-compose up -d
	@echo "Application running at http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs and http://localhost:8000/redoc"

docker-prod:
	@echo "Starting in PRODUCTION mode..."
	docker-compose -f docker-compose.yml up -d
	@echo "Application running at http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs and http://localhost:8000/redoc"

docker-up: docker-dev
	@echo "Use 'make docker-dev' for development or 'make docker-prod' for production"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

all: format lint type-check test
	@echo "All checks passed!"

