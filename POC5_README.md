# POC-5: Multimodal AI Correspondence & Cross-Sensor Retrieval

**NEXUS-LUNAR Project | Smart India Hackathon**  
**Subsystem:** Core Data Pipeline & AI Cross-Modal Correspondence Engine  
**Status:** Completed, Fully Verified, Tested (63/63 Unit Tests Passing)

---

## 1. Overview & Research Objective

Cross-modal lunar observation matching involves pairing observations from heterogeneous orbital sensors:
- **Targeted High-Resolution Instruments:** Chandrayaan-2 OHRC (0.25 m/pixel)
- **Global Context Reconnaissance:** NASA LROC NAC (0.5–2.0 m/pixel)
- **Spectral / Context Triplet Cameras:** Chandrayaan-2 TMC-2 (5.0 m/pixel) and Chandrayaan-2 IIRS (infrared)

Due to severe resolution disparity ($4\times$ to $20\times$ GSD ratio), different sensor spectral response functions, and non-linear photometric shifts under grazing polar illumination, direct pixel matching fails.

**POC-5 Goal:** Build an AI-based feature embedding and cross-modal retrieval system that takes a query patch from one sensor and retrieves/ranks candidate corresponding patches from another sensor to feed directly into downstream **POC-6 Geometric Verification**.

```
  [ Query Patch (CH-2 OHRC) ]          [ Reference Collection (NASA LROC NAC) ]
               │                                           │
               ▼                                           ▼
   [ Preprocessing & Normalization ]           [ Preprocessing & Normalization ]
               │                                           │
               ▼                                           ▼
   [ Multimodal AI Dense Encoder ]             [ Multimodal AI Dense Encoder ]
     (128-D L2-Normalized Vector)                (128-D L2-Normalized Vector)
               │                                           │
               └───────────────────┬───────────────────────┘
                                   ▼
                   [ Cross-Modal Similarity Matrix ]
                                   ▼
                     [ Top-K Candidate Ranking ]
                                   ▼
                   [ Geographic Provenance Check ]
                                   ▼
                  [ Handover to POC-6 Verification ]
```

---

## 2. Scientific Integrity & Data Provenance

- **Data Provenance:** All experimental runs are tagged explicitly with their exact data basis:
  - `REAL SCIENTIFIC DATA` (for native PDS/ISSDC rasters)
  - `REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT` (for authentic lunar crater topography with synthetic cross-sensor transformations)
  - `SYNTHETIC OFFLINE DEMO` (for lightweight offline pipeline verification)
- **Ground Truth Integrity:**
  - For synthetic experiments, ground truth is defined by the known geographic pair association.
  - For uncalibrated real data without verified geographic ground truth, metrics strictly report `GROUND TRUTH UNAVAILABLE` ($NaN$) rather than fabricating performance claims.
- **Role Boundary:** AI similarity alone does **not** constitute proof of geometric registration. POC-5 produces candidate correspondence rankings; **POC-6** performs rigorous keypoint detection, homography, and RANSAC geometric verification.

---

## 3. Algorithmic Architecture

### Pluggable Multimodal Encoders (`poc5_models.py`)
- **`BaseMultimodalEncoder`**: Abstract base class defining `encode_image(...) -> np.ndarray` and `encode_patch(...) -> MultimodalPatchEmbedding`.
- **`DeterministicMultimodalProxyEncoder`**: 128-D dense descriptor combining 4-octave spatial gradient orientation histograms, illumination-invariant morphological moments, and orthogonal projection with L2 unit normalization.
- **`PixelBaselineEncoder`**: 64-D downsampled spatial intensity baseline for ablation benchmarking.
- **`PretrainedMultimodalEncoder`**: Pluggable wrapper for deep learning backbones (PyTorch/ViT/CLIP) when GPU/deep-learning libraries are present in the environment.

### Cross-Modal Retrieval Engine (`poc5_retrieval.py`)
- Calculates pairwise cosine similarity matrix:
  $$\text{Sim}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2} \in [-1.0, 1.0]$$
- Sorts and indexes the Top-$K$ candidates ($K = 1, 3, 5, 10$).
- Computes bounding box spatial relationships (`OVERLAPPING`, `NEARBY`, `DISJOINT`).

---

## 4. Handover Schema for POC-6 Geometric Verification

POC-5 exports a clean, standardized candidate dataset (`outputs/poc5/poc5_candidates_for_poc6.json`) consumable by POC-6:

```json
{
  "query_patch_id": "OHRC_PATCH_0001",
  "candidate_patch_id": "LROC_PATCH_0001",
  "query_sensor": "CH2_OHRC",
  "candidate_sensor": "LRO_NAC",
  "query_coordinates": {"lat": -73.25, "lon": 26.00},
  "candidate_coordinates": {"lat": -73.25, "lon": 26.00},
  "query_bbox": {"min_lat": -73.25, "max_lat": -73.23, "min_lon": 26.00, "max_lon": 26.02},
  "candidate_bbox": {"min_lat": -73.25, "max_lat": -73.23, "min_lon": 26.00, "max_lon": 26.02},
  "query_gsd": 0.25,
  "candidate_gsd": 1.00,
  "similarity_score": 0.925,
  "rank": 1,
  "embedding_model": "DeterministicMultimodalProxyEncoder",
  "embedding_dim": 128,
  "experiment_id": "EXP_POC5_DEMO",
  "ground_truth_status": "AVAILABLE",
  "is_ground_truth": true,
  "geographic_relation": "OVERLAPPING",
  "provenance": "REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT"
}
```

---

## 5. Summary of Experimental Results

### AI Multimodal Proxy vs Pixel Baseline Ablation

| Evaluation Metric | AI Multimodal Proxy (128-D) | Pixel Baseline (64-D) | Relative Gain |
|---|:---:|:---:|:---:|
| **Recall@1 (Top-1 Accuracy)** | **27.3%** | 9.1% | **+200.0%** |
| **Recall@3 (Top-3 Inclusions)** | **45.5%** | 18.2% | **+150.0%** |
| **Recall@5 (Top-5 Inclusions)** | **72.7%** | 18.2% | **+300.0%** |
| **Recall@10 (Top-10 Inclusions)** | **90.9%** | 18.2% | **+400.0%** |
| **Mean Reciprocal Rank (MRR)** | **0.432** | 0.121 | **+257.0%** |
| **Mean Cosine Similarity** | **0.868** | 0.999 | (Discriminative margin) |

---

## 6. Generated Visualizations & Artifacts

All outputs are saved to `outputs/poc5/`:
1. `query_retrieval_gallery.png` — Query patch alongside Top-4 retrieved candidate patches with true-match highlighting.
2. `similarity_ranking_curve.png` — Top-K candidate similarity decay gradients.
3. `retrieval_score_distribution.png` — Distribution of true positive matches vs negative distractors.
4. `cross_sensor_embedding_space.png` — 2D PCA projection of cross-sensor latent embeddings.
5. `ablation_baseline_comparison.png` — Bar chart comparing AI Multimodal Embedding vs Pixel Baseline across Recall@K.
6. `failure_analysis_breakdown.png` — Categorized breakdown of challenging retrieval queries.
7. `poc5_results.json` & `poc5_results.csv` — Full machine-readable metrics and candidate tables.
8. `poc5_metadata.json` — Reproducibility, platform, and seed metadata.
9. `poc5_failure_cases.json` — Diagnostic log of failed queries.
10. `poc5_candidates_for_poc6.json` — Standardized handover dataset for POC-6.

---

## 7. How to Run & Verify

### 1. Run Offline Demo
```bash
python scripts/demo_poc5.py
```

### 2. Run Comprehensive Unit Tests
```bash
python -m pytest tests/ -v
```
*Executes all 63 unit tests across POC-2, POC-4, and POC-5 with 100% pass rate.*

### 3. Launch Web Dashboard Studio
```bash
python scripts/launch_dashboard.py --port 8000
```
- Open `http://localhost:8000/#poc5`
- Click **`[ RUN POC-5 RETRIEVAL ]`** to trigger live cross-modal candidate retrieval.
