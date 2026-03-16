"""HTTP client service for retrieving response headers."""

import logging
import ssl
import uuid
from collections.abc import Mapping
from urllib.parse import urlparse

import httpx

DEFAULT_USER_AGENT = "AI-Web-Security-Scanner/0.1"
logger = logging.getLogger(__name__)


class UpstreamFetchError(Exception):
    """Raised when the target URL cannot be fetched successfully."""


class HeaderFetcher:
    """Fetch headers from a target URL with a HEAD-first strategy."""

    def __init__(self, timeout: float = 5.0) -> None:
        self._timeout = timeout

    async def fetch(self, url: str) -> dict[str, str]:
        """Fetch normalized headers, falling back from HEAD to GET when needed."""
        request_id = uuid.uuid4().hex[:8]
        hostname = urlparse(url).hostname or ""
        async with httpx.AsyncClient(
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=self._timeout,
            follow_redirects=True,
            verify=ssl.create_default_context(),
            trust_env=False,
        ) as client:
            headers = await self._request_headers(
                client,
                "HEAD",
                url,
                request_id=request_id,
                hostname=hostname,
                fallback_attempted=False,
            )
            if headers:
                return headers

            headers = await self._request_headers(
                client,
                "GET",
                url,
                request_id=request_id,
                hostname=hostname,
                fallback_attempted=True,
            )
            if headers:
                return headers

        logger.error(
            "header_fetch_exhausted",
            extra={
                "request_id": request_id,
                "hostname": hostname,
                "failure_path": "head_and_get_failed",
            },
        )
        raise UpstreamFetchError(
            "Unable to retrieve security headers from the target URL."
        )

    async def _request_headers(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        *,
        request_id: str,
        hostname: str,
        fallback_attempted: bool,
    ) -> dict[str, str]:
        try:
            response = await client.request(method, url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning(
                "header_fetch_failed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "hostname": hostname,
                    "exception_class": exc.__class__.__name__,
                    "exception": str(exc),
                    "fallback_attempted": fallback_attempted,
                    "failure_path": f"{method.lower()}_failed",
                },
            )
            return {}

        return self._normalize_headers(response.headers)

    @staticmethod
    def _normalize_headers(headers: Mapping[str, str]) -> dict[str, str]:
        return {key.lower(): value for key, value in headers.items()}
