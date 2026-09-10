"""Frequency & Electromagnetic Wave Mechanics Engine.
Models radio-frequency penetration, skin depth, radar backscatter, dielectric permittivity,
and multi-spectral harmonic wave interactions across the lunar surface.
"""

from __future__ import annotations
import math
from typing import Dict, Any, List
import numpy as np


class FrequencyEngine:
    """Calculates radio-frequency electromagnetic wave propagation in lunar regolith."""

    SPEED_OF_LIGHT = 299792458.0  # m/s
    VACUUM_PERMITTIVITY = 8.8541878128e-12  # F/m
    VACUUM_PERMEABILITY = 1.25663706212e-6  # H/m

    # Standard Spaceborne Radar Frequencies
    RADAR_BANDS = {
        "S_BAND": {"name": "Chandrayaan-2 DFSAR S-Band", "freq_hz": 3.2e9, "wavelength_m": 0.0937},
        "L_BAND": {"name": "Chandrayaan-2 DFSAR L-Band", "freq_hz": 1.25e9, "wavelength_m": 0.2398},
        "C_BAND": {"name": "ISRO RISAT-1 C-Band", "freq_hz": 5.35e9, "wavelength_m": 0.0560},
        "P_BAND": {"name": "Low-Frequency Sounder P-Band", "freq_hz": 430e6, "wavelength_m": 0.6972},
    }

    @classmethod
    def estimate_dielectric_permittivity(cls, bulk_density_g_cm3: float = 1.55, tio2_fe2o3_pct: float = 8.0) -> Dict[str, float]:
        """Estimates real (epsilon') and imaginary (epsilon'') dielectric permittivity.
        Using Carrier, Olhoeft, and Strangway lunar empirical relationships:
        epsilon' = 1.93^rho
        tan_delta = 10^(0.038 * (TiO2 + FeO) - 2.8)
        """
        rho = max(0.8, min(3.2, bulk_density_g_cm3))
        eps_real = math.pow(1.93, rho)

        # Loss tangent calculation from titanium/iron mineral weight percentage
        tot_metals = max(0.0, min(30.0, tio2_fe2o3_pct))
        log_tan_delta = (0.038 * tot_metals) - 2.8
        tan_delta = math.pow(10.0, log_tan_delta)

        eps_imag = eps_real * tan_delta
        return {
            "bulk_density_g_cm3": rho,
            "epsilon_real": round(eps_real, 4),
            "epsilon_imag": round(eps_imag, 6),
            "loss_tangent": round(tan_delta, 6),
        }

    @classmethod
    def compute_skin_depth(
        cls,
        frequency_hz: float,
        bulk_density_g_cm3: float = 1.55,
        tio2_pct: float = 5.0,
    ) -> Dict[str, float]:
        """Computes RF penetration skin depth delta (meters) where wave power decays to 1/e:
        delta = c / (2 * pi * f * sqrt(epsilon') * tan_delta)
        """
        diel = cls.estimate_dielectric_permittivity(bulk_density_g_cm3, tio2_pct)
        eps_r = diel["epsilon_real"]
        tan_d = diel["loss_tangent"]

        wavelength_m = cls.SPEED_OF_LIGHT / frequency_hz

        # Low-loss dielectric approximation
        if tan_d > 0:
            skin_depth_m = cls.SPEED_OF_LIGHT / (2.0 * math.pi * frequency_hz * math.sqrt(eps_r) * tan_d)
        else:
            skin_depth_m = 50.0

        two_way_attenuation_db_per_m = 8.686 / skin_depth_m

        return {
            "frequency_hz": frequency_hz,
            "frequency_ghz": round(frequency_hz / 1e9, 3),
            "free_space_wavelength_m": round(wavelength_m, 4),
            "dielectric_constant": eps_r,
            "loss_tangent": tan_d,
            "skin_depth_m": round(skin_depth_m, 3),
            "max_detectable_depth_m": round(skin_depth_m * 2.5, 3),
            "two_way_attenuation_db_per_m": round(two_way_attenuation_db_per_m, 3),
        }

    @classmethod
    def analyze_multi_frequency_penetration(cls, bulk_density: float = 1.6, tio2_pct: float = 6.0) -> Dict[str, Any]:
        """Calculates multi-frequency penetration matrix for all radar bands."""
        results = {}
        for band_key, band_meta in cls.RADAR_BANDS.items():
            res = cls.compute_skin_depth(band_meta["freq_hz"], bulk_density, tio2_pct)
            res["band_name"] = band_meta["name"]
            results[band_key] = res

        return {
            "regolith_bulk_density": bulk_density,
            "tio2_weight_pct": tio2_pct,
            "bands": results,
            "ice_detection_recommended_band": "L_BAND" if results["L_BAND"]["skin_depth_m"] >= 2.0 else "P_BAND",
        }

    @classmethod
    def compute_rayleigh_roughness(cls, rms_height_m: float, incidence_deg: float, frequency_hz: float) -> Dict[str, Any]:
        """Computes Rayleigh roughness criterion Ra:
        Ra = 4 * pi * sigma * cos(theta) / lambda
        Ra < 0.1: Specular flat surface
        Ra > 1.0: Diffuse rough surface
        """
        wl = cls.SPEED_OF_LIGHT / frequency_hz
        theta_rad = math.radians(incidence_deg)
        ra = (4.0 * math.pi * rms_height_m * math.cos(theta_rad)) / wl

        is_rough = ra > 1.0
        return {
            "frequency_hz": frequency_hz,
            "wavelength_m": round(wl, 4),
            "rms_height_m": rms_height_m,
            "incidence_deg": incidence_deg,
            "rayleigh_parameter": round(ra, 4),
            "scattering_regime": "DIFFUSE_ROUGH" if ra > 1.0 else ("MODERATE_SCATTERING" if ra > 0.3 else "SPECULAR_SMOOTH"),
        }
