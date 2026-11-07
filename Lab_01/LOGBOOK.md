# Lab 1 - Experiment logbook

FFNN 16 -> 64 -> 4, ReLU; cross-entropy; AdamW lr=5e-4, weight decay=0.01; batch 64. Stratified 70/15/15 split, random_state=42.

## Training runs

| Run | Task | Model / change | Reason / expectation | Validation result | Train s | Conclusion |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2A | Initial FFNN, raw features | Not recorded before training | Lowest printed loss: 819.4080 (epoch 15) | Not measured | We interrupted training after 17 completed epochs; losses fluctuate strongly. |
| 2 | 2A | StandardScaler baseline; seed 42; early stopping | Brute Force hardest (999 training samples); DoS Hulk easier (highest separability score); Benign may also be difficult | Accuracy 0.9519; macro-F1 0.9234; best loss 0.11698 (epoch 98) | 26.55 | Brute Force has lowest F1 (0.8450), mainly due to precision. Curves flatten together; early stopping did not trigger within 100 epochs. |

Run 2 uses CPU (one thread), maximum 100 epochs, patience 20 and min_delta=1e-4. We restore the lowest-validation-loss weights. Time includes training and per-epoch validation. We recorded our hypothesis before training; test remains unused.

Run 1 had no training seed or early stopping. Run 2 establishes our working baseline rather than a one-factor comparison with run 1.

**Budget:** 2 recorded training attempts; approximately 25 runs for the whole lab.
