"""Header analysis service for common web security headers."""

from app.models.scan_result import HeaderReportItem


HEADER_SPECS = (
    {
        "key": "content-security-policy",
        "name": "Content-Security-Policy",
        "description": "Controls which sources the browser can trust for content.",
        "recommendation": "Add a strict Content-Security-Policy tailored to your frontend.",
    },
    {
        "key": "strict-transport-security",
        "name": "Strict-Transport-Security",
        "description": "Forces browsers to prefer HTTPS for future requests.",
        "recommendation": "Enable HSTS with an appropriate max-age on HTTPS responses.",
    },
    {
        "key": "x-frame-options",
        "name": "X-Frame-Options",
        "description": "Reduces clickjacking risk by limiting framing.",
        "recommendation": "Set X-Frame-Options to DENY or SAMEORIGIN.",
    },
    {
        "key": "x-content-type-options",
        "name": "X-Content-Type-Options",
        "description": "Prevents MIME sniffing for declared content types.",
        "recommendation": "Set X-Content-Type-Options to nosniff.",
    },
    {
        "key": "referrer-policy",
        "name": "Referrer-Policy",
        "description": "Controls how much referrer information is shared.",
        "recommendation": "Set a Referrer-Policy such as strict-origin-when-cross-origin.",
    },
    {
        "key": "permissions-policy",
        "name": "Permissions-Policy",
        "description": "Restricts access to powerful browser features.",
        "recommendation": "Define a Permissions-Policy that disables unused browser capabilities.",
    },
)


def analyze_headers(headers: dict[str, str]) -> tuple[list[HeaderReportItem], list[str]]:
    """Generate a report and missing header list from normalized headers."""
    report: list[HeaderReportItem] = []
    missing_headers: list[str] = []

    for spec in HEADER_SPECS:
        value = headers.get(spec["key"])
        present = bool(value)

        report.append(
            HeaderReportItem(
                name=spec["name"],
                status="✔" if present else "✘",
                value=value,
                description=spec["description"],
                recommendation=(
                    "Header is present."
                    if present
                    else spec["recommendation"]
                ),
            )
        )

        if not present:
            missing_headers.append(spec["name"])

    return report, missing_headers
