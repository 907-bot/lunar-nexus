# NEXUS-LUNAR
## AI-Driven Lunar Image Registration, Spatial Intelligence & Habitat Planning

**SIH-oriented project blueprint**

---

# 1. Executive Summary

NEXUS-LUNAR is a layered scientific AI platform built around the SIH problem of registering Chandrayaan-2 lunar optical observations against reference lunar imagery.

The core SIH problem is:

> Given a moving/source lunar image and a fixed/reference lunar image, find reliable correspondences and geometrically register the source image to the reference image despite illumination, viewpoint and scale variations.

NEXUS-LUNAR extends this core capability into a **spatial intelligence and habitat-site planning system**.

The key idea is:

```text
Lunar Observation
       ↓
Geospatial Understanding
       ↓
Image Correspondence
       ↓
Geometric Verification
       ↓
Registered Lunar Terrain
       ↓
Spatial Knowledge Graph
       ↓
Terrain / Illumination / Spectral Intelligence
       ↓
Explainable Site Selection
       ↓
Habitat Constraint Planning
       ↓
3D Digital Twin
       ↓
Design → Simulate → Stress-Test → Redesign
```

The SIH registration engine remains the scientifically measurable core. NEXUS is the higher-level intelligence layer built on top of verified lunar terrain correspondence.

---

# 2. Project Positioning

## Recommended title

### NEXUS-LUNAR
**AI-Driven Lunar Terrain Correspondence, Spatial Intelligence & Habitat Planning**

Alternative SIH-facing title:

### NEXUS
**Intelligent Lunar Image Registration and Habitat-Site Intelligence Platform**

---

# 3. Why This Architecture

The project should NOT be presented as merely:

- an image-matching application
- an LLM chatbot
- a generic lunar visualization
- an AI-generated habitat

Instead, it should be presented as a progression:

```text
IMAGE REGISTRATION
        ↓
SPATIAL REASONING
        ↓
SPATIAL INTELLIGENCE
        ↓
MISSION INTELLIGENCE
        ↓
HABITAT PLANNING
```

The central scientific principle is:

> Two observations should be treated as corresponding when they represent the same physical lunar terrain/ground footprint, not merely because they look visually similar.

---

# 4. SIH Problem Statement Mapping

The system directly addresses:

### Illumination variation

Changes in solar azimuth/elevation can alter shadows, contrast and surface appearance.

### Viewpoint variation

Different spacecraft/camera positions and orientations cause translation, rotation, scale and perspective differences.

### Scale variation

Chandrayaan-2 sensors and external reference missions operate at different spatial resolutions and imaging geometries.

### Expected SIH output

The system should produce:

- registered lunar imagery
- corresponding match/tie points
- confidence values
- geometric transformation
- RMSE / localization error
- inlier count
- inlier ratio
- retrieval metrics such as Recall@K
- reproducible processing metadata

---

# 5. High-Level Architecture

```text
                         LUNAR DATA SOURCES
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
             OHRC              TMC-2             IIRS
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                    LRO NAC / SELENE
                                │
                                ▼
                  ┌────────────────────────┐
                  │ DATA INGESTION LAYER   │
                  │ + METADATA ENGINE      │
                  └────────────┬───────────┘
                               │
                               ▼
                  ┌────────────────────────┐
                  │ GEOSPATIAL NORMALIZER  │
                  │ footprints / CRS / DEM │
                  └────────────┬───────────┘
                               │
                               ▼
                  ┌────────────────────────┐
                  │ MULTI-SCALE PATCH      │
                  │ GENERATION              │
                  └────────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      Illumination        Scale/Viewpoint   Cross-Modal
      Robustness          Robustness        Representation
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                  ┌────────────────────────┐
                  │ CORRESPONDENCE ENGINE  │
                  │ Retrieval + Matching   │
                  └────────────┬───────────┘
                               │
                               ▼
                  ┌────────────────────────┐
                  │ GEOMETRIC VERIFIER     │
                  │ RANSAC / transforms    │
                  └────────────┬───────────┘
                               │
                               ▼
                  ┌────────────────────────┐
                  │ CONFIDENCE + UNCERTAINTY│
                  │ + TIE POINTS           │
                  └────────────┬───────────┘
                               │
                               ▼
                    REGISTERED LUNAR REGION
                               │
                               ▼
                    ╔══════════════════════╗
                    ║    NEXUS LAYER       ║
                    ╚══════════╤═══════════╝
                               │
             ┌─────────────────┼──────────────────┐
             │                 │                  │
             ▼                 ▼                  ▼
        Terrain           Illumination       Spectral /
       Intelligence        Intelligence       Resource
             │                 │                  │
             └─────────────────┼──────────────────┘
                               ▼
                  SPATIAL KNOWLEDGE GRAPH
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
                   GNN                   XAI
                    │                     │
                    └──────────┬──────────┘
                               ▼
                    EXPLAINABLE SITE SCORE
                               │
                               ▼
                    HABITAT CONSTRAINT GRAPH
                               │
                               ▼
                     HABITAT PLANNER AGENT
                               │
                               ▼
                       3D DIGITAL TWIN
                               │
                               ▼
                 DESIGN → SIMULATE → TEST
                               │
                               ▼
                           REDESIGN
```

---

# 6. System Layers

## Layer 1 — Lunar Data

Inputs:

- Chandrayaan-2 OHRC
- Chandrayaan-2 TMC-2
- Chandrayaan-2 IIRS
- LRO NAC
- SELENE/Kaguya reference observations

The system preserves source metadata rather than treating imagery as anonymous files.

---

## Layer 2 — Geospatial Foundation

Responsibilities:

- metadata parsing
- coordinate systems
- geographic footprints
- spatial overlap
- product indexing
- acquisition geometry
- ground sampling information
- optional DEM/DTM integration

Core question:

> Which observations actually cover the same lunar region?

---

## Layer 3 — Registration Engine

Responsibilities:

- keypoint extraction
- descriptors
- candidate matching
- illumination normalization
- multi-scale matching
- cross-modal retrieval
- geometric verification
- transformation estimation
- tie-point generation

---

## Layer 4 — Spatial Intelligence

The registered observations become structured spatial information.

Responsibilities:

- terrain analysis
- slope
- elevation
- roughness
- crater/hazard proximity
- illumination analysis
- spectral indicators
- temporal observation relationships

---

## Layer 5 — Spatial Knowledge Graph

Represents the Moon as connected scientific entities.

Example:

```text
Lunar Region
    │
    ├── contains → Crater
    │                  │
    │                  └── has_terrain → Patch
    │
    ├── observed_by → OHRC
    │
    ├── observed_by → TMC-2
    │
    ├── observed_by → IIRS
    │
    └── corresponds_to → LRO NAC Patch
```

---

## Layer 6 — Intelligence

Includes:

- graph reasoning
- Graph Neural Networks
- temporal/spiking models
- multimodal embeddings
- uncertainty estimation
- explainable AI

---

## Layer 7 — Habitat Intelligence

Converts verified lunar terrain into:

- candidate-site analysis
- constraint generation
- habitat placement
- conceptual design
- simulation
- stress testing
- redesign

---

# 7. POC Roadmap

The project is best developed as **16 progressively integrated POCs**.

The POCs are not 16 separate applications. They are capabilities that progressively become one platform.

---

# POC 1 — Lunar Data Explorer

## Goal

Understand and visualize the available lunar products.

## Inputs

- OHRC
- TMC-2
- IIRS
- LRO NAC
- SELENE

## Outputs

```text
Product ID
Sensor
Acquisition time
Spatial resolution
Coordinates
Footprint
Illumination metadata
File reference
```

## UI

```text
┌──────────────────────────────────────┐
│ LUNAR DATA EXPLORER                 │
├──────────────────────────────────────┤
│ Sensor: OHRC                         │
│ Resolution: ...                      │
│ Acquisition: ...                     │
│ Latitude: ...                        │
│ Longitude: ...                       │
│                                      │
│          LUNAR IMAGE                 │
│                                      │
│        COVERAGE FOOTPRINT            │
└──────────────────────────────────────┘
```

---

# POC 2 — Geographic Overlap Engine

## Goal

Determine whether two observations cover the same physical lunar region.

```text
Source footprint
      +
Reference footprint
      ↓
Polygon intersection
      ↓
Overlap region
```

## Output

- overlap percentage
- intersection polygon
- candidate correspondence region
- geographic bounds

This prevents the AI from attempting impossible matches.

---

# POC 3 — Classical Registration Engine

## Goal

Create a transparent non-AI baseline.

Implement:

- SIFT
- RootSIFT
- ORB
- AKAZE
- descriptor matching
- RANSAC
- affine transformation
- homography
- phase correlation where appropriate

Pipeline:

```text
Image A
 ↓
Keypoints
 ↓
Descriptors
 ↓
Image B
 ↓
Candidate matches
 ↓
RANSAC
 ↓
Transformation
 ↓
Registered image
```

Metrics:

- match count
- inlier count
- inlier ratio
- RMSE
- runtime

---

# POC 4 — Illumination Robustness

## Goal

Reduce the impact of changing solar illumination.

Representations:

- raw grayscale
- local contrast
- gradients
- edges
- normalized intensity
- shadow-aware features

Benchmark:

```text
Raw
vs
Normalized
vs
Gradient
vs
Combined representation
```

The system should report which representation works best under different lighting conditions.

---

# POC 5 — Scale & Viewpoint Robustness

## Goal

Handle different image scales and camera viewpoints.

Methods:

- image pyramids
- ground-footprint resampling
- multi-scale patches
- rotation augmentation
- affine augmentation
- perspective augmentation
- metadata-aware scaling

Core principle:

> Compare equivalent physical ground footprints rather than equivalent pixel counts.

---

# POC 6 — Cross-Modal AI Matcher

## Goal

Learn representations that make different lunar sensors comparable.

Architecture:

```text
OHRC/TMC-2
     ↓
Vision Encoder
     ↓
Embedding
     │
     │ shared embedding space
     │
     ↑
Spectral Encoder
     ↑
IIRS
```

Training:

```text
Positive:
same physical terrain

Negative:
different physical terrain
```

Possible methods:

- Siamese networks
- two-tower models
- contrastive learning
- triplet loss
- supervised contrastive learning

Metadata can condition the model on:

- scale
- illumination geometry
- sensor
- acquisition conditions

---

# POC 7 — Retrieval Engine

## Goal

Search large reference collections efficiently.

Pipeline:

```text
Query patch
    ↓
Embedding
    ↓
Vector database
    ↓
Top-K candidates
```

Potential technology:

- FAISS
- PostgreSQL + pgvector
- Qdrant if required

Metrics:

- Recall@1
- Recall@5
- Recall@10
- retrieval latency

---

# POC 8 — Geometric Verification & Uncertainty

## Goal

Never trust AI similarity alone.

Pipeline:

```text
AI Retrieval
     ↓
Top-K candidates
     ↓
Local correspondence
     ↓
RANSAC
     ↓
Geometric consistency
     ↓
Inliers
     ↓
RMSE
     ↓
Confidence
```

Output:

```text
Candidate: #1
Retrieval score: ...
Inliers: ...
Inlier ratio: ...
RMSE: ...
Localization error: ...
Confidence: ...
```

The system should be able to reject low-confidence matches.

---

# POC 9 — Lunar Spatial Knowledge Graph

## Goal

Represent lunar observations, terrain and relationships as a graph.

## Nodes

- lunar region
- image
- sensor
- observation
- terrain patch
- crater
- ridge
- slope zone
- hazard
- illumination state
- spectral observation
- candidate site
- habitat component

## Edges

```text
OBSERVED_BY
OVERLAPS
CORRESPONDS_TO
LOCATED_NEAR
CONTAINS
HAS_SLOPE
HAS_ELEVATION
HAS_ILLUMINATION
HAS_SPECTRAL_INDICATOR
CONSTRAINS
SUITABLE_FOR
```

Example:

```text
          Lunar Region
                │
       ┌────────┼────────┐
       ↓        ↓        ↓
     OHRC     TMC-2     IIRS
       │        │        │
       └────────┼────────┘
                ↓
          Terrain Patch
                │
       ┌────────┼─────────┐
       ↓        ↓         ↓
     slope    hazard   illumination
```

---

# POC 10 — Terrain Intelligence Engine

## Goal

Extract spatial terrain properties from registered observations and terrain models.

Features:

- elevation
- slope
- aspect
- roughness
- local relief
- crater proximity
- boulder/hazard indicators where data support them
- terrain uniformity
- accessibility proxies

Output:

```text
Site A
 ├── elevation
 ├── slope
 ├── roughness
 ├── hazard proximity
 └── terrain score
```

---

# POC 11 — Illumination Intelligence

## Goal

Turn an SIH challenge into a mission-planning signal.

Inputs:

- acquisition times
- solar geometry
- image shadows
- illumination metadata
- repeated observations where available

Outputs:

- illuminated regions
- shadow regions
- temporal illumination profile
- solar-access indicator
- persistent-darkness indicator

Important:

A permanently shadowed region is not automatically a good habitat location.

The system should treat illumination as one constraint among many.

---

# POC 12 — IIRS Spectral / Resource Intelligence

## Goal

Use IIRS observations as a source of spectral information.

Pipeline:

```text
IIRS
 ↓
Spectral preprocessing
 ↓
Spectral features
 ↓
Material/mineral indicators
 ↓
Spatial mapping
 ↓
Knowledge graph
```

The output should be described as:

- spectral evidence
- material indicators
- resource indicators

Do not claim direct discovery of economically mineable resources unless the methodology and evidence support it.

---

# POC 13 — Explainable AI Site Selection

## Goal

Answer:

> Why did NEXUS recommend this location?

Example:

```text
SITE 07
Overall suitability: 82

Positive factors:
+ favorable terrain
+ relatively low slope
+ good illumination access
+ strong correspondence confidence

Negative factors:
- nearby terrain hazard
- limited spectral evidence
```

Use:

- feature attribution
- rule-based explanations
- SHAP where appropriate
- evidence tracing
- uncertainty visualization

Every recommendation should link back to observations and derived features.

---

# POC 14 — Graph Neural Network Spatial Reasoner

## Goal

Learn spatial relationships over the lunar knowledge graph.

Potential architectures:

- GraphSAGE
- GCN
- GAT

Pipeline:

```text
Spatial Knowledge Graph
          ↓
        GNN
          ↓
Node embeddings
          ↓
Site-level prediction
```

Possible tasks:

- candidate-site ranking
- link prediction
- terrain relationship learning
- spatial similarity
- missing-edge inference

Important:

Do not create a GNN merely to use a GNN. Build the real graph first and use a learned GNN only where sufficient data/labels justify it.

---

# POC 15 — Spiking Neural Network Temporal Reasoner

## Goal

Use SNNs for event-driven temporal/spatial modelling rather than forcing them into the core registration algorithm.

Possible inputs:

```text
Observation t1
Observation t2
Observation t3
Observation t4
       ↓
Temporal encoding
       ↓
Spiking neural network
       ↓
Temporal spatial representation
```

Potential applications:

- temporal illumination modelling
- multi-observation site-state modelling
- event-driven change detection
- temporal spatial embeddings

SNN should be an advanced research module rather than a mandatory SIH dependency.

---

# POC 16 — Habitat Constraint Planner + Digital Twin

## Goal

Convert verified lunar terrain into a conceptual habitat planning environment.

Pipeline:

```text
Registered Terrain
       ↓
Terrain Intelligence
       ↓
Illumination
       ↓
Hazards
       ↓
Spectral/Resource Indicators
       ↓
Communication/mission constraints
       ↓
Constraint Graph
       ↓
Habitat Planner
       ↓
3D Habitat
       ↓
Simulation
       ↓
Stress Test
       ↓
Redesign
```

---

# 8. NEXUS Habitat Intelligence Architecture

```text
                 CANDIDATE SITE
                       │
       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼
    TERRAIN          ENERGY          RESOURCES
       │               │                │
    slope           sunlight         spectral
    elevation       shadow           indicators
    roughness       access            materials
    hazards         duration          uncertainty
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                 SITE CONSTRAINTS
                       │
                       ▼
               SPATIAL KNOWLEDGE
                    GRAPH
                       │
                       ▼
                  GNN / RULES
                       │
                       ▼
                   XAI LAYER
                       │
                       ▼
                SITE SUITABILITY
                       │
                       ▼
              HABITAT CONSTRAINTS
                       │
                       ▼
               HABITAT PLANNER
                       │
                       ▼
                3D DIGITAL TWIN
                       │
                       ▼
             SIMULATE / TEST / REDESIGN
```

---

# 9. Habitat Site Scoring

Use a transparent, configurable model.

Conceptually:

```text
HabitatScore =
    w1 * TerrainSuitability
  + w2 * IlluminationSuitability
  + w3 * CommunicationSuitability
  + w4 * ResourceIndicator
  - w5 * HazardRisk
  - w6 * ConstructionDifficulty
```

The weights should be configurable.

Do not present the score as an absolute scientific truth.

Present it as:

> A decision-support score based on defined mission constraints.

---

# 10. Habitat Constraint Graph

Instead of asking an LLM to hallucinate a habitat, create explicit constraints.

```text
Candidate Site
      │
      ├── terrain constraint
      ├── slope constraint
      ├── hazard constraint
      ├── illumination constraint
      ├── communication constraint
      ├── resource constraint
      └── construction constraint
              │
              ▼
       Habitat Design Space
              │
              ▼
        Candidate Designs
              │
              ▼
           Simulation
              │
              ▼
       Constraint Violations
              │
              ▼
           Redesign
```

This makes NEXUS a constraint-driven engineering system.

---

# 11. Agentic Architecture

Agents should orchestrate scientific tools rather than replace them.

```text
                    NEXUS ORCHESTRATOR
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ▼                   ▼                   ▼
  Data Agent          Geo Agent          Vision Agent
       │                   │                   │
       ▼                   ▼                   ▼
  Metadata tools      GIS tools          ML models
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                 ┌─────────┴──────────┐
                 ▼                    ▼
          Retrieval Agent      Geometry Agent
                 │                    │
                 └─────────┬──────────┘
                           ▼
                  Uncertainty Agent
                           │
                           ▼
                  Habitat Planning Agent
```

Possible orchestration framework:

- LangGraph
- typed tool contracts
- Pydantic schemas
- deterministic scientific tools

---

# 12. Agent Responsibilities

## Data Agent

- identify products
- validate metadata
- locate candidate observations
- manage ingestion

## Geospatial Agent

- compute footprints
- determine overlaps
- coordinate transformations
- spatial queries

## Vision Agent

- generate patches
- run feature extraction
- compute embeddings
- perform retrieval

## Geometry Agent

- run matching
- RANSAC
- transformation estimation
- calculate residuals

## Uncertainty Agent

- confidence
- failure detection
- ambiguity
- evidence tracing

## Habitat Agent

- collect site constraints
- generate candidate habitat configurations
- invoke simulation
- iterate designs

---

# 13. Technology Stack

## Programming

```text
Python
TypeScript
SQL
```

---

## Scientific Computing

```text
NumPy
SciPy
scikit-image
OpenCV
PyTorch
JAX (optional)
```

---

## Geospatial

```text
GDAL
Rasterio
GeoPandas
Shapely
pyproj
PostGIS
```

---

## Image Registration

```text
SIFT
RootSIFT
ORB
AKAZE
RANSAC
Phase Correlation
Affine Transform
Homography
Learned local feature models
```

---

## Deep Learning

```text
PyTorch
timm
Siamese networks
Two-tower encoders
Contrastive learning
Vision Transformers
```

---

## Vector Search

```text
FAISS
pgvector
Qdrant (optional)
```

---

## Knowledge Graph

Primary option:

```text
Neo4j
```

Alternative:

```text
PostgreSQL + graph layer
```

---

## Graph ML

```text
PyTorch Geometric
GraphSAGE
GCN
GAT
```

---

## Spiking Neural Networks

```text
snnTorch
```

Potential future alternatives:

```text
Norse
Brian2
```

---

## Explainable AI

```text
SHAP
Captum
feature attribution
rule-based evidence tracing
```

---

## Backend

```text
FastAPI
Pydantic
Celery/RQ where required
Redis
```

---

## Database

```text
PostgreSQL
PostGIS
Neo4j
Redis
pgvector
```

Not every database is mandatory. Start with PostgreSQL + PostGIS and add Neo4j/vector infrastructure only when justified.

---

## Frontend

```text
Next.js
React
TypeScript
Three.js
WebGPU
MapLibre GL JS
```

---

## 3D

```text
Three.js
Blender
glTF
WebGPU
```

---

## Agent Orchestration

```text
LangGraph
MCP where useful
Pydantic tool contracts
```

---

## Deployment

```text
Docker
Docker Compose
GitHub Actions
Cloud GPU where required
Local inference where possible
```

---

# 14. Recommended Repository Structure

```text
nexus-lunar/
│
├── apps/
│   ├── web/
│   └── api/
│
├── packages/
│   ├── registration/
│   ├── geospatial/
│   ├── retrieval/
│   ├── multimodal/
│   ├── terrain/
│   ├── illumination/
│   ├── spectral/
│   ├── knowledge_graph/
│   ├── gnn/
│   ├── snn/
│   ├── xai/
│   ├── habitat/
│   ├── simulation/
│   └── agents/
│
├── data/
│   ├── raw/
│   │   ├── ohrc/
│   │   ├── tmc2/
│   │   ├── iirs/
│   │   ├── lro/
│   │   └── selene/
│   │
│   ├── processed/
│   ├── patches/
│   └── splits/
│
├── experiments/
│   ├── registration/
│   ├── illumination/
│   ├── scale/
│   ├── multimodal/
│   ├── gnn/
│   └── snn/
│
├── configs/
│
├── notebooks/
│
├── evaluation/
│
├── docs/
│
├── docker/
│
└── README.md
```

---

# 15. Data Model

Every processed observation should retain provenance.

Example:

```text
Observation
├── product_id
├── sensor
├── mission
├── acquisition_time
├── image_path
├── footprint
├── CRS
├── spatial_resolution
├── viewing_geometry
├── illumination_geometry
├── preprocessing_version
└── source_reference
```

Every correspondence should retain:

```text
Correspondence
├── source_product
├── reference_product
├── source_coordinates
├── reference_coordinates
├── transformation
├── candidate_score
├── inlier_count
├── inlier_ratio
├── RMSE
├── localization_error
├── confidence
├── method
├── model_version
└── random_seed
```

This makes the system reproducible.

---

# 16. Evaluation Framework

## Retrieval

```text
Recall@1
Recall@5
Recall@10
```

## Registration

```text
RMSE
mean localization error
median localization error
95th percentile error
```

## Match quality

```text
total matches
inlier matches
inlier ratio
```

## Robustness

Test across:

```text
illumination changes
scale changes
viewpoint changes
sensor combinations
terrain types
```

## Operational

```text
runtime
GPU memory
CPU memory
throughput
failure rate
```

---

# 17. Dataset Split

Avoid random pixel-level or neighboring-patch splits.

Preferred:

```text
Moon
 │
 ├── Region A → TRAIN
 ├── Region B → TRAIN
 ├── Region C → VALIDATION
 └── Region D → TEST
```

The test region should be geographically separated.

This helps prevent spatial leakage.

---

# 18. Synthetic Data Policy

The main demonstration should use real lunar observations.

Synthetic data can still be used for:

- unit testing
- controlled geometric transformations
- controlled illumination perturbations
- robustness experiments
- algorithm debugging
- simulation stress tests

But the headline SIH results should preferably come from real data.

---

# 19. Final Product Workflow

The final user experience should be:

```text
1. Select source image
        ↓
2. Select reference archive/sensor
        ↓
3. Inspect metadata
        ↓
4. Determine geographic overlap
        ↓
5. Generate multi-scale representations
        ↓
6. Retrieve candidate correspondences
        ↓
7. Geometrically verify candidates
        ↓
8. Register source → reference
        ↓
9. Show tie points + confidence + RMSE
        ↓
10. Create registered lunar region
        ↓
11. Send region to NEXUS
        ↓
12. Build spatial knowledge graph
        ↓
13. Analyze terrain
        ↓
14. Analyze illumination
        ↓
15. Analyze spectral/resource indicators
        ↓
16. Generate site suitability score
        ↓
17. Explain recommendation
        ↓
18. Generate habitat constraints
        ↓
19. Place conceptual habitat in 3D
        ↓
20. Simulate
        ↓
21. Identify constraint violations
        ↓
22. Redesign
        ↓
23. Present final candidate
```

---

# 20. Final UI Concept

```text
┌──────────────────────────────────────────────────────────────┐
│                     NEXUS-LUNAR                              │
│       Lunar Correspondence & Habitat Intelligence            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  SOURCE IMAGE                 REFERENCE IMAGE                │
│  ┌───────────────┐            ┌───────────────┐              │
│  │               │            │               │              │
│  │     OHRC      │ ─────────→ │    LRO NAC    │              │
│  │               │            │               │              │
│  └───────────────┘            └───────────────┘              │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ CORRESPONDENCE                                                │
│                                                              │
│ Top-1 candidate       ████████████████  96.2%                │
│ Inliers                                      842             │
│ Inlier ratio                                78.4%            │
│ RMSE                                          ...             │
│ Localization error                            ...             │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                       NEXUS                                   │
│                                                              │
│ Terrain       ████████████████                                │
│ Illumination ██████████████                                  │
│ Hazard        ███████████                                    │
│ Resources     █████████                                      │
│                                                              │
│ Site Suitability: 82/100                                     │
│                                                              │
│ WHY?                                                         │
│ ✓ favorable terrain                                         │
│ ✓ acceptable illumination                                   │
│ ✓ strong registration confidence                             │
│ ⚠ moderate hazard proximity                                  │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                  3D LUNAR DIGITAL TWIN                       │
│                                                              │
│                   /\                                         │
│              ____/  \____                                    │
│          ___/    HABITAT   \___                              │
│       __/______________________\__                            │
│                                                              │
│ [SIMULATE] [STRESS TEST] [REDESIGN] [EXPORT]                │
└──────────────────────────────────────────────────────────────┘
```

---

# 21. The Spatial Intelligence Story

Your project can be explicitly described at four levels.

## Level 1 — Spatial perception

The system detects terrain features and visual patterns.

## Level 2 — Spatial reasoning

The system determines:

- where a feature is
- whether two observations correspond
- how coordinate systems relate
- how terrain features relate spatially

## Level 3 — Spatial intelligence

The system combines:

- geometry
- terrain
- illumination
- spectral information
- uncertainty
- graph relationships

to evaluate locations.

## Level 4 — Mission intelligence

NEXUS uses those spatial constraints to support:

- site selection
- habitat planning
- conceptual design
- simulation
- iterative redesign

---

# 22. Role of GNN

GNN is not simply another model.

It operates on:

```text
SPATIAL KNOWLEDGE GRAPH
```

Example:

```text
Site
 ├── terrain
 ├── crater
 ├── illumination
 ├── OHRC observation
 ├── TMC-2 observation
 ├── IIRS observation
 └── LRO reference
```

The GNN learns relationships between these connected entities.

---

# 23. Role of SNN

SNN is best used for temporal/event-driven information.

Example:

```text
Time
 ↓
illumination observations
 ↓
temporal encoding
 ↓
SNN
 ↓
spatio-temporal state
```

This creates a scientifically meaningful role for spiking neural networks rather than adding them as a buzzword.

---

# 24. Role of XAI

XAI provides the answer to:

> Why?

The final recommendation should be traceable:

```text
Recommendation
      ↓
Site score
      ↓
Feature contributions
      ↓
Observations
      ↓
Original lunar data
```

This is particularly important for scientific AI.

---

# 25. Recommended Development Order

## Stage 1 — SIH Core

Build first:

```text
POC 1
POC 2
POC 3
POC 4
POC 5
POC 6
POC 7
POC 8
```

Exit condition:

> Reliable lunar image correspondence and registration with measurable metrics.

---

## Stage 2 — NEXUS Spatial Intelligence

Build:

```text
POC 9
POC 10
POC 11
POC 12
POC 13
```

Exit condition:

> A registered lunar site can be represented as explainable spatial intelligence.

---

## Stage 3 — Advanced Research

Build:

```text
POC 14
POC 15
```

Exit condition:

> Graph and temporal neural reasoning can be demonstrated on top of real spatial data.

---

## Stage 4 — Habitat Intelligence

Build:

```text
POC 16
```

Exit condition:

> A real registered lunar region can drive conceptual habitat placement and iterative design in a 3D environment.

---

# 26. SIH MVP vs Full NEXUS

## SIH MVP

```text
OHRC/TMC-2/IIRS
      ↓
Geospatial overlap
      ↓
Registration
      ↓
Correspondence AI
      ↓
Geometric verification
      ↓
Tie points
      ↓
RMSE
      ↓
Registered image
```

## Strong SIH Version

```text
SIH Core
   ↓
Spatial Knowledge Graph
   ↓
Terrain Intelligence
   ↓
Illumination Intelligence
   ↓
XAI
```

## Full NEXUS Vision

```text
Strong SIH Version
      ↓
GNN
      ↓
SNN
      ↓
Habitat constraints
      ↓
3D Digital Twin
      ↓
Design
      ↓
Simulation
      ↓
Stress Test
      ↓
Redesign
```

---

# 27. Presentation Strategy

Do not say:

> “I am not from a space background.”

Instead say:

> “My background is AI and data science, so I approached the problem as a multimodal scientific AI problem. I started from the physical constraints of lunar observations and designed the AI around those constraints.”

The key narrative:

```text
Problem
   ↓
Same terrain looks different
   ↓
Insight
   ↓
Correspondence must be geographic, not merely visual
   ↓
Solution
   ↓
Metadata-aware coarse-to-fine registration
   ↓
Verification
   ↓
Geometric consistency + uncertainty
   ↓
Extension
   ↓
Spatial knowledge graph
   ↓
NEXUS
   ↓
Habitat-site intelligence
```

---

# 28. Recommended 60-Second Pitch

> Our project addresses a fundamental challenge in lunar exploration: the same physical terrain can look very different when observed by different sensors, at different scales, viewing angles and illumination conditions.
>
> We built NEXUS-LUNAR, a metadata-aware, coarse-to-fine lunar correspondence and registration system. It first understands the geographic footprint and observation geometry, then performs multi-scale and illumination-robust matching, retrieves candidate correspondences using multimodal AI, and finally verifies them geometrically using tie points, RANSAC and measurable registration errors.
>
> The important part is that we do not treat an AI similarity score as ground truth. Every correspondence is geometrically verified and accompanied by confidence and error measurements.
>
> On top of this SIH core, NEXUS converts registered lunar observations into spatial intelligence using a lunar knowledge graph, terrain analysis, illumination intelligence, spectral indicators and explainable site selection.
>
> The final layer is a conceptual habitat-planning digital twin where the selected terrain becomes a set of engineering constraints for habitat design, simulation and redesign.
>
> So our pipeline is observation → correspondence → verification → spatial intelligence → habitat planning.

---

# 29. Core Technical Principle

The most important sentence in the project is:

> **NEXUS-LUNAR does not simply find visually similar lunar images. It determines whether heterogeneous observations correspond to the same physical lunar terrain, verifies that correspondence geometrically, and then uses the resulting registered terrain as the foundation for spatial intelligence and habitat-site planning.**

---

# 30. Final Vision

```text
                         NEXUS-LUNAR

                         OBSERVE
                            │
                            ▼
                    UNDERSTAND DATA
                            │
                            ▼
                       REGISTER
                            │
                            ▼
                     VERIFY GEOMETRY
                            │
                            ▼
                   BUILD SPATIAL GRAPH
                            │
                 ┌──────────┼──────────┐
                 ▼          ▼          ▼
              TERRAIN   ILLUMINATION  SPECTRAL
                 │          │          │
                 └──────────┼──────────┘
                            ▼
                    SPATIAL REASONING
                            │
                            ▼
                     GNN / XAI / SNN
                            │
                            ▼
                    SITE INTELLIGENCE
                            │
                            ▼
                  HABITAT CONSTRAINTS
                            │
                            ▼
                     HABITAT DESIGN
                            │
                            ▼
                      SIMULATION
                            │
                            ▼
                     STRESS TEST
                            │
                            ▼
                        REDESIGN
                            │
                            └───────────────┐
                                            │
                                            ▼
                                      NEW DESIGN
```

The long-term goal is not to make NEXUS an artificial astronaut or an unrestricted autonomous engineer.

The goal is to build a **scientifically grounded spatial intelligence platform that transforms heterogeneous lunar observations into verified geographic knowledge and then into explainable mission and habitat-planning decisions.**
