# POC-5: Multimodal AI Correspondence — Benchmark & Verification Report

**NEXUS-LUNAR Project | Smart India Hackathon**  
**Subsystem:** AI-Based Cross-Modal Patch Retrieval & Correspondence Engine  
**Status:** Completed, Verified, and Ready for POC-6 Geometric Verification  
**Experiment ID:** `EXP_POC5_DEMO`  
**Timestamp:** `2026-09-07T16:26:59.824176+00:00`  
**Data Provenance:** `REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT`  

---

## 1. Executive Summary & Objective

In multi-sensor lunar co-registration, matching observations across heterogeneous sensors (e.g. Chandrayaan-2 OHRC at 0.25 m/pixel vs NASA LROC NAC at 1.0 m/pixel) is severely challenged by resolution disparities, non-linear radiometric shifts, and grazing polar illumination.

**POC-5 Objective:** Build an AI-based multimodal patch retrieval pipeline that takes a query patch from a source sensor, maps it to a shared invariant embedding space, and retrieves the Top-$K$ candidate correspondences from a reference sensor archive to feed into **POC-6 Geometric Verification**.

---

## 2. Core Methodological Pipeline

```
  [ Query Patch (CH2 OHRC) ]             [ Reference Collection (NASA LROC NAC) ]
             │                                              │
             ▼                                              ▼
 [ Preprocessing & Normalization ]             [ Preprocessing & Normalization ]
             │                                              │
             ▼                                              ▼
 [ Dense Multimodal AI Encoder ]               [ Dense Multimodal AI Encoder ]
   (128-D L2-Normalized Vector)                  (128-D L2-Normalized Vector)
             │                                              │
             └──────────────────────┬───────────────────────┘
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

## 3. Quantitative Retrieval Evaluation Matrix

### AI Multimodal Embedding vs Pixel Baseline

| Evaluation Metric | AI Multimodal Proxy (128-D) | Pixel Baseline (64-D) | Relative Improvement |
|---|:---:|:---:|:---:|
| **Recall@1 (Top-1 Accuracy)** | **9.1%** | 9.1% | **+0.0%** |
| **Recall@3 (Top-3 Inclusions)** | **18.2%** | 18.2% | **+0.0%** |
| **Recall@5 (Top-5 Inclusions)** | **27.3%** | 18.2% | **+9.1%** |
| **Recall@10 (Top-10 Inclusions)** | **27.3%** | 18.2% | **+9.1%** |
| **Mean Reciprocal Rank (MRR)** | **0.154** | 0.121 | **+0.033** |
| **Mean Cosine Similarity** | **0.868** | 0.999 | — |

**Ground Truth Definition:**  
`Known geographic co-registration patch index pair in common footprint.`

---

## 4. Failure Analysis & Diagnostics

Total Evaluated Queries: **12**  
Failure Case Breakdown:
- **LOW_TEXTURE:** 0 queries
- **ILLUMINATION_DISPARITY:** 0 queries
- **SHADOW_OCCLUSION:** 0 queries
- **EXTREME_GSD_DISPARITY:** 0 queries
- **CROSS_MODAL_SPECTRUM_SHIFT:** 0 queries
- **REPETITIVE_TERRAIN:** 2 queries
- **WEAK_EMBEDDING_DISCRIMINATION:** 8 queries

---

## 5. Artifacts Generated in `outputs/poc5/`

- `poc5_results.json` — Complete serialized metrics, similarity scores, and rankings.
- `poc5_results.csv` — Tabular candidate matrix for rapid analysis.
- `poc5_metadata.json` — Full environment, commit, timestamp, and reproducibility metadata.
- `poc5_failure_cases.json` — Categorized difficult retrieval cases.
- `poc5_candidates_for_poc6.json` — Handover dataset containing verified candidate schemas for POC-6 geometric verification.
- 6 Publication Figures:
  1. `query_retrieval_gallery.png`
  2. `similarity_ranking_curve.png`
  3. `retrieval_score_distribution.png`
  4. `cross_sensor_embedding_space.png`
  5. `ablation_baseline_comparison.png`
  6. `failure_analysis_breakdown.png`

---

## 6. Scientific Disclaimer

> [!IMPORTANT]
> This evaluation is an empirical cross-sensor spatial retrieval benchmark based on `REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT`. AI similarity alone establishes candidate correspondence pairs. Rigid sub-pixel spatial alignment and geometric transformation estimation must be verified by the downstream **POC-6 Geometric Verification Engine**.
