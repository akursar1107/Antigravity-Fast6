"""
Resilience Utilities
Retry with exponential backoff and a lightweight circuit breaker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Optional, Tuple, TypeVar
import random
import time

T = TypeVar("T")


class CircuitBreakerOpen(RuntimeError):
    """Raised when a circuit breaker is open."""


@dataclass
class CircuitBreakerState:
    failure_count: int = 0
    last_failure_ts: float = 0.0
    state: str = "closed"  # closed | open | half-open


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, cooldown_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._state = CircuitBreakerState()

    def allow_request(self) -> bool:
        if self._state.state == "open":
            now = time.monotonic()
            if now - self._state.last_failure_ts >= self.cooldown_seconds:
                self._state.state = "half-open"
                return True
            return False
        return True

    def record_success(self) -> None:
        self._state.failure_count = 0
        self._state.state = "closed"

    def record_failure(self) -> None:
        self._state.failure_count += 1
        self._state.last_failure_ts = time.monotonic()
        if self._state.failure_count >= self.failure_threshold:
            self._state.state = "open"


_BREAKERS: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    key: str,
    failure_threshold: int,
    cooldown_seconds: int,
) -> CircuitBreaker:
    if key not in _BREAKERS:
        _BREAKERS[key] = CircuitBreaker(failure_threshold, cooldown_seconds)
    return _BREAKERS[key]


def _sleep_backoff(attempt: int, base: float, factor: float, jitter: float) -> None:
    delay = base * (factor ** attempt)
    if jitter > 0:
        delay += random.uniform(0, jitter)
    time.sleep(delay)


def request_with_retry(
    request_fn: Callable[[], T],
    breaker: CircuitBreaker,
    retries: int,
    backoff_base: float,
    backoff_factor: float,
    jitter: float,
    retry_on_statuses: Optional[Iterable[int]] = None,
    get_status: Optional[Callable[[T], Optional[int]]] = None,
) -> T:
    if not breaker.allow_request():
        raise CircuitBreakerOpen("Circuit breaker open")

    last_exc: Optional[Exception] = None

    for attempt in range(retries + 1):
        try:
            result = request_fn()
            status = get_status(result) if get_status else None
            if status is not None and retry_on_statuses and status in retry_on_statuses:
                breaker.record_failure()
                if attempt < retries:
                    _sleep_backoff(attempt, backoff_base, backoff_factor, jitter)
                    continue
            breaker.record_success()
            return result
        except Exception as exc:  # noqa: BLE001 - handled retry flow
            last_exc = exc
            breaker.record_failure()
            if attempt < retries:
                _sleep_backoff(attempt, backoff_base, backoff_factor, jitter)
                continue
            raise

    if last_exc:
        raise last_exc
    raise RuntimeError("request_with_retry failed without exception")
