from __future__ import annotations

import logging
import random
import time
from typing import Optional

import httpx

from .constants import DEFAULT_DELAY, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT
from .exceptions import FetchError

logger = logging.getLogger(__name__)


class HttpClient:
    def __init__(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        delay: float = DEFAULT_DELAY,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self.timeout = timeout
        self.delay = delay
        self.max_retries = max_retries
        self._client = httpx.Client(
            follow_redirects=True,
            timeout=httpx.Timeout(timeout),
        )
        self._last_request_at = 0.0

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _sleep_if_needed(self) -> None:
        elapsed = time.time() - self._last_request_at
        if elapsed < self.delay:
            wait = self.delay - elapsed + max(0.0, random.gauss(0.2, 0.08))
            time.sleep(wait)

    def get_text(self, url: str, *, headers: Optional[dict[str, str]] = None) -> str:
        self._sleep_if_needed()
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            start = time.time()
            try:
                response = self._client.get(url, headers=headers)
                elapsed = time.time() - start
                self._last_request_at = time.time()
                logger.info("GET %s -> %s (%.2fs)", url, response.status_code, elapsed)
                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt >= self.max_retries:
                        response.raise_for_status()
                    time.sleep((2**attempt) + random.uniform(0.0, 0.4))
                    continue
                response.raise_for_status()
                return response.text
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep((2**attempt) + random.uniform(0.0, 0.4))
        raise FetchError(f"Request failed for {url}: {last_error}") from last_error
