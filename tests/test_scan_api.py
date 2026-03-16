from fastapi.testclient import TestClient

from app.api import scan
from app.main import app
from app.services.header_fetcher import UpstreamFetchError

client = TestClient(app)


def test_scan_rejects_invalid_scheme() -> None:
    response = client.post("/scan", json={"url": "ftp://example.com"})

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Request validation failed.",
            "details": [
                {
                    "field": "url",
                    "message": "Value error, URL scheme must be http or https.",
                }
            ],
        }
    }


def test_scan_rejects_localhost() -> None:
    response = client.post("/scan", json={"url": "http://localhost:8000"})

    assert response.status_code == 400


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scan_returns_structured_upstream_error(monkeypatch) -> None:
    async def fake_fetch(url: str) -> dict[str, str]:
        raise UpstreamFetchError("hidden internal detail")

    monkeypatch.setattr(scan.fetcher, "fetch", fake_fetch)

    with TestClient(app) as test_client:
        response = test_client.post("/scan", json={"url": "https://example.com"})

    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "upstream_request_failed",
            "message": "Unable to retrieve security headers from the target URL.",
        }
    }
