"""Shared logger factory for application modules."""

from __future__ import annotations

import logging


def get_app_logger(name: str) -> logging.Logger:
    """Return a configured namespaced logger instance."""

    return logging.getLogger(name)
