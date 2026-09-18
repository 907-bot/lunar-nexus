# NEXUS-LUNAR `nexus-unified` Branch — Complete Recursive Audit

> **Branch confirmed:** `nexus-unified`
> **HEAD commit:** `ebc2ed8e29cc166042596894aacf919d67d88e06`
> **Working tree:** Clean — nothing to commit
> **Audit date:** 2026-09-10

---

## 5. GIT CHECK

| Field | Value |
|---|---|
| **Current branch** | `nexus-unified` |
| **HEAD hash** | `ebc2ed8e29cc166042596894aacf919d67d88e06` |
| **Tracking** | `origin/nexus-unified` (up to date) |
| **Working tree status** | Clean — nothing to commit |
| **Modified files** | None |
| **Deleted files** | None |
| **Untracked files** | None |

**Recent commits (last 5):**

| Hash | Message |
|---|---|
| `ebc2ed8` | feat(test): add Playwright end-to-end browser automation test suite and runner |
| `6e6b7aa` | fix(poc5): crop zero-padded margins and correctly fit candidate images into retrieval gallery frames |
| `4a21e6a` | fix(frontend): restore missing closing brace in openSiteModal and resolve favicon 404 |
| `8905947` | feat: implement Physics-Informed Neural Network (PINN) with PyTorch autograd PDE residual solving |
| `e9409bb` | feat: integrate first-principles scientific engine (physics, chemistry, biology, frequency) into nexus platform |

---

## 1. COMPLETE FILE TREE

```
NEXUS-LUNAR/  (root)
├── .gitignore
├── .vscode/
│   └── settings.json
├── LICENSE
├── NEXUS_LUNAR_SIH_Complete_Blueprint.md          (44,484 bytes / 1548 lines)
├── NEXUS-LUNAR_SIH_Complete_Project_Blueprint.md  (41,251 bytes / 1520 lines)
├── POC2_README.md
├── POC4_README.md
├── POC4_REPORT.md
├── POC5_README.md
├── POC5_REPORT.md
├── POC6_README.md
├── POC6_REPORT.md
├── README.md
├── requirements.txt
│
├── data/
│   ├── catalog.json
│   └── raw/
│       ├── lro_nac/
│       │   ├── M1123456789_SHACKLETON_REF/
│       │   │   └── M1123456789_SHACKLETON_REF.png
│       │   ├── M1198765432_APOLLO17_REF/
│       │   │   └── M1198765432_APOLLO17_REF.png
│       │   ├── M1345982701LR_BOGUSLAWSKY_REF/
│       │   │   └── M1345982701LR_BOGUSLAWSKY_REF.png
│       │   ├── nac.m1417928961le/
│       │   │   ├── nac.m1417928961le_browse.tif
│       │   │   └── nac.m1417928961le_preview.png
│       │   ├── nac.m1417928961re/
│       │   │   ├── nac.m1417928961re_browse.tif
│       │   │   └── nac.m1417928961re_preview.png
│       │   ├── nac.m1417929126le/
│       │   │   ├── nac.m1417929126le_browse.tif
│       │   │   └── nac.m1417929126le_preview.png
│       │   ├── nac.m1417929126re/
│       │   │   ├── nac.m1417929126re_browse.tif
│       │   │   └── nac.m1417929126re_preview.png
│       │   ├── nac.m1417929185le/
│       │   │   ├── nac.m1417929185le_browse.tif
│       │   │   └── nac.m1417929185le_preview.png
│       │   ├── nac.m1419447916le/
│       │   │   ├── nac.m1419447916le_browse.tif
│       │   │   └── nac.m1419447916le_preview.png
│       │   └── nac.m1419447916re/
│       │       └── nac.m1419447916re_preview.png  (ONLY preview — no .tif committed)
│       ├── ohrc/
│       │   ├── ch2_ohr_ncp_20230712t081545_apollo17_site/
│       │   │   └── ch2_ohr_ncp_20230712t081545_apollo17_site.png
│       │   ├── ch2_ohr_ncp_20230823t123015_shackleton_rim/
│       │   │   └── ch2_ohr_ncp_20230823t123015_shackleton_rim.png
│       │   ├── ch2_ohr_ncp_20230915t041230_boguslawsky_d18/
│       │   │   ├── ch2_ohr_ncp_20230915t041230_boguslawsky_d18.png
│       │   │   ├── ch2_ohr_ncp_20230915t041230_boguslawsky_d18.xml
│       │   │   └── ch2_ohr_ncp_20230915t041230_boguslawsky_d18_preview.png
│       │   ├── ch2_ohr_ncp_20230916t062010_boguslawsky_pass2/
│       │   │   └── ch2_ohr_ncp_20230916t062010_boguslawsky_pass2.png
│       │   └── ch2_ohr_ncp_20231005t141020_manzinus_crater/
│       │       └── ch2_ohr_ncp_20231005t141020_manzinus_crater.png
│       └── tmc2/
│           ├── ch2_tmc_ncn_20230712t081200_apollo17_context/
│           │   └── ch2_tmc_ncn_20230712t081200_apollo17_context.png
│           ├── ch2_tmc_ncn_20230823t122800_shackleton_triplet/
│           │   └── ch2_tmc_ncn_20230823t122800_shackleton_triplet.png
│           └── ch2_tmc_ncn_20230915t041000_boguslawsky_triplet/
│               └── ch2_tmc_ncn_20230915t041000_boguslawsky_triplet.png
│
├── packages/
│   ├── data_pipeline/           (34 tracked files)
│   │   ├── __init__.py
│   │   ├── catalog.py
│   │   ├── footprint_engine.py
│   │   ├── illumination_robustness.py
│   │   ├── issdc_client.py
│   │   ├── metadata_parser.py
│   │   ├── models.py
│   │   ├── overlap_engine.py
│   │   ├── patch_extractor.py
│   │   ├── pds_ode_client.py
│   │   ├── poc4_experiment.py
│   │   ├── poc4_matching.py
│   │   ├── poc4_metrics.py
│   │   ├── poc4_visualization.py
│   │   ├── poc5_experiment.py
│   │   ├── poc5_metrics.py
│   │   ├── poc5_models.py
│   │   ├── poc5_retrieval.py
│   │   ├── poc5_visualization.py
│   │   ├── poc6_experiment.py
│   │   ├── poc6_verification.py
│   │   ├── poc6_visualization.py
│   │   ├── poc7_experiment.py
│   │   ├── poc7_hazards.py
│   │   ├── poc7_illumination.py
│   │   ├── poc7_knowledge_graph.py
│   │   ├── poc7_models.py
│   │   ├── poc7_resources.py
│   │   ├── poc7_site_intelligence.py
│   │   ├── poc7_terrain.py
│   │   ├── poc7_visualization.py
│   │   ├── sample_benchmark.py
│   │   ├── scale_robustness.py
│   │   └── visualization.py
│   ├── first_principles/        (6 tracked files)
│   │   ├── __init__.py
│   │   ├── biology.py
│   │   ├── chemistry.py
│   │   ├── frequency.py
│   │   ├── physics.py
│   │   └── pinn_model.py
│   ├── nexus_core/              (10 tracked files)
│   │   ├── __init__.py
│   │   ├── blender_mcp_client.py
│   │   ├── poc1_knowledge_graph.py
│   │   ├── poc2_terrain_intelligence.py
│   │   ├── poc3_illumination_intelligence.py
│   │   ├── poc4_resource_intelligence.py
│   │   ├── poc5_explainable_ai.py
│   │   ├── poc6_gnn_reasoner.py
│   │   ├── poc7_snn_temporal.py
│   │   └── poc8_habitat_planner.py
│   └── registration/            (6 tracked files)
│       ├── __init__.py
│       ├── algorithms.py
│       ├── geometric.py
│       ├── matchers.py
│       ├── metrics.py
│       └── visualizer.py
│
├── scripts/                     (17 tracked files)
│   ├── demo_nexus_poc8.py
│   ├── demo_poc2.py
│   ├── demo_poc4.py
│   ├── demo_poc5.py
│   ├── demo_poc6.py
│   ├── demo_poc7.py
│   ├── download_lunar_data.py
│   ├── extract_overlap_patches.py
│   ├── ingest_issdc.py
│   ├── launch_dashboard.py
│   ├── query_catalog.py
│   ├── render_blender_scene.py
│   ├── run_playwright_e2e.py
│   ├── run_poc4_experiment.py
│   ├── run_poc5_experiment.py
│   ├── run_poc6_experiment.py
│   └── run_poc7_experiment.py
│
├── services/
│   ├── lunar_data/
│   │   └── server.py
│   └── registration/
│       └── server.py
│
├── tests/                       (14 tracked files)
│   ├── test_classical_registration.py
│   ├── test_first_principles.py
│   ├── test_nexus_poc6_gnn.py
│   ├── test_nexus_poc7_snn.py
│   ├── test_nexus_poc8_habitat.py
│   ├── test_overlap_engine.py
│   ├── test_patch_extractor.py
│   ├── test_playwright_e2e.py
│   ├── test_poc2_advanced_validation.py
│   ├── test_poc4_illumination_scale.py
│   ├── test_poc5_multimodal.py
│   ├── test_poc6_ui_playwright.py
│   ├── test_poc6_verification.py
│   └── test_poc7_spatial_intelligence.py
│
└── web/                         (4 tracked files)
    ├── app.js
    ├── index.html
    ├── style.css
    └── three.min.js

--- UNTRACKED (gitignored / generated, present on disk) ---
data/demo_poc2/           generated POC2 demo TIFFs + PNGs
data/processed/patches/   extracted patches (gitignored)
outputs/poc2_cli_demo/    5 PNG/JSON output files
outputs/poc2_demo/        5 PNG/JSON output files
outputs/poc2_extract_demo/ 5 PNG/JSON output files
outputs/poc4/             9 PNG/JSON/CSV result files
outputs/poc5/             8 PNG/JSON/CSV result files
outputs/poc6/             8 PNG/JSON/CSV result files
outputs/poc7/             15 PNG/JSON result files
scripts/__pycache__/      compiled .pyc bytecode
tests/__pycache__/        compiled .pyc bytecode
packages/data_pipeline/__pycache__/ compiled bytecode
```

---

## 2. FILE INVENTORY

### Source Code

| File Path | Name | Type | Purpose |
|---|---|---|---|
| `packages/data_pipeline/__init__.py` | `__init__.py` | Python | Package entry; re-exports ALL public API symbols for POC4-POC7 |
| `packages/data_pipeline/models.py` | `models.py` | Python | Core Pydantic models: LunarObservation, BoundingBox, SensorType, MissionType |
| `packages/data_pipeline/catalog.py` | `catalog.py` | Python | LunarDataCatalog — JSON-backed observation registry |
| `packages/data_pipeline/footprint_engine.py` | `footprint_engine.py` | Python | Geographic footprint polygon computation (FootprintEngine) |
| `packages/data_pipeline/overlap_engine.py` | `overlap_engine.py` | Python | Overlap detection between sensor footprints (OverlapEngine) |
| `packages/data_pipeline/patch_extractor.py` | `patch_extractor.py` | Python | Aligned patch extraction from overlapping image pairs |
| `packages/data_pipeline/metadata_parser.py` | `metadata_parser.py` | Python | PDS/ISSDC XML + JSON metadata parsing |
| `packages/data_pipeline/pds_ode_client.py` | `pds_ode_client.py` | Python | HTTP client for NASA PDS ODE REST API |
| `packages/data_pipeline/issdc_client.py` | `issdc_client.py` | Python | ISRO ISSDC data catalogue client |
| `packages/data_pipeline/illumination_robustness.py` | `illumination_robustness.py` | Python | Image preprocessing: normalisation, gradient, edge, shadow mask |
| `packages/data_pipeline/scale_robustness.py` | `scale_robustness.py` | Python | Multi-scale image pyramid generation, GSD resampling |
| `packages/data_pipeline/sample_benchmark.py` | `sample_benchmark.py` | Python | Synthetic benchmark observation dataset generator |
| `packages/data_pipeline/visualization.py` | `visualization.py` | Python | Geospatial footprint and patch comparison PNG generator |
| `packages/data_pipeline/poc4_matching.py` | `poc4_matching.py` | Python | POC4: Pure-NumPy keypoint detection, descriptors, RANSAC matching |
| `packages/data_pipeline/poc4_metrics.py` | `poc4_metrics.py` | Python | POC4: Registration metrics (Recall@K, inlier ratio, RMSE) |
| `packages/data_pipeline/poc4_experiment.py` | `poc4_experiment.py` | Python | POC4: Full experiment runner with failure tracking |
| `packages/data_pipeline/poc4_visualization.py` | `poc4_visualization.py` | Python | POC4: Result figure generators (comparison, heatmap, ablation) |
| `packages/data_pipeline/poc5_models.py` | `poc5_models.py` | Python | POC5: Multimodal patch embedding models and encoders |
| `packages/data_pipeline/poc5_retrieval.py` | `poc5_retrieval.py` | Python | POC5: Cross-modal retrieval engine, candidate matching |
| `packages/data_pipeline/poc5_metrics.py` | `poc5_metrics.py` | Python | POC5: Retrieval metrics (mAP, Recall@K, failure tracking) |
| `packages/data_pipeline/poc5_experiment.py` | `poc5_experiment.py` | Python | POC5: Multimodal AI correspondence experiment runner |
| `packages/data_pipeline/poc5_visualization.py` | `poc5_visualization.py` | Python | POC5: Embedding space, retrieval gallery, score distribution |
| `packages/data_pipeline/poc6_verification.py` | `poc6_verification.py` | Python | POC6: Geometric verification + XAI confidence scoring |
| `packages/data_pipeline/poc6_experiment.py` | `poc6_experiment.py` | Python | POC6: Full geometric verification experiment runner |
| `packages/data_pipeline/poc6_visualization.py` | `poc6_visualization.py` | Python | POC6: Verification gallery, inlier scatter, XAI breakdown figures |
| `packages/data_pipeline/poc7_models.py` | `poc7_models.py` | Python | POC7: Data models — CandidateSite, GraphNode, POC7Handover, enums |
| `packages/data_pipeline/poc7_knowledge_graph.py` | `poc7_knowledge_graph.py` | Python | POC7: SpatialKnowledgeGraph — in-memory KG with nodes/edges |
| `packages/data_pipeline/poc7_terrain.py` | `poc7_terrain.py` | Python | POC7: TerrainIntelligenceEngine — slope, crater proximity, roughness |
| `packages/data_pipeline/poc7_illumination.py` | `poc7_illumination.py` | Python | POC7: IlluminationIntelligenceEngine — shadow mapping, solar angle |
| `packages/data_pipeline/poc7_resources.py` | `poc7_resources.py` | Python | POC7: ResourceIntelligenceEngine — ice, regolith, mineral proxies |
| `packages/data_pipeline/poc7_hazards.py` | `poc7_hazards.py` | Python | POC7: HazardIntelligenceEngine — boulder, slope, shadow hazard scoring |
| `packages/data_pipeline/poc7_site_intelligence.py` | `poc7_site_intelligence.py` | Python | POC7: CandidateSiteScoringEngine — composite site suitability scoring |
| `packages/data_pipeline/poc7_experiment.py` | `poc7_experiment.py` | Python | POC7: Spatial Intelligence experiment runner |
| `packages/data_pipeline/poc7_visualization.py` | `poc7_visualization.py` | Python | POC7: Terrain, hazard, illumination, resource, KG visualisation |
| `packages/first_principles/physics.py` | `physics.py` | Python | PhysicsEngine — lunar gravity, orbital mechanics, thermal physics |
| `packages/first_principles/chemistry.py` | `chemistry.py` | Python | ChemistryEngine — regolith chemistry, volatiles |
| `packages/first_principles/biology.py` | `biology.py` | Python | BiologyEngine — life support gas/water/caloric requirements |
| `packages/first_principles/frequency.py` | `frequency.py` | Python | FrequencyEngine — EM/RF propagation, antenna, comms |
| `packages/first_principles/pinn_model.py` | `pinn_model.py` | Python | LunarThermalPINN + LunarMultiphysicsPINN (PyTorch autograd PDE solver) |
| `packages/first_principles/__init__.py` | `__init__.py` | Python | Package entry for first-principles engines |
| `packages/nexus_core/__init__.py` | `__init__.py` | Python | nexus_core package header (v1.0.0, documents POC 1-8) |
| `packages/nexus_core/poc1_knowledge_graph.py` | `poc1_knowledge_graph.py` | Python | POC1: Lunar spatial knowledge graph (nexus_core variant) |
| `packages/nexus_core/poc2_terrain_intelligence.py` | `poc2_terrain_intelligence.py` | Python | POC2: Terrain intelligence engine (nexus_core) |
| `packages/nexus_core/poc3_illumination_intelligence.py` | `poc3_illumination_intelligence.py` | Python | POC3: Illumination analysis (nexus_core) |
| `packages/nexus_core/poc4_resource_intelligence.py` | `poc4_resource_intelligence.py` | Python | POC4: IIRS spectral resource intelligence (nexus_core) |
| `packages/nexus_core/poc5_explainable_ai.py` | `poc5_explainable_ai.py` | Python | POC5: Explainable AI site selection (nexus_core) |
| `packages/nexus_core/poc6_gnn_reasoner.py` | `poc6_gnn_reasoner.py` | Python | POC6: Graph Neural Network spatial reasoner (nexus_core) |
| `packages/nexus_core/poc7_snn_temporal.py` | `poc7_snn_temporal.py` | Python | POC7: Spiking Neural Network temporal reasoner (nexus_core) |
| `packages/nexus_core/poc8_habitat_planner.py` | `poc8_habitat_planner.py` | Python | POC8: Habitat constraint planner and 3D digital twin |
| `packages/nexus_core/blender_mcp_client.py` | `blender_mcp_client.py` | Python | Blender MCP protocol client for 3D scene rendering |
| `packages/registration/__init__.py` | `__init__.py` | Python | Package entry: classical registration API |
| `packages/registration/algorithms.py` | `algorithms.py` | Python | Feature extraction algorithms (SIFT, ORB, AKAZE, RootSIFT) |
| `packages/registration/matchers.py` | `matchers.py` | Python | Descriptor matching (Lowe's ratio test, BF matcher) |
| `packages/registration/geometric.py` | `geometric.py` | Python | Geometric transform estimation (RANSAC, homography, affine) |
| `packages/registration/metrics.py` | `metrics.py` | Python | Registration quality metrics |
| `packages/registration/visualizer.py` | `visualizer.py` | Python | Match visualisation, checkerboard overlay, warp |

### Pages / Frontend

| File Path | Name | Type | Purpose |
|---|---|---|---|
| `web/index.html` | `index.html` | HTML | Main NEXUS-LUNAR dashboard (Mission Control UI with starfield canvas, Leaflet GIS) |
| `web/style.css` | `style.css` | CSS | Full theme, layout, glassmorphism, HUD, Leaflet panel styling |
| `web/app.js` | `app.js` | JavaScript | Dashboard logic: starfield, Leaflet map, modal system, telemetry |
| `web/three.min.js` | `three.min.js` | JavaScript | Bundled Three.js library for 3D rendering |

### Services / API

| File Path | Name | Type | Purpose |
|---|---|---|---|
| `services/lunar_data/server.py` | `server.py` | Python | HTTP microservice: catalog queries, spatial search, illumination telemetry |
| `services/registration/server.py` | `server.py` | Python | HTTP microservice: classical image registration endpoints |
| `scripts/launch_dashboard.py` | `launch_dashboard.py` | Python | Dashboard HTTP server launcher (serves web/ directory) |

### Scripts (CLI Runners and Demos)

| File Path | Name | Type | Purpose |
|---|---|---|---|
| `scripts/download_lunar_data.py` | `download_lunar_data.py` | Python | Downloads LRO NAC/OHRC data via PDS ODE client |
| `scripts/ingest_issdc.py` | `ingest_issdc.py` | Python | Ingests Chandrayaan-2 observations from ISSDC into catalog |
| `scripts/query_catalog.py` | `query_catalog.py` | Python | CLI tool to query the data catalog |
| `scripts/extract_overlap_patches.py` | `extract_overlap_patches.py` | Python | Extracts overlapping patch pairs from ingested data |
| `scripts/run_poc4_experiment.py` | `run_poc4_experiment.py` | Python | POC4 experiment CLI runner |
| `scripts/run_poc5_experiment.py` | `run_poc5_experiment.py` | Python | POC5 experiment CLI runner |
| `scripts/run_poc6_experiment.py` | `run_poc6_experiment.py` | Python | POC6 experiment CLI runner |
| `scripts/run_poc7_experiment.py` | `run_poc7_experiment.py` | Python | POC7 experiment CLI runner |
| `scripts/run_playwright_e2e.py` | `run_playwright_e2e.py` | Python | Playwright end-to-end test runner |
| `scripts/demo_poc2.py` | `demo_poc2.py` | Python | POC2 demo runner |
| `scripts/demo_poc4.py` | `demo_poc4.py` | Python | POC4 demo runner |
| `scripts/demo_poc5.py` | `demo_poc5.py` | Python | POC5 demo runner |
| `scripts/demo_poc6.py` | `demo_poc6.py` | Python | POC6 demo runner |
| `scripts/demo_poc7.py` | `demo_poc7.py` | Python | POC7 demo runner |
| `scripts/demo_nexus_poc8.py` | `demo_nexus_poc8.py` | Python | POC8 demo runner |
| `scripts/render_blender_scene.py` | `render_blender_scene.py` | Python | Blender 3D scene rendering script (no callers found — possibly orphaned) |

### Tests

| File Path | Name | Type | Purpose |
|---|---|---|---|
| `tests/test_classical_registration.py` | `test_classical_registration.py` | Python/pytest | Tests for classical registration package |
| `tests/test_first_principles.py` | `test_first_principles.py` | Python/pytest | Tests for first-principles engines |
| `tests/test_nexus_poc6_gnn.py` | `test_nexus_poc6_gnn.py` | Python/pytest | Tests for nexus_core GNN reasoner |
| `tests/test_nexus_poc7_snn.py` | `test_nexus_poc7_snn.py` | Python/pytest | Tests for nexus_core SNN reasoner |
| `tests/test_nexus_poc8_habitat.py` | `test_nexus_poc8_habitat.py` | Python/pytest | Tests for nexus_core habitat planner |
| `tests/test_overlap_engine.py` | `test_overlap_engine.py` | Python/pytest | Tests for OverlapEngine |
| `tests/test_patch_extractor.py` | `test_patch_extractor.py` | Python/pytest | Tests for PatchExtractor |
| `tests/test_playwright_e2e.py` | `test_playwright_e2e.py` | Python/pytest | End-to-end browser tests via Playwright |
| `tests/test_poc2_advanced_validation.py` | `test_poc2_advanced_validation.py` | Python/pytest | POC2 advanced validation tests |
| `tests/test_poc4_illumination_scale.py` | `test_poc4_illumination_scale.py` | Python/pytest | POC4 illumination and scale robustness tests |
| `tests/test_poc5_multimodal.py` | `test_poc5_multimodal.py` | Python/pytest | POC5 multimodal AI tests |
| `tests/test_poc6_ui_playwright.py` | `test_poc6_ui_playwright.py` | Python/pytest | POC6 UI Playwright tests |
| `tests/test_poc6_verification.py` | `test_poc6_verification.py` | Python/pytest | POC6 geometric verification unit tests |
| `tests/test_poc7_spatial_intelligence.py` | `test_poc7_spatial_intelligence.py` | Python/pytest | POC7 spatial intelligence unit tests |

### Database / Schema

| File Path | Name | Type | Purpose |
|---|---|---|---|
| `data/catalog.json` | `catalog.json` | JSON | Master observation catalog (LRO NAC + OHRC metadata) |

### Assets (Images + Data)

| File Path | Name | Type | Purpose |
|---|---|---|---|
| `data/raw/lro_nac/*/*.tif` (6 files) | `*_browse.tif` | GeoTIFF | LRO NAC browse-resolution raster images |
| `data/raw/lro_nac/*/*.png` (10 files) | `*_preview.png` | PNG | LRO NAC preview images + 3 named reference PNGs |
| `data/raw/ohrc/**/*.png` (5 files) | OHRC images | PNG | Chandrayaan-2 OHRC lunar images |
| `data/raw/ohrc/**/*.xml` (1 file) | OHRC metadata | XML | Chandrayaan-2 OHRC PDS metadata |
| `data/raw/tmc2/**/*.png` (3 files) | TMC2 images | PNG | Chandrayaan-2 TMC2 context images |

### Documentation

| File Path | Name | Type | Purpose |
|---|---|---|---|
| `README.md` | `README.md` | Markdown | Main project README |
| `POC2_README.md` | `POC2_README.md` | Markdown | POC2 documentation |
| `POC4_README.md` | `POC4_README.md` | Markdown | POC4 documentation |
| `POC4_REPORT.md` | `POC4_REPORT.md` | Markdown | POC4 experiment report |
| `POC5_README.md` | `POC5_README.md` | Markdown | POC5 documentation |
| `POC5_REPORT.md` | `POC5_REPORT.md` | Markdown | POC5 experiment report |
| `POC6_README.md` | `POC6_README.md` | Markdown | POC6 documentation |
| `POC6_REPORT.md` | `POC6_REPORT.md` | Markdown | POC6 experiment report |
| `NEXUS_LUNAR_SIH_Complete_Blueprint.md` | `NEXUS_LUNAR_SIH_Complete_Blueprint.md` | Markdown | SIH blueprint v1 (44,484 bytes / 1548 lines) |
| `NEXUS-LUNAR_SIH_Complete_Project_Blueprint.md` | `NEXUS-LUNAR_SIH_Complete_Project_Blueprint.md` | Markdown | SIH blueprint v2 (41,251 bytes / 1520 lines) |

### Configuration

| File Path | Name | Type | Purpose |
|---|---|---|---|
| `.gitignore` | `.gitignore` | gitignore | Ignores __pycache__, *.tif, venv, outputs/, data/processed/ |
| `.vscode/settings.json` | `settings.json` | JSON | Python 3.14 interpreter path, extra analysis paths |
| `requirements.txt` | `requirements.txt` | Text | Python dependencies (requests, pydantic, tqdm, xmltodict, shapely, numpy, Pillow) |
| `LICENSE` | `LICENSE` | (no ext) | Software license file |

---

## 3. PROJECT STRUCTURE ANALYSIS

### What the Project Contains

**NEXUS-LUNAR** is an AI-powered lunar image registration, spatial intelligence, and habitat planning platform for the **Smart India Hackathon (SIH)**. It co-registers **Chandrayaan-2 (OHRC/TMC2)** and **NASA LRO NAC** lunar imagery to identify safe landing/habitat sites near the lunar south pole.

### Architecture

```
Frontend (web/)
  HTML + CSS + JS + Three.js (3D) + Leaflet (GIS)
  Served by: scripts/launch_dashboard.py

HTTP Microservices (services/)
  services/lunar_data/server.py    — catalog API, spatial queries
  services/registration/server.py  — classical image registration API

Python Packages (packages/)
  data_pipeline/    — POC4-POC7 experiment pipeline (34 files)
  registration/     — Classical feature matching engine (6 files)
  first_principles/ — Physics/Chemistry/Biology/EM + PINN (6 files)
  nexus_core/       — Advanced AI POC1-POC8 modules (10 files)

Data (data/)
  catalog.json + raw sensor images (LRO NAC, OHRC, TMC2)

Tests (tests/) — 14 pytest test files
Scripts (scripts/) — 17 CLI runners and demo scripts
```

### POC Progression

| POC | Package | Description |
|---|---|---|
| POC1 | nexus_core | Lunar Spatial Knowledge Graph |
| POC2 | nexus_core | Terrain Intelligence Engine |
| POC3 | nexus_core | Illumination Intelligence |
| POC4 | data_pipeline | Illumination and Scale Robustness (classical matching) |
| POC5 | data_pipeline | Multimodal AI Cross-Sensor Correspondence |
| POC6 | data_pipeline | Geometric Verification + Explainable AI |
| POC7 | data_pipeline | Spatial Intelligence Knowledge Graph |
| POC8 | nexus_core | Habitat Constraint Planner + 3D Digital Twin |

### Entry Points

- **Web dashboard:** `scripts/launch_dashboard.py` serves `web/` on HTTP
- **Data ingestion:** `scripts/download_lunar_data.py` then `scripts/ingest_issdc.py`
- **Experiments:** `scripts/run_poc4_experiment.py` through `run_poc7_experiment.py`
- **Microservices:** `services/lunar_data/server.py`, `services/registration/server.py`
- **Tests:** `pytest tests/`

### Major Dependencies

**In requirements.txt:** requests, pydantic>=2.0, tqdm, xmltodict, shapely>=2.0, numpy>=1.22, Pillow>=9.0

**Implicit (NOT in requirements.txt):**
- `cv2` (OpenCV) — services/registration/server.py
- `torch` (PyTorch) — packages/first_principles/pinn_model.py
- `playwright` — tests/test_playwright_e2e.py, test_poc6_ui_playwright.py
- `matplotlib` — all POC4-POC7 visualization modules
- `scipy` — registration and POC4 modules
- `networkx` — knowledge graph modules

---

## 4. PROBLEMS / CLEANUP

### Duplicate Files

| Issue | Files Involved | Details |
|---|---|---|
| **Two near-identical Blueprint docs** | `NEXUS_LUNAR_SIH_Complete_Blueprint.md` (44,484 B) vs `NEXUS-LUNAR_SIH_Complete_Project_Blueprint.md` (41,251 B) | Same subject, different filenames (underscore vs hyphen), different sizes. Likely two versions — one likely supersedes the other. |
| **POC numbering collision across packages** | `nexus_core/poc4_resource_intelligence.py` vs `data_pipeline/poc4_*` | Both labelled "POC4" but implement completely different features. Same naming conflict applies to POC5, POC6, POC7. Confusing and error-prone. |
| **TerrainIntelligenceEngine implemented twice** | `nexus_core/poc2_terrain_intelligence.py` AND `data_pipeline/poc7_terrain.py` | Both implement terrain intelligence. nexus_core version is standalone; data_pipeline version is the live pipeline one. |

### Broken Path Reference

| Issue | File | Detail |
|---|---|---|
| **WEB_DIR points to non-existent apps/web/** | `services/lunar_data/server.py` (line 21) | `WEB_DIR = WORKSPACE_ROOT / "apps" / "web"` — the `apps/` directory does NOT exist. The web frontend lives at `web/` (root). This means the lunar_data microservice will 404 on every frontend page request. `scripts/launch_dashboard.py` correctly uses `WEB_DIR = PROJECT_ROOT / "web"`. |

### Missing / Incomplete Files

| Missing File | Why It's Needed |
|---|---|
| `apps/web/` directory | Hardcoded in `services/lunar_data/server.py`. Does not exist — frontend serving broken. |
| Complete `requirements.txt` | Missing: opencv-python, torch, playwright, matplotlib, scipy, networkx. Fresh install will fail at runtime. |
| `pyproject.toml` or `setup.py` | No installable package configuration. Path hackery required via .vscode/settings.json. |
| `tests/conftest.py` | No shared pytest path/fixture setup. Tests may fail to import packages/ without manual sys.path. |
| `scripts/run_poc3_experiment.py` | POC3 has a module (nexus_core) but no script runner — inconsistent with POC4-POC7. |
| `scripts/run_poc8_experiment.py` | POC8 has a module and demo but no script runner. |

### Suspicious / Unexpected Files

| Issue | File | Detail |
|---|---|---|
| **6 .tif files committed despite gitignore** | `data/raw/lro_nac/*/nac.*_browse.tif` | .gitignore explicitly excludes `*.tif`. These 6 browse TIFs were committed before the rule was added. `nac.m1419447916re_browse.tif` is on disk but untracked (matches gitignore). |
| **render_blender_scene.py has no callers** | `scripts/render_blender_scene.py` | No imports or references found anywhere in the codebase. Possibly orphaned. |
| **blender_mcp_client.py only used lazily** | `packages/nexus_core/blender_mcp_client.py` | Only imported inside try/except blocks in launch_dashboard.py (lines 512, 735). Not tested. |
| **Favicon control character** | `web/index.html` line 13 | Favicon SVG contains a raw `\x07` (bell) control character — may cause rendering issues. |
| **Untracked outputs/ folders on disk** | `outputs/poc2-poc7`, `data/demo_poc2/` | Generated experiment artifacts present locally; correctly gitignored. |
| **__pycache__ directories present** | scripts/, tests/, packages/data_pipeline/ | Gitignored and harmless, but present on disk. |

### Possibly Unused / Orphaned

| File | Reason |
|---|---|
| `packages/data_pipeline/visualization.py` | Not exported in `__init__.py`. Generates footprint/patch PNGs but may be superseded by poc4_visualization.py etc. |
| `scripts/render_blender_scene.py` | No callers found anywhere in the project. |
| `NEXUS_LUNAR_SIH_Complete_Blueprint.md` | Likely superseded by the other blueprint file (or vice versa). |

### Empty Files / Folders

- **No empty Python files found** — all `__init__.py` files have content.
- **No empty user-space directories** — only `.git/refs/heads` and `.git/refs/tags` are empty (normal git internals).

---

## 6. FINAL SUMMARY

```
TOTAL TRACKED FOLDERS:  11 top-level directories (excl. .git, __pycache__)
TOTAL TRACKED FILES:    134

By file type:
  .py          89
  .png         19
  .tif          6  (committed despite *.tif gitignore rule)
  .md          10
  .js           2
  .json         2
  .css          1
  .html         1
  .txt          1
  .xml          1
  .gitignore    1
  LICENSE       1  (no extension)
```

**IMPORTANT FILES:**
- `packages/data_pipeline/__init__.py` — master public API registry (POC4-POC7 pipeline)
- `packages/data_pipeline/models.py` — core domain models (LunarObservation, BoundingBox)
- `web/index.html`, `web/app.js`, `web/style.css` — main dashboard frontend
- `services/lunar_data/server.py` — primary HTTP catalog API
- `scripts/launch_dashboard.py` — main server entry point
- `data/catalog.json` — live observation catalog
- `requirements.txt` — dependency manifest (currently incomplete)

**IMPORTANT MODULES:**
- `packages/data_pipeline` — full POC4-POC7 experiment pipeline (34 files)
- `packages/registration` — classical SIFT/ORB/AKAZE/RANSAC image registration
- `packages/nexus_core` — high-level AI modules POC1-POC8 (GNN, SNN, habitat planner)
- `packages/first_principles` — physics, chemistry, biology, frequency + PINN model

**POSSIBLE DUPLICATES:**
1. `NEXUS_LUNAR_SIH_Complete_Blueprint.md` vs `NEXUS-LUNAR_SIH_Complete_Project_Blueprint.md` — two near-identical SIH blueprints
2. `nexus_core/poc2_terrain_intelligence.py` vs `data_pipeline/poc7_terrain.py` — both implement TerrainIntelligenceEngine
3. `nexus_core/poc4_resource_intelligence.py` vs `data_pipeline/poc4_*` — POC4 label used for two different feature sets
4. `nexus_core/poc6_gnn_reasoner.py` vs `data_pipeline/poc6_verification.py` — both POC6, different concerns (GNN vs geometric verification)
5. `data_pipeline/visualization.py` vs `poc4_visualization.py` / `poc5_visualization.py` — overlapping visualization concerns

**POSSIBLY UNUSED:**
- `scripts/render_blender_scene.py` — no callers found anywhere
- `packages/data_pipeline/visualization.py` — not exported in __init__.py
- `NEXUS_LUNAR_SIH_Complete_Blueprint.md` — likely superseded by the other blueprint

**POSSIBLY MISSING:**
- `apps/web/` directory — hardcoded in services/lunar_data/server.py; does not exist; breaks frontend serving
- Complete `requirements.txt` — missing: opencv-python, torch, playwright, matplotlib, scipy, networkx
- `pyproject.toml` / `setup.py` — no installable package specification
- `tests/conftest.py` — no shared pytest path/fixture setup
- `scripts/run_poc3_experiment.py` — POC3 has no script runner (inconsistent with POC4-POC7)
- `scripts/run_poc8_experiment.py` — POC8 has no script runner

**POSSIBLE ISSUES:**
1. CRITICAL — `services/lunar_data/server.py`: WEB_DIR points to `apps/web/` which does not exist. Frontend serving is broken for this microservice.
2. WARNING — 6 LRO NAC `.tif` files committed to git despite gitignore excluding `*.tif`. Large binary files in git history.
3. WARNING — `requirements.txt` missing critical runtime deps (OpenCV, PyTorch, Playwright, matplotlib, scipy, networkx). Fresh install will fail.
4. WARNING — Dual POC numbering: `nexus_core` and `data_pipeline` both use POC1-POC8 labels for different implementations, causing confusion.
5. WARNING — No `pyproject.toml` — packages cannot be pip-installed cleanly.
6. MINOR — Favicon SVG in `web/index.html` contains a `\x07` bell control character.
7. MINOR — `nac.m1419447916re` is missing its `_browse.tif` in git (file exists on disk untracked); inconsistent with all other NAC image sets.

---

*Complete inspection of the `nexus-unified` branch is finished. The above inventory represents the files and structure found in this branch.*
