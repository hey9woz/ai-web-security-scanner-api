"""Scan API routes."""

from fastapi import APIRouter

from app.core.scoring import calculate_rank, calculate_score
from app.models.scan_request import ScanRequest
from app.models.scan_result import ScanResult
from app.services.header_analyzer import analyze_headers
from app.services.header_fetcher import HeaderFetcher

router = APIRouter()
fetcher = HeaderFetcher()


@router.post("/scan", response_model=ScanResult)
async def scan_url(payload: ScanRequest) -> ScanResult:
    """Fetch and analyze security headers for a target URL."""
    headers = await fetcher.fetch(payload.url)
    report, missing_headers = analyze_headers(headers)
    total_headers = len(report)
    present_headers = total_headers - len(missing_headers)

    return ScanResult(
        url=payload.url,
        score=calculate_score(present_headers, total_headers),
        rank=calculate_rank(present_headers, total_headers),
        report=report,
        missing_headers=missing_headers,
    )
