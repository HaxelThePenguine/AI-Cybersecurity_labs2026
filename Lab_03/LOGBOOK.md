# Lab 3 - Experiment logbook

One row per retained training run (every fit of an anomaly detector, clustering algorithm or Autoencoder). Runs are numbered sequentially; notebook labels identify configurations. Task 1 (data analysis/preprocessing) is not logged here. A diagnostic sweep used to choose a parameter (SSE elbow, k-distance plot, PCA explained variance) counts as one run. Hypotheses are written **before** running and are not rewritten afterwards.

**Budget:** ~25 runs. Rough guide: ~7 OC-SVM (Task 2), ~2 LOF (Task 3), ~4 clustering (Task 4), ~2 Isolation Forest (Task 5), ~5 Autoencoder (Task 6), ~3 representations (Task 7).

| Run | Task | What we changed (one thing) | Why this run / hypothesis before running | Key result (val/train) | Time s | What we concluded |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2A | Baseline: OC-SVM rbf, `gamma='scale'`, **normal training data only**, `nu=0.01` | Clean normal data → tight boundary. `nu` bounds the fraction of training points left outside, so we expect training FPR ≈ 1%. DoS/probe should fall outside the normal region; R2L, closest to normal in the heatmaps, should be mostly missed. | Train FPR 0.0104; macro-F1 0.9367 (full train); recall dos 0.910, probe 0.844, r2l 0.017 (3/181); 153 SV | 0.3 | Confirmed: FPR ≈ `nu`. R2L almost entirely inside the normal boundary; 9% of DoS and 16% of probe also missed. Retained as Task 2A model. |
| 2 | 2A | `nu=0.01` → `nu=0.5` (default); rest as run 1 | `nu=0.5` forces ~50% of the clean normal data outside the boundary: training FPR ≈ 50%, attack recall ≥ run 1 but many more false alarms, so macro-F1 well below run 1. | Train FPR 0.5000; macro-F1 0.6367; recall dos 0.974, probe 1.000, r2l 0.994; 6,726 SV | 13.5 | Confirmed: half of normal traffic flagged (6,724 FP). Higher recall, including R2L, does not compensate. `nu` must reflect the expected outlier fraction, not a default. |

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
