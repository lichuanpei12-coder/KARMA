"""Shared pacing and cancellable, unlimited retries for transient API failures."""
import logging
import math
import random
import time
import threading
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import httpx
from openai import APIConnectionError, APIStatusError

logger = logging.getLogger(__name__)


def wait_interruptibly(seconds):
    # KeyboardInterrupt propagates; long server delays still leave periodic logs.
    remaining = seconds
    while remaining > 0:
        chunk = min(remaining, 30.0)
        time.sleep(chunk)
        remaining -= chunk
        if remaining > 0:
            logger.info('API retry wait: %.1fs remaining (Ctrl+C to cancel)', remaining)


class RequestPacer:
    def __init__(self, min_interval=1.0):
        if not math.isfinite(min_interval) or min_interval < 0:
            raise ValueError('API minimum request interval must be finite and nonnegative')
        self.min_interval = min_interval
        self.last_start = None
        self.lock = threading.Lock()

    def acquire(self):
        with self.lock:
            if self.last_start is not None:
                wait_interruptibly(max(0, self.min_interval - (time.monotonic() - self.last_start)))
            self.last_start = time.monotonic()


def retry_delay(response, attempt):
    headers = response.headers if response is not None else {}
    for header, scale in (('retry-after-ms', .001), ('retry-after', 1.0)):
        value = headers.get(header)
        if value is None:
            continue
        try:
            delay = float(value) * scale
        except (TypeError, ValueError):
            try:
                deadline = parsedate_to_datetime(value)
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                delay = (deadline - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                continue
        if math.isfinite(delay) and delay >= 0:
            return max(1.0, delay)
    return min(60.0, 2.0 * 2 ** min(attempt, 5)) + random.uniform(0, 1)


def call_with_retry(call, pacer, retry_events, agent_name):
    attempt = 0
    while True:
        pacer.acquire()
        try:
            return call()
        except (httpx.HTTPStatusError, APIStatusError, httpx.RequestError, APIConnectionError) as exc:
            response = getattr(exc, 'response', None)
            status = getattr(response, 'status_code', None)
            if status is not None and status not in (408, 409, 429) and not 500 <= status < 600:
                raise  # Preserve the existing agent-level error/fallback policy.
            wait = retry_delay(response, attempt)
            attempt += 1
            retry_events.append(dict(attempt=attempt, status=status, wait_seconds=wait,
                                     error_type=type(exc).__name__))
            logger.warning('%s API %s, retry %d, waiting %.1fs; no retry limit (Ctrl+C to cancel)',
                           agent_name, status or type(exc).__name__, attempt, wait)
            wait_interruptibly(wait)
