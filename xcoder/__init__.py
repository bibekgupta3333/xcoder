"""
XCoder - A Local Personal Coding Agent CLI

XCoder is a local-first coding agent powered by Ollama that provides
autonomous code generation, research, and task execution capabilities.
"""

__version__ = "0.1.0"
__author__ = "Bibek Gupta"
__license__ = "MIT"

from xcoder.logging_config import get_logger

logger = get_logger(__name__)
