# Development Guide

## Setup

### 1. Clone and Setup Environment

```bash
git clone https://github.com/yourusername/xcoder.git
cd xcoder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 2. Install Pre-commit Hooks

```bash
pre-commit install
```

### 3. Start Docker Services

```bash
docker-compose up -d
```

## Development Workflow

### Code Style

- Use **Black** for code formatting (line length: 100)
- Use **Ruff** for linting
- Follow PEP 8 style guide
- Use type hints where applicable

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=xcoder --cov-report=html

# Specific test file
pytest tests/test_rag.py

# Verbose
pytest -v
```

### Code Formatting

```bash
# Format code
black xcoder tests

# Check with ruff
ruff check xcoder tests

# Fix issues
ruff check --fix xcoder tests
```

### Pre-commit Checks

```bash
# Run all pre-commit hooks
pre-commit run --all-files
```

## Project Structure

```
xcoder/
├── xcoder/              # Main package
│   ├── __init__.py
│   ├── cli.py           # CLI entry point
│   ├── agents/          # Agent implementations
│   ├── rag/             # RAG system
│   ├── memory/          # Memory system
│   ├── services/        # External services
│   └── utils/           # Utilities
├── tests/               # Test suite
├── docs/                # Documentation
└── scripts/             # Utility scripts
```

## Adding New Features

1. Create feature branch
2. Write tests first (TDD)
3. Implement feature
4. Ensure tests pass
5. Format and lint code
6. Submit pull request

## Logging

Use the configured logger:

```python
from xcoder import get_logger

logger = get_logger(__name__)

logger.info("Info message")
logger.error("Error message")
logger.debug("Debug message")
```

## Docker Development

```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f xcoder

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```
