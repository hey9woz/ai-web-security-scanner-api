import ssl

import httpx
import pytest

from app.services.header_fetcher import (
    DEFAULT_USER_AGENT,
    HeaderFetcher,
    UpstreamFetchError,
)


@pytest.mark.anyio
async def test_fetch_uses_successful_head_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "HEAD"
        assert request.headers["User-Agent"] == DEFAULT_USER_AGENT
        return httpx.Response(200, headers={"Content-Type": "text/html"})

    transport = httpx.MockTransport(handler)
    fetcher = HeaderFetcher()

    async with httpx.AsyncClient(
        transport=transport,
        headers={"User-Agent": DEFAULT_USER_AGENT},
        timeout=5.0,
        follow_redirects=True,
        verify=ssl.create_default_context(),
    ) as client:
        headers = await fetcher._request_headers(client, "HEAD", "https://example.com")

    assert headers == {"content-type": "text/html"}


@pytest.mark.anyio
async def test_fetch_falls_back_to_get_when_head_fails(monkeypatch) -> None:
    calls: list[str] = []

    async def fake_request_headers(
        client: httpx.AsyncClient,
        method: str,
        url: str,
    ) -> dict[str, str]:
        calls.append(method)
        if method == "HEAD":
            return {}
        return {"content-type": "text/html"}

    fetcher = HeaderFetcher()
    monkeypatch.setattr(fetcher, "_request_headers", fake_request_headers)

    headers = await fetcher.fetch("https://example.com")

    assert calls == ["HEAD", "GET"]
    assert headers == {"content-type": "text/html"}


@pytest.mark.anyio
async def test_fetch_raises_only_when_head_and_get_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_request_headers(
        client: httpx.AsyncClient,
        method: str,
        url: str,
    ) -> dict[str, str]:
        return {}

    fetcher = HeaderFetcher()
    monkeypatch.setattr(fetcher, "_request_headers", fake_request_headers)

    with pytest.raises(UpstreamFetchError):
        await fetcher.fetch("https://example.com")
