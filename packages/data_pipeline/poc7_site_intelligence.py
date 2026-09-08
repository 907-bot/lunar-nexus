"""NEXUS-LUNAR POC-7: Candidate Site Intelligence & Multi-Factor Scoring Engine.

Implements a transparent, fully explainable multi-factor scoring methodology for evaluating
lunar surface candidate sites for future infrastructure exploration (POC-8 handoff):
- Terrain Score: Favors low slope and low roughness
- Illumination Score: Favors high mean solar flux and minimal shadow fraction
- Hazard Penalty: Quantifies risk from steep slopes, roughness boulders, crater rims, or cryogenic shadow
- Resource Indicator Score: Bonus for nearby mineralogical / volatile spectral indicators
- Spatial Data Quality Score: Ingests POC-6 verified geometric registration confidence & inlier ratio

Provides explainable rationale cards ("WHY IS THIS SITE INTERESTING?") with checklists
of positive and constraining spatial factors.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from packages.data_pipeline.poc7_models import (
    CandidateSite,
    CandidateSiteExplanation,
    SiteDataStatus,
    TerrainMetrics,
    IlluminationMetrics,
    ResourceIndicator,
    HazardIndicator,
    HazardSeverity,
    SlopeCategory,
    IlluminationStatus,
    ProvenanceRecord,
)


class CandidateSiteScoringEngine:
    """Evaluates and explains candidate lunar surface sites using multi-criteria decision analysis."""

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
    ):
        # Transparent configurable weights summing to 1.0 (suitability = weighted_sum - hazard_penalty)
        self.weights = weights or {
            "terrain": 0.30,
            "illumination": 0.25,
            "hazard_penalty": 0.20,
            "resource": 0.10,
            "data_quality": 0.15,
        }

    def compute_terrain_score(self, terrain: Optional[TerrainMetrics]) -> Tuple[float, List[str], List[str]]:
        """Compute terrain score (0.0 to 1.0) and generate positive/negative factor tags."""
        if terrain is None:
            return 0.5, [], ["Terrain data NOT_AVAILABLE (assigned neutral score)"]

        pos = []
        neg = []

        # Slope evaluation
        slope = terrain.slope_degrees
        if slope < 5.0:
            slope_s = 1.0
            pos.append(f"Gentle terrain slope ({slope:.1f}° - LOW risk)")
        elif slope < 12.0:
            slope_s = 0.70
            pos.append(f"Moderate operational slope ({slope:.1f}°)")
        elif slope < 20.0:
            slope_s = 0.35
            neg.append(f"High slope gradient ({slope:.1f}° - rovers require high traction)")
        else:
            slope_s = 0.05
            neg.append(f"Very steep slope ({slope:.1f}° - exceeds safe rover transit limits)")

        # Roughness evaluation
        rough = terrain.roughness_score
        if rough < 2.0:
            rough_s = 1.0
            pos.append(f"Smooth regolith surface (roughness {rough:.2f}m std dev)")
        elif rough < 4.0:
            rough_s = 0.65
        elif rough < 6.0:
            rough_s = 0.30
            neg.append(f"Elevated surface roughness ({rough:.2f}m std dev - blocky ejecta risk)")
        else:
            rough_s = 0.05
            neg.append(f"Severe surface roughness ({rough:.2f}m std dev - landing hazard)")

        score = 0.6 * slope_s + 0.4 * rough_s
        return round(score, 4), pos, neg

    def compute_illumination_score(self, illumination: Optional[IlluminationMetrics]) -> Tuple[float, List[str], List[str]]:
        """Compute illumination score (0.0 to 1.0) and generate lighting factor tags."""
        if illumination is None:
            return 0.5, [], ["Illumination data NOT_AVAILABLE (assigned neutral score)"]

        pos = []
        neg = []

        mean_illum = illumination.illumination_mean
        shadow_frac = illumination.shadow_fraction

        if illumination.illumination_state == IlluminationStatus.ILLUMINATED:
            pos.append(f"Favorable solar illumination ({mean_illum * 100:.1f}% mean intensity)")
        elif illumination.illumination_state == IlluminationStatus.PARTIALLY_ILLUMINATED:
            pos.append(f"Partially illuminated surface ({mean_illum * 100:.1f}% mean intensity)")
        elif illumination.illumination_state == IlluminationStatus.LOW_LIGHT:
            neg.append(f"Low ambient lighting ({mean_illum * 100:.1f}% mean intensity)")
        elif illumination.illumination_state == IlluminationStatus.SHADOWED:
            neg.append(f"Deep shadow regime ({shadow_frac * 100:.1f}% shadow coverage)")

        if shadow_frac < 0.15:
            pos.append(f"Low shadow fraction ({shadow_frac * 100:.1f}%)")
        elif shadow_frac > 0.60:
            neg.append(f"High shadow fraction ({shadow_frac * 100:.1f}% - cryogenic trap)")

        score = max(0.0, min(1.0, mean_illum * (1.0 - 0.7 * shadow_frac)))
        return round(score, 4), pos, neg

    def compute_hazard_penalty(self, hazards: List[HazardIndicator]) -> Tuple[float, List[str]]:
        """Compute hazard penalty score (0.0 = no hazards, 1.0 = severe hazards)."""
        if not hazards:
            return 0.0, []

        penalty = 0.0
        neg = []
        for h in hazards:
            if h.severity == HazardSeverity.CRITICAL:
                penalty += 0.50
                neg.append(f"[CRITICAL HAZARD] {h.description}")
            elif h.severity == HazardSeverity.HIGH:
                penalty += 0.25
                neg.append(f"[HIGH HAZARD] {h.description}")
            elif h.severity == HazardSeverity.MODERATE:
                penalty += 0.10
                neg.append(f"[MODERATE HAZARD] {h.description}")
            else:
                penalty += 0.05
                neg.append(f"[LOW HAZARD] {h.description}")

        return round(min(1.0, penalty), 4), neg

    def evaluate_site(
        self,
        site_id: str,
        patch_id: str,
        coordinates: Dict[str, float],
        bbox: Dict[str, float],
        terrain: Optional[TerrainMetrics] = None,
        illumination: Optional[IlluminationMetrics] = None,
        resource: Optional[ResourceIndicator] = None,
        hazards: Optional[List[HazardIndicator]] = None,
        poc6_registration_confidence: float = 0.95,
        poc6_inlier_ratio: float = 1.0,
        contributing_observations: Optional[List[str]] = None,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> CandidateSite:
        """Score candidate site across all dimensions and generate structured explainability."""
        haz_list = hazards or []
        prov = provenance or {}

        # 1. Dimension scores and factor checklists
        t_score, t_pos, t_neg = self.compute_terrain_score(terrain)
        i_score, i_pos, i_neg = self.compute_illumination_score(illumination)
        h_penalty, h_neg = self.compute_hazard_penalty(haz_list)

        r_score = resource.indicator_score if resource else 0.0
        r_pos = [f"Resource-related spectral indicator present (score {r_score:.2f})"] if r_score > 0.35 else []

        # Data quality score from POC-6 verified correspondence
        q_score = round(0.7 * poc6_registration_confidence + 0.3 * poc6_inlier_ratio, 4)
        q_pos = [f"High-confidence verified geometric registration ({poc6_registration_confidence:.3f}, {poc6_inlier_ratio*100:.0f}% inliers)"]

        # 2. Weighted overall suitability score
        # suitability = w_t * t + w_i * i + w_r * r + w_q * q - w_h * h_penalty
        w = self.weights
        composite = (
            w["terrain"] * t_score
            + w["illumination"] * i_score
            + w["resource"] * r_score
            + w["data_quality"] * q_score
            - w["hazard_penalty"] * h_penalty
        )
        suitability = round(float(max(0.0, min(1.0, composite))), 4)

        # 3. Assemble explanation
        all_pos = t_pos + i_pos + r_pos + q_pos
        if not haz_list:
            all_pos.append("No constraining physical hazards detected")
        all_neg = t_neg + i_neg + h_neg

        if suitability >= 0.65:
            verdict = "FAVORABLE CANDIDATE SITE FOR FURTHER HABITAT DIGITAL TWIN EVALUATION"
        elif suitability >= 0.45:
            verdict = "MARGINAL / CONSTRAINED CANDIDATE SITE (MODERATE RISK / LIGHTING CONSTRAINTS)"
        else:
            verdict = "HIGH-RISK / UNFAVORABLE SITE (STEEP TERRAIN OR SEVERE HAZARDS)"

        explanation = CandidateSiteExplanation(
            site_id=site_id,
            positive_factors=all_pos,
            negative_factors=all_neg,
            summary_verdict=verdict,
        )

        # Determine data status — conservatively propagate from component data_status fields.
        # If ANY component is synthetic, the site is at minimum SYNTHETIC_DEMO.
        # Only all-DATA-DRIVEN components justify DATA_DRIVEN site status.
        component_statuses = []
        if terrain:
            component_statuses.append(getattr(terrain, "data_status", "SYNTHETIC OFFLINE DEMO"))
        if illumination:
            component_statuses.append(getattr(illumination, "data_status", "SYNTHETIC OFFLINE DEMO"))
        if resource:
            component_statuses.append(getattr(resource, "data_status", "SYNTHETIC OFFLINE DEMO"))

        if not component_statuses:
            data_status = SiteDataStatus.PARTIALLY_OBSERVABLE
        elif all(s == "DATA-DRIVEN" for s in component_statuses) and terrain and illumination and resource:
            data_status = SiteDataStatus.DATA_DRIVEN
        elif any("SYNTHETIC" in s for s in component_statuses):
            data_status = SiteDataStatus.SYNTHETIC_DEMO
        else:
            data_status = SiteDataStatus.PARTIALLY_OBSERVABLE

        return CandidateSite(
            site_id=site_id,
            patch_id=patch_id,
            coordinates=coordinates,
            bbox=bbox,
            terrain_score=t_score,
            illumination_score=i_score,
            hazard_penalty=h_penalty,
            resource_indicator_score=r_score,
            spatial_data_quality_score=q_score,
            overall_suitability_score=suitability,
            scoring_weights=self.weights,
            data_status=data_status,
            hazards_affecting=[h.hazard_id for h in haz_list],
            contributing_observations=contributing_observations or [],
            explanation=explanation,
            provenance=prov,
        )
