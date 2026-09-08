"""NEXUS-LUNAR POC-7: Hazard Intelligence Engine.

Identifies, classifies, and grades lunar surface hazards that constrain exploration,
lander descent, surface mobility, and habitat placement:
- STEEP_SLOPE: Slopes exceeding operational mobility thresholds (> 12 deg moderate, > 20 deg critical)
- ROUGH_TERRAIN: Micro-topographic boulder/roughness variance (std dev > 5m)
- CRATER_RIM: Proximity to steep crater rims with structural slumping risk
- PERMANENT_SHADOW: Thermal extreme cold-trap and zero-solar power risk
- UNSTABLE_TERRAIN: Loose regolith indicator or steep slope-wash zones

Severities: LOW, MODERATE, HIGH, CRITICAL.
Preserves source metrics, severity ratings, and full provenance.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from packages.data_pipeline.poc7_models import (
    HazardIndicator,
    HazardType,
    HazardSeverity,
    TerrainMetrics,
    IlluminationMetrics,
    IlluminationStatus,
    SlopeCategory,
)


class HazardIntelligenceEngine:
    """Detects and grades environmental and topographic lunar hazards."""

    def __init__(
        self,
        critical_slope_threshold: float = 20.0,
        high_slope_threshold: float = 12.0,
        critical_roughness_threshold: float = 6.0,
        high_roughness_threshold: float = 3.5,
        crater_rim_danger_dist_m: float = 500.0,
    ):
        self.critical_slope = critical_slope_threshold
        self.high_slope = high_slope_threshold
        self.critical_roughness = critical_roughness_threshold
        self.high_roughness = high_roughness_threshold
        self.crater_rim_danger_dist_m = crater_rim_danger_dist_m

    def assess_hazards(
        self,
        patch_id: str,
        terrain: TerrainMetrics,
        illumination: IlluminationMetrics,
        coordinates: Dict[str, float],
        provenance: Optional[Dict[str, Any]] = None,
    ) -> List[HazardIndicator]:
        """Evaluate all physical, topographic, and lighting hazards for a terrain patch."""
        hazards: List[HazardIndicator] = []
        prov = provenance or {}

        # 1. Slope Hazard
        if terrain.slope_degrees >= self.critical_slope:
            hazards.append(
                HazardIndicator(
                    hazard_id=f"HAZARD_SLOPE_CRITICAL_{patch_id}",
                    hazard_type=HazardType.STEEP_SLOPE,
                    severity=HazardSeverity.CRITICAL,
                    description=f"Severe slope gradient of {terrain.slope_degrees} deg exceeds rover tip-over threshold (> 20 deg).",
                    source_metric=f"slope_degrees={terrain.slope_degrees}",
                    affected_patch_id=patch_id,
                    coordinates=coordinates,
                    confidence=0.98,
                    provenance=prov,
                )
            )
        elif terrain.slope_degrees >= self.high_slope:
            hazards.append(
                HazardIndicator(
                    hazard_id=f"HAZARD_SLOPE_HIGH_{patch_id}",
                    hazard_type=HazardType.STEEP_SLOPE,
                    severity=HazardSeverity.HIGH,
                    description=f"Elevated slope gradient of {terrain.slope_degrees} deg imposes operational transit constraints.",
                    source_metric=f"slope_degrees={terrain.slope_degrees}",
                    affected_patch_id=patch_id,
                    coordinates=coordinates,
                    confidence=0.92,
                    provenance=prov,
                )
            )

        # 2. Roughness Hazard
        if terrain.roughness_score >= self.critical_roughness:
            hazards.append(
                HazardIndicator(
                    hazard_id=f"HAZARD_ROUGHNESS_CRITICAL_{patch_id}",
                    hazard_type=HazardType.ROUGH_TERRAIN,
                    severity=HazardSeverity.CRITICAL,
                    description=f"Extreme local elevation roughness ({terrain.roughness_score}m std dev) indicates severe boulder fields or blocky ejecta.",
                    source_metric=f"roughness_score={terrain.roughness_score}",
                    affected_patch_id=patch_id,
                    coordinates=coordinates,
                    confidence=0.90,
                    provenance=prov,
                )
            )
        elif terrain.roughness_score >= self.high_roughness:
            hazards.append(
                HazardIndicator(
                    hazard_id=f"HAZARD_ROUGHNESS_MODERATE_{patch_id}",
                    hazard_type=HazardType.ROUGH_TERRAIN,
                    severity=HazardSeverity.MODERATE,
                    description=f"Moderate elevation roughness ({terrain.roughness_score}m std dev) requires hazard-avoidance path planning.",
                    source_metric=f"roughness_score={terrain.roughness_score}",
                    affected_patch_id=patch_id,
                    coordinates=coordinates,
                    confidence=0.88,
                    provenance=prov,
                )
            )

        # 3. Crater Proximity / Rim Instability Hazard
        if terrain.distance_to_crater_m is not None:
            if terrain.distance_to_crater_m < self.crater_rim_danger_dist_m:
                hazards.append(
                    HazardIndicator(
                        hazard_id=f"HAZARD_CRATER_RIM_{patch_id}",
                        hazard_type=HazardType.CRATER_RIM,
                        severity=HazardSeverity.HIGH,
                        description=f"Proximity to crater rim ({terrain.distance_to_crater_m}m to {terrain.nearest_crater_id}) carries regolith slump and steep rim edge risk.",
                        source_metric=f"distance_to_crater_m={terrain.distance_to_crater_m}",
                        affected_patch_id=patch_id,
                        coordinates=coordinates,
                        confidence=0.94,
                        provenance=prov,
                    )
                )

        # 4. Illumination / Thermal Hazard
        if illumination.illumination_state == IlluminationStatus.SHADOWED or illumination.shadow_fraction > 0.70:
            # PERMANENT_SHADOW requires multi-epoch temporal confirmation.
            # A single deep-shadow observation is treated as a severe lighting hazard.
            hazards.append(
                HazardIndicator(
                    hazard_id=f"HAZARD_SHADOW_CRITICAL_{patch_id}",
                    hazard_type=HazardType.PERMANENT_SHADOW,
                    severity=HazardSeverity.CRITICAL,
                    description=(
                        "Deep shadow regime detected (single epoch). Consistent with cryogenic cold-trap "
                        "candidate. Temporal confirmation unavailable — multi-epoch validation required "
                        "to confirm persistence."
                    ),
                    source_metric=f"shadow_fraction={illumination.shadow_fraction}",
                    affected_patch_id=patch_id,
                    coordinates=coordinates,
                    confidence=0.75,  # Reduced from 0.96: single-epoch only
                    provenance=prov,
                )
            )
        elif illumination.illumination_state == IlluminationStatus.LOW_LIGHT:
            # LOW_LIGHT from a single epoch: do NOT claim PERMANENT_SHADOW.
            # Use LOW_LIGHT_CONSTRAINT: an operational lighting limitation indicator.
            hazards.append(
                HazardIndicator(
                    hazard_id=f"HAZARD_LOW_LIGHT_{patch_id}",
                    hazard_type=HazardType.LOW_LIGHT_CONSTRAINT,
                    severity=HazardSeverity.MODERATE,
                    description=(
                        "Low illumination detected (single epoch). Imposes battery power management "
                        "and thermal control constraints. Cannot claim persistent shadow without "
                        "multi-epoch temporal confirmation."
                    ),
                    source_metric=f"illumination_mean={illumination.illumination_mean}",
                    affected_patch_id=patch_id,
                    coordinates=coordinates,
                    confidence=0.85,
                    provenance=prov,
                )
            )

        return hazards
