# Lab 1 - Experiment logbook

FFNN 16 -> 64 -> 4, ReLU; cross-entropy; AdamW lr=5e-4, weight decay=0.01; batch 64. Stratified 70/15/15 split, random_state=42.

## Training runs

| Run | Task | Model / change | Reason / expectation | Validation result | Train s | Conclusion |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2A | StandardScaler baseline; seed 42; early stopping | Brute Force hardest (999 training samples); DoS Hulk easier (highest separability score); Benign may also be difficult | Accuracy 0.9519; macro-F1 0.9234; best loss 0.11698 (epoch 98) | 26.55 | Brute Force has lowest F1 (0.8450), mainly due to precision. Curves flatten together; early stopping did not trigger within 100 epochs. |
| 2 | 2A | Same scaled FFNN; 150 epochs; min_delta=5e-5 | Not recorded before this run | Accuracy 0.9578; macro-F1 0.9325; best loss 0.10890 (epoch 145) | 39.91 | Macro-F1 improves by 0.0091 over run 1. Brute Force remains hardest (F1 0.8652), with better precision (0.8089). Early stopping did not trigger. |
| 3 | 2B | S1: raw inputs; lr=5e-4 | Without scaling, we expect large/unstable losses | Accuracy 0.9326; macro-F1 0.8931; best loss 1218.416544 (epoch 15) | 9.24 | Large, erratic losses; macro-F1 below baseline. Early stop at 35; restored epoch 15. |
| 4 | 2B | S2: scaled inputs; lr=0.5 | We expect oscillation or divergence | Accuracy 0.9363; macro-F1 0.8953; best loss 0.333414 (epoch 13) | 8.80 | Repeated loss spikes; poorer validation performance, but no sustained divergence. Early stop at 33; restored epoch 13. |
| 5 | 2B | S3: scaled inputs; lr=5e-6 | We expect slow improvement within 150 epochs | Accuracy 0.9004; macro-F1 0.7391; best loss 0.370412 (epoch 150) | 39.71 | Smooth but slow learning; largest macro-F1 drop. All 150 epochs completed; best at 150. |

All runs use CPU (one thread), seed 42 and patience 20. Run 1 uses at most 100 epochs and min_delta=1e-4; runs 2-5 use at most 150 epochs and min_delta=5e-5. S1-S3 each change one setting relative to run 2. We restore the lowest-validation-loss weights. Times include training and per-epoch validation; test remains unused.

**Budget:** 5 logged runs; approximately 25 runs for the whole lab.
