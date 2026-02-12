"""
Observability Utilities
Lightweight, human-readable logging helpers for key operations.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Generator, Optional
import logging
import time
import uuid

logger = logging.getLogger(__name__)


def _format_fields(fields: Dict[str, object]) -> str:
    parts = []
    for key, value in fields.items():
        if value is None:
            continue
        parts.append(f"{key}={value}")
    return " ".join(parts)


def log_event(event: str, **fields: object) -> None:
    """Log a single observability event in a human-readable format."""
    msg = f"[OBS] {event}"
    formatted = _format_fields(fields)
    if formatted:
        msg = f"{msg} {formatted}"
    logger.info(msg)


@contextmanager
def track_operation(event: str, **fields: object) -> Generator[Dict[str, object], None, None]:
    """
    Track an operation duration and status.

    Usage:
        with track_operation("api.request", endpoint="/v1") as obs:
            ...
            obs["status_code"] = 200
    """
    start = time.perf_counter()
    op_id = uuid.uuid4().hex[:8]
    context: Dict[str, object] = {"op_id": op_id}
    context.update(fields)
    try:
        yield context
        duration_ms = int((time.perf_counter() - start) * 1000)
        context["duration_ms"] = duration_ms
        context["status"] = "ok"
        log_event(event, **context)
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        context["duration_ms"] = duration_ms
        context["status"] = "error"
        context["error"] = type(exc).__name__
        log_event(event, **context)
        raise
