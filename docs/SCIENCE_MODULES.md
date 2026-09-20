# Science Modules Documentation

## 1. Physics Methodology
The Physics module provides geometrically and physically informed analysis of lunar observations.

### Illumination & Shadow
- **Formulas:** 
  - `solar_elevation = 90 - solar_zenith_angle` (or 90 - incidence_angle)
  - `shadow_length = local_relief / tan(solar_elevation)`
- **Variables:** `solar_zenith_angle`, `incidence_angle`, `local_relief`
- **Units:** Angles in degrees, Relief and length in meters.
- **Assumptions:** Shadows are derived from simple geometric projection over a flat local horizon unless high-resolution DEM is fully integrated.
- **Limitations:** Only approximations. Returns `INSUFFICIENT_DATA` if geometry is missing.

### Thermal Model
- **Methodology:** Cautious thermal estimation based on latitude and solar elevation.
- **Variables:** `solar_elevation_deg`, `latitude`
- **Assumptions:** Lower solar elevation generally corresponds to cooler temperatures. This is a *model-derived estimate*, NOT a measured temperature.
- **Limitations:** Does not account for local thermal inertia, shadowing effects, or true radiometric temperatures.

## 2. Chemistry Methodology
The Chemistry module processes spectral data to match against known lunar mineral signatures.

- **Methodology:** Spectral matching using a configurable `SIGNATURE_LIBRARY`.
- **Variables:** Wavelength (nm), Reflectance.
- **Assumptions:** Requires actual hyperspectral or multiband data.
- **Limitations:** Does not definitively claim presence of minerals; only reports "candidate" or "consistent with". If spectral data is missing, returns `INSUFFICIENT_DATA`.

## 3. Habitability / Biology Methodology
The Biology module is strictly framed around **Environmental Habitability & Biological Experiment Support**. It does NOT perform life detection.

- **Methodology:** Evaluates environmental constraints (water/ice, thermal, radiation) against experimental requirements.
- **Variables:** `water_ice_evidence`, `radiation_availability`, `terrain_roughness`.
- **Assumptions:** "Confirmed" data must come from authoritative sources.
- **Limitations:** If radiation data is unavailable, it reports `INSUFFICIENT_DATA`. It strictly assesses suitability for future experiments, not existing life.

## 4. Confidence & Provenance
- **Confidence:** Components (physics, chemistry, biology) have independent confidence scores (0.0 to 1.0) instead of an arbitrary fused weight.
- **Provenance:** Every science result includes a provenance record detailing the `source`, `processing_method`, and whether it is `derived` or `observed`.

## 5. API Endpoints
- `GET /science/region/{region_id}/physics`
- `GET /science/region/{region_id}/chemistry`
- `GET /science/region/{region_id}/biology`
- `GET /science/region/{region_id}/fusion`

Each endpoint requires a region ID and returns structured JSON with the calculated scientific intelligence and full provenance.
