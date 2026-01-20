# XCoder Test Suite

This directory contains tests for XCoder.

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=xcoder --cov-report=html

# Specific test file
pytest tests/test_cli.py

# Verbose
pytest -v
```

## Test Structure

- `test_cli.py` - CLI command tests
- `test_rag.py` - RAG system tests (TODO)
- `test_agents.py` - Agent system tests (TODO)
- `test_memory.py` - Memory system tests (TODO)
- `conftest.py` - Shared fixtures
