"""Scoring helpers for header scan results."""


def calculate_score(present_count: int, total_count: int) -> str:
    """Return score as a display string."""
    return f"{present_count} / {total_count}"


def calculate_rank(present_count: int, total_count: int) -> str:
    """Convert a header coverage ratio into a letter rank."""
    if total_count <= 0:
        return "F"

    ratio = (present_count / total_count) * 100
    if ratio == 100:
        return "A+"
    if ratio >= 90:
        return "A"
    if ratio >= 75:
        return "B"
    if ratio >= 50:
        return "C"
    if ratio >= 25:
        return "D"
    return "F"
