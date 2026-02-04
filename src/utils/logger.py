"""
Logging utility using loguru.
"""
import sys
import os
from loguru import logger

from src.config.settings import settings


def setup_logging():
    """Configure logging for the application."""
    # Remove default logger
    logger.remove()

    # Create logs directory
    log_dir = os.path.dirname(settings.log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # Console logging
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    # File logging
    logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )

    return logger


# Export configured logger
__all__ = ["logger", "setup_logging"]
