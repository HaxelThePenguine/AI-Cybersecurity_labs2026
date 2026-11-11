# Lab 3 - Experiment logbook

One row per retained training run (every fit of an anomaly detector, clustering algorithm or Autoencoder). Runs are numbered sequentially; notebook labels identify configurations. Task 1 (data analysis/preprocessing) is not logged here. A diagnostic sweep used to choose a parameter (SSE elbow, k-distance plot, PCA explained variance) counts as one run. Hypotheses are written **before** running and are not rewritten afterwards.

**Budget:** ~25 runs. Rough guide: ~7 OC-SVM (Task 2), ~2 LOF (Task 3), ~4 clustering (Task 4), ~2 Isolation Forest (Task 5), ~5 Autoencoder (Task 6), ~3 representations (Task 7).

| Run | Task | What we changed (one thing) | Why this run / hypothesis before running | Key result (val/train) | Time s | What we concluded |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | | | | | |

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

**Count:** 0 retained runs so far.
