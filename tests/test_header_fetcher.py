import httpx
import pytest

from app.services.header_fetcher import (
    DEFAULT_USER_AGENT,
    HeaderFetcher,
    UpstreamFetchError,
    _create_ssl_context,
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
        verify=_create_ssl_context(),
        trust_env=False,
    ) as client:
        headers, exception_class, exception_message = await fetcher._request_headers(
            client,
            "HEAD",
            "https://example.com",
            request_id="req-1234",
            hostname="example.com",
            fallback_attempted=False,
        )

    assert headers == {"content-type": "text/html"}
    assert exception_class == ""
    assert exception_message == ""


@pytest.mark.anyio
async def test_fetch_falls_back_to_get_when_head_fails(monkeypatch) -> None:
    calls: list[str] = []

    async def fake_request_headers(
        client: httpx.AsyncClient,
        method: str,
        url: str,
        *,
        request_id: str,
        hostname: str,
        fallback_attempted: bool,
    ) -> tuple[dict[str, str], str, str]:
        calls.append(method)
        if method == "HEAD":
            return {}, "ConnectTimeout", "timed out"
        return {"content-type": "text/html"}, "", ""

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
        *,
        request_id: str,
        hostname: str,
        fallback_attempted: bool,
    ) -> tuple[dict[str, str], str, str]:
        return {}, "ConnectError", "certificate verify failed"

    fetcher = HeaderFetcher()
    monkeypatch.setattr(fetcher, "_request_headers", fake_request_headers)

    with pytest.raises(UpstreamFetchError):
        await fetcher.fetch("https://example.com")


@pytest.mark.anyio
async def test_request_headers_logs_failure(caplog: pytest.LogCaptureFixture) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out")

    transport = httpx.MockTransport(handler)
    fetcher = HeaderFetcher()

    async with httpx.AsyncClient(
        transport=transport,
        headers={"User-Agent": DEFAULT_USER_AGENT},
        timeout=5.0,
        follow_redirects=True,
        verify=_create_ssl_context(),
        trust_env=False,
    ) as client:
        with caplog.at_level("WARNING"):
            headers, exception_class, exception_message = await fetcher._request_headers(
                client,
                "HEAD",
                "https://example.com",
                request_id="req-1234",
                hostname="example.com",
                fallback_attempted=False,
            )

    assert headers == {}
    assert exception_class == "ConnectTimeout"
    assert exception_message == "timed out"
    assert caplog.records[0].msg == "header_fetch_failed"
    assert caplog.records[0].request_id == "req-1234"
    assert caplog.records[0].method == "HEAD"
    assert caplog.records[0].hostname == "example.com"
    assert caplog.records[0].exception_class == "ConnectTimeout"
    assert caplog.records[0].exception == "timed out"
    assert caplog.records[0].fallback_attempted is False
    assert caplog.records[0].failure_path == "head_failed"
