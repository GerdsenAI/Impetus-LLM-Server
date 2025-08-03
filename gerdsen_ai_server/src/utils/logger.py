import sys
from pathlib import Path

from loguru import logger

from ..config.settings import settings


def setup_logger():
    """Configure application logging with loguru"""
    # Remove default logger
    logger.remove()

    # Console logging with color
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Add console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=settings.environment == "development"
    )

    # Add file handler if log file is specified
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_path,
            format=log_format.replace("<green>", "").replace("</green>", "")
                           .replace("<cyan>", "").replace("</cyan>", "")
                           .replace("<level>", "").replace("</level>", ""),
            level=settings.log_level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            backtrace=True,
            diagnose=settings.environment == "development"
        )

    # Add error file handler for production
    if settings.environment == "production":
        error_log_path = Path.home() / ".impetus" / "logs" / "errors.log"
        error_log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            error_log_path,
            format=log_format.replace("<green>", "").replace("</green>", "")
                           .replace("<cyan>", "").replace("</cyan>", "")
                           .replace("<level>", "").replace("</level>", ""),
            level="ERROR",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=False
        )

    logger.info(f"Logger initialized for {settings.environment} environment")
    return logger


# Initialize logger on import
app_logger = setup_logger()
