from __future__ import annotations

import logging

import pytest

from debate.logging_setup import RotatingJsonlHandler


@pytest.fixture(autouse=True)
def isolate_debate_logger_handlers():
    debate_logger = logging.getLogger("debate")
    saved = debate_logger.handlers[:]
    debate_logger.handlers.clear()
    yield
    for handler in list(debate_logger.handlers):
        if isinstance(handler, RotatingJsonlHandler):
            handler.close()
    debate_logger.handlers.clear()
    for handler in saved:
        debate_logger.addHandler(handler)


@pytest.fixture
def app_config():
    from debate.config import load_config

    return load_config()
