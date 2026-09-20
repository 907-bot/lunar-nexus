"""Synthetic Demo."""

from packages.science_engine.fusion import fuse_evidence
from packages.science_engine.physics.illumination import calculate_illumination
from packages.science_engine.chemistry.spectral_analysis import analyze_spectra
from packages.science_engine.biology.habitability import analyze_habitability
from packages.science_engine.models import PhysicsResult, ChemistryResult, BiologyResult, ScienceStatus, EvidenceStatus
from packages.data_pipeline.models import ObservationGeometry
from packages.science_engine.provenance import create_provenance

def run_demo():
    print("NEXUS-LUNAR SCIENCE INTELLIGENCE")
    print("=================================")
    print("SYNTHETIC DEMONSTRATION")
    
    geom = ObservationGeometry(solar_zenith_deg=80.0, solar_azimuth_deg=45.0)
    illum = calculate_illumination(0.0, 0.0, geom)
    
    physics = PhysicsResult(
        illumination_condition=illum["illumination_condition"],
        status=ScienceStatus.COMPLETE
    )
    
    chem_data = analyze_spectra(True, [1000], [0.5])
    chemistry = ChemistryResult(
        spectral_coverage=True,
        candidate_materials=chem_data["candidate_materials"],
        status=ScienceStatus.COMPLETE
    )
    
    bio_data = analyze_habitability(False, True, False)
    biology = BiologyResult(
        water_ice_evidence=bio_data["water_ice_evidence"],
        radiation_availability=bio_data["radiation_availability"],
        status=ScienceStatus.COMPLETE
    )
    
    prov = create_provenance(source="Synthetic demo script", processing_method="Mock", derived=True)
    fusion = fuse_evidence("DEMO_REGION_001", physics, chemistry, biology, [prov])
    
    print(f"\nPhysics:")
    print(f"  Illumination: {fusion.physics.illumination_condition}")
    
    print(f"\nChemistry:")
    print(f"  Spectral coverage: {fusion.chemistry.spectral_coverage}")
    print(f"  Candidate materials: {len(fusion.chemistry.candidate_materials)}")
    
    print(f"\nHabitability:")
    print(f"  Water/Ice evidence: {fusion.habitability.water_ice_evidence}")
    
    print(f"\nConfidence:")
    print(f"  Physics: {fusion.confidence.physics}")
    print(f"  Chemistry: {fusion.confidence.chemistry}")
    print(f"  Habitability: {fusion.confidence.biology}")
    
if __name__ == "__main__":
    run_demo()
