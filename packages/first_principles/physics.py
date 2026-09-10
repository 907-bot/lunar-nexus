"""Physics & Mechanics First-Principles Engine.
Models Hapke Photometric BRDF radiative transfer, 1D sub-surface thermal diffusion,
cryogenic volatile cold-traps, and Bekker-Wong rover terramechanics.
"""

from __future__ import annotations
import math
from typing import Dict, Any, List
import numpy as np


class PhysicsEngine:
    """Rigorous physical laws and mechanical dynamics for the lunar environment."""

    STEFAN_BOLTZMANN = 5.670374419e-8  # W/(m^2 K^4)
    SOLAR_CONSTANT_MOON = 1361.0  # W/m^2
    LUNAR_GRAVITY = 1.625  # m/s^2
    SYNODIC_MONTH_SEC = 29.530589 * 86400.0  # seconds

    # =========================================================================
    # 1. Hapke Photometric BRDF Model (Radiative Transfer)
    # =========================================================================
    @classmethod
    def compute_hapke_reflectance(
        cls,
        incidence_deg: float,
        emission_deg: float,
        phase_deg: float,
        single_scattering_albedo: float = 0.28,
        opposition_h: float = 0.065,
        opposition_b0: float = 1.6,
        asymmetry_xi: float = -0.37,
    ) -> Dict[str, float]:
        """Calculates bidirectional reflectance factor r(i, e, g) using Hapke's equation.
        Corrects low-sun polar grazing illumination.
        """
        i_rad = math.radians(min(89.5, max(0.0, incidence_deg)))
        e_rad = math.radians(min(89.5, max(0.0, emission_deg)))
        g_rad = math.radians(min(179.0, max(0.0, phase_deg)))

        mu0 = math.cos(i_rad)
        mu = math.cos(e_rad)
        w = max(0.01, min(0.99, single_scattering_albedo))

        # 1. Opposition surge term B(g)
        b_g = opposition_b0 / (1.0 + (1.0 / opposition_h) * math.tan(g_rad / 2.0))

        # 2. Single particle phase function P(g) - Henyey-Greenstein
        cos_g = math.cos(g_rad)
        xi = asymmetry_xi
        denom_pg = math.pow(1.0 + xi * xi + 2.0 * xi * cos_g, 1.5)
        p_g = (1.0 - xi * xi) / max(1e-6, denom_pg)

        # 3. Chandrasekhar H-functions approximation
        gamma = math.sqrt(1.0 - w)
        r0 = (1.0 - gamma) / (1.0 + gamma)
        h_mu0 = (1.0 + 2.0 * mu0) / (1.0 + 2.0 * mu0 * gamma)
        h_mu = (1.0 + 2.0 * mu) / (1.0 + 2.0 * mu * gamma)

        # 4. Total Hapke Reflectance
        geom_factor = mu0 / (4.0 * math.pi * (mu0 + mu))
        bracket = (1.0 + b_g) * p_g + (h_mu0 * h_mu - 1.0)
        reflectance = w * geom_factor * bracket

        # Normalization factor relative to standard 30-deg incidence
        ref_standard = w * (math.cos(math.radians(30)) / (4.0 * math.pi * 2.0 * math.cos(math.radians(30))))
        norm_factor = reflectance / max(1e-6, ref_standard)

        return {
            "incidence_deg": incidence_deg,
            "emission_deg": emission_deg,
            "phase_deg": phase_deg,
            "hapke_reflectance": round(reflectance, 6),
            "relative_brightness_factor": round(norm_factor, 4),
            "opposition_surge_multiplier": round(1.0 + b_g, 3),
            "is_deep_grazing_shadow": incidence_deg >= 85.0,
        }

    # =========================================================================
    # 2. Sub-Surface 1D Thermal Diffusion & Cold Trap Physics
    # =========================================================================
    @classmethod
    def simulate_subsurface_thermal_profile(
        cls,
        max_surface_temp_k: float = 240.0,
        min_surface_temp_k: float = 40.0,
        depth_m: float = 1.5,
        bulk_density_kg_m3: float = 1600.0,
        specific_heat_j_kg_k: float = 650.0,
        thermal_conductivity_w_m_k: float = 0.015,
        num_layers: int = 15,
    ) -> Dict[str, Any]:
        """Models 1D lunar regolith heat diffusion:
        rho * c_p * (dT/dt) = d/dz [ k * (dT/dz) ]
        Computes diurnal temperature damping depth skin depth:
        l_th = sqrt(k / (rho * c_p * omega))
        """
        omega = 2.0 * math.pi / cls.SYNODIC_MONTH_SEC
        thermal_diffusivity = thermal_conductivity_w_m_k / (bulk_density_kg_m3 * specific_heat_j_kg_k)
        thermal_skin_depth_m = math.sqrt(2.0 * thermal_diffusivity / omega)

        mean_surface_k = (max_surface_temp_k + min_surface_temp_k) / 2.0
        delta_t0 = (max_surface_temp_k - min_surface_temp_k) / 2.0

        depths = np.linspace(0.0, depth_m, num_layers)
        profile = []
        cold_trap_detected = False

        for z in depths:
            # Exponential damping of temperature oscillation with depth
            amplitude_z = delta_t0 * math.exp(-z / thermal_skin_depth_m)
            t_max_z = mean_surface_k + amplitude_z
            t_min_z = mean_surface_k - amplitude_z

            is_ice_stable = t_max_z <= 110.0  # H2O ice sublimation threshold (<110K)
            if is_ice_stable and z > 0.1:
                cold_trap_detected = True

            profile.append({
                "depth_cm": round(float(z * 100.0), 1),
                "max_temp_k": round(float(t_max_z), 2),
                "min_temp_k": round(float(t_min_z), 2),
                "mean_temp_k": round(float(mean_surface_k), 2),
                "temp_amplitude_k": round(float(amplitude_z), 2),
                "water_ice_thermally_stable": is_ice_stable,
            })

        return {
            "surface_temp_range_k": [min_surface_temp_k, max_surface_temp_k],
            "thermal_skin_depth_cm": round(thermal_skin_depth_m * 100.0, 2),
            "thermal_diffusivity_m2_s": f"{thermal_diffusivity:.3e}",
            "cold_trap_at_depth": cold_trap_detected,
            "depth_profile": profile,
            "ice_stability_verdict": "PERMANENT_SUB_SURFACE_TRAP" if cold_trap_detected else "TRANSIENT_SEASONAL",
        }

    # =========================================================================
    # 3. Bekker-Wong Rover Terramechanics (Wheel-Soil Mechanics)
    # =========================================================================
    @classmethod
    def compute_rover_terramechanics(
        cls,
        rover_mass_kg: float = 350.0,
        wheel_radius_m: float = 0.25,
        wheel_width_m: float = 0.20,
        slope_deg: float = 12.0,
        cohesion_pa: float = 800.0,  # Lunar regolith cohesion
        friction_angle_deg: float = 38.0,  # Lunar internal friction angle
        sinkage_modulus_kc: float = 1400.0,
        sinkage_modulus_kphi: float = 820000.0,
        sinkage_exponent_n: float = 1.0,
    ) -> Dict[str, Any]:
        """Computes wheel sinkage z0, compaction resistance Rc, and drawbar pull:
        p = (kc/b + kphi) * z^n
        Rc = (b * (kc/b + kphi) * z^(n+1)) / (n + 1)
        """
        wheel_count = 4
        normal_load_per_wheel = (rover_mass_kg * cls.LUNAR_GRAVITY) / wheel_count
        b = wheel_width_m
        r = wheel_radius_m

        # Contact pressure modulus
        k_mod = (sinkage_modulus_kc / b) + sinkage_modulus_kphi
        # Sinkage depth estimation
        contact_length_est = 2.0 * math.sqrt(r * 0.03)  # initial estimate
        pressure = normal_load_per_wheel / (b * contact_length_est)
        sinkage_z = math.pow(pressure / max(1.0, k_mod), 1.0 / sinkage_exponent_n)
        sinkage_z = min(r * 0.5, max(0.005, sinkage_z))  # physical limits

        # Compaction motion resistance Rc (N) per wheel
        rc_per_wheel = (b * k_mod * math.pow(sinkage_z, sinkage_exponent_n + 1)) / (sinkage_exponent_n + 1)
        total_motion_resistance = rc_per_wheel * wheel_count

        # Maximum available gross traction H using Mohr-Coulomb soil shear
        phi_rad = math.radians(friction_angle_deg)
        contact_area = wheel_count * b * math.sqrt(2.0 * r * sinkage_z)
        max_traction = contact_area * cohesion_pa + (rover_mass_kg * cls.LUNAR_GRAVITY * math.cos(math.radians(slope_deg))) * math.tan(phi_rad)

        # Gravitational slope resistance Rg
        grav_resistance = rover_mass_kg * cls.LUNAR_GRAVITY * math.sin(math.radians(slope_deg))

        # Net Drawbar Pull DP
        net_drawbar_pull = max_traction - total_motion_resistance - grav_resistance
        traversable = net_drawbar_pull > 50.0 and slope_deg < (friction_angle_deg - 5.0)

        return {
            "rover_mass_kg": rover_mass_kg,
            "slope_deg": slope_deg,
            "wheel_sinkage_cm": round(sinkage_z * 100.0, 2),
            "motion_resistance_n": round(total_motion_resistance, 2),
            "max_available_traction_n": round(max_traction, 2),
            "slope_gravity_resistance_n": round(grav_resistance, 2),
            "net_drawbar_pull_n": round(net_drawbar_pull, 2),
            "traction_margin_ratio": round(max_traction / max(1.0, total_motion_resistance + grav_resistance), 3),
            "mobility_verdict": "GO_SAFE_TRAVERSAL" if traversable else "NO_GO_RISK_OF_IMMOBILIZATION",
        }
