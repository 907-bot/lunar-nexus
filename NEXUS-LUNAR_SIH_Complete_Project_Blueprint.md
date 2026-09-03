# NEXUS-LUNAR
## AI-Driven Lunar Image Registration, Spatial Intelligence & Habitat Digital Twin

**Purpose:** Smart India Hackathon (SIH) project blueprint  
**Primary problem:** Register Chandrayaan-2 lunar optical observations against reference lunar imagery with accurate, uniformly distributed correspondence points and measurable geometric accuracy.  
**Extension:** Use the registered scientific observations as the foundation for NEXUS, a spatial-intelligence and conceptual habitat-planning layer.

---

# 1. Executive Summary

The SIH problem asks for a generic software solution that finds correspondences between Chandrayaan-2 optical images and lunar reference images, aligns the source image to the reference image, and produces match points with sub-pixel accuracy and uniform spatial distribution.

The proposed system, **NEXUS-LUNAR**, treats registration as the reliable scientific foundation and then builds spatial intelligence on top of it.

The complete pipeline is:

```text
Chandrayaan-2 / Reference Data
            |
            v
      Data & Metadata
            |
            v
   Geographic Overlap Engine
            |
            v
     Image Preprocessing
            |
            v
 Classical Registration
            |
            v
 Multimodal AI Matching
            |
            v
 Geometric Verification
            |
            v
 Confidence + XAI
            |
            v
 Lunar Spatial Knowledge Graph
            |
            v
 Terrain / Illumination / Spectral Intelligence
            |
            v
     Candidate Site Analysis
            |
            v
      NEXUS Habitat Layer
            |
            v
     3D Digital Twin
            |
            v
 Design -> Simulate -> Stress-test -> Redesign
```

The first six POCs directly address the SIH registration problem. POCs 7 and 8 turn the resulting registered observations into a demonstrable spatial-intelligence and habitat-planning system.

---

# 2. Original SIH Problem

## Background

Image registration aligns two or more images of the same scene acquired at different times, viewpoints, or sensors into a common coordinate system.

Two primary images are involved:

- **Source / Moving image:** geometrically transformed to align with the reference.
- **Reference / Fixed image:** target coordinate system.

## Lunar registration challenges

### 2.1 Illumination variation

The Moon is observed under different Sun azimuths and elevations. The same terrain can therefore have substantially different lighting, shadows, and local contrast.

### 2.2 Viewpoint variation

Different camera positions and orientations introduce:

- translation
- rotation
- scale changes
- perspective/geometric distortion

### 2.3 Scale variation

Lunar missions observe from different altitudes and instruments have different spatial resolutions and ground sampling distances.

## Expected solution

The system should provide:

- correspondence between Chandrayaan-2 optical images and lunar reference images
- registered source imagery
- corresponding match points
- sub-pixel-level geometric accuracy where supported by the method and data
- approximately uniform spatial distribution of reliable matches
- measurable evaluation

Suggested metrics:

- RMSE
- inlier count
- inlier ratio
- reprojection/alignment error
- spatial distribution / coverage
- retrieval Recall@K for learned matching
- robustness under illumination and scale changes

---

# 3. Data Sources

## Chandrayaan-2

### OHRC — Orbiter High Resolution Camera

Primary use:

- high-resolution lunar surface morphology
- crater/ridge/boulder/terrain-detail correspondence
- fine image matching

### TMC-2 — Terrain Mapping Camera-2

Primary use:

- terrain mapping
- broader spatial context
- stereo/topographic information where appropriate

### IIRS — Imaging Infrared Spectrometer

Primary use:

- spectral information
- mineral/material indicators
- resource-related scientific interpretation

## Reference imagery

### LRO NAC — Lunar Reconnaissance Orbiter Narrow Angle Camera

Primary use:

- high-resolution reference imagery
- geometric registration target
- independent reference coverage

### SELENE

Potential additional reference source for multi-mission validation.

## Important data principle

Do not synthesize the primary demonstration data.

The main pipeline should use real lunar observations:

```text
Real OHRC/TMC-2/IIRS
        +
Real LRO/SELENE
        |
        v
Real overlap
        |
        v
Real registration
        |
        v
Real spatial intelligence
```

Synthetic data may be used only for controlled unit tests, ablations, model pretraining, or failure/stress experiments where real labels are insufficient.

---

# 4. What Makes This a Spatial Intelligence Project?

The core SIH task already involves geometric and spatial reasoning.

The system must reason about:

- where an image was acquired
- which ground region it covers
- whether two observations describe the same terrain
- how coordinate systems differ
- how scale and viewpoint affect correspondence
- whether matched points are geometrically consistent
- where terrain features lie relative to each other

The NEXUS extension goes further:

```text
Geospatial reasoning
        |
        v
Spatial relationships
        |
        v
Spatial knowledge graph
        |
        v
Terrain + illumination + spectral intelligence
        |
        v
Site reasoning
        |
        v
Habitat constraints
```

Use the terminology carefully:

- **Geospatial reasoning:** coordinate, footprint, projection and geometry operations.
- **Spatial reasoning:** reasoning about relationships among locations, terrain and observations.
- **Spatial intelligence:** combining spatial evidence to make useful decisions.
- **Agentic reasoning:** deciding which tools/analyses to execute.
- **Scientific reasoning:** applying physical and engineering constraints.

Do not claim human-level spatial reasoning. Present it as a measurable computational spatial-intelligence system.

---

# 5. Eight POCs

## POC 1 — Lunar Data & Geo Explorer

### Timeline
**Days 1–4**

### Goal

Create a reliable data foundation.

### Pipeline

```text
OHRC
TMC-2
IIRS
LRO
SELENE
 |
 v
Metadata parser
 |
 v
Coordinate normalization
 |
 v
Geographic footprints
 |
 v
Interactive map/image explorer
```

### Features

- sensor selection
- image metadata
- acquisition time
- coordinates
- spatial resolution/GSD when available
- illumination metadata when available
- footprint visualization
- image preview
- quality flags

### Exit criterion

A user can select a lunar observation and see its imagery, metadata and geographic footprint.

---

# 6. POC 2 — Geographic Overlap & Patch Engine

### Timeline
**Days 5–7**

### Goal

Determine whether source and reference observations cover the same lunar surface.

### Pipeline

```text
Source footprint
       +
Reference footprint
       |
       v
Geographic intersection
       |
       v
Common ground footprint
       |
       v
Resolution-aware patch extraction
```

### Key principle

Do not simply crop arbitrary pixel windows.

Create patches based on common ground footprint.

This matters because OHRC, TMC-2, IIRS and LRO have different spatial resolutions.

### Outputs

- overlap polygons
- paired image patches
- ground coordinates
- source/reference IDs
- resolution information
- overlap confidence

### Exit criterion

The system can state that two patches correspond to approximately the same physical lunar region before visual matching begins.

---

# 7. POC 3 — Classical Registration Engine

### Timeline
**Week 2**

### Goal

Build transparent, explainable baselines before deep learning.

### Candidate methods

- SIFT
- RootSIFT
- ORB
- AKAZE
- phase correlation where appropriate
- descriptor matching
- ratio tests
- RANSAC
- affine transformation
- homography where justified
- local geometric refinement

### Pipeline

```text
Source image
     |
     v
Keypoint detection
     |
     v
Descriptors
     |
     v
Candidate matches
     |
     v
Ratio/cross-check filtering
     |
     v
RANSAC
     |
     v
Geometric transform
     |
     v
Registered image
```

### Outputs

```text
Source image
Reference image
Matched keypoints
Inlier keypoints
Transformation
Registered image
RMSE
Inlier count
Inlier ratio
```

### Exit criterion

A working classical registration baseline with quantitative evaluation.

---

# 8. POC 4 — Illumination + Scale Robustness

### Timeline
**Week 3**

### Goal

Directly address two major SIH challenges.

## Illumination

Potential preprocessing/features:

- local contrast normalization
- gradient-domain representation
- edge/structural representation
- multi-scale representations
- shadow-aware comparison
- illumination metadata conditioning

Do not claim theoretical illumination invariance unless experimentally demonstrated.

## Scale

Use:

- image pyramids
- multi-resolution patches
- GSD-aware resizing
- ground-footprint-aware patch construction
- coarse-to-fine matching

### Experiment design

Compare:

```text
Raw
  vs
Normalized
  vs
Gradient
  vs
Multi-scale
  vs
Multi-scale + illumination-aware
```

Measure actual:

- Recall@K
- inlier ratio
- RMSE
- alignment success rate

### Exit criterion

A measurable improvement in difficult illumination/scale cases.

---

# 9. POC 5 — Multimodal AI Correspondence

### Timeline
**Week 4**

### Goal

Move beyond hand-crafted feature matching and learn cross-sensor correspondence.

### Core architecture

```text
Source image
     |
Vision Encoder
     |
Embedding
     |
     +---------------- Shared representation
     |
Embedding
     |
Reference encoder
     |
Reference image
```

For multiple sensors:

```text
OHRC ----> Vision Encoder ----\
TMC-2 ---> Vision Encoder -----+--> Shared embedding space
IIRS ----> Spectral Encoder --/
```

### Learning approaches

- Siamese networks
- two-tower architecture
- contrastive learning
- triplet loss
- hard negative mining
- metadata conditioning

### Metadata features

Where available:

- scale/GSD
- acquisition geometry
- illumination geometry
- sensor identity
- viewing geometry

### Retrieval output

```text
Query: OHRC patch #124

Top candidates:
1. LRO patch #872
2. LRO patch #641
3. LRO patch #203
...
```

### Metrics

- Recall@1
- Recall@5
- Recall@10
- embedding similarity
- geometric verification success

### Exit criterion

The model retrieves likely corresponding lunar terrain patches.

---

# 10. POC 6 — Geometric Verification + Explainable AI

### Timeline
**Week 5**

### Goal

Prevent an AI similarity score from being treated as proof of correspondence.

### Pipeline

```text
AI retrieval
    |
    v
Top-K candidates
    |
    v
Geometric verification
    |
    v
RANSAC
    |
    v
Inliers + RMSE + transformation
    |
    v
Confidence
    |
    v
XAI explanation
```

## Confidence

Possible components:

- match score
- number of inliers
- inlier ratio
- reprojection error
- geographic overlap
- spatial distribution
- transformation stability
- sensor/viewing compatibility

## XAI

The system should answer:

> Why was this match accepted?

Example:

```text
MATCH ACCEPTED

+ Strong geographic overlap
+ High geometric inlier count
+ Low reprojection error
+ Good spatial coverage
+ Compatible multi-scale structure

Caution:
Moderate illumination difference
```

Failure explanation:

```text
MATCH REJECTED

Reason:
Insufficient geometrically consistent matches.

Possible causes:
- low texture
- excessive illumination difference
- insufficient overlap
- scale mismatch
- viewpoint distortion
```

### Important design principle

A system that can explain rejection is more credible than a system that always returns a confident answer.

---

# 11. POC 7 — NEXUS Spatial Intelligence

### Timeline
**Week 6**

### Goal

Transform registered observations into structured lunar knowledge.

## Spatial Knowledge Graph

Suggested technology:

- Neo4j
- spatial metadata
- graph algorithms
- GraphSAGE/GAT as optional learning modules

### Nodes

- lunar region
- image
- sensor
- observation
- terrain patch
- crater
- ridge
- slope region
- hazard
- illumination state
- spectral observation
- candidate site
- habitat component

### Edges

- OBSERVED_BY
- CORRESPONDS_TO
- OVERLAPS
- LOCATED_NEAR
- CONTAINS
- HAS_SLOPE
- HAS_ELEVATION
- HAS_ILLUMINATION
- HAS_RESOURCE_INDICATOR
- SUITABLE_FOR
- CONSTRAINS

### Example

```text
Lunar Region
    |
    +-- observed by --> OHRC
    |
    +-- observed by --> TMC-2
    |
    +-- observed by --> IIRS
    |
    +-- reference --> LRO NAC
    |
    +-- contains --> Terrain Patch
                         |
                         +-- slope
                         +-- roughness
                         +-- elevation
                         +-- hazards
                         +-- illumination
                         +-- spectral indicators
```

## Terrain Intelligence

Derive/consume:

- slope
- aspect
- elevation
- roughness
- crater proximity
- terrain boundaries
- hazard indicators

## Illumination Intelligence

Use multi-temporal observations to reason about:

- illuminated regions
- shadow regions
- illumination variation
- potential solar-energy zones
- persistent/low-light areas

## IIRS Resource Intelligence

Use spectral observations for scientifically defensible:

- material indicators
- mineralogical indicators
- resource-related evidence

Do not claim confirmed mineable resources unless the data and scientific validation justify that claim.

## GNN

GraphSAGE or GAT can be added after the graph exists.

```text
Spatial graph
     |
     v
Graph neural network
     |
     v
Site representation
     |
     v
Suitability prediction/ranking
```

Do not build a GNN only to add a buzzword. If labels are insufficient, use graph algorithms and keep GNN as an experimental extension.

---

# 12. POC 8 — NEXUS Habitat Digital Twin

### Timeline
**Week 7**

### Goal

Demonstrate how registered lunar observations can support conceptual habitat site planning.

### Pipeline

```text
Registered lunar region
        |
        v
NEXUS spatial intelligence
        |
        v
Candidate site
        |
        v
Terrain constraints
Illumination constraints
Resource indicators
Hazard constraints
        |
        v
Habitat constraints
        |
        v
3D conceptual habitat
        |
        v
Digital twin
```

## Habitat constraint graph

```text
Candidate Site
     |
     +-- Terrain
     |
     +-- Illumination
     |
     +-- Hazard
     |
     +-- Resource indicators
     |
     +-- Access/operational constraints
     |
     v
Habitat design constraints
```

## 3D digital twin

The 3D environment should not be only a visual demo.

It should be connected to:

- registered imagery
- terrain representation
- candidate site coordinates
- spatial graph
- habitat placement
- constraint results

Possible interface:

```text
+------------------------------------------------+
|                 NEXUS-LUNAR                    |
+------------------------------------------------+
|                                                |
|  REGISTERED MAP             3D TERRAIN         |
|                                                |
|       [image]                 /\               |
|                             _/  \_             |
|                           _/ HABITAT \_         |
|                                                |
+------------------------------------------------+
| SITE INTELLIGENCE                              |
| Terrain          [calculated score]            |
| Illumination     [calculated score]            |
| Hazard           [calculated score]            |
| Resource         [calculated evidence]         |
|                                                |
| Overall suitability: [calculated]              |
+------------------------------------------------+
| [SIMULATE] [STRESS TEST] [REDESIGN]            |
+------------------------------------------------+
```

The habitat is conceptual unless supported by detailed engineering analysis.

---

# 13. GNN and SNN Strategy

## GNN

Best placement:

**POC 7 — Spatial Intelligence**

Purpose:

- graph representation learning
- site embeddings
- spatial relationship reasoning
- candidate ranking

Recommended starting point:

- GraphSAGE

Potential advanced model:

- GAT

## SNN

Do not force SNN into image registration.

Use it for temporal/spatio-temporal reasoning:

```text
Observation t1
Observation t2
Observation t3
Observation t4
      |
      v
Temporal spatial features
      |
      v
Spike encoding
      |
      v
SNN
      |
      v
Temporal spatial representation
```

Potential use:

- temporal illumination-state modelling
- multi-observation terrain state
- event-driven temporal changes

SNN should be a research extension, not a mandatory SIH dependency.

---

# 14. Final Architecture

```text
                         NEXUS-LUNAR
                              |
        +---------------------+----------------------+
        |                                            |
        v                                            v
    SIH CORE                                    NEXUS LAYER
        |                                            |
        v                                            v
Data ingestion                              Spatial Knowledge Graph
        |                                            |
        v                                  +---------+---------+
Geographic overlap                         |                   |
        |                                  v                   v
        v                                 GNN              Graph reasoning
Preprocessing                               |                   |
        |                                   +---------+---------+
        v                                             |
Classical registration                               v
        |                                   Terrain Intelligence
        v                                             |
AI correspondence                            Illumination Intelligence
        |                                             |
        v                                      Spectral Intelligence
Geometric verification                                |
        |                                              v
        v                                             XAI
Confidence + XAI                                       |
        |                                               v
        +---------------------> Site Suitability <-----+
                                      |
                                      v
                              Habitat Constraints
                                      |
                                      v
                               3D Digital Twin
                                      |
                                      v
                         Design -> Simulate -> Stress-test
                                      |
                                      v
                                   Redesign
```

---

# 15. Seven-Week Implementation Timeline

## Week 1 — Data foundation

### Days 1–4
POC 1:

- data ingestion
- metadata
- coordinate handling
- footprints
- basic map/UI

### Days 5–7
POC 2:

- footprint intersection
- common ground region
- patch extraction
- resolution-aware pairing

### Deliverable

A working lunar data and overlap explorer.

---

## Week 2 — Classical registration

POC 3:

- SIFT
- RootSIFT
- ORB/AKAZE
- matching
- RANSAC
- transforms
- registered images
- metrics

### Deliverable

Baseline registration engine.

---

## Week 3 — Robustness

POC 4:

- illumination normalization
- gradients/local contrast
- image pyramids
- scale handling
- GSD-aware matching
- ablation experiments

### Deliverable

Robust registration experiments with measurable improvements.

---

## Week 4 — Learned correspondence

POC 5:

- dataset construction
- positive/negative pairs
- Siamese/two-tower model
- contrastive/triplet training
- retrieval
- Recall@K

### Deliverable

Learned cross-sensor correspondence engine.

---

## Week 5 — Verification + XAI

POC 6:

- geometric verification
- RANSAC refinement
- confidence
- spatial match coverage
- uncertainty
- XAI
- failure explanations

### Deliverable

Trustworthy registration result.

---

## Week 6 — NEXUS spatial intelligence

POC 7:

- spatial knowledge graph
- terrain features
- illumination intelligence
- spectral/resource indicators
- site ranking
- GraphSAGE/GAT experiment
- XAI evidence tracing

### Deliverable

Candidate-site intelligence engine.

---

## Week 7 — Habitat digital twin

POC 8:

- site selection
- habitat constraints
- 3D terrain
- conceptual habitat placement
- digital twin
- simulation hooks
- final UI integration
- stress testing
- presentation

### Deliverable

End-to-end NEXUS-LUNAR prototype.

---

# 16. Recommended Development Strategy

Do not build eight isolated projects.

Build one product incrementally:

```text
Week 1
Dashboard
   |
Week 2
+ Registration
   |
Week 3
+ Robustness
   |
Week 4
+ AI retrieval
   |
Week 5
+ Verification + XAI
   |
Week 6
+ Spatial graph
   |
Week 7
+ Habitat digital twin
```

The frontend should evolve alongside the backend.

---

# 17. Core Evaluation Framework

## Registration metrics

### RMSE

Measure geometric alignment error.

Conceptually:

```text
RMSE = sqrt(
    mean(
        squared reprojection error
    )
)
```

Use the appropriate coordinate/measurement unit for the evaluation.

### Inlier count

Number of geometrically consistent matches after verification.

### Inlier ratio

```text
inlier ratio =
inliers / candidate matches
```

### Spatial distribution

Measure whether matches are concentrated in one small region or distributed across the image.

A good registration should avoid having all useful matches clustered in one corner.

---

# 18. Learned-model metrics

Use:

- Recall@1
- Recall@5
- Recall@10
- embedding similarity
- retrieval success
- geometric verification success

The learned model should not replace geometric verification.

---

# 19. Robustness Experiments

Create a test matrix:

```text
                  Scale
              Low  Med  High

Illumination
Low           ✓    ✓    ✓
Medium        ✓    ✓    ✓
High          ✓    ✓    ✓
```

For each condition measure:

- registration success
- RMSE
- inlier ratio
- spatial coverage
- Recall@K

---

# 20. Failure Taxonomy

The system should explicitly identify failure modes.

## Failure type 1 — Insufficient overlap

Two images do not sufficiently cover the same ground region.

## Failure type 2 — Low texture

A terrain region lacks distinctive features.

## Failure type 3 — Illumination difference

Shadows and lighting make correspondence difficult.

## Failure type 4 — Scale mismatch

Resolution difference is too large for the current matching configuration.

## Failure type 5 — Viewpoint distortion

Geometric difference exceeds the chosen transformation model.

## Failure type 6 — False visual similarity

Two different terrain areas look similar but fail geometric verification.

This failure taxonomy can become part of the XAI interface.

---

# 21. Proposed Technology Stack

## Frontend

- Next.js
- React
- TypeScript
- Three.js
- WebGPU where useful
- Map visualization library
- WebGL/Three.js overlays

## Backend

- Python
- FastAPI
- Pydantic
- NumPy
- OpenCV
- raster/geospatial tooling

## AI/ML

- PyTorch
- torchvision
- timm where appropriate
- PyTorch Geometric for GNNs
- snnTorch for SNN experiments

## Graph

- Neo4j
- Cypher
- GraphSAGE/GAT

## Data

- object storage
- PostgreSQL/PostGIS where appropriate
- metadata database
- cache such as Redis where needed

## Visualization

- Three.js
- WebGL/WebGPU
- interactive maps
- 2D/3D synchronized views

## Optional scientific computing

- JAX
- SciPy
- rasterio
- GDAL
- xarray

---

# 22. Suggested Repository Structure

```text
nexus-lunar/
|
├── apps/
│   ├── web/
│   └── api/
|
├── packages/
│   ├── registration/
│   ├── geospatial/
│   ├── matching/
│   ├── geometry/
│   ├── xai/
│   ├── graph/
│   ├── terrain/
│   ├── illumination/
│   ├── spectral/
│   ├── nexus/
│   └── digital_twin/
|
├── experiments/
│   ├── classical/
│   ├── illumination/
│   ├── scale/
│   ├── multimodal/
│   ├── gnn/
│   └── snn/
|
├── data/
│   ├── raw/
│   ├── metadata/
│   ├── footprints/
│   ├── patches/
│   └── processed/
|
├── configs/
|
├── evaluation/
│   ├── metrics/
│   ├── benchmarks/
│   └── reports/
|
├── docs/
│
└── README.md
```

---

# 23. Data Lineage

Every result should retain provenance.

Example:

```text
Source image ID
     |
Sensor
     |
Acquisition metadata
     |
Preprocessing version
     |
Registration method
     |
Model version
     |
Thresholds
     |
Transformation
     |
Inliers
     |
RMSE
     |
Confidence
     |
NEXUS-derived features
     |
Site recommendation
```

This makes the system reproducible and scientifically defensible.

---

# 24. NEXUS Site-Selection Logic

Do not allow an LLM to simply invent a site score.

Use measurable evidence.

Conceptually:

```text
Site Score =
f(
  terrain suitability,
  illumination suitability,
  hazard constraints,
  spectral/resource evidence,
  registration confidence,
  operational constraints
)
```

The exact weights should be configurable and experimentally justified.

Example explanation:

```text
SITE 07

Recommended because:

Terrain:
  favorable

Illumination:
  favorable

Hazard:
  moderate

Spectral evidence:
  available but uncertain

Registration confidence:
  high

Main limitation:
  incomplete temporal illumination coverage
```

---

# 25. Habitat Layer Philosophy

NEXUS should not claim:

> "This is the optimal real lunar habitat."

Instead say:

> "NEXUS generates a conceptual habitat configuration from observed spatial constraints and evaluates it against the available evidence."

This distinction is important.

The system can demonstrate:

- site selection
- habitat placement
- constraint checking
- conceptual geometry
- simulated scenarios
- explainable decisions

Detailed aerospace certification is outside the scope of an SIH prototype.

---

# 26. The Ultimate Agentic Loop

The long-term version of NEXUS can become:

```text
OBSERVE
   |
   v
UNDERSTAND
   |
   v
REGISTER
   |
   v
BUILD SPATIAL GRAPH
   |
   v
REASON
   |
   v
SELECT SITE
   |
   v
DESIGN HABITAT
   |
   v
SIMULATE
   |
   v
FIND FAILURE
   |
   v
REDESIGN
   |
   +---------------> REASON
```

The agent can decide which analysis to invoke, but scientific calculations should remain deterministic and auditable.

---

# 27. How to Present the Project to SIH Judges

Do not start with:

> "We built an autonomous lunar habitat AI using GNNs, SNNs, LLMs, agents and digital twins."

That sounds like a collection of technologies.

Start with the actual SIH problem.

## Presentation narrative

### Step 1 — Problem

> Lunar images from different missions do not always align because of illumination, viewpoint and scale differences.

### Step 2 — Core solution

> We build a geospatially aware, multimodal registration pipeline that first identifies the common lunar ground region and then performs correspondence and geometric verification.

### Step 3 — Evidence

Show:

```text
Source image
      |
      v
AI candidate matches
      |
      v
Verified matches
      |
      v
Registered image
      |
      v
RMSE / inliers / confidence
```

### Step 4 — Differentiator

Then say:

> "We do not stop at registration. The registered observations become a spatial knowledge layer."

Show the graph.

### Step 5 — NEXUS

Then demonstrate:

```text
registered terrain
       |
       v
terrain intelligence
       |
       v
illumination intelligence
       |
       v
spectral evidence
       |
       v
candidate site
       |
       v
habitat constraints
       |
       v
3D digital twin
```

### Step 6 — Vision

End with:

> "Our goal is to transform lunar observations from isolated images into a machine-readable spatial intelligence system that can support future planetary engineering."

---

# 28. Best Way to Present Yourself

Since you do not come from a formal space-science background, do not pretend to be a lunar scientist.

Position yourself as:

> **An AI/DS engineer building a scientifically grounded geospatial intelligence system for lunar exploration.**

Your strengths are:

- AI/ML
- computer vision
- multimodal learning
- graph intelligence
- agentic systems
- software engineering
- 3D visualization

Your approach to space science should be:

```text
Space science domain knowledge
            +
AI/ML engineering
            +
Geospatial computation
            +
Scientific validation
```

A strong statement:

> "I am not trying to replace domain scientists. I am building the computational infrastructure that allows heterogeneous lunar observations to be registered, connected, interpreted and used for downstream spatial reasoning."

That is a credible position.

---

# 29. What You Should Learn Before Building

## Lunar fundamentals

Learn:

- lunar coordinate systems
- latitude/longitude on the Moon
- lunar reference frames
- lunar orbit basics
- Sun illumination geometry
- solar azimuth/elevation
- lunar phases versus local illumination
- crater/ridge/mare terminology
- nadir/off-nadir viewing
- spatial resolution/GSD
- DEM
- orthorectification
- map projection
- sensor geometry

## Image registration

Learn:

- keypoints
- descriptors
- feature matching
- homography
- affine transformation
- RANSAC
- reprojection error
- RMSE
- tie points
- sub-pixel refinement
- image pyramids

## Geospatial

Learn:

- CRS
- georeferencing
- footprints
- spatial intersection
- raster/vector concepts
- GeoTIFF
- DEM
- spatial indexing

## AI

Learn:

- Siamese networks
- contrastive learning
- triplet loss
- metric learning
- retrieval
- hard negatives
- multimodal embeddings

## Graph AI

Learn:

- nodes
- edges
- graph embeddings
- message passing
- GCN
- GraphSAGE
- GAT

## XAI

Learn:

- feature attribution
- confidence
- uncertainty
- evidence tracing
- failure explanations

## SNN

Learn only after the main pipeline works:

- spikes
- membrane potential
- temporal encoding
- event-driven computation
- surrogate gradients

---

# 30. Priority Matrix

| Component | SIH importance | NEXUS importance | Priority |
|---|---:|---:|---:|
| Data ingestion | High | High | Must |
| Geographic overlap | Very High | High | Must |
| Classical registration | Very High | High | Must |
| Illumination robustness | Very High | High | Must |
| Scale robustness | Very High | High | Must |
| Multimodal AI | High | High | Must |
| Geometric verification | Very High | Very High | Must |
| XAI | High | Very High | Strong |
| Spatial knowledge graph | Medium | Very High | Strong |
| Terrain intelligence | Low | Very High | Strong |
| Illumination intelligence | Medium | Very High | Strong |
| IIRS spectral intelligence | Medium | High | Strong |
| GNN | Low | High | Advanced |
| SNN | Low | Medium | Research |
| Habitat planner | Low | Very High | Demo |
| 3D digital twin | Low | Very High | Demo |
| Autonomous redesign | Low | Very High | Future |

---

# 31. What Must Be Working for SIH

If time becomes limited, protect this chain:

```text
Real lunar data
     ↓
Correct overlap
     ↓
Registration
     ↓
Correspondence
     ↓
Geometric verification
     ↓
Metrics
```

Then add:

```text
XAI
 ↓
Spatial graph
 ↓
NEXUS
 ↓
3D habitat
```

Never sacrifice the scientific core just to add another AI model.

---

# 32. Minimum Viable Prototype

The minimum credible system is:

```text
OHRC/TMC-2/IIRS + LRO
        |
        v
Geographic overlap
        |
        v
Registration
        |
        v
Match points
        |
        v
RANSAC verification
        |
        v
RMSE + inliers + spatial coverage
        |
        v
Interactive visualization
```

A strong SIH prototype adds:

```text
        |
        v
Multimodal AI retrieval
        |
        v
XAI
        |
        v
Spatial knowledge graph
```

The full demonstration adds:

```text
        |
        v
NEXUS site intelligence
        |
        v
3D conceptual habitat
```

---

# 33. Final Project Identity

## Project name

**NEXUS-LUNAR**

### Suggested subtitle

**Geospatially Aware Multimodal Lunar Image Registration and Spatial Intelligence for Future Habitat Planning**

Alternative:

**NEXUS-LUNAR: From Lunar Image Registration to Explainable Spatial Intelligence**

---

# 34. One-Line Pitch

> **NEXUS-LUNAR registers heterogeneous lunar observations with geometrically verified correspondence, converts them into an explainable spatial knowledge system, and uses that evidence to support conceptual lunar habitat site planning.**

---

# 35. Final Demo Flow

The final demonstration should take approximately:

### 0:00–0:30 — Problem

Show two misaligned lunar observations.

### 0:30–1:30 — Registration

Show:

```text
source
reference
matches
RANSAC
registered result
```

### 1:30–2:00 — Metrics

Show:

```text
RMSE
inliers
inlier ratio
spatial coverage
confidence
```

### 2:00–2:45 — NEXUS

Show:

```text
registered region
       ↓
spatial graph
       ↓
terrain
illumination
spectral evidence
       ↓
candidate sites
```

### 2:45–3:30 — Habitat

Select a site and show:

```text
site
 ↓
constraints
 ↓
3D terrain
 ↓
conceptual habitat
```

### 3:30–4:00 — XAI

Ask:

> "Why did NEXUS choose this site?"

Show evidence.

### 4:00–4:30 — Vision

End with:

> "The SIH problem begins with image registration. NEXUS turns that registration into a foundation for spatial intelligence and future planetary engineering."

---

# 36. Final Architecture in One Diagram

```text
                    ┌───────────────────────────┐
                    │       LUNAR DATA          │
                    │ OHRC | TMC-2 | IIRS | LRO│
                    └─────────────┬─────────────┘
                                  |
                                  v
                    ┌───────────────────────────┐
                    │  GEO OVERLAP / PATCHING   │
                    └─────────────┬─────────────┘
                                  |
                                  v
                    ┌───────────────────────────┐
                    │   REGISTRATION ENGINE     │
                    │ SIFT | AI | MULTI-SCALE   │
                    └─────────────┬─────────────┘
                                  |
                                  v
                    ┌───────────────────────────┐
                    │ GEOMETRIC VERIFICATION    │
                    │ RANSAC | RMSE | INLIERS   │
                    └─────────────┬─────────────┘
                                  |
                                  v
                    ┌───────────────────────────┐
                    │       XAI + CONFIDENCE    │
                    └─────────────┬─────────────┘
                                  |
                                  v
                 ╔══════════════════════════════════╗
                 ║            NEXUS                  ║
                 ║                                  ║
                 ║  Spatial Knowledge Graph         ║
                 ║          |                       ║
                 ║   ┌──────┼────────┐              ║
                 ║   v      v        v              ║
                 ║ Terrain Illum. Spectral          ║
                 ║   |      |        |              ║
                 ║   └──────┼────────┘              ║
                 ║          v                       ║
                 ║    Site Intelligence             ║
                 ║          |                       ║
                 ║       XAI/GNN                    ║
                 ╚══════════╪═══════════════════════╝
                            |
                            v
                 ┌───────────────────────────┐
                 │ HABITAT CONSTRAINT ENGINE│
                 └─────────────┬─────────────┘
                               |
                               v
                 ┌───────────────────────────┐
                 │    3D DIGITAL TWIN        │
                 │ Terrain + Habitat + Data  │
                 └─────────────┬─────────────┘
                               |
                               v
                 ┌───────────────────────────┐
                 │ DESIGN → SIMULATE → TEST  │
                 │          → REDESIGN       │
                 └───────────────────────────┘
```

---

# 37. Final Recommendation

Build the project in this order:

1. **Make the real lunar data pipeline work.**
2. **Prove geographic overlap.**
3. **Build classical registration.**
4. **Solve illumination and scale robustness.**
5. **Add learned multimodal matching.**
6. **Use geometry to verify AI results.**
7. **Add XAI and uncertainty.**
8. **Convert observations into a spatial knowledge graph.**
9. **Add terrain, illumination and spectral intelligence.**
10. **Add GNN only where the graph/data justify it.**
11. **Add NEXUS site selection.**
12. **Build the 3D habitat digital twin.**
13. **Add SNN as a temporal research extension.**
14. **Finally add autonomous design/simulation/redesign.**

The central principle is:

> **Registration is the scientific foundation. NEXUS is the intelligence layer. The habitat digital twin is the demonstration of what that intelligence enables.**

This keeps the project directly relevant to SIH while giving it a much larger research and engineering trajectory.
