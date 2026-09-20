🌕 NEXUS-LUNAR
==============

Lunar Data Ingestion, Spatial Co-Registration & Science-Informed Intelligence Platform
--------------------------------------------------------------------------------------

**NEXUS-LUNAR** is a modular lunar intelligence platform designed to acquire, ingest, catalog, spatially align, and analyze multi-mission lunar observations from **ISRO Chandrayaan-2, NASA LRO, and JAXA SELENE/Kaguya**.

The platform combines high-resolution imagery, hyperspectral observations, spatial metadata, and science-informed analysis into a unified workflow for **lunar mapping, multi-sensor comparison, terrain analysis, spectral interpretation, and environmental suitability assessment**.

---

🚀 Key Capabilities
-------------------

🛰️ Multi-Mission Data Acquisition
---------------------------------

Supports lunar observations from:

| Mission                 | Instrument       | Approx. Resolution | Data Type               |
| ----------------------- | ---------------- | -----------------: | ----------------------- |
| 🇮🇳 Chandrayaan-2      | OHRC             |             0.25 m | High-resolution imagery |
| 🇮🇳 Chandrayaan-2      | TMC-2            |                5 m | Terrain / imaging       |
| 🇮🇳 Chandrayaan-2      | IIRS             |               80 m | Hyperspectral           |
| 🇺🇸 NASA LRO           | NAC              |              0.5 m | High-resolution imagery |
| 🇯🇵 JAXA SELENE/Kaguya | Terrain Camera   |               10 m | Terrain imaging         |
| 🇯🇵 JAXA SELENE/Kaguya | Multiband Imager |                  — | Multispectral imaging   |

---

🧠 Platform Architecture
------------------------

```text
                    NEXUS-LUNAR
                         │
                         ▼
              Multi-Mission Data Sources
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   Chandrayaan-2      NASA LRO       JAXA SELENE
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                Data Ingestion Layer
                         │
                         ▼
              Metadata Extraction
                         │
                         ▼
                 Spatial Catalog
                         │
                         ▼
             Geographic Overlap Engine
                         │
                         ▼
        Resolution-Aware Patch Extraction
                         │
                         ▼
          Science Intelligence Layer
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     Physics         Chemistry      Habitability
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                 Evidence Fusion
                         │
                         ▼
            Confidence + Provenance
                         │
                         ▼
              Lunar Intelligence UI
```

---

📌 Project Phases
-----------------

Phase 1 — Multi-Sensor Lunar Data Pipeline
------------------------------------------

The first phase focuses on reliable acquisition and spatial processing of heterogeneous lunar observations.

Core capabilities
-----------------

* Multi-mission data ingestion
* PDS/PDS4 metadata parsing
* Spatial footprint extraction
* Geographic overlap detection
* Resolution-aware image matching
* Co-registered patch generation
* Spatial catalog indexing

---

Phase 2 — Science-Informed Lunar Intelligence
---------------------------------------------

The second phase extends the data pipeline with science-informed analysis.

🔭 Physics
----------

Potential analyses include:

* Solar illumination
* Solar geometry
* Shadow estimation
* Terrain characteristics
* Slope and aspect
* Terrain roughness
* Model-derived thermal estimates

Results are clearly identified as **observed, derived, or model-derived**.

---

🧪 Chemistry / Spectral Science
-------------------------------

Where suitable spectral observations are available, particularly from instruments such as **Chandrayaan-2 IIRS**, the platform can support:

* Spectral preprocessing
* Spectral feature extraction
* Band analysis
* Candidate material signatures
* Spectral anomaly detection
* Confidence-aware interpretation

The system does **not** claim confirmed mineral composition without appropriate supporting spectral evidence.

---

🧬 Habitability & Biological Experiment Support
-----------------------------------------------

The platform does not perform biological life detection.

Instead, this module evaluates whether available environmental evidence may be relevant to future biological experiments.

Possible factors include:

* Water/ice evidence
* Thermal conditions
* Radiation data availability
* Illumination
* Terrain accessibility
* Environmental constraints
* Experimental requirement matching

When required evidence is unavailable, the system explicitly reports:

```text
INSUFFICIENT_DATA
```

---

🛰️ Supported Data Sources
-------------------------

Chandrayaan-2
-------------

Data can be obtained from the **ISRO ISSDC PRADAN** ecosystem.

Supported instruments include:

* OHRC
* TMC-2
* IIRS

The ingestion pipeline supports downloaded bundles containing:

* ZIP archives
* TAR archives
* PDS4 XML labels
* Image products

Metadata such as the following can be extracted where available:

* Geographic coordinates
* Observation geometry
* Spatial resolution
* Solar incidence angle
* Solar azimuth
* Phase angle
* Instrument metadata

---

NASA LRO
--------

The platform supports **Lunar Reconnaissance Orbiter Narrow Angle Camera (LRO NAC)** observations through NASA planetary data services and the LROC archive.

The download pipeline can search observations using:

* Bounding boxes
* Product IDs
* Geographic regions
* Sensor type

---

JAXA SELENE / Kaguya
--------------------

Reference datasets can include:

* Terrain Camera (TC)
* Multiband Imager (MI)

These observations can be incorporated into the common catalog and spatial-analysis workflow.

---

🛠️ Installation
----------------

Clone the repository:

```bash
git clone https://github.com/907-bot/lunar-nexus.git
cd lunar-nexus
```

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Recommended Python version:

```text
Python 3.10+
```

---

🖥️ Launch the Dashboard
-----------------------

Start the interactive Lunar Intelligence Dashboard:

```bash
python scripts/launch_dashboard.py
```

Then open:

```text
http://localhost:8000
```

The dashboard provides access to:

* Lunar GIS footprint visualization
* Observation catalog
* Sensor information
* Spatial overlap analysis
* POC 2 Patch Studio
* Science Intelligence capabilities

---

⚡ Quick Start
--------------

Generate Benchmark Dataset
--------------------------

Generate a benchmark dataset for multi-sensor processing:

```bash
python scripts/download_lunar_data.py --benchmark
```

The benchmark workflow can include observations from:

* Chandrayaan-2 OHRC
* LRO NAC
* TMC-2

for the configured lunar study region.

---

🛰️ NASA LRO NAC Downloads
-------------------------

Search by Geographic Region
---------------------------

Example:

```bash
python3 scripts/download_lunar_data.py \
  --sensor LRO_NAC \
  --min-lat -85.0 \
  --max-lat -80.0 \
  --min-lon 0.0 \
  --max-lon 30.0 \
  --limit 5
```

Download a Specific Product
---------------------------

```bash
python3 scripts/download_lunar_data.py \
  --sensor LRO_NAC \
  --product-id M1144485705LR
```

---

🇮🇳 Chandrayaan-2 ISSDC Ingestion
--------------------------------

After downloading a Chandrayaan-2 data bundle from ISSDC PRADAN, ingest it using:

```bash
python3 scripts/ingest_issdc.py \
  --input /path/to/downloaded_ch2_bundle.zip
```

A directory containing PDS4 products can also be processed:

```bash
python3 scripts/ingest_issdc.py \
  --input /path/to/ch2_raw_folder/
```

The ingestion pipeline performs:

1. Archive extraction
2. PDS4 XML parsing
3. Observation metadata extraction
4. Geographic footprint extraction
5. Resolution extraction
6. Solar geometry extraction where available
7. Catalog registration

---

🗂️ Catalog Search
-----------------

List Indexed Observations
-------------------------

```bash
python3 scripts/query_catalog.py --list
```

Find Overlapping Observations
-----------------------------

Example:

```bash
python3 scripts/query_catalog.py \
  --find-pairs \
  --source OHRC \
  --reference LRO_NAC \
  --min-overlap 5.0
```

Search Using a Bounding Box
---------------------------

```bash
python3 scripts/query_catalog.py \
  --min-lat -75 \
  --max-lat -70 \
  --min-lon 20 \
  --max-lon 35
```

---

🗺️ POC 2 — Geographic Overlap & Resolution-Aware Patch Extraction
------------------------------------------------------------------

POC 2 identifies geographically overlapping observations and generates spatially aligned image patches.

Extract All Overlapping Pairs
-----------------------------

```bash
python scripts/extract_overlap_patches.py \
  --all-pairs \
  --patch-size 512 \
  --stride 256
```

Extract a Specific Observation Pair
-----------------------------------

```bash
python scripts/extract_overlap_patches.py \
  --source-id ch2_ohr_ncp_20230915t041230_boguslawsky_d18 \
  --reference-id M1345982701LR_BOGUSLAWSKY_REF \
  --patch-size 256 \
  --stride 128 \
  --strategy match_coarser
```

Generated Output
----------------

The pipeline produces paired patches such as:

```text
patch_0001_src.png
patch_0001_ref.png
```

and a metadata file:

```text
patch_manifest.json
```

The manifest can contain:

* Ground coordinates
* Source resolution
* Reference resolution
* Overlap percentage
* Patch dimensions
* Matching strategy
* Confidence information

---

🔬 Science Intelligence
-----------------------

The Science Intelligence layer operates on available observations and metadata.

Physics Pipeline
----------------

```text
Observation
     │
     ▼
Geometry Validation
     │
     ▼
Solar / Illumination Analysis
     │
     ├── Shadow Analysis
     ├── Terrain Analysis
     └── Thermal Estimation
```

---

Chemistry Pipeline
------------------

```text
Spectral Observation
        │
        ▼
Spectral Validation
        │
        ▼
Preprocessing
        │
        ▼
Feature Extraction
        │
        ▼
Candidate Signature Analysis
        │
        ▼
Confidence + Provenance
```

Chemistry analysis requires appropriate spectral information.

If the necessary spectral data is unavailable:

```text
INSUFFICIENT_DATA
```

---

Habitability Pipeline
---------------------

```text
Environmental Evidence
        │
        ├── Water / Ice
        ├── Thermal Conditions
        ├── Radiation
        ├── Illumination
        └── Terrain
                │
                ▼
       Requirement Matching
                │
                ▼
       Experiment Suitability
```

This represents **environmental suitability analysis**, not biological life detection.

---

🔗 Evidence Fusion
------------------

The fusion layer combines available science outputs while preserving their individual confidence and provenance.

```text
Physics
   │
   ├──────────────┐
   ▼              │
Chemistry         │
   │              ▼
   └────────► Evidence Fusion
                  │
                  ▼
        Confidence + Provenance
                  │
                  ▼
          Science Intelligence
```

Missing evidence is explicitly preserved rather than replaced with fabricated values.

---

📊 Data Provenance
------------------

Science results should identify where the information originated.

Example:

```json
{
  "source": "Chandrayaan-2 IIRS",
  "dataset_id": "example_dataset",
  "observation_id": "example_observation",
  "processing_method": "spectral_feature_analysis",
  "derived": true
}
```

The platform distinguishes between:

```text
OBSERVED
DERIVED
MODEL_DERIVED
ASSUMED
SYNTHETIC
INSUFFICIENT_DATA
```

This prevents synthetic or model-generated results from being confused with direct observations.

---

📁 Project Structure
--------------------

```text
NEXUS-LUNAR/
│
├── packages/
│   └── data_pipeline/
│       ├── __init__.py
│       ├── models.py
│       ├── pds_ode_client.py
│       ├── issdc_client.py
│       ├── metadata_parser.py
│       ├── catalog.py
│       └── sample_benchmark.py
│
├── scripts/
│   ├── download_lunar_data.py
│   ├── ingest_issdc.py
│   ├── query_catalog.py
│   ├── extract_overlap_patches.py
│   └── launch_dashboard.py
│
├── data/
│   ├── raw/
│   │   ├── ohrc/
│   │   ├── tmc2/
│   │   ├── iirs/
│   │   └── lro/
│   │
│   ├── processed/
│   └── catalog.json
│
├── tests/
│
├── requirements.txt
└── README.md
```

The repository may evolve as additional science modules and POCs are integrated.

---

🧩 Core Components
------------------

| Component                    | Responsibility                        |
| ---------------------------- | ------------------------------------- |
| `pds_ode_client.py`          | NASA ODE data discovery and download  |
| `issdc_client.py`            | Chandrayaan-2 ISSDC ingestion         |
| `metadata_parser.py`         | Metadata extraction and normalization |
| `catalog.py`                 | Spatial indexing and overlap analysis |
| `download_lunar_data.py`     | Multi-sensor acquisition CLI          |
| `ingest_issdc.py`            | Chandrayaan-2 ingestion CLI           |
| `query_catalog.py`           | Catalog and overlap queries           |
| `extract_overlap_patches.py` | Spatial patch extraction              |
| `launch_dashboard.py`        | Web dashboard launcher                |

---

🧪 Testing
----------

Run the complete test suite:

```bash
pytest tests/
```

When science modules are present, their dedicated tests can also be run with:

```bash
pytest tests/science/
```

The project should maintain regression coverage so that new science functionality does not break existing data-ingestion and POC workflows.

---

⚠️ Scientific Limitations
-------------------------

NEXUS-LUNAR is designed to provide **data-driven and science-informed analysis**.

The platform must not:

* fabricate lunar observations
* present estimated temperatures as measurements
* claim confirmed mineral composition without supporting spectral evidence
* claim confirmed water/ice without appropriate source evidence
* fabricate radiation measurements
* claim biological life detection
* present synthetic demonstration data as real observations

When required information is unavailable, the appropriate result is:

```text
INSUFFICIENT_DATA
```

Model-derived outputs should be clearly labelled as estimates.

---

🎯 Use Cases
------------

NEXUS-LUNAR can support:

* Lunar surface mapping
* Multi-mission image comparison
* Lunar South Pole studies
* Multi-resolution image co-registration
* Hyperspectral exploration
* Candidate material analysis
* Terrain characterization
* Illumination and shadow studies
* Lunar resource research
* Environmental suitability analysis
* Future lunar science and exploration missions
* AI/ML dataset generation

---

🌕 Vision
---------

NEXUS-LUNAR aims to evolve from a **multi-mission lunar data pipeline** into an integrated **Lunar Science Intelligence Platform**.

The long-term vision is:

```text
Multi-Mission Lunar Data
          ↓
Unified Spatial Catalog
          ↓
Co-Registered Observations
          ↓
Physics + Spectral Science
          ↓
Environmental / Habitability Analysis
          ↓
Evidence Fusion
          ↓
Lunar Science Intelligence
```

The goal is to make heterogeneous lunar observations easier to **discover, compare, analyze, and interpret** while maintaining clear scientific provenance and uncertainty.

---

📜 License
----------

Add the project's applicable license here.

---

👥 Project
----------

**NEXUS-LUNAR**

A science-informed lunar data and intelligence platform integrating observations from **ISRO, NASA, and JAXA missions**.

---

⭐ If you find this project useful, consider starring the repository.
