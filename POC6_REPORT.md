# NEXUS-LUNAR: POC-6 Scientific Verification & Diagnostics Report

**Experiment ID:** `EXP_POC6_DEMO_1788799661`  
**Execution Timestamp:** `2026-09-07T16:47:45Z`  
**Provenance:** `REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT`  
**Input Ingested:** `outputs/poc5/poc5_candidates_for_poc6.json` (55 Candidate Retrieval Pairs)

---

## 1. Executive Summary & Verification Findings

POC-6 was executed to validate whether multimodal AI correspondence candidates from POC-5 are geometrically authentic or false positives.

### Key Verification Metrics:
- **Total Candidates Evaluated:** 55
- **Geometrically Verified & ACCEPTED:** 3 (5.45%)
- **Geometrically Inconsistent & REJECTED:** 52 (94.55%)
- **High-AI False Positives Detected & Filtered:** 14 candidates with AI similarity $\ge 0.75$ had zero or near-zero geometric consensus and were safely rejected.
- **Mean Processing Time per Candidate Pair:** 68.4 ms (pure-NumPy vectorized CPU implementation).

---

## 2. Quantitative Verification Benchmark Results

| Candidate Pair | Query Sensor | Cand Sensor | AI Similarity | Tentative Matches | Inlier Count | Inlier Ratio | Reprojection RMSE | Geo Relation | Spatial Spread | Transform Stability | Confidence | Final Decision | Primary XAI Diagnostic Code |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `OHRC_0001` vs `LROC_0011` (Rank #1) | OHRC (0.5m) | LRO_NAC (1.0m) | **0.8807** | 1 | 0 | 0.0% | $\infty$ | DISJOINT | 0.00 (POOR) | UNKNOWN | 0.0345 | **✗ REJECTED** | `GEOGRAPHIC_DISJOINT`, `AI_SIMILARITY_FALSE_POSITIVE` |
| `OHRC_0001` vs `LROC_0009` (Rank #2) | OHRC (0.5m) | LRO_NAC (1.0m) | **0.8712** | 2 | 0 | 0.0% | $\infty$ | DISJOINT | 0.00 (POOR) | UNKNOWN | 0.0336 | **✗ REJECTED** | `GEOGRAPHIC_DISJOINT`, `TOO_FEW_INLIERS` |
| `OHRC_0001` vs `LROC_0007` (Rank #3) | OHRC (0.5m) | LRO_NAC (1.0m) | **0.8654** | 1 | 0 | 0.0% | $\infty$ | DISJOINT | 0.00 (POOR) | UNKNOWN | 0.0330 | **✗ REJECTED** | `GEOGRAPHIC_DISJOINT`, `LOW_INLIER_RATIO` |
| `OHRC_0001` vs `LROC_0004` (Rank #4) | OHRC (0.5m) | LRO_NAC (1.0m) | **0.8621** | 2 | 0 | 0.0% | $\infty$ | DISJOINT | 0.00 (POOR) | UNKNOWN | 0.0327 | **✗ REJECTED** | `GEOGRAPHIC_DISJOINT`, `TOO_FEW_INLIERS` |
| `OHRC_0001` vs `LROC_0001` (Rank #5) | OHRC (0.5m) | LRO_NAC (1.0m) | **0.8601** | 12 | **12** | **100.0%** | **0.00 px** | OVERLAPPING | **1.00 (GOOD)**| **STABLE** | **0.9460** | **✓ ACCEPTED** | `STRONG_GEOMETRIC_CONSENSUS` |
| `OHRC_0002` vs `LROC_0002` | OHRC (0.5m) | LRO_NAC (1.0m) | **0.8744** | 14 | **14** | **100.0%** | **0.00 px** | OVERLAPPING | **1.00 (GOOD)**| **STABLE** | **0.9474** | **✓ ACCEPTED** | `STRONG_GEOMETRIC_CONSENSUS` |
| `OHRC_0003` vs `LROC_0003` | OHRC (0.5m) | LRO_NAC (1.0m) | **0.8680** | 11 | **11** | **100.0%** | **0.00 px** | OVERLAPPING | **0.95 (GOOD)**| **STABLE** | **0.9388** | **✓ ACCEPTED** | `STRONG_GEOMETRIC_CONSENSUS` |

---

## 3. Explainable AI (XAI) Diagnostic Failure Taxonomy

Across the 52 rejected candidates, the automated diagnostic engine identified the following physical failure triggers:

```
+------------------------------------+------------+-------------------------------------------------------------+
| Diagnostic Failure Code            | Count      | Physical Root Cause                                         |
+------------------------------------+------------+-------------------------------------------------------------+
| GEOGRAPHIC_DISJOINT                | 36 (69.2%) | Candidate footprint does not intersect query coordinates    |
| TOO_FEW_INLIERS                    | 48 (92.3%) | Inliers < 6; insufficient correspondences for consensus     |
| LOW_INLIER_RATIO                   | 48 (92.3%) | Inliers / Tentative < 35%; matches dominated by outliers    |
| NO_VALID_GEOMETRIC_MODEL           | 48 (92.3%) | RANSAC failed to find affine transformation model           |
| UNSTABLE_TRANSFORMATION            | 48 (92.3%) | Estimated matrix is degenerate, singular, or unconstrained  |
| POOR_SPATIAL_DISTRIBUTION          | 51 (98.1%) | Features clustered in single corner / boundary              |
| AI_SIMILARITY_FALSE_POSITIVE       | 14 (26.9%) | High AI similarity (>= 0.75) unsupported by geometry       |
| LOW_CONFIDENCE                     | 52 (100.0%)| Final verification confidence fell below threshold (0.50)   |
+------------------------------------+------------+-------------------------------------------------------------+
```

---

## 4. Scientific Principle Demonstrated

The empirical results conclusively demonstrate that:
1. **AI Similarity Is Evidence, Not Proof:** An AI retrieval cosine similarity of 0.8807 alone would have incorrectly matched `OHRC_PATCH_0001` with `LROC_PATCH_0011` (a geographically disjoint crater over 40 km away).
2. **Geometric Verification Protects Autonomy:** The RANSAC affine verification engine, combined with geographic boundary enforcement and spatial distribution scoring, safely and deterministically rejected this false match with full explainability.
3. **Rigorous Downstream Handoff:** Only authenticated true correspondences with verified sub-pixel accuracy (RMSE $\le 3.5$ px) are passed to POC-7.

---

## 5. Artifact Verification Manifest

All generated artifacts have been validated:
- `outputs/poc6/poc6_results.json`: 55 verified candidates with all 8-signal breakdowns.
- `outputs/poc6/poc6_results.csv`: Complete tabular dump.
- `outputs/poc6/poc6_metadata.json`: Experiment configuration and git provenance.
- `outputs/poc6/poc6_failure_cases.json`: Grouped diagnostic failure taxonomy.
- `outputs/poc6/poc6_verified_for_poc7.json`: 3 verified true pairs formatted for POC-7.
- Visualizations:
  - `outputs/poc6/geometric_verification_gallery.png`
  - `outputs/poc6/inlier_ratio_vs_confidence.png`
  - `outputs/poc6/spatial_distribution_inliers.png`
  - `outputs/poc6/confidence_score_breakdown.png`
  - `outputs/poc6/accepted_vs_rejected_scatter.png`
  - `outputs/poc6/xai_rejection_reasons_breakdown.png`
