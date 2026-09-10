"""Tests for First-Principles Scientific Core Package (Physics, Chemistry, Biology, Frequency)."""

import pytest
import math
from packages.first_principles import (
    FrequencyEngine,
    PhysicsEngine,
    ChemistryEngine,
    BiologyEngine,
)


def test_frequency_engine_permittivity_and_skin_depth():
    # 1. Dielectric permittivity calculation
    diel = FrequencyEngine.estimate_dielectric_permittivity(bulk_density_g_cm3=1.6, tio2_fe2o3_pct=8.0)
    assert 2.5 <= diel["epsilon_real"] <= 3.2
    assert diel["loss_tangent"] > 0

    # 2. SAR skin depth calculation
    l_band = FrequencyEngine.compute_skin_depth(frequency_hz=1.25e9, bulk_density_g_cm3=1.6, tio2_pct=5.0)
    assert l_band["skin_depth_m"] > 1.0  # L-band must penetrate > 1m in lunar regolith

    s_band = FrequencyEngine.compute_skin_depth(frequency_hz=3.2e9, bulk_density_g_cm3=1.6, tio2_pct=5.0)
    assert s_band["skin_depth_m"] < l_band["skin_depth_m"]  # Higher frequency has lower penetration

    # 3. Multi-frequency matrix
    matrix = FrequencyEngine.analyze_multi_frequency_penetration(bulk_density=1.6, tio2_pct=6.0)
    assert "L_BAND" in matrix["bands"]
    assert "S_BAND" in matrix["bands"]

    # 4. Rayleigh roughness
    roughness = FrequencyEngine.compute_rayleigh_roughness(rms_height_m=0.08, incidence_deg=35.0, frequency_hz=1.25e9)
    assert "scattering_regime" in roughness


def test_physics_engine_hapke_and_thermodynamics():
    # 1. Hapke BRDF
    hapke = PhysicsEngine.compute_hapke_reflectance(
        incidence_deg=65.0,
        emission_deg=10.0,
        phase_deg=55.0,
        single_scattering_albedo=0.30,
    )
    assert hapke["hapke_reflectance"] > 0.0
    assert hapke["relative_brightness_factor"] > 0.0

    # Test grazing shadow detection
    grazing = PhysicsEngine.compute_hapke_reflectance(incidence_deg=87.0, emission_deg=5.0, phase_deg=82.0)
    assert grazing["is_deep_grazing_shadow"] is True

    # 2. Thermal diffusion
    thermal = PhysicsEngine.simulate_subsurface_thermal_profile(
        max_surface_temp_k=220.0,
        min_surface_temp_k=40.0,
        depth_m=1.2,
    )
    assert thermal["thermal_skin_depth_cm"] > 0.0
    assert len(thermal["depth_profile"]) > 5
    # Sub-surface temperature amplitude must damp exponentially with depth
    amp_surface = thermal["depth_profile"][0]["temp_amplitude_k"]
    amp_deep = thermal["depth_profile"][-1]["temp_amplitude_k"]
    assert amp_deep < amp_surface

    # 3. Bekker rover terramechanics
    rover = PhysicsEngine.compute_rover_terramechanics(rover_mass_kg=300.0, slope_deg=10.0)
    assert rover["wheel_sinkage_cm"] > 0.0
    assert rover["net_drawbar_pull_n"] > 0.0
    assert rover["mobility_verdict"] == "GO_SAFE_TRAVERSAL"


def test_chemistry_engine_isru_and_band_depth():
    # 1. Molecular absorption band depth
    wavelengths = [2.4, 2.55, 2.7, 2.85, 3.0, 3.15, 3.3]
    reflectance = [0.25, 0.26, 0.24, 0.20, 0.23, 0.27, 0.28]  # Dip at 2.85 um
    band = ChemistryEngine.compute_band_depth(wavelengths, reflectance, band_center_um=2.85)
    assert band["band_depth"] > 0.05
    assert band["estimated_water_equivalent_ppm"] > 100.0

    # 2. Stoichiometric ISRU Hydrogen reduction
    # FeTiO3 (151.71) -> 0.5 O2 (16) -> theoretical max yield ~10.55%
    isru = ChemistryEngine.compute_isru_oxygen_yield(
        regolith_tonnes=10.0,
        ilmenite_weight_pct=100.0,  # Pure ilmenite baseline
        reaction_efficiency=1.0,
        electrolysis_efficiency=1.0,
    )
    assert math.isclose(isru["oxygen_yield_kg"], 1054.6, rel_tol=1e-2)
    assert isru["thermal_energy_kwh"] > 0.0

    # Real lunar regolith test (4.5% ilmenite)
    isru_regolith = ChemistryEngine.compute_isru_oxygen_yield(regolith_tonnes=5.0, ilmenite_weight_pct=4.5)
    assert isru_regolith["oxygen_yield_kg"] > 10.0


def test_biology_engine_eclss_and_radiation_shielding():
    # 1. Closed-loop ECLSS simulation
    eclss = BiologyEngine.simulate_habitat_eclss(
        crew_size=4,
        mission_duration_days=30,
        water_recovery_ratio=0.95,
        sabatier_co2_recovery_ratio=0.88,
        o2_isru_daily_feed_kg=4.0,
    )
    assert eclss["gross_o2_demand_kg"] == 4 * 0.84 * 30
    assert eclss["water_recycled_kg"] > 0.9 * eclss["water_demand_total_kg"]
    assert eclss["o2_loop_closure_pct"] >= 100.0

    # 2. Radiation mass-depth biological shielding
    shield_safe = BiologyEngine.compute_radiation_shielding(regolith_shield_thickness_m=2.5)
    assert shield_safe["attenuated_annual_dose_msv_yr"] <= 20.0
    assert shield_safe["radiation_safety_verdict"] == "SAFE_PERMANENT_HABITATION"

    # Thin shield must exceed safe limits
    shield_thin = BiologyEngine.compute_radiation_shielding(regolith_shield_thickness_m=0.3)
    assert shield_thin["attenuated_annual_dose_msv_yr"] > 20.0
    assert shield_thin["radiation_safety_verdict"] == "EXCEEDS_CAREER_DOSE_LIMIT"
