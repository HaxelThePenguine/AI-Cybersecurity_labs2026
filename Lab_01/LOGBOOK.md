# Lab 1 - Experiment logbook

FFNN 16 -> 64 -> 4, ReLU; cross-entropy; AdamW, default lr=5e-4 (overrides below), weight decay=0.01; batch 64. Stratified 70/15/15 split, random_state=42.

## Training runs

| Run | Task | Model / change | Reason / expectation | Validation result | Train s | Conclusion |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2A | Historical first attempt; 100 epochs; StandardScaler | Brute Force hardest (999 training samples); DoS Hulk easier (highest separability score); Benign may also be difficult | Accuracy 0.9519; macro-F1 0.9234; best loss 0.11698 (epoch 98) | 26.55 | Brute Force has lowest F1 (0.8450), mainly due to precision. Curves flatten together; early stopping did not trigger within 100 epochs. |
| 2 | 2A | Historical second attempt; 150 epochs; min_delta=5e-5; current notebook output | Not recorded before this run | Accuracy 0.9578; macro-F1 0.9325; best loss 0.10890 (epoch 145) | 41.57 | Macro-F1 improves by 0.0091 over run 1. Brute Force remains hardest (F1 0.8652), with better precision (0.8089). Early stopping did not trigger. |
| 3 | 2B | S1: raw inputs; lr=5e-4 | Without scaling, we expect large/unstable losses | Accuracy 0.9326; macro-F1 0.8931; best loss 1218.416544 (epoch 15) | 9.24 | Large, erratic losses; macro-F1 below baseline. Early stop at 35; restored epoch 15. |
| 4 | 2B | S2: scaled inputs; lr=0.5 | We expect oscillation or divergence | Accuracy 0.9363; macro-F1 0.8953; best loss 0.333414 (epoch 13) | 8.80 | Repeated loss spikes; poorer validation performance, but no sustained divergence. Early stop at 33; restored epoch 13. |
| 5 | 2B | S3: scaled inputs; lr=5e-6 | We expect slow improvement within 150 epochs | Accuracy 0.9004; macro-F1 0.7391; best loss 0.370412 (epoch 150) | 39.71 | Smooth but slow learning; largest macro-F1 drop. All 150 epochs completed; best at 150. |
| 6 | 2C | ReLU; lr=1e-3; max_epochs=200 | Validation-based tuning | Accuracy 0.96688; macro-F1 0.95076; best loss 0.09209 (epoch 200) | 52.74 | Macro-F1 improves by 0.0183 over run 2; Brute Force F1 0.9238. We also increased the epoch budget, so the gain is not attributable to LR alone. |
| 7 | 2C | ReLU; weight_decay 0.01 -> 0.005; other settings as run 6 | Validation-based weight-decay tuning | Accuracy 0.96756; macro-F1 0.95135; best loss 0.08986 (epoch 196) | 50.33 | Our selected baseline: macro-F1 +0.00059 over run 6. Small gain on this seed; 200 epochs completed. |
| 7bis | 2C | Identity instead of ReLU; other settings as run 7 | We expect removing ReLU to hurt per-class performance | Accuracy 0.91402; macro-F1 0.87240; best loss 0.28591 (epoch 55) | 18.05 | Macro-F1 below ReLU; Brute Force F1 0.7737. Early stop at 75; restored epoch 55. We keep run 7. |
| 8 | 4 | Port-free 15 -> 64 -> 4; unweighted CE; Task 2C hyperparameters | We expect PortScan to be hardest: only 199 training samples remain | Accuracy 0.96172; macro-F1 0.86815; best loss 0.10506 (epoch 129) | 30.14 | Prediction confirmed: PortScan F1 0.6526, recall 0.7209 (31/43 detected). Early stop at 149. |
| 9 | 4B | Balanced training-only class weights; other settings as run 8 | We expect accuracy to decrease, macro-F1 and PortScan recall to increase | Accuracy 0.91573; macro-F1 0.77160; best weighted CE 0.18363 (epoch 117) | 28.40 | Accuracy and macro-F1 both fall; PortScan recall rises to 0.9535 but precision falls to 0.2515. We keep run 8. |

All runs use CPU (one thread), seed 42 and patience 20. Run 1 uses at most 100 epochs and min_delta=1e-4; runs 2-5 use at most 150 epochs and min_delta=5e-5; runs 6-9 and 7bis use at most 200 epochs and min_delta=5e-5. S1-S3 each change one setting relative to run 2. We restore the lowest-validation-loss weights. Times include training and per-epoch validation. Runs 1-5, 7bis, 8 and 9 use validation only; runs 6 and 7 are also evaluated on test. Our port-based reference is run 7; run 8 is our unweighted port-free reference (lr=1e-3, weight_decay=0.005).

**Budget:** 10 logged training entries (1-9 and 7bis); approximately 25 runs for the whole lab.

**Run 6 - fixed-model test:** accuracy 0.96665; macro-F1 0.95369; loss 0.08992. Model selection uses validation.

**Run 7 - final baseline test:** accuracy 0.96779; macro-F1 0.95516; loss 0.08612. Each time belongs to its own model: run 7 ReLU 50.33 s; run 7bis Linear 18.05 s.

Run 9 uses weighted CE for checkpoint selection; its ordinary validation CE is 0.20914. Run 8 remains our selected port-free baseline.
