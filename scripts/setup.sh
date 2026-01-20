#!/bin/bash
# Setup script for XCoder development environment

set -e

echo "🚀 Setting up XCoder development environment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "⚠️  Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install xcoder in editable mode
echo "📦 Installing xcoder in development mode..."
pip install -e ".[dev]"

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p .xcoder/data .xcoder/logs .xcoder/cache

# Check if Ollama is installed
echo "🤖 Checking for Ollama..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is installed"
else
    echo "⚠️  Ollama is not installed. Please install from https://ollama.ai/"
fi

# Check if Docker is installed
echo "🐳 Checking for Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed"
    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose is installed"
    else
        echo "⚠️  Docker Compose is not installed"
    fi
else
    echo "⚠️  Docker is not installed. Please install from https://www.docker.com/"
fi

# Create .env file from example
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created (please update as needed)"
else
    echo "⚠️  .env file already exists"
fi

echo ""
echo "${GREEN}✨ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo "2. Start Docker services: ${YELLOW}docker-compose up -d${NC}"
echo "3. Run tests: ${YELLOW}pytest${NC}"
echo "4. Start coding: ${YELLOW}xcoder --help${NC}"
echo ""
