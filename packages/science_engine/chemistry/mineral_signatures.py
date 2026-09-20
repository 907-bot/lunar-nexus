"""Mineral Signatures Library."""

from typing import Dict, Any

SIGNATURE_LIBRARY: Dict[str, Dict[str, Any]] = {
    "pyroxene": {
        "diagnostic_features": ["1000nm_absorption", "2000nm_absorption"],
        "wavelength_ranges": [(900, 1100), (1900, 2100)],
        "source": "Literature standard (e.g. Pieters et al.)",
        "assumptions": ["Requires hyperspectral data in near-IR"]
    },
    "olivine": {
        "diagnostic_features": ["broad_1000nm_absorption", "no_2000nm_absorption"],
        "wavelength_ranges": [(950, 1050)],
        "source": "Literature standard",
        "assumptions": ["Requires near-IR coverage"]
    },
    "plagioclase": {
        "diagnostic_features": ["1250nm_absorption"],
        "wavelength_ranges": [(1200, 1300)],
        "source": "Literature standard",
        "assumptions": ["Feature can be weak, requires high SNR"]
    },
    "ilmenite": {
        "diagnostic_features": ["uv_vis_slope"],
        "wavelength_ranges": [(300, 700)],
        "source": "Literature standard",
        "assumptions": ["Uses UV/VIS ratio as proxy for TiO2"]
    }
}
