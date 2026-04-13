from typing import Any


CONFIDENCE_THRESHOLDS = {
    "high": 0.90,    # Green - auto-verified candidate
    "medium": 0.70,  # Yellow - needs staff review
    "low": 0.70,     # Red (below medium) - priority review
}


def _classify_confidence(score: float) -> str:
    if score >= CONFIDENCE_THRESHOLDS["high"]:
        return "high"
    if score >= CONFIDENCE_THRESHOLDS["medium"]:
        return "medium"
    return "low"


def get_confidence_badge(overall_confidence: float) -> dict:
    """
    Returns confidence badge metadata for overall OCR confidence.
    """
    level = _classify_confidence(float(overall_confidence or 0.0))
    if level == "high":
        return {
            "level": "high",
            "color": "green",
            "label": "High Confidence",
            "icon": "check-circle",
        }
    if level == "medium":
        return {
            "level": "medium",
            "color": "yellow",
            "label": "Needs Review",
            "icon": "alert-triangle",
        }
    return {
        "level": "low",
        "color": "red",
        "label": "Low Confidence",
        "icon": "x-circle",
    }


def get_field_badges(confidence_scores: dict) -> dict:
    """
    Returns per-field confidence badges for split-screen verification UI.
    """
    badges: dict[str, Any] = {}
    for field_name, score in (confidence_scores or {}).items():
        level = _classify_confidence(float(score or 0.0))
        if level == "high":
            color = "green"
        elif level == "medium":
            color = "yellow"
        else:
            color = "red"
        badges[field_name] = {"level": level, "color": color}
    return badges
