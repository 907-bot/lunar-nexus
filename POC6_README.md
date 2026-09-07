# NEXUS-LUNAR: POC-6 — Geometric Verification & Explainable AI (XAI)

> **Objective:** Prevent an AI similarity score from being treated as proof of a correct lunar correspondence.  
> **Core Principle:** *"AI similarity is candidate evidence, not proof."*

---

## 1. Executive Summary

In high-latitude lunar terrain and South Pole exploration (e.g. Chandrayaan-2 OHRC, NASA LRO NAC, Chandrayaan-2 TMC-2), severe low solar elevation angles create deep polar shadows, extreme lighting disparities, and repetitive crater geomorphology. Under such conditions, deep multimodal AI retrieval models (such as those developed in POC-5) can assign high cosine similarity scores to visually similar craters that are physically unrelated, geographically disjoint, or unalignable.

**POC-6 establishes rigid geometric verification and transparent Explainable AI (XAI)**:
1. It ingests Top-K candidate pairs directly from POC-5 retrieval outputs (`outputs/poc5/poc5_candidates_for_poc6.json`).
2. It detects sub-pixel feature keypoints and generates 128-D spatial orientation descriptors.
3. It performs bidirectional Lowe's ratio test matching.
4. It estimates a 2D affine transformation matrix via RANSAC with least-squares consensus refinement.
5. It computes quantitative inlier metrics: tentative match count, consensus inlier count, inlier ratio, and reprojection Root Mean Squared Error (RMSE).
6. It evaluates **spatial distribution quality** ($4 \times 4$ grid occupancy and bounding hull spread) to ensure inliers are not clustered on a single tiny crater edge.
7. It integrates **geographic overlap constraints** and **sensor GSD compatibility**. Geographically `DISJOINT` pairs receive an immediate severe penalty and are filtered out.
8. It computes a transparent, documented **Verification Confidence Score** combining 8 weighted signals.
9. It applies a deterministic **ACCEPT / REJECT** policy.
10. It generates human- and machine-interpretable **Explainable AI (XAI)** diagnostics answering:
    - **"Why was this match accepted?"**
    - **"Why was this match rejected?"**
11. It serializes verified correspondences and transformation matrices into `outputs/poc6/poc6_verified_for_poc7.json` for downstream **POC-7** relative pose and 3D surface reconstruction.

---

## 2. Architecture & Verification Pipeline

```
              outputs/poc5/poc5_candidates_for_poc6.json
                                 |
                                 v
               [ Candidate Ingestion & Schema Check ]
                                 |
                                 v
               [ Patch Retrieval / Deterministic Loader ]
                                 |
                                 v
               [ Classical Feature Extraction & Matching ]
             (Harris Corner Detector + 128D Descriptors +
                  Lowe's Ratio Test Cross-Checking)
                                 |
                                 v
               [ RANSAC Geometric Verification Engine ]
             (Affine Model Estimation + Inlier Consensus +
                  Overdetermined Least-Squares Refinement)
                                 |
                                 v
        +------------------------+------------------------+
        |                        |                        |
        v                        v                        v
 [ Inlier Metrics ]     [ Spatial Spread ]     [ Transformation ]
 - Inlier Count         - Grid Occupancy (4x4)  - Determinant check
 - Inlier Ratio         - Bounding Area Ratio   - Residual stability
 - Reprojection RMSE    - Status (GOOD / POOR)  - Condition number
        |                        |                        |
        +------------------------+------------------------+
                                 |
                                 v
           [ Geographic Overlap & Sensor Compatibility ]
           (OVERLAPPING / NEARBY / DISJOINT / UNKNOWN)
           (Sensor GSD ratio disparity evaluation)
                                 |
                                 v
           [ Multi-Signal Verification Confidence Score ]
       Conf = w_ai*S_ai + w_inl*S_inl + w_ratio*S_ratio +
              w_rmse*S_rmse + w_geo*S_geo + w_dist*S_dist +
              w_stab*S_stab + w_sensor*S_sensor
                                 |
                                 v
           [ Deterministic ACCEPT / REJECT Decision Policy ]
           (Thresholds: min_inliers, min_ratio, max_rmse,
                min_confidence, disallow DISJOINT)
                                 |
                                 v
           [ Explainable AI (XAI) Diagnostic Engine ]
           - Accepted: Positive evidence verification checklist
           - Rejected: Structured diagnostic failure codes & messages
                                 |
        +------------------------+------------------------+
        |                        |                        |
        v                        v                        v
 [ Visualizations ]      [ JSON/CSV Outputs ]     [ POC-7 Handover ]
 - 6 PNG figures        - poc6_results.json       - poc6_verified_
 - Inlier match lines   - poc6_results.csv          for_poc7.json
 - XAI breakdowns       - poc6_failure_cases.json
                        - poc6_metadata.json
```

---

## 3. Mathematical & Algorithmic Foundations

### A. Feature Extraction & Tentative Matching
- **Detector:** Pure-NumPy multi-scale Harris Corner detection incorporating shadow-aware downweighting.
- **Descriptors:** 128-dimensional spatial gradient orientation descriptors computed on normalized local patches.
- **Matcher:** Vectorized pairwise Euclidean distance matrix with Lowe's ratio test ($d_1 / d_2 \le 0.75$) and bidirectional cross-check filtering.

### B. RANSAC Affine Geometric Verification
- **Transformation Model:** 2D Affine Transformation ($2 \times 3$ matrix $M = [A \mid t]$):
  $$\begin{bmatrix} x_{ref} \\ y_{ref} \end{bmatrix} = \begin{bmatrix} a_{11} & a_{12} \\ a_{21} & a_{22} \end{bmatrix} \begin{bmatrix} x_{src} \\ y_{src} \end{bmatrix} + \begin{bmatrix} t_x \\ t_y \end{bmatrix}$$
- **Minimal Sample:** 3 correspondences (yielding 6 linear equations).
- **Consensus Threshold:** Inlier distance $\le 4.0$ pixels.
- **Refinement:** Global least-squares solution $\mathbf{M} = (\mathbf{A}^T \mathbf{A})^{-1} \mathbf{A}^T \mathbf{b}$ computed on all inlier points.
- **Inlier Ratio:**
  $$\text{Inlier Ratio} = \frac{N_{inliers}}{\max(1, N_{tentative})}$$
- **Reprojection RMSE:**
  $$\text{RMSE} = \sqrt{\frac{1}{N_{inliers}} \sum_{i=1}^{N_{inliers}} \| M p_i^{src} - p_i^{ref} \|^2}$$

### C. Spatial Distribution Quality Metric
A match with inliers clustered tightly in one corner (e.g. along a single high-contrast shadow edge) cannot be trusted as global alignment.
1. **Bounding Area Ratio:**
   $$\text{Area Ratio} = \frac{(x_{max}^{inl} - x_{min}^{inl})(y_{max}^{inl} - y_{min}^{inl})}{W \cdot H}$$
2. **Grid Occupancy (4x4 cells):**
   The patch is partitioned into 16 equal spatial bins ($4 \times 4$ grid). We count the number of cells containing $\ge 1$ consensus inlier point.
3. **Spatial Distribution Score:**
   $$S_{dist} = 0.5 \cdot \min\left(1.0, \frac{\text{Area Ratio}}{0.20}\right) + 0.5 \cdot \min\left(1.0, \frac{\text{Occupied Cells}}{4.0}\right)$$
4. **Status:** `GOOD` if $S_{dist} \ge 0.35$ and $\text{Occupied Cells} \ge 3$; else `POOR`.

### D. Transformation Stability Analysis
To ensure physical plausibility and detect numerical collapse:
1. $\det(A) = a_{11} a_{22} - a_{12} a_{21} > 0.05$ (must be positive to prevent inverted reflection).
2. Singular values of $A$: $\sigma_{min} \ge 0.15$ and $\sigma_{max} \le 8.0$ (consistent with lunar orbital camera scaling and rotation).
3. Condition number $\kappa(A) = \sigma_{max} / \sigma_{min} \le 8.0$ (prevents 1D dimensional collapse).
4. Residual RMSE $\le 4.0$ px and inlier count $\ge 6$.
- **Status:** `STABLE` if all criteria pass, `UNSTABLE` if distorted, `UNKNOWN` if $< 3$ inliers.

### E. Geographic Overlap & Sensor Compatibility
- **Geographic Relation:** Directly ingested from POC-5 candidate metadata (`OVERLAPPING`, `NEARBY`, `DISJOINT`, `UNKNOWN`).
  - Score $S_{geo}$: `OVERLAPPING` = 1.0, `NEARBY` = 0.5, `UNKNOWN` = 0.3, `DISJOINT` = 0.0.
  - **Critical Rule:** If `DISJOINT`, candidate confidence is dampened by $0.25\times$ and candidate is rejected by default.
- **Sensor Resolution Compatibility:**
  - Evaluates GSD ratio: $\rho = \max(GSD_{src}, GSD_{ref}) / \min(GSD_{src}, GSD_{ref})$.
  - $\rho \le 4.0$: `GOOD` ($S_{sensor} = 1.0$)
  - $4.0 < \rho \le 8.0$: `MODERATE` ($S_{sensor} = 0.7$)
  - $\rho > 8.0$: `LOW` ($S_{sensor} = 0.3$)

---

## 4. Transparent Verification Confidence Score

Verification confidence is a transparent linear combination of 8 normalized signals (weights sum to $1.00$):

$$\text{Confidence} = \sum_{i=1}^{8} w_i S_i$$

| Signal | Component | Weight | Normalized Score Calculation |
| :--- | :--- | :--- | :--- |
| $S_{ai}$ | AI Retrieval Match | **0.10** | $\text{similarity\_score}$ (POC-5 cosine similarity) |
| $S_{inl}$ | Geometric Inlier Count | **0.20** | $\min(1.0, N_{inliers} / 15.0)$ |
| $S_{ratio}$ | Inlier Ratio | **0.20** | $N_{inliers} / \max(1, N_{tentative})$ |
| $S_{rmse}$ | Reprojection Error | **0.15** | $\max(0.0, 1.0 - \text{RMSE} / 5.0)$ |
| $S_{geo}$ | Geographic Overlap | **0.15** | `OVERLAPPING`: 1.0, `NEARBY`: 0.5, `DISJOINT`: 0.0 |
| $S_{dist}$ | Spatial Inlier Spread | **0.10** | Spatial distribution score $\in [0, 1]$ |
| $S_{stab}$ | Transform Stability | **0.05** | `STABLE`: 1.0, `UNSTABLE`: 0.4, `UNKNOWN`: 0.0 |
| $S_{sensor}$| Sensor Compatibility | **0.05** | `GOOD`: 1.0, `MODERATE`: 0.7, `LOW`: 0.3 |

> [!IMPORTANT]
> This metric is designated as **"Verification Confidence Score"** rather than a probability, avoiding uncalibrated probability claims.

---

## 5. Acceptance / Rejection Policy

A candidate is **`ACCEPTED`** if and only if **all** of the following conditions hold:
1. $N_{inliers} \ge 6$ (`MIN_INLIERS`)
2. $\text{Inlier Ratio} \ge 0.35$ (`MIN_INLIER_RATIO`)
3. $\text{RMSE} \le 3.5$ px (`MAX_RMSE`)
4. $\text{Geographic Relation} \ne \text{"DISJOINT"}$
5. $\text{Transformation Stability} == \text{"STABLE"}$
6. $\text{Verification Confidence} \ge 0.50$ (`MIN_CONFIDENCE`)

Otherwise, the candidate is **`REJECTED`**.

---

## 6. Explainable AI (XAI) Diagnostic Engine

### For ACCEPTED Matches ("Why was this match accepted?")
Returns an evidence-based physical checklist:
- `✓ Strong AI retrieval similarity (0.860)`
- `✓ Strong geometric consensus: 12/12 inliers (100.0%)`
- `✓ Low reprojection error: RMSE = 0.00 px (configured max: 3.5 px)`
- `✓ Consistent geographic footprint (OVERLAPPING)`
- `✓ Physically stable affine transformation (determinant = 1.00)`
- `✓ Well-distributed spatial spread across patch (11/16 cells occupied, score = 1.00)`
- `✓ Compatible cross-sensor acquisition: GSD ratio 2.0x (GOOD)`

### For REJECTED Matches ("Why was this match rejected?")
Returns structured, machine-readable diagnostic objects `[{"code": "...", "message": "..."}]`:

| Diagnostic Code | Trigger Condition | Physical Explanation |
| :--- | :--- | :--- |
| `GEOGRAPHIC_DISJOINT` | Candidate footprint is disjoint | "Candidate patch footprint is geographically disjoint from query observation." |
| `TOO_FEW_INLIERS` | Inliers $< 6$ | "Only {inliers} geometric inliers found, below required threshold of 6." |
| `LOW_INLIER_RATIO` | Inlier ratio $< 35\%$ | "Geometric inlier ratio of {ratio}% is below acceptable threshold of 35.0%." |
| `HIGH_REPROJECTION_ERROR`| RMSE $> 3.5$ px | "Reprojection RMSE of {rmse} px exceeds maximum allowable error of 3.5 px." |
| `NO_VALID_GEOMETRIC_MODEL`| RANSAC failed | "RANSAC failed to estimate a valid geometric transformation model." |
| `UNSTABLE_TRANSFORMATION`| Det $\le 0$ or ill-conditioned | "Estimated affine transformation is degenerate or numerically unstable." |
| `POOR_SPATIAL_DISTRIBUTION`| Inliers clustered | "Geometric inliers are clustered locally (spread score < threshold)." |
| `AI_SIMILARITY_FALSE_POSITIVE`| AI Sim $\ge 0.75$, geometry fails | "High AI similarity ({sim}) was not supported by verified physical geometry." |
| `LOW_CONFIDENCE` | Conf $< 0.50$ | "Verification confidence score fell below minimum acceptance threshold." |

---

## 7. Key Empirical Finding: False Positive Rejection

POC-6 demonstrates the scientific principle:
- **Candidate #1 from POC-5:** `OHRC_PATCH_0001` vs `LROC_PATCH_0011` had a high AI cosine similarity of **0.8807** (Rank #1 in retrieval).
  - Physical geometry: Geographically **DISJOINT**, **0 consensus inliers**, **0.0% inlier ratio**.
  - Final Verification Confidence: **0.0345**.
  - Decision: **✗ REJECTED**.
  - Diagnostic: `AI_SIMILARITY_FALSE_POSITIVE`, `GEOGRAPHIC_DISJOINT`, `TOO_FEW_INLIERS`.
- **Candidate #5 from POC-5:** `OHRC_PATCH_0001` vs `LROC_PATCH_0001` had an AI similarity of **0.8601** (Rank #5 in retrieval).
  - Physical geometry: Geographically **OVERLAPPING**, **12 inliers (100.0%)**, **RMSE = 0.00 px**, **Spatial Spread = 1.00**, **Stable Transform**.
  - Final Verification Confidence: **0.9460**.
  - Decision: **✓ ACCEPTED**.

---

## 8. Output Artifacts Manifest

All outputs are saved to `outputs/poc6/`:

| File | Type | Description |
| :--- | :--- | :--- |
| `poc6_results.json` | JSON | Complete list of all 55 verified candidates with all metrics, breakdowns, and XAI reasons. |
| `poc6_results.csv` | CSV | Tabular summary of verification metrics for scientific analysis. |
| `poc6_metadata.json` | JSON | Full reproducibility record: commit hash, OS, Python version, seed, weights, thresholds. |
| `poc6_failure_cases.json` | JSON | Rejection taxonomy grouped by diagnostic failure code. |
| `poc6_verified_for_poc7.json` | JSON | Downstream handover dataset containing verified pairs, inliers, and transformations. |
| `geometric_verification_gallery.png` | PNG | Visual verification figure showing tentative vs consensus inlier lines with decision badges. |
| `inlier_ratio_vs_confidence.png` | PNG | Scatter plot of Inlier Ratio vs Verification Confidence with acceptance boundaries. |
| `spatial_distribution_inliers.png` | PNG | Inlier spread diagram showing $4 \times 4$ spatial grid occupancy. |
| `confidence_score_breakdown.png` | PNG | Stacked component bar chart showing the 8 normalized signal contributions. |
| `accepted_vs_rejected_scatter.png` | PNG | AI Similarity vs Geometric Evidence scatter showing rejection of false positives. |
| `xai_rejection_reasons_breakdown.png` | PNG | Frequency distribution of all XAI failure diagnostic codes. |

---

## 9. Downstream Handover to POC-7

POC-7 will perform **Relative Pose Estimation and 3D Surface Disparity Mapping**.  
It directly ingests `outputs/poc6/poc6_verified_for_poc7.json` with the following schema:
```json
{
  "query_patch_id": "OHRC_PATCH_0001",
  "candidate_patch_id": "LROC_PATCH_0001",
  "accepted": true,
  "decision": "ACCEPTED",
  "verification_confidence": 0.946,
  "transformation_model": "affine",
  "transformation_matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
  "rmse": 0.0,
  "inlier_count": 12,
  "inlier_ratio": 1.0,
  "geographic_relation": "OVERLAPPING",
  "query_sensor": "OHRC",
  "candidate_sensor": "LRO_NAC",
  "query_gsd": 0.5,
  "candidate_gsd": 1.0,
  "inliers": [{"src_pt": [64.0, 22.0], "ref_pt": [64.0, 22.0], "distance": 0.2266}],
  "provenance": "REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT"
}
```

---

## 10. How to Run

### Standalone Demonstration
```powershell
python scripts/demo_poc6.py
```

### CLI Benchmark Runner
```powershell
python scripts/run_poc6_experiment.py --candidates outputs/poc5/poc5_candidates_for_poc6.json --min-inliers 6 --min-confidence 0.50
```

### Run Unit & Regression Tests
```powershell
python -m pytest tests/test_poc6_verification.py -v
python -m pytest tests/ -v
```

### Interactive Web Dashboard Studio
```powershell
python scripts/launch_dashboard.py --port 8000
```
Navigate to `http://localhost:8000` and click the **`POC 6 Geometric XAI`** tab.
