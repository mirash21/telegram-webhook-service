# Makefile for Telegram Webhook Service

.PHONY: help install dev-install test run clean format lint

# Default target
help:
	@echo "Telegram Webhook Service - Development Commands"
	@echo ""
	@echo "Usage:"
	@echo "  make install      - Install production dependencies"
	@echo "  make dev-install  - Install development dependencies"
	@echo "  make run          - Start the development server"
	@echo "  make test         - Run tests"
	@echo "  make format       - Format code with black"
	@echo "  make lint         - Run code linting"
	@echo "  make clean        - Clean build artifacts"

# Install production dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
dev-install:
	pip install -r requirements.txt
	pip install black flake8 pytest pytest-asyncio httpx

# Start development server
run:
	python main.py

# Run tests
test:
	python -m pytest tests/ -v

# Format code
format:
	black .

# Run linting
lint:
	flake8 .

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

# Development server with auto-reload
dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Create virtual environment
venv:
	python -m venv venv
	./venv/bin/pip install --upgrade pip

# Activate virtual environment (Unix/Linux/macOS)
activate:
	source venv/bin/activate

# Activate virtual environment (Windows)
activate-win:
	venv\Scripts\activate.bat