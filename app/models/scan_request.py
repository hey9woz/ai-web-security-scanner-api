"""Request models for scan endpoints."""

from ipaddress import ip_address
from urllib.parse import urlparse

from pydantic import BaseModel, field_validator


BLOCKED_HOSTS = {"localhost", "127.0.0.1", "::1"}


class ScanRequest(BaseModel):
    """Input payload for scanning a target URL."""

    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        parsed = urlparse(value)

        if parsed.scheme not in {"http", "https"}:
            raise ValueError("URL scheme must be http or https.")

        if not parsed.netloc or not parsed.hostname:
            raise ValueError("URL must include a hostname.")

        hostname = parsed.hostname.lower()
        if hostname in BLOCKED_HOSTS:
            raise ValueError("Localhost addresses are not allowed.")

        try:
            if ip_address(hostname).is_loopback:
                raise ValueError("Loopback addresses are not allowed.")
        except ValueError as exc:
            if str(exc) == "Loopback addresses are not allowed.":
                raise

        return value
