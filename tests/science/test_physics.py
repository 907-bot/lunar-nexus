import pytest
from packages.science_engine.physics.illumination import calculate_illumination
from packages.data_pipeline.models import ObservationGeometry
from packages.science_engine.models import ScienceStatus

def test_illumination_calculation():
    geom = ObservationGeometry(solar_zenith_deg=45.0, solar_azimuth_deg=120.0)
    res = calculate_illumination(0.0, 0.0, geom)
    assert res["status"] == ScienceStatus.COMPLETE
    assert res["solar_elevation_deg"] == 45.0
    assert res["illumination_condition"] == "WELL_ILLUMINATED"

def test_illumination_missing_data():
    geom = ObservationGeometry()
    res = calculate_illumination(0.0, 0.0, geom)
    assert res["status"] == ScienceStatus.INSUFFICIENT_DATA
