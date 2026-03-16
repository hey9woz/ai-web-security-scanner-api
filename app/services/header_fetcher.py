"""HTTP client service for retrieving response headers."""

import ssl
from collections.abc import Mapping

import httpx

DEFAULT_USER_AGENT = "AI-Web-Security-Scanner/0.1"


class UpstreamFetchError(Exception):
    """Raised when the target URL cannot be fetched successfully."""


class HeaderFetcher:
    """Fetch headers from a target URL with a HEAD-first strategy."""

    def __init__(self, timeout: float = 5.0) -> None:
        self._timeout = timeout

    async def fetch(self, url: str) -> dict[str, str]:
        """Fetch normalized headers, falling back from HEAD to GET when needed."""
        async with httpx.AsyncClient(
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=self._timeout,
            follow_redirects=True,
            verify=ssl.create_default_context(),
        ) as client:
            headers = await self._request_headers(client, "HEAD", url)
            if headers:
                return headers

            headers = await self._request_headers(client, "GET", url)
            if headers:
                return headers

        raise UpstreamFetchError(
            "Unable to retrieve security headers from the target URL."
        )

    async def _request_headers(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
    ) -> dict[str, str]:
        try:
            response = await client.request(method, url)
            response.raise_for_status()
        except httpx.HTTPError:
            return {}

        return self._normalize_headers(response.headers)

    @staticmethod
    def _normalize_headers(headers: Mapping[str, str]) -> dict[str, str]:
        return {key.lower(): value for key, value in headers.items()}
