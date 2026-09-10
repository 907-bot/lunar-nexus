"""Biology, Astrobiology & Human ECLSS First-Principles Engine.
Models human metabolic consumption, closed-loop life support (ECLSS), Sabatier recovery,
and Galactic Cosmic Ray (GCR) radiation mass-depth biological attenuation.
"""

from __future__ import annotations
import math
from typing import Dict, Any, List


class BiologyEngine:
    """Life support bio-energetics, metabolic balance, and cosmic radiation bio-shielding."""

    # Human Metabolic Daily Constants per Astronaut (NASA-STD-3001)
    DAILY_O2_CONSUMPTION_KG = 0.84       # kg O2 / crew-day
    DAILY_CO2_PRODUCTION_KG = 1.00        # kg CO2 / crew-day
    DAILY_DRINKING_WATER_KG = 2.50       # kg H2O / crew-day
    DAILY_HYGIENE_WATER_KG = 22.5        # kg H2O / crew-day
    DAILY_METABOLIC_WATER_KG = 0.35      # kg H2O produced internally
    DAILY_FOOD_DRY_KG = 0.65             # kg dry biomass / crew-day (3000 kcal)

    # Lunar Radiation Environment
    SURFACE_GCR_ANNUAL_MSV = 380.0       # Average lunar surface GCR dose (mSv/year)
    SOLAR_PARTICLE_EVENT_MAX_MSV = 2500.0# Peak unshielded SPE dose (mSv)
    CAREER_ASTRONAUT_LIMIT_MSV = 20.0    # ALARA occupational safety threshold (mSv/year)
    REGOLITH_ATTENUATION_LENGTH_G_CM2 = 92.0  # Effective mass-attenuation length

    # =========================================================================
    # 1. Closed-Loop ECLSS Mass Balance Simulation
    # =========================================================================
    @classmethod
    def simulate_habitat_eclss(
        cls,
        crew_size: int = 4,
        mission_duration_days: int = 30,
        water_recovery_ratio: float = 0.95,
        sabatier_co2_recovery_ratio: float = 0.88,
        o2_isru_daily_feed_kg: float = 5.0,
    ) -> Dict[str, Any]:
        """Simulates complete life-support closed loop over the lunar mission duration."""
        crew = max(1, crew_size)
        days = max(1, mission_duration_days)

        # Gross requirements without recycling
        gross_o2_kg = crew * cls.DAILY_O2_CONSUMPTION_KG * days
        gross_drinking_h2o_kg = crew * cls.DAILY_DRINKING_WATER_KG * days
        gross_hygiene_h2o_kg = crew * cls.DAILY_HYGIENE_WATER_KG * days
        total_water_demand_kg = gross_drinking_h2o_kg + gross_hygiene_h2o_kg

        # Closed-loop recycling credits
        recycled_water_kg = total_water_demand_kg * min(0.99, water_recovery_ratio)
        net_water_makeup_kg = total_water_demand_kg - recycled_water_kg

        # Sabatier CO2 reduction: CO2 + 4H2 -> CH4 + 2H2O
        co2_total_kg = crew * cls.DAILY_CO2_PRODUCTION_KG * days
        co2_scrubbed_kg = co2_total_kg * sabatier_co2_recovery_ratio
        recovered_o2_from_co2_kg = co2_scrubbed_kg * (32.0 / 44.01) * 0.90

        # ISRU contributions
        isru_o2_total_kg = o2_isru_daily_feed_kg * days
        total_o2_available_kg = recovered_o2_from_co2_kg + isru_o2_total_kg
        net_o2_deficit_kg = max(0.0, gross_o2_kg - total_o2_available_kg)
        o2_autonomy_pct = min(100.0, (total_o2_available_kg / max(1e-3, gross_o2_kg)) * 100.0)

        # Night survival buffer (354 hours of lunar darkness = 14.75 days)
        lunar_night_days = 14.75
        night_buffer_o2_kg = crew * cls.DAILY_O2_CONSUMPTION_KG * lunar_night_days
        night_buffer_h2o_kg = crew * cls.DAILY_DRINKING_WATER_KG * lunar_night_days

        return {
            "crew_size": crew,
            "mission_duration_days": days,
            "gross_o2_demand_kg": round(gross_o2_kg, 2),
            "recovered_o2_kg": round(recovered_o2_from_co2_kg, 2),
            "isru_o2_produced_kg": round(isru_o2_total_kg, 2),
            "net_o2_deficit_kg": round(net_o2_deficit_kg, 2),
            "o2_loop_closure_pct": round(o2_autonomy_pct, 1),
            "water_demand_total_kg": round(total_water_demand_kg, 2),
            "water_recycled_kg": round(recycled_water_kg, 2),
            "water_resupply_needed_kg": round(net_water_makeup_kg, 2),
            "lunar_night_reserve_o2_kg": round(night_buffer_o2_kg, 2),
            "lunar_night_reserve_h2o_kg": round(night_buffer_h2o_kg, 2),
            "eclss_status": "CLOSED_AUTONOMOUS" if o2_autonomy_pct >= 100.0 else "PARTIALLY_OPEN_REQUIRES_STORED_CRYOGENICS",
        }

    # =========================================================================
    # 2. Lunar Radiation Bio-Shielding Mass-Depth Attenuation
    # =========================================================================
    @classmethod
    def compute_radiation_shielding(
        cls,
        regolith_shield_thickness_m: float = 2.5,
        regolith_bulk_density_g_cm3: float = 1.6,
    ) -> Dict[str, Any]:
        """Calculates biological radiation exposure:
        Areal Mass (g/cm^2) = rho * thickness
        Dose(z) = D0 * exp(-Areal_Mass / lambda_eff)
        """
        thickness_cm = regolith_shield_thickness_m * 100.0
        areal_mass_g_cm2 = regolith_bulk_density_g_cm3 * thickness_cm

        # Exponential attenuation of primary GCR flux and secondary particle build-up factor
        attenuation_factor = math.exp(-areal_mass_g_cm2 / cls.REGOLITH_ATTENUATION_LENGTH_G_CM2)
        annual_dose_msv = cls.SURFACE_GCR_ANNUAL_MSV * attenuation_factor
        spe_attenuated_msv = cls.SOLAR_PARTICLE_EVENT_MAX_MSV * attenuation_factor

        # Minimum thickness to achieve career threshold (< 20 mSv/year)
        target_atten = cls.CAREER_ASTRONAUT_LIMIT_MSV / cls.SURFACE_GCR_ANNUAL_MSV
        required_areal_mass = -cls.REGOLITH_ATTENUATION_LENGTH_G_CM2 * math.log(target_atten)
        min_required_thickness_m = (required_areal_mass / regolith_bulk_density_g_cm3) / 100.0

        is_safe = annual_dose_msv <= cls.CAREER_ASTRONAUT_LIMIT_MSV

        return {
            "shield_thickness_m": round(regolith_shield_thickness_m, 2),
            "regolith_areal_mass_g_cm2": round(areal_mass_g_cm2, 1),
            "surface_unshielded_dose_msv_yr": cls.SURFACE_GCR_ANNUAL_MSV,
            "attenuated_annual_dose_msv_yr": round(annual_dose_msv, 2),
            "worst_case_spe_dose_msv": round(spe_attenuated_msv, 2),
            "minimum_safe_thickness_m": round(min_required_thickness_m, 2),
            "radiation_safety_verdict": "SAFE_PERMANENT_HABITATION" if is_safe else "EXCEEDS_CAREER_DOSE_LIMIT",
            "shielding_adequacy_ratio": round(regolith_shield_thickness_m / max(0.01, min_required_thickness_m), 2),
        }
