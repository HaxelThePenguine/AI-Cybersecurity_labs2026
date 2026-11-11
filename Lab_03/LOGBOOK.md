# Lab 3 - Experiment logbook

One row per retained training run (every fit of an anomaly detector, clustering algorithm or Autoencoder). Runs are numbered sequentially; notebook labels identify configurations. Task 1 (data analysis/preprocessing) is not logged here. A diagnostic sweep used to choose a parameter (SSE elbow, k-distance plot, PCA explained variance) counts as one run. Hypotheses are written **before** running and are not rewritten afterwards.

**Budget:** ~25 runs. Rough guide: ~7 OC-SVM (Task 2), ~2 LOF (Task 3), ~4 clustering (Task 4), ~2 Isolation Forest (Task 5), ~5 Autoencoder (Task 6), ~3 representations (Task 7).

| Run | Task | What we changed (one thing) | Why this run / hypothesis before running | Key result (val/train) | Time s | What we concluded |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2A | Baseline: OC-SVM rbf, `gamma='scale'`, **normal training data only**, `nu=0.01` | Clean normal data → tight boundary. `nu` bounds the fraction of training points left outside, so we expect training FPR ≈ 1%. DoS/probe should fall outside the normal region; R2L, closest to normal in the heatmaps, should be mostly missed. | Train FPR 0.0104; macro-F1 0.9367 (full train); recall dos 0.910, probe 0.844, r2l 0.017 (3/181); 153 SV | 0.3 | Confirmed: FPR ≈ `nu`. R2L almost entirely inside the normal boundary; 9% of DoS and 16% of probe also missed. Retained as Task 2A model. |
| 2 | 2A | `nu=0.01` → `nu=0.5` (default); rest as run 1 | `nu=0.5` forces ~50% of the clean normal data outside the boundary: training FPR ≈ 50%, attack recall ≥ run 1 but many more false alarms, so macro-F1 well below run 1. | Train FPR 0.5000; macro-F1 0.6367; recall dos 0.974, probe 1.000, r2l 0.994; 6,726 SV | 13.5 | Confirmed: half of normal traffic flagged (6,724 FP). Higher recall, including R2L, does not compensate. `nu` must reflect the expected outlier fraction, not a default. |
| 8 | 3 | LOF sweep (diagnostic, one run): `n_neighbors` ∈ {5, 20, 100, 500} on the **full** train, `contamination` = known train rate 0.286, `fit_predict` | Selection criterion: train macro-F1 (labels for evaluation only), ROC-AUC as threshold-free check. DoS = many near-identical connections → dense groups with high local density, so LOF should miss most DoS at small k and flag more only when k exceeds the group size. Probe is heterogeneous (scans vs sweeps) → isolated points, detected already at small k. R2L looks like normal → mostly missed at every k. Overall macro-F1 below OC-SVM run 1, which knew what normal looks like. | Macro-F1 k=5/20/100/500: 0.515 / 0.529 / **0.577** / 0.522; ROC-AUC 0.497 / 0.513 / **0.593** / 0.488. k=100: FPR 0.242, recall dos 0.533, probe 0.240, r2l 0.166 (train) | 3.0 (all 4) | Partly wrong. Near-random detector at every k: attacks are as dense as their neighbours (median LOF ≈ 1.04 for all classes at k ≤ 20). DoS is detected only at k=100, when neighbourhoods extend past the DoS groups. **Probe is not isolated** and is the most missed class. R2L is best at small k. Selected k=100. |
| 9 | 3 | Selected `n_neighbors` refit with `novelty=True` on the full train; evaluated on **test** | Test contamination (63%) is much higher than the 28.6% used to set the threshold, so recall should drop; DoS (44% of test) dominates the result and is expected to be the main source of FN. | Test macro-F1 0.569; ROC-AUC 0.605; FPR 0.352; recall dos 0.611, probe 0.336; TN 1,395, FP 757, FN 1,731, TP 1,943 (test) | 0.6 | Partly wrong. 46% of the test is flagged, not 28.6%: test dos points score above the training threshold more often, so dos recall rises instead of dropping. Probe is the main source of FN. FPR rises to 35%. LOF remains close to chance. |

<!-- Add one row per run. Planned slots:
Task 2  (OC-SVM)        : runs ~1-7
Task 3  (LOF)           : runs ~8-9
Task 4A (K-Means)       : runs ~10-11
Task 4B (DBSCAN)        : runs ~12-13
Task 5  (Isolation F.)  : runs ~14-15
Task 6  (Autoencoder)   : runs ~16-20
Task 7  (PCA / AE+OCSVM): runs ~21-23
-->

Seed 42; preprocessing fitted on training data only (see NOTES Task 1). Labels are used only to build training subsets and to evaluate, never as a supervised signal. The test set is used only where a task explicitly asks for it. Times are indicative and may change on rerun.

**Count:** 2 retained runs (Task 2A).
