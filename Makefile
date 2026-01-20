.PHONY: help install test lint format clean docker-up docker-down

help:
	@echo "XCoder Makefile Commands:"
	@echo "  make install       - Install dependencies and setup dev environment"
	@echo "  make test          - Run tests with coverage"
	@echo "  make lint          - Run linting checks"
	@echo "  make format        - Format code with black and ruff"
	@echo "  make clean         - Clean build artifacts and caches"
	@echo "  make docker-up     - Start Docker services"
	@echo "  make docker-down   - Stop Docker services"
	@echo "  make run           - Run xcoder CLI"

install:
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	. venv/bin/activate && pip install -e ".[dev]"
	. venv/bin/activate && pre-commit install

test:
	pytest --cov=xcoder --cov-report=term-missing --cov-report=html

lint:
	ruff check xcoder tests
	black --check xcoder tests

format:
	black xcoder tests
	ruff check --fix xcoder tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

run:
	python -m xcoder.cli
