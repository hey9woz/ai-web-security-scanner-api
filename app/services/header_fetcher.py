"""HTTP client service for retrieving response headers."""

import logging
import ssl
import sys
import uuid
from collections.abc import Mapping
from urllib.parse import urlparse

import httpx
import truststore

DEFAULT_USER_AGENT = "AI-Web-Security-Scanner/0.1"
logger = logging.getLogger(__name__)


def _create_ssl_context() -> ssl.SSLContext:
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


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
        head_failed = False
        get_failed = False
        last_exception_class = ""
        last_exception = ""
        ssl_context = _create_ssl_context()
        logger.info(
            "header_fetch_ssl_setup",
            extra={
                "request_id": request_id,
                "hostname": hostname,
                "python_version": sys.version.split()[0],
                "openssl_version": ssl.OPENSSL_VERSION,
                "ssl_context_class": ssl_context.__class__.__name__,
                "ca_cert_count": len(ssl_context.get_ca_certs()),
                "trust_env": False,
                "http2": False,
            },
        )
        async with httpx.AsyncClient(
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=self._timeout,
            follow_redirects=True,
            verify=ssl_context,
            trust_env=False,
            http2=False,
        ) as client:
            headers, exception_class, exception_message = await self._request_headers(
                client,
                "HEAD",
                url,
                request_id=request_id,
                hostname=hostname,
                fallback_attempted=False,
            )
            if headers:
                return headers
            head_failed = True
            last_exception_class = exception_class
            last_exception = exception_message

            headers, exception_class, exception_message = await self._request_headers(
                client,
                "GET",
                url,
                request_id=request_id,
                hostname=hostname,
                fallback_attempted=True,
            )
            if headers:
                return headers
            get_failed = True
            last_exception_class = exception_class
            last_exception = exception_message

        logger.error(
            "header_fetch_exhausted",
            extra={
                "request_id": request_id,
                "hostname": hostname,
                "head_failed": head_failed,
                "get_failed": get_failed,
                "last_exception_class": last_exception_class,
                "last_exception": last_exception,
                "failure_path": "head_and_get_failed",
            },
        )
        print(
            "header_fetch_exhausted "
            f"request_id={request_id} "
            f"hostname={hostname} "
            f"head_failed={head_failed} "
            f"get_failed={get_failed} "
            f"last_exception_class={last_exception_class} "
            f"last_exception={last_exception!r} "
            "failure_path=head_and_get_failed"
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
    ) -> tuple[dict[str, str], str, str]:
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
            return {}, exc.__class__.__name__, str(exc)

        return self._normalize_headers(response.headers), "", ""

    @staticmethod
    def _normalize_headers(headers: Mapping[str, str]) -> dict[str, str]:
        return {key.lower(): value for key, value in headers.items()}
