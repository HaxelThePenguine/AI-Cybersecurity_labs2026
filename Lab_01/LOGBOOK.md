# Lab 1 - Experiment logbook

CPU; FFNN 16 -> 64 -> 4, ReLU; cross-entropy; AdamW lr=5e-4, weight decay=0.01; batch 64. Stratified 70/15/15 split, seed 42 for the split only.

## Training runs

| Run | Task | Model / change | Reason / expectation | Validation result | Train s | Conclusion |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2A | Initial FFNN, raw features | Not recorded before training | Lowest printed loss: 819.4080 (epoch 15); final printed loss: 2784.0391 | Not measured | We interrupted training after 17 completed epochs; losses fluctuate strongly. Our baseline is not complete. |

We prepared the scalers but used raw inputs in this run. Early stopping and best-checkpoint restoration are not implemented yet. Classification metrics and test results are not available.

**Budget:** 1 recorded training attempt; approximately 25 runs for the whole lab.
