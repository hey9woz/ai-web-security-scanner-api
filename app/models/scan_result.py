"""Response models for scan results."""

from pydantic import BaseModel


class HeaderReportItem(BaseModel):
    """Human-readable report for a single security header."""

    name: str
    status: str
    value: str | None
    description: str
    recommendation: str


class ScanResult(BaseModel):
    """API response payload for a completed scan."""

    url: str
    score: str
    rank: str
    report: list[HeaderReportItem]
    missing_headers: list[str]
