"""
XCoder Logging Configuration

Configures structured logging for the entire application.
"""

import sys
from pathlib import Path
from loguru import logger

# Remove default handler
logger.remove()

# Configuration
LOG_LEVEL = "INFO"
LOG_DIR = Path(".xcoder/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Console handler with rich formatting
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=LOG_LEVEL,
    colorize=True,
)

# File handler for all logs
logger.add(
    LOG_DIR / "xcoder.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
)

# File handler for errors only
logger.add(
    LOG_DIR / "errors.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="10 MB",
    retention="90 days",
    compression="zip",
)

# JSON log file for structured logging
logger.add(
    LOG_DIR / "xcoder.json",
    format="{message}",
    level="INFO",
    rotation="10 MB",
    retention="30 days",
    serialize=True,
)


def get_logger(name: str = "xcoder"):
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logger.bind(name=name)
