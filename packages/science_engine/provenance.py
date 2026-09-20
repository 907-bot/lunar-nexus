"""Provenance tracking for the Science Engine."""

from typing import List, Optional
from .models import Provenance

def create_provenance(
    source: str, 
    processing_method: str, 
    dataset_id: Optional[str] = None, 
    observation_id: Optional[str] = None, 
    timestamp: Optional[str] = None,
    derived: bool = True,
    assumptions: List[str] = None
) -> Provenance:
    """Create a standard provenance record."""
    return Provenance(
        source=source,
        processing_method=processing_method,
        dataset_id=dataset_id,
        observation_id=observation_id,
        timestamp=timestamp,
        derived=derived,
        assumptions=assumptions or []
    )
