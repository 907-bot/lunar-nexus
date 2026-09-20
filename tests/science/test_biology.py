import pytest
from packages.science_engine.biology.habitability import analyze_habitability
from packages.science_engine.models import ScienceStatus, EvidenceStatus

def test_biology_analysis():
    res = analyze_habitability(True, True, False)
    assert res["status"] == ScienceStatus.COMPLETE
    assert res["water_ice_evidence"] == EvidenceStatus.CONFIRMED_BY_SOURCE
    assert res["radiation_availability"] == EvidenceStatus.INSUFFICIENT_DATA
