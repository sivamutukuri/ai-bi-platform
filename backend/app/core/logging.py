"""Centralised logging configuration using loguru.

Intercepts the standard logging module so third-party libraries
(uvicorn, sqlalchemy) route through a single structured sink.
"""
import logging
import sys

from loguru import logger

from app.core.config import settings


class InterceptHandler(logging.Handler):
    """Redirect standard logging records to loguru."""

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logging() -> None:
    """Configure application-wide logging sinks."""
    logger.remove()
    log_level = "DEBUG" if settings.DEBUG else "INFO"
    logger.add(
        sys.stdout,
        level=log_level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        backtrace=settings.DEBUG,
        diagnose=settings.DEBUG,
    )
    logger.add(
        "logs/app.log",
        level=log_level,
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(name).handlers = [InterceptHandler()]

    logger.info("Logging configured (level=%s)" % log_level)


__all__ = ["logger", "configure_logging"]
