"""Confidence tracking for the Science Engine."""

from .models import ConfidenceScore

def calculate_confidence(physics: float, chemistry: float, biology: float) -> ConfidenceScore:
    """Creates a confidence score object keeping components separate as required."""
    return ConfidenceScore(
        physics=physics,
        chemistry=chemistry,
        biology=biology
    )
