"""Chemistry & Mineralogy First-Principles Engine.
Models hyperspectral continuum removal, absorption band depths (OH/H2O, Pyroxene),
and stoichiometric ISRU pyrolysis reduction yields.
"""

from __future__ import annotations
import math
from typing import Dict, Any, List
import numpy as np


class ChemistryEngine:
    """Chemical stoichiometry, spectroscopy, and In-Situ Resource Utilization (ISRU)."""

    # Molar masses (g/mol)
    MOLAR_MASS_FETIO3 = 151.71  # Ilmenite
    MOLAR_MASS_FE = 55.845      # Iron
    MOLAR_MASS_TIO2 = 79.866    # Rutile
    MOLAR_MASS_O2 = 31.9988     # Oxygen gas
    MOLAR_MASS_H2O = 18.01528   # Water
    MOLAR_MASS_H2 = 2.01588     # Hydrogen gas

    # Thermochemical Reaction Enthalpies
    DELTA_H_ILMENITE_REDUCTION = 64.5e3  # J/mol of FeTiO3 at 1100 K (850°C)
    REGOLITH_HEAT_CAPACITY = 1200.0      # J/(kg K) at elevated temp
    REACTION_TEMP_K = 1123.15            # 850 °C

    # =========================================================================
    # 1. Hyperspectral Continuum Removal & Molecular Band Depth
    # =========================================================================
    @classmethod
    def compute_band_depth(
        cls,
        wavelengths_um: List[float],
        reflectance: List[float],
        band_center_um: float = 2.85,
        left_continuum_um: float = 2.55,
        right_continuum_um: float = 3.15,
    ) -> Dict[str, Any]:
        """Calculates absorption band depth:
        BD = 1 - (R_band / R_continuum)
        Proxy for molecular OH/H2O absorption and mineral phase identification.
        """
        wl = np.array(wavelengths_um)
        refl = np.array(reflectance)

        idx_left = int(np.argmin(np.abs(wl - left_continuum_um)))
        idx_right = int(np.argmin(np.abs(wl - right_continuum_um)))
        idx_center = int(np.argmin(np.abs(wl - band_center_um)))

        w_left, r_left = wl[idx_left], refl[idx_left]
        w_right, r_right = wl[idx_right], refl[idx_right]
        w_center, r_center = wl[idx_center], refl[idx_center]

        # Linear continuum interpolation
        slope = (r_right - r_left) / max(1e-6, (w_right - w_left))
        continuum_at_center = r_left + slope * (w_center - w_left)

        band_depth = 1.0 - (r_center / max(1e-6, continuum_at_center))
        band_depth = max(0.0, band_depth)

        # Estimate volatile proxy concentration
        water_equiv_wt_ppm = round(float(band_depth * 1850.0), 1)

        return {
            "target_molecule": "OH_H2O_HYDRATION" if abs(band_center_um - 2.85) < 0.2 else "MINERAL_ABSORPTION",
            "band_center_um": band_center_um,
            "measured_reflectance": round(float(r_center), 4),
            "interpolated_continuum": round(float(continuum_at_center), 4),
            "band_depth": round(float(band_depth), 5),
            "estimated_water_equivalent_ppm": water_equiv_wt_ppm,
            "detection_confidence": "HIGH" if band_depth > 0.04 else ("MARGINAL" if band_depth > 0.015 else "BACKGROUND_NOISE"),
        }

    # =========================================================================
    # 2. ISRU Ilmenite Hydrogen Reduction Stoichiometry
    # =========================================================================
    @classmethod
    def compute_isru_oxygen_yield(
        cls,
        regolith_tonnes: float = 10.0,
        ilmenite_weight_pct: float = 4.5,
        reaction_efficiency: float = 0.88,
        electrolysis_efficiency: float = 0.92,
    ) -> Dict[str, Any]:
        """Computes exact mass balance for:
        FeTiO3 + H2 -> Fe + TiO2 + H2O
        2 H2O -> 2 H2 + O2 (via electrolysis)
        """
        regolith_kg = regolith_tonnes * 1000.0
        ilmenite_mass_kg = regolith_kg * (ilmenite_weight_pct / 100.0)

        # Theoretical yield factor of Oxygen from Ilmenite: (1/2 * M_O2) / M_FeTiO3
        # 1 mol FeTiO3 -> 1 mol H2O -> 0.5 mol O2
        theoretical_o2_fraction = (0.5 * cls.MOLAR_MASS_O2) / cls.MOLAR_MASS_FETIO3  # ~ 0.10546
        theoretical_fe_fraction = cls.MOLAR_MASS_FE / cls.MOLAR_MASS_FETIO3          # ~ 0.3681

        total_system_efficiency = reaction_efficiency * electrolysis_efficiency
        actual_o2_kg = ilmenite_mass_kg * theoretical_o2_fraction * total_system_efficiency
        actual_fe_kg = ilmenite_mass_kg * theoretical_fe_fraction * reaction_efficiency
        actual_water_intermediate_kg = actual_o2_kg * (cls.MOLAR_MASS_H2O / (0.5 * cls.MOLAR_MASS_O2))

        # Thermal energy requirement to heat regolith from 200K to 1123K
        delta_t = cls.REACTION_TEMP_K - 200.0
        thermal_energy_heating_j = ilmenite_mass_kg * cls.REGOLITH_HEAT_CAPACITY * delta_t
        moles_ilmenite = (ilmenite_mass_kg * 1000.0) / cls.MOLAR_MASS_FETIO3
        reaction_enthalpy_j = moles_ilmenite * cls.DELTA_H_ILMENITE_REDUCTION
        total_energy_kwh = (thermal_energy_heating_j + reaction_enthalpy_j) / 3.6e6

        return {
            "processed_regolith_tonnes": regolith_tonnes,
            "ilmenite_content_pct": ilmenite_weight_pct,
            "ilmenite_available_kg": round(ilmenite_mass_kg, 2),
            "oxygen_yield_kg": round(actual_o2_kg, 2),
            "iron_byproduct_kg": round(actual_fe_kg, 2),
            "intermediate_water_kg": round(actual_water_intermediate_kg, 2),
            "o2_kg_per_regolith_tonne": round(actual_o2_kg / max(0.01, regolith_tonnes), 3),
            "thermal_energy_kwh": round(total_energy_kwh, 2),
            "energy_kwh_per_kg_o2": round(total_energy_kwh / max(0.1, actual_o2_kg), 2),
        }
