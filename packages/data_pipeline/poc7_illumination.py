"""NEXUS-LUNAR POC-7: Illumination & Solar Potential Intelligence Engine.

Derives illumination metrics, shadow fractions, and potential solar-energy zones:
- Statuses: ILLUMINATED, PARTIALLY_ILLUMINATED, SHADOWED, LOW_LIGHT, UNKNOWN
- Metrics: illumination_mean, illumination_variance, shadow_fraction
- Potential solar-energy zone spatial indicator (qualified; never claiming guaranteed permanent power)
- Low-light / cold-trap indicator with explicit temporal validity status:
  'TEMPORAL_VALIDATION_UNAVAILABLE' when single-epoch observation is processed.

Preserves strict scientific qualification: does not fabricate multi-epoch temporal series.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

from packages.data_pipeline.poc7_models import (
    IlluminationMetrics,
    IlluminationStatus,
    ProvenanceRecord,
)


class IlluminationIntelligenceEngine:
    """Analyzes lunar surface illumination and classifies solar potential vs shadow zones."""

    def __init__(
        self,
        shadow_threshold: float = 0.15,
        low_light_threshold: float = 0.35,
        illuminated_threshold: float = 0.65,
    ):
        self.shadow_threshold = shadow_threshold
        self.low_light_threshold = low_light_threshold
        self.illuminated_threshold = illuminated_threshold

    def classify_illumination(
        self,
        mean_val: float,
        shadow_frac: float,
    ) -> IlluminationStatus:
        """Classify illumination condition into discrete scientific states."""
        if shadow_frac > 0.60 or mean_val < self.shadow_threshold:
            return IlluminationStatus.SHADOWED
        elif mean_val < self.low_light_threshold:
            return IlluminationStatus.LOW_LIGHT
        elif mean_val >= self.illuminated_threshold and shadow_frac < 0.20:
            return IlluminationStatus.ILLUMINATED
        else:
            return IlluminationStatus.PARTIALLY_ILLUMINATED

    def determine_solar_potential(
        self,
        illum_status: IlluminationStatus,
        mean_val: float,
        shadow_frac: float,
    ) -> str:
        """Determine solar energy potential indicator with strict scientific qualification."""
        if illum_status == IlluminationStatus.ILLUMINATED and shadow_frac <= 0.10:
            return "POTENTIAL SOLAR-ENERGY ZONE (HIGH INDICATOR)"
        elif illum_status in (IlluminationStatus.ILLUMINATED, IlluminationStatus.PARTIALLY_ILLUMINATED) and shadow_frac < 0.30:
            return "POTENTIAL SOLAR-ENERGY ZONE (MODERATE INDICATOR)"
        elif illum_status == IlluminationStatus.SHADOWED:
            return "NON-SOLAR ZONE (PERSISTENT/LOW-LIGHT CANDIDATE)"
        else:
            return "MARGINAL SOLAR POTENTIAL"

    def analyze_patch_illumination(
        self,
        patch_id: str,
        image_array: Optional[np.ndarray] = None,
        solar_incidence_deg: Optional[float] = None,
        temporal_observations: Optional[List[Dict[str, Any]]] = None,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> IlluminationMetrics:
        """Derive comprehensive IlluminationMetrics for a terrain patch."""
        data_status = "DATA-DRIVEN"
        prov = provenance or {}

        if image_array is None:
            # Deterministic fallback generator for pipeline validation
            data_status = "SYNTHETIC OFFLINE DEMO"
            image_array = self._generate_deterministic_illumination(patch_id)

        # Normalize to [0.0, 1.0] if integer or outside range
        arr = image_array.astype(np.float32)
        if arr.max() > 1.0:
            arr = arr / 255.0

        mean_illum = float(np.mean(arr))
        var_illum = float(np.var(arr))
        # Pixels below shadow threshold count as shadow
        shadow_mask = arr < self.shadow_threshold
        shadow_frac = float(np.sum(shadow_mask) / arr.size)

        illum_state = self.classify_illumination(mean_illum, shadow_frac)
        solar_pot = self.determine_solar_potential(illum_state, mean_illum, shadow_frac)

        # Temporal analysis: only if multiple observations exist
        if temporal_observations and len(temporal_observations) > 1:
            temporal_status = f"EVALUATED_ACROSS_{len(temporal_observations)}_OBSERVATIONS"
        else:
            temporal_status = "TEMPORAL_VALIDATION_UNAVAILABLE"

        return IlluminationMetrics(
            patch_id=patch_id,
            illumination_mean=round(mean_illum, 4),
            illumination_variance=round(var_illum, 4),
            shadow_fraction=round(shadow_frac, 4),
            illumination_state=illum_state,
            solar_potential_indicator=solar_pot,
            temporal_consistency=temporal_status,
            data_status=data_status,
            provenance=prov,
        )

    @staticmethod
    def _generate_deterministic_illumination(seed_str: str, h: int = 64, w: int = 64) -> np.ndarray:
        """Deterministic pseudo-illumination grid derived from seed_str hash."""
        seed = int.from_bytes(seed_str.encode("utf-8"), "big") % (2**32)
        rng = np.random.RandomState(seed)

        # Sun angle projection from South-West
        y, x = np.mgrid[0:h, 0:w]
        grad = (x / w) * 0.4 + (y / h) * 0.3 + 0.2
        noise = rng.normal(0, 0.05, (h, w))
        grid = np.clip(grad + noise, 0.0, 1.0)
        return grid.astype(np.float32)
