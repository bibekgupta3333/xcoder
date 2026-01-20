# XCoder 🤖

**A Free Local Personal Coding Agent CLI** - Powered by Ollama for autonomous code generation, research, and task execution

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Note**: XCoder is currently in active development (Alpha stage). Expect breaking changes.

## 🎯 What is XCoder?

XCoder is a local-first coding agent that runs entirely on your machine using Ollama. It provides capabilities similar to Cursor, Claude Code, and Codex CLI but keeps your code and data completely private and free.

### Key Features

- 🔒 **100% Local & Private** - All processing happens on your machine
- 🚀 **Agentic Code Generation** - Multi-step autonomous task execution
- 🧠 **Smart Code Understanding** - RAG-powered codebase vectorization
- 💾 **Persistent Memory** - Remembers context across sessions
- 🎭 **Multi-Agent Roles** - Backend, Frontend, DevOps, Testing, and more
- 🔧 **Easy Configuration** - Project-specific `.xcoderules` files
- 📦 **Zero External Dependencies** - No API keys, no cloud services

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- [Ollama](https://ollama.ai/) installed and running
- Docker and Docker Compose (for full setup)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/xcoder.git
cd xcoder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Docker Setup

```bash
# Start all services (vector DB, memory DB, etc.)
docker-compose up -d

# Verify services are running
docker-compose ps
```

### First Steps

```bash
# Initialize a project
xcoder init

# Vectorize your codebase
xcoder ragify

# Start coding with AI
xcoder agent

# Check memory
xcoder memory list
```

## 📚 Usage

### Initialize a Project

```bash
# Initialize in current directory
xcoder init

# This creates:
# - .xcoderules (project configuration)
# - .xcoder/ (local storage for vectors and memory)
```

### Vectorize Your Codebase

```bash
# Index entire codebase
xcoder ragify

# Watch for changes and auto-update
xcoder ragify --watch

# Ragify specific directories
xcoder ragify --path src/
```

### Work with Agents

```bash
# Interactive chat mode
xcoder agent

# One-shot task execution
xcoder agent "Create a FastAPI endpoint for user authentication"

# Use specific agent role
xcoder agent --role backend "Add database migration for users table"

# Multi-agent collaboration
xcoder agent --multi "Build a todo app with FastAPI backend and React frontend"
```

### Manage Memory

```bash
# List conversation history
xcoder memory list

# Search memory
xcoder memory search "authentication"

# Export memory
xcoder memory export --format json

# Clear old memories
xcoder memory clear --older-than 30d
```

## 🏗️ Architecture

```
xcoder/
├── xcoder/              # Main package
│   ├── cli.py           # CLI entry point
│   ├── agents/          # Agent implementations
│   │   ├── base.py      # Base agent class
│   │   ├── backend.py   # Backend specialist
│   │   ├── frontend.py  # Frontend specialist
│   │   └── ...
│   ├── rag/             # RAG system
│   │   ├── vectorizer.py
│   │   ├── chunker.py
│   │   └── retriever.py
│   ├── memory/          # Memory system
│   │   ├── short_term.py
│   │   └── long_term.py
│   ├── services/        # External service integrations
│   │   ├── ollama.py    # Ollama client
│   │   └── vectordb.py  # Vector database
│   └── utils/           # Utilities
├── tests/               # Test suite
├── docs/                # Documentation
├── scripts/             # Utility scripts
└── docker-compose.yml   # Service orchestration
```

## ⚙️ Configuration

### `.xcoderules` File

Create a `.xcoderules` file in your project root:

```yaml
# Project metadata
project:
  name: "my-awesome-app"
  type: "python"
  description: "A FastAPI-based web application"

# Coding standards
standards:
  style_guide: "PEP 8"
  max_line_length: 100
  use_type_hints: true
  docstring_style: "google"

# Agent behavior
agents:
  default_role: "backend"
  auto_test: true
  auto_format: true
  
  roles:
    backend:
      language: "python"
      framework: "fastapi"
      focus: ["api", "database", "business-logic"]
    
    frontend:
      language: "typescript"
      framework: "react"
      focus: ["ui", "components", "state-management"]

# RAG configuration
rag:
  chunk_size: 1000
  chunk_overlap: 200
  embedding_model: "nomic-embed-text"
  
# LLM configuration
llm:
  default_model: "deepseek-coder:6.7b"
  temperature: 0.2
  context_window: 8192

# File patterns
ignore:
  - "node_modules/**"
  - "venv/**"
  - "*.pyc"
  - ".git/**"
  - "dist/**"
```

## 🎭 Agent Roles

XCoder comes with pre-built agent roles:

- **BackendAgent** - Python/FastAPI/Django specialist
- **FrontendAgent** - React/Vue/HTML/CSS expert
- **DatabaseAgent** - SQL/ORM/migrations expert
- **DevOpsAgent** - Docker/CI/CD specialist
- **TestingAgent** - pytest/unittest expert
- **DocumentationAgent** - README/API docs writer
- **ReviewerAgent** - Code review specialist
- **DebuggerAgent** - Error analysis expert

## 🛠️ Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run tests with coverage
pytest --cov=xcoder --cov-report=html

# Format code
black xcoder tests
ruff check --fix xcoder tests
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_rag.py

# With coverage
pytest --cov=xcoder

# Verbose mode
pytest -v
```

## 📖 Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Guide](docs/configuration.md)
- [Agent System](docs/agents.md)
- [RAG System](docs/rag.md)
- [API Reference](docs/api.md)
- [Contributing](CONTRIBUTING.md)

## 🗺️ Roadmap

See [WBS.md](docs/WBS.md) for detailed work breakdown structure.

### Milestone 1: MVP ✅ (Current)
- [x] Basic CLI framework
- [x] Project initialization
- [ ] Code vectorization (ragify)
- [ ] Simple Q&A agent
- [ ] Ollama integration
- [ ] Docker setup

### Milestone 2: Core Features
- [ ] Full agent system with roles
- [ ] Long-term memory
- [ ] Task execution engine
- [ ] Code generation capabilities

### Milestone 3: Advanced Features
- [ ] Plugin system
- [ ] Multi-agent collaboration
- [ ] Advanced code understanding
- [ ] Comprehensive testing

### Milestone 4: Release
- [ ] PyPI package
- [ ] CI/CD pipeline
- [ ] Documentation
- [ ] Community setup

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by Cursor, Claude Code, and Codex CLI
- Built with [Ollama](https://ollama.ai/) for local LLM inference
- Uses [ChromaDB](https://www.trychroma.com/) for vector storage
- CLI powered by [Typer](https://typer.tiangolo.com/)

## 📞 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/yourusername/xcoder/issues)
- 💬 [Discussions](https://github.com/yourusername/xcoder/discussions)

---

**Made with ❤️ for the developer community**

*Keep your code local. Keep it free. Keep coding.*
