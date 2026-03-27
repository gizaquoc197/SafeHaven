"""Logging configuration for SafeHaven.

Provides a ``setup_logging()`` function that configures structured logging
across all modules with appropriate levels and formatters.
"""

from __future__ import annotations

import logging


def setup_logging(*, level: int = logging.INFO) -> None:
    """Configure application-wide logging.

    Call once at startup (e.g. in ``main.py``) before any other module runs.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logging.root.setLevel(level)
    logging.root.addHandler(handler)
