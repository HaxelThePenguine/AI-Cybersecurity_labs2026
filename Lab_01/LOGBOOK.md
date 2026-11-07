# Lab 1 - Experiment logbook

FFNN 16 -> 64 -> 4, ReLU; cross-entropy; AdamW lr=5e-4, weight decay=0.01; batch 64. Stratified 70/15/15 split, random_state=42.

## Training runs

| Run | Task | Model / change | Reason / expectation | Validation result | Train s | Conclusion |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2A | StandardScaler baseline; seed 42; early stopping | Brute Force hardest (999 training samples); DoS Hulk easier (highest separability score); Benign may also be difficult | Accuracy 0.9519; macro-F1 0.9234; best loss 0.11698 (epoch 98) | 26.55 | Brute Force has lowest F1 (0.8450), mainly due to precision. Curves flatten together; early stopping did not trigger within 100 epochs. |
| 2 | 2A | Same scaled FFNN; 150 epochs; min_delta=5e-5 | Not recorded before this run | Accuracy 0.9578; macro-F1 0.9325; best loss 0.10890 (epoch 145) | 39.91 | Macro-F1 improves by 0.0091 over run 1. Brute Force remains hardest (F1 0.8652), with better precision (0.8089). Early stopping did not trigger. |

Both runs use CPU (one thread), seed 42 and patience 20. Run 1 completes 100 epochs with min_delta=1e-4; run 2 completes 150 with min_delta=5e-5. We restore the lowest-validation-loss weights. Times include training and per-epoch validation; test remains unused.

**Budget:** 2 logged runs; approximately 25 runs for the whole lab.
