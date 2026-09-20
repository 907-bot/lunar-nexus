import pytest
from packages.science_engine.chemistry.spectral_analysis import analyze_spectra
from packages.science_engine.models import ScienceStatus

def test_chemistry_missing_data():
    res = analyze_spectra(False)
    assert res["status"] == ScienceStatus.INSUFFICIENT_DATA
    assert res["spectral_coverage"] == False
