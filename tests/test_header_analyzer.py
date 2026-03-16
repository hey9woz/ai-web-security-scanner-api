from app.core.scoring import calculate_rank
from app.services.header_analyzer import analyze_headers


def test_analyzer_returns_expected_missing_headers() -> None:
    report, missing_headers = analyze_headers(
        {
            "strict-transport-security": "max-age=31536000",
            "x-content-type-options": "nosniff",
        }
    )

    assert len(report) == 6
    assert missing_headers == [
        "Content-Security-Policy",
        "X-Frame-Options",
        "Referrer-Policy",
        "Permissions-Policy",
    ]


def test_rank_calculation_basics() -> None:
    assert calculate_rank(6, 6) == "A+"
    assert calculate_rank(5, 6) == "B"
    assert calculate_rank(3, 6) == "C"
    assert calculate_rank(2, 6) == "D"
    assert calculate_rank(2, 8) == "D"
    assert calculate_rank(1, 6) == "F"
    assert calculate_rank(0, 6) == "F"
