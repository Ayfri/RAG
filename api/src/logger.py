"""
Lightweight Rich-powered logger utilities for the API.

Features:
- Colorized logs and nice tracebacks via Rich (required)
- Compact format: time | level | name | message
- log_step context manager: start/end timing and exceptions with stack traces
- setup_logging to initialize root logging once, honoring LOG_LEVEL env

Usage:
    from src.logger import get_logger, log_step, setup_logging
    setup_logging()  # once at app startup
    log = get_logger(__name__)
    log.info('hello')
    with log_step(log, 'building-index'):
        ...
"""

import contextlib
import logging
import os
import time
from collections.abc import Iterator
from typing import Literal

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as rich_traceback_install



def _make_handler() -> logging.Handler:
    """Create a logging handler using Rich (no fallback)."""

    # Force using Rich; respect TTY for color emission
    console = Console(stderr=True, soft_wrap=False)
    rich_traceback_install(console=console, show_locals=False, max_frames=25)
    return RichHandler(console=console, rich_tracebacks=True, show_path=False, markup=True, log_time_format='%H:%M:%S')


def setup_logging(default_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] | None = None) -> None:
    """Initialize root logging once with colored stderr handler.

    LOG_LEVEL env var can override level. Accepts DEBUG, INFO, WARNING, ERROR.
    """
    if getattr(setup_logging, '_initialized', False):
        return

    level_name = (os.getenv('LOG_LEVEL') or default_level or 'INFO').upper().strip()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to avoid duplicates in reload
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = _make_handler()
    root.addHandler(handler)

    # Make third-party loggers less noisy by default
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)
    logging.getLogger('uvicorn.error').setLevel(logging.INFO)
    logging.getLogger('llama_index').setLevel(logging.INFO)
    logging.getLogger('openai').setLevel(logging.INFO)

    setup_logging._initialized = True  # type: ignore[attr-defined]


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a module-level logger."""
    return logging.getLogger(name or 'app')


@contextlib.contextmanager
def log_step(log: logging.Logger, title: str, *, level: int = logging.INFO) -> Iterator[None]:
    """Context manager to log start/end with duration and exceptions.

    Example:
        with log_step(log, 'create-index'):
            expensive_work()
    """
    t0 = time.perf_counter()
    log.log(level, f'▶ {title}...')
    try:
        yield
    except Exception:
        # Include stack trace automatically
        log.exception(f'✖ {title} failed')
        raise
    else:
        dt = (time.perf_counter() - t0) * 1000
        log.log(level, f'✔ {title} done in {dt:.0f} ms')
