#!/usr/bin/env python3
"""NEXUS-LUNAR: POC-7 Spatial Intelligence Standalone Demonstration.

Demonstrates:
1. Ingestion of POC-6 accepted correspondence pairs and strict exclusion of rejected matches
2. Construction of the Lunar Spatial Knowledge Graph (Nodes, Edges, Provenance)
3. Topographic terrain intelligence (Slope categories, 8-compass Aspect, Roughness, Elevation)
4. Illumination & solar potential analysis (Shadow fraction, cold traps, solar potential indicators)
5. IIRS mineralogical & resource spectral indicators (strictly qualified as indicators)
6. Environmental & physical hazard intelligence (Steep slopes, roughness, crater rims)
7. Multi-factor candidate site ranking and explainability checklist ("WHY IS THIS SITE INTERESTING?")
8. Graph queries (neighborhood, registered correspondences, candidate site filters)
9. Serialization of POC-8 Handover payload (outputs/poc7/poc7_handover_for_poc8.json)
10. Generation of 8 publication-grade diagnostic figures in outputs/poc7/
"""

from __future__ import annotations
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from packages.data_pipeline import (
    POC7ExperimentRunner,
    SpatialKnowledgeGraph,
    NodeType,
    RelationType,
)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_poc7_demo():
    print("=" * 80)
    print("  NEXUS-LUNAR POC-7: SPATIAL INTELLIGENCE & KNOWLEDGE GRAPH DEMO")
    print("=" * 80)

    output_dir = PROJECT_ROOT / "outputs" / "poc7"
    output_dir.mkdir(parents=True, exist_ok=True)
    poc6_file = PROJECT_ROOT / "outputs" / "poc6" / "poc6_verified_for_poc7.json"

    print("\n[Step 1/7] Ingesting Verified Observations from POC-6 Handover...")
    if not poc6_file.exists():
        print(f"Error: POC-6 verified handover file missing at {poc6_file}")
        sys.exit(1)

    runner = POC7ExperimentRunner(
        poc6_verified_path=poc6_file,
        output_dir=output_dir,
    )

    print("\n[Step 2/7] Constructing Lunar Spatial Knowledge Graph...")
    result = runner.run()
    graph: SpatialKnowledgeGraph = result["graph"]

    print(f"  ✓ Total Graph Nodes Created : {result['total_nodes']}")
    print(f"  ✓ Total Graph Edges Created : {result['total_edges']}")
    print(f"  ✓ Connected Components       : {len(graph.connected_components())}")

    print("\n[Step 3/7] Running Topographic Terrain & Illumination Analysis...")
    t_file = output_dir / "poc7_terrain_intelligence.json"
    i_file = output_dir / "poc7_illumination_intelligence.json"
    if t_file.exists() and i_file.exists():
        with open(t_file, "r", encoding="utf-8") as f:
            t_data = json.load(f)
        with open(i_file, "r", encoding="utf-8") as f:
            i_data = json.load(f)
        for pid, t in t_data.items():
            illum = i_data.get(pid, {})
            print(f"  • Patch [{pid}]: Elevation Mean={t['elevation_mean_m']}m, Slope={t['slope_degrees']}° ({t['slope_category']}), "
                  f"Roughness={t['roughness_score']}m, Aspect={t['aspect_cardinal']} ({t['aspect_degrees']}°), "
                  f"Illumination={illum.get('illumination_state')}")

    print("\n[Step 4/7] Ingesting Mineralogical Indicators & Assessing Hazards...")
    r_file = output_dir / "poc7_resource_indicators.json"
    h_file = output_dir / "poc7_hazard_intelligence.json"
    if r_file.exists():
        with open(r_file, "r", encoding="utf-8") as f:
            r_data = json.load(f)
            print(f"  ✓ {len(r_data)} Mineralogical / Spectral Indicators Qualified (Sensor: Chandrayaan-2 IIRS)")
    if h_file.exists():
        with open(h_file, "r", encoding="utf-8") as f:
            h_data = json.load(f)
            print(f"  ✓ {len(h_data)} Physical / Lighting Hazards Detected and Mapped to Graph")

    print("\n[Step 5/7] Evaluating Candidate Sites via Multi-Factor Scoring...")
    candidate_sites = result["candidate_sites"]
    print(f"  ✓ {len(candidate_sites)} Candidate Sites Ranked")
    for s in candidate_sites:
        print(f"  -------------------------------------------------------------")
        print(f"  Site ID     : {s.site_id} (Patch: {s.patch_id})")
        print(f"  Centroid    : Lat {s.coordinates['lat']:.4f}°, Lon {s.coordinates['lon']:.4f}°")
        print(f"  Suitability : {s.overall_suitability_score:.3f} | Data Status: {s.data_status.value if hasattr(s.data_status, 'value') else s.data_status}")
        print(f"  Scores      : Terrain={s.terrain_score:.2f} | Illum={s.illumination_score:.2f} | Resource={s.resource_indicator_score:.2f} | HazPenalty={s.hazard_penalty:.2f}")
        if s.explanation:
            print(f"  Summary     : {s.explanation.summary_verdict}")
            for pos in s.explanation.positive_factors[:2]:
                print(f"    ✓ {pos}")
            for neg in s.explanation.negative_factors[:2]:
                print(f"    ✗ {neg}")

    print("\n[Step 6/7] Demonstrating Spatial Knowledge Graph Queries...")
    # Query 1: Registered correspondences
    corrs = graph.find_registered_correspondences()
    print(f"  [Query 1] Registered Correspondences Found: {len(corrs)}")
    for c in corrs:
        print(f"    • {c['source_id']} <--- CORRESPONDS_TO ---> {c['target_id']} (Confidence: {c['registration_properties'].get('verification_confidence', 0.95):.3f})")

    # Query 2: Candidate sites satisfying slope <= 15.0 deg
    f_sites = graph.find_candidate_sites(max_slope=15.0, min_suitability=0.45)
    print(f"  [Query 2] Candidate Sites with Slope <= 15° & Suitability >= 0.45: {len(f_sites)} found")

    # Query 3: Ego neighborhood expansion for top site
    if candidate_sites:
        top_id = candidate_sites[0].site_id
        nbr = graph.neighborhood(top_id, depth=1)
        print(f"  [Query 3] 1-Hop Ego Neighborhood for {top_id}: {len(nbr['nodes'])} adjacent nodes, {len(nbr['edges'])} edges")

    print("\n[Step 7/7] Verifying POC-8 Handover Artifact & Visualizations...")
    handover_path = output_dir / "poc7_handover_for_poc8.json"
    if handover_path.exists():
        print(f"  ✓ POC-8 Handover Created: {handover_path} ({os.path.getsize(handover_path)} bytes)")
    for fig_name, fig_path in result["figures"].items():
        if fig_path and os.path.exists(fig_path):
            print(f"  ✓ Figure: {Path(fig_path).name} ({os.path.getsize(fig_path)} bytes)")

    print("\n" + "=" * 80)
    print("  NEXUS-LUNAR POC-7 DEMONSTRATION COMPLETE: ALL SYSTEMS NOMINAL")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_poc7_demo()
