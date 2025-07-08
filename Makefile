.PHONY: help install test lint format clean docker-build docker-run docker-stop setup-dev

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies"
	@echo "  setup-dev    - Setup development environment"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  format-check - Check code formatting"
	@echo "  security     - Run security checks"
	@echo "  clean        - Clean temporary files"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"
	@echo "  docker-stop  - Stop Docker container"
	@echo "  db-init      - Initialize database"
	@echo "  db-migrate   - Run database migrations"
	@echo "  serve        - Start development server"
	@echo "  ci           - Run full CI pipeline locally"

# Python environment setup
install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

setup-dev: install
	pre-commit install
	python database.py

# Testing
test:
	python -m pytest test_agora.py -v

test-cov:
	python -m pytest test_agora.py -v --cov=. --cov-report=term-missing --cov-report=html

# Code quality
lint:
	flake8 .
	mypy .
	bandit -r . -f json -o bandit-report.json

format:
	black .
	isort .

format-check:
	black --check .
	isort --check-only .

security:
	bandit -r . -f json -o bandit-report.json
	safety check

# Database operations
db-init:
	python database.py

db-migrate:
	python database.py

# Development server
serve:
	python main.py

# Docker operations
docker-build:
	docker build -t agora:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf bandit-report.json
	rm -rf safety-report.json

# Full CI pipeline
ci: format-check lint security test-cov

# Development workflow
dev: clean setup-dev test serve