"""
SIH 26090: Telemetry & Logging Subsystem
Configures structured application logging with standardized formats and correlation tracking.
"""

import logging
import sys
from backend.app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configures root logger with uniform formatting."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True
    )

    logger = logging.getLogger("sih26090")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
