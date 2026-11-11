# Lab 1 - Answers and notes

`[PDF §...]` marks assignment questions. Run numbers match the sequential logbook; notebook labels use configuration names. CE means cross-entropy; PS means PortScan; FP counts all non-PortScan flows predicted as PortScan, not only Benign flows.

**Status:** Tasks 2-5 and all six Task 6 validation experiments are executed. For Task 6, we retain the original 256-128-64-32-16 model with early stopping and no additional regularizer. Its final test comparison is pending.

## Task 1 - Preprocessing

**[PDF §5.1] Samples, class balance and data quality.**

The CSV contains 31,507 flows, 16 numerical features and Label. We initially retain Destination Port as numerical.

| Class | Raw samples | Raw % | Clean samples | Clean % | Removed |
| --- | --- | --- | --- | --- | --- |
| Benign | 20,000 | 63.48 | 19,240 | 65.48 | 760 |
| DoS Hulk | 5,000 | 15.87 | 3,868 | 13.16 | 1,132 |
| PortScan | 5,000 | 15.87 | 4,849 | 16.50 | 151 |
| Brute Force | 1,507 | 4.78 | 1,427 | 4.86 | 80 |

Brute Force is initially rarest. We find 20 missing Flow Bytes/s values and 2,111 duplicate rows. After cleaning, no missing/infinite/negative values or constant features remain. Two feature pairs are identical in this subset: Fwd PSH Flags/SYN Flag Count and Subflow Fwd Packets/Total Fwd Packets. We retain the supplied features for consistency.

Seven distinct feature vectors have conflicting Benign/DoS Hulk labels. We retain these ambiguous observations rather than assign an unsupported replacement label.

**[PDF §5.2] Cleaning policy and sample counts.**

We remove incomplete/non-finite observations rather than impute them, and deduplicate before splitting to avoid repeating identical labelled rows across partitions. Negative durations/counts/lengths and ports are rejected using explicitly named columns.

| Step | Rows removed at this step | Rows remaining |
| --- | --- | --- |
| Raw CSV | - | 31,507 |
| Drop missing values | 20 | 31,487 |
| Drop exact duplicates | 2,094 | 29,393 |
| Replace +/- infinity with NaN, then drop NaN | 7 | 29,386 |
| Reject selected negative feature values | 2 | 29,384 |

The steps remove 2,123 rows. Only 2,094 duplicates remain after missing-value removal, explaining the difference from the raw duplicate count. Deduplication changes class frequencies, so we report the cleaned balance rather than interpret it as real traffic prevalence.

**[PDF §5.3] Split, stratification and leakage.**

We use a stratified 70/15/15 split with random_state=42, preserving minority-class representation. LabelEncoder and both candidate scalers are fitted on training only and reused unchanged on validation/test. Fitting on all data would expose held-out distributions to preprocessing.

| Class | Train | Validation | Test |
| --- | --- | --- | --- |
| Benign | 13,467 | 2,886 | 2,887 |
| Brute Force | 999 | 214 | 214 |
| DoS Hulk | 2,708 | 580 | 580 |
| PortScan | 3,394 | 728 | 727 |
| Total | 20,568 | 4,408 | 4,408 |

Labels are Benign=0, Brute Force=1, DoS Hulk=2, PortScan=3.

**[PDF §5.4] Scaling and outliers.**

We use StandardScaler to address large differences in feature magnitude. Training statistics show long tails:

| Feature | Minimum | Median | 99th percentile | Maximum |
| --- | --- | --- | --- | --- |
| Flow Duration | 1 | 31,094.5 | 117,651,856.57 | 119,998,546 |
| Flow Bytes/s | 0 | 5,250.04 | 12,333,333 | 2,070,000,000 |

StandardScaler does not remove skewness and remains sensitive to extremes. We also inspect log1p(Flow Duration)+standardization, which compresses that tail, but have not trained that alternative. Our choice is a simple reference, not a claim of optimal scaling.

Our exploratory mean one-vs-rest scores are Benign 0.0929, Brute Force 0.1424, PortScan 0.1706 and DoS Hulk 1.0462. They summarize individual-feature separation and do not predict nonlinear classifier performance reliably.

## Task 2 - Your first network

### Task 2A - Minimal classifier

**[PDF §6.1] Configuration.** Our retained minimal classifier is run 1: 16 -> 64 -> 4, ReLU, ordinary CE, AdamW lr=5e-4/weight_decay=0.01, batch 64, maximum 150 epochs, patience 20, min_delta=5e-5, seed 42 and CPU. We restore the minimum-validation-loss checkpoint; min_delta controls patience.

**Prediction:** Brute Force would be hardest because it has only 999 training samples; DoS Hulk might be easier given its higher exploratory separation score.

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| Benign | 0.9663 | 0.9740 | 0.9701 | 2886 |
| Brute Force | 0.8089 | 0.9299 | 0.8652 | 214 |
| DoS Hulk | 0.9907 | 0.9207 | 0.9544 | 580 |
| PortScan | 0.9496 | 0.9313 | 0.9404 | 728 |

**[PDF §6.1] Best epoch and convergence.** We restore epoch 145: validation CE 0.10890, accuracy 0.9578 and macro-F1 0.9325. Early stopping does not trigger. Final train/validation CE is 0.10901/0.11041: curves flatten together, although small improvements continue.

**[PDF §6.1] Per-class interpretation.** Brute Force has the lowest F1 (0.8652), supporting our prediction; recall is 0.9299 and precision 0.8089. Benign performs best despite its low exploratory score: averaging individual-feature scores misses nonlinear interactions and compares Benign with a heterogeneous mixture of attacks. Class frequency alone does not prove the cause of difficulty.

### Task 2B - Why the fundamentals matter

**[PDF §6.2] Hypotheses and controlled changes.**

Relative to run 1, S1 changes only to raw features; S2 raises LR to 0.5; S3 lowers it to 5e-6. We reset model, optimizer and seed for every run. Before training, we predicted unstable large losses for S1, oscillation/divergence for S2 and slow learning for S3, with expected damage S2 > S1 > S3.

| Run | Setup | Val loss | Accuracy | Macro-F1 | Epochs | Best epoch | Train + val s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Scaled reference, lr=5e-4 | 0.10890 | 0.9578 | 0.9325 | 150 | 145 | 63.60 |
| 2 | S1: raw inputs, lr=5e-4 | 1218.416544 | 0.9326 | 0.8931 | 35 | 15 | 13.19 |
| 3 | S2: scaled, lr=0.5 | 0.333414 | 0.9363 | 0.8953 | 33 | 13 | 14.82 |
| 4 | S3: scaled, lr=5e-6 | 0.370412 | 0.9004 | 0.7391 | 150 | 150 | 55.19 |

**[PDF §6.2] Failure modes and diagnosis from curves.**

- **S1:** losses are large and erratic, starting near 78,000 in training. Unequal input scales make optimization difficult and can produce extreme logits. Good accuracy can coexist with huge CE because confident mistakes are heavily penalized.
- **S2:** repeated sharp spikes show unstable updates consistent with overshooting. The run learns something useful; lr=0.5 does not cause sustained numerical divergence.
- **S3:** losses fall smoothly but slowly; the best checkpoint is epoch 150. It is under-optimized within the fixed budget, rather than unstable.

**[PDF §6.2] Ranking and which fundamental to fix first.**

By validation macro-F1, observed damage is **S3 > S1 > S2**: drops of 0.1934, 0.0394 and 0.0372 from the reference. Our ranking prediction was wrong; S1/S2 are nearly tied. By numerical loss behavior, S1 is clearly worst. Curve shapes suggest causes but are not unique diagnoses.

We would fix **scaling first**, then LR: sensible magnitudes make optimization easier to tune, while S3 shows that scaling cannot compensate for updates that are too small.

### Task 2C - Lock in our baseline

**[PDF §6.3] Selected port-based baseline.**

Run 5 uses 16 -> 64 -> 4, ReLU, ordinary CE, AdamW lr=1e-3/weight_decay=0.005, batch 64, up to 200 epochs, patience 20, min_delta=5e-5 and seed 42. We restore epoch 196. This is our selected port-based baseline.

**[PDF §6.3] Validation versus test: does it generalize?**

| Partition | Cross-entropy | Accuracy | Macro-F1 |
| --- | --- | --- | --- |
| Validation | 0.08986 | 0.96756 | 0.95135 |
| Test | 0.08612 | 0.96779 | 0.95516 |

| Class | Validation F1 | Test F1 |
| --- | --- | --- |
| Benign | 0.9780 | 0.9772 |
| Brute Force | 0.9238 | 0.9385 |
| DoS Hulk | 0.9555 | 0.9608 |
| PortScan | 0.9481 | 0.9441 |

The gaps are small: test - validation is +0.02 percentage points in accuracy and +0.38 in macro-F1; the largest class-F1 difference is Brute Force (+0.0147). This supports generalization on this stratified split, not necessarily on different networks or future traffic.

**[PDF §6.3] Activation comparison and test-set selection.**

Before training, we expected ReLU to outperform Linear. Both start from the same seeded linear-layer weights and use identical settings. Linear means Identity between the layers, so the whole classifier is linear.

| Class | ReLU precision | ReLU recall | ReLU F1 | Linear precision | Linear recall | Linear F1 |
| --- | --- | --- | --- | --- | --- | --- |
| Benign | 0.9716 | 0.9844 | 0.9780 | 0.9472 | 0.9321 | 0.9396 |
| Brute Force | 0.9132 | 0.9346 | 0.9238 | 0.8071 | 0.7430 | 0.7737 |
| DoS Hulk | 0.9665 | 0.9448 | 0.9555 | 0.9941 | 0.8672 | 0.9263 |
| PortScan | 0.9685 | 0.9286 | 0.9481 | 0.7827 | 0.9299 | 0.8500 |

ReLU confirms our prediction (macro-F1 0.95135 versus 0.87240). Linear particularly loses Brute Force recall and PortScan precision. ReLU restores epoch 196/200; Linear restores 55/75. Their times are **73.18 s** and **26.29 s**, respectively, not a combined time.

We choose configurations/activations by validation macro-F1 and checkpoints by validation loss. Using test scores to choose would turn test into tuning data; we evaluate the selected ReLU model there.

## Task 3 - When a feature biases the model

**[PDF §7] Port-80 artefact and prediction before inference.**

All Brute Force flows use port 80: 1,507 raw, 1,427 cleaned and 214 in test. This is a dataset association, not a general property of brute-force attacks. We expected recall to drop if the model had learned this shortcut.

We change only the 214 Brute Force test ports, 80 -> 8080, keeping labels, other inputs, model weights and the fitted scaler fixed. No fitting or retraining is involved.

| Metric | Original test | Brute Force port 8080 |
| --- | --- | --- |
| Brute Force recall | 0.9626 | 0.0374 |
| Brute Force precision | 0.9156 | 0.2963 |
| Brute Force F1 | 0.9385 | 0.0664 |
| Overall accuracy | 0.96779 | 0.92287 |
| Macro-F1 | 0.95516 | 0.72906 |
| Cross-entropy | 0.08612 | 0.40250 |

**[PDF §7] Did our prediction hold, and what did the model learn?**

Yes: recall drops by **92.52 percentage points**, from 206/214 detected to 8/214. All 198 changed predictions become Benign; non-Brute-Force predictions stay unchanged. This supports heavy reliance on the port-80 shortcut. It does not establish that the model used no other feature. Accuracy still exceeds 92% because Brute Force represents only 214/4,408 test flows; per-class recall and macro-F1 expose the failure.

### Task 3B - Port-free preprocessing

**[PDF §7] 1. Class counts before and after removing the port.**

| Class | With port | Without port |
| --- | --- | --- |
| Benign | 19,240 | 16,888 |
| Brute Force | 1,427 | 1,427 |
| DoS Hulk | 3,868 | 3,868 |
| PortScan | 4,849 | 285 |

PortScan loses **4,564 samples (94.12%)**. Total cleaned samples fall from 29,384 to 22,468. Benign also decreases by 12.22%; the other two classes are unchanged.

**[PDF §7] 2. Why the collapse, and what did the model know?**

Many PortScan rows differed only in destination port. Removing it makes their labelled feature vectors identical. Earlier performance could exploit this port-specific structure rather than diverse, port-independent scan behavior.

**[PDF §7] 3. Rarest class and balance.**

PortScan is now rarest: **285 samples (1.27%)**. Benign is 75.16%, DoS Hulk 17.22% and Brute Force 6.35%. The largest/smallest class ratio rises from about 13.5:1 to **59.3:1**.

**[PDF §7] 4. Do we still deduplicate?**

Yes: repeated labelled vectors could otherwise occur across training and held-out partitions without adding feature information. We accept fewer unique PortScan examples and greater metric uncertainty. Feature-only conflicts are different: 103 patterns still carry different labels (60 Benign/Brute Force, 42 Benign/DoS Hulk, one Benign/PortScan). We keep these labels rather than invent a correction.

We use the 15-feature data for all later tasks, with a fresh stratified 70/15/15 split, seed 42 and a training-fitted scaler. Train/validation/test contain **15,727 / 3,370 / 3,371** samples; PortScan has **199 / 43 / 43**. The `_3b` variables preserve this dataset separately from the port-based experiments.

## Task 4 - The rare class: loss and imbalance

**[PDF §8] Prediction and rare-class detection.**

Before the unweighted run, we expected PortScan to be hardest because only 199 training examples remain. Run 7 confirms this: lowest F1 (0.6526) and recall (0.7209), but **31/43** PortScan flows are still detected. We reuse the Task 2C settings with 15 inputs and ordinary CE.

**[PDF §8] Where do the class weights come from?**

Training labels only, using `N / (4 * class_count)`: Benign 0.3326, Brute Force 3.9357, DoS Hulk 1.4519 and PortScan 19.7575. Using validation/test labels would feed held-out distribution information into the training objective. Run 8 keeps initialization, data and other settings fixed.

**[PDF §8] Prediction versus measured accuracy/macro-F1 changes.**

We predicted slightly lower accuracy, higher macro-F1 and higher PortScan recall, with possible additional false alarms. **Accuracy and macro-F1 both fall**, by 4.60 and 9.66 percentage points. The macro-F1 prediction fails; lower accuracy, higher recall and more false alarms are confirmed.

| Validation metric | Unweighted (run 7) | Weighted (run 8) |
| --- | --- | --- |
| Accuracy | 0.96172 | 0.91573 |
| Macro-F1 | 0.86815 | 0.77160 |
| PortScan precision | 0.5962 | 0.2515 |
| PortScan recall | 0.7209 | 0.9535 |
| PortScan F1 | 0.6526 | 0.3981 |
| PortScan detected | 31/43 | 41/43 |
| Ordinary cross-entropy | 0.10506 | 0.20914 |

| Class | Unweighted F1 | Weighted F1 |
| --- | --- | --- |
| Benign | 0.9772 | 0.9511 |
| Brute Force | 0.9009 | 0.8523 |
| DoS Hulk | 0.9419 | 0.8849 |
| PortScan | 0.6526 | 0.3981 |

The weights recover ten more PortScan flows but increase false PortScan predictions from **21 to 122**. Precision loss outweighs the recall gain in macro-F1. Run 7 restores epoch 129/149 (43.88 s); run 8 restores 117/137 (45.55 s). Weighted checkpoint CE is 0.18363; the comparison table uses ordinary CE for both models.

**[PDF §8] Which metric should we optimize?**

We prioritize **PortScan recall**, accepting lower precision to miss fewer rare attacks. Between accuracy and macro-F1, macro-F1 better exposes minority-class errors; we report it alongside recall and false alarms. **Run 8's weighted loss is retained for Task 5**; run 7 remains the unweighted reference. At this stage, the port-free test stays reserved for Task 5D.

## Task 5 - Varying the hyperparameters

### Task 5A - Weighted depth comparison

**[PDF §9.1] Choice and predictions.** We retain Task 4B's balanced training-only weights: rare-attack recall matters more to us than precision. All four runs use ReLU, AdamW lr=1e-3/weight_decay=0.005, batch 64, up to 200 epochs, patience 20, min_delta=5e-5 and seed 42; split/scaler are unchanged.

- **Run 9, 64 -> 64:** an extra nonlinear stage should retain recall and reduce false alarms.
- **Run 10, 64 -> 64 -> 32:** a compact third stage may improve selectivity without losing rare flows.
- **Run 11, 64 -> 128 -> 32:** middle-layer expansion should capture richer interactions than run 10.
- **Run 12, 64 -> 128 -> 32 -> 16:** our exploratory comparison suggests extra compression may reduce false alarms at similar recall.

We select by PortScan recall, then macro-F1 when recall ties. Checkpoints minimize weighted validation CE; reported ordinary CE remains separate. Superseded unweighted trials are omitted from the current logbook.

| Run | Hidden layers | Accuracy | Macro-F1 | PS precision | PS recall | PS F1 | TP/43 | FP | Train + val s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | 64 (weighted reference) | 0.91573 | 0.77160 | 0.2515 | 0.9535 | 0.3981 | 41 | 122 | 45.55 |
| 9 | 64-64 | 0.93798 | 0.80917 | 0.3277 | 0.9070 | 0.4815 | 39 | 80 | 28.47 |
| 10 | 64-64-32 | 0.94866 | 0.83485 | 0.3571 | 0.9302 | 0.5161 | 40 | 72 | 21.83 |
| 11 | 64-128-32 | 0.94243 | 0.82179 | 0.3478 | 0.9302 | 0.5063 | 40 | 75 | 25.55 |
| 12 | 64-128-32-16 | 0.94214 | 0.83696 | 0.4082 | 0.9302 | 0.5674 | 40 | 58 | 35.04 |

**[PDF §9.1] Does depth help?** We select **run 12, 64-128-32-16**, among the deeper candidates: PortScan recall 0.9302 (40/43), precision 0.4082, macro-F1 0.83696; 58 false PortScan predictions. Selection uses recall first, macro-F1 on ties.

The weighted single-layer baseline still has higher PortScan recall (41/43 versus 40/43); depth improves precision and macro-F1, but has not beaten it on our primary metric. Added layers do not guarantee higher recall; parameter count also changes. If a single-layer model stays competitive, this small tabular task does not justify depth by itself.

The compact third stage helps (9→10); widening it does not (10→11); the fourth stage reduces false alarms at unchanged recall (11→12).

The saved execution reports 16 CPU threads; the code leaves PyTorch's thread count at its default. The current logbook retains these four weighted depth experiments. Timing includes epoch validation; comparisons use validation only.

### Task 5B - Batch size

**[PDF §9.2] Predictions.** Batch 16: better generalization from noisier updates, but slower epochs. Batch 64: a good generalization/time compromise. Batch 256: faster epochs, possibly worse generalization and more epochs to converge. Architecture, weighted loss, LR and other settings stay fixed.

**Q: Report validation results and training time, and explain both.**

| Batch | Accuracy | Macro-F1 | PS precision | PS recall | PS F1 | Epochs | Train + val s | Mean s/epoch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 16 | 0.92315 | 0.81112 | 0.3939 | 0.9070 | 0.5493 | 36 | 49.87 | 1.385 |
| 64 | 0.94214 | 0.83696 | 0.4082 | 0.9302 | 0.5674 | 71 | 35.04 | 0.494 |
| 256 | 0.93116 | 0.78885 | 0.2797 | 0.9302 | 0.4301 | 87 | 16.72 | 0.192 |

We keep **batch 64**: it has the highest accuracy and macro-F1, detects 40/43 PortScan flows with 58 false positives. Batch 16 detects 39/43 with 60 false positives, so the predicted generalization benefit is not supported. Batch 256 detects 40/43 but produces 103 false positives.

The timing prediction holds: batch 16 performs more updates and takes 1.385 s/epoch; batch 256 takes 0.192 s/epoch. Batch 256 runs for more epochs (87 versus 71 for batch 64), yet finishes sooner overall. Batch 64 takes 35.04 s, between 49.87 s and 16.72 s. Times include validation; stopping epochs and updates per epoch both affect totals. Batch 64 reuses run 12; only batches 16/256 add training runs.

### Task 5C - Optimizer versus learning rate

**[PDF §9.3] What did we find?** LR strongly changes SGD's behavior: moving from 0.001 to 0.01 raises PortScan recall from 90.70% to 100%, but lowers precision from 21.55% to 16.23%. AdamW is also sensitive: the same increase drops accuracy from 94.21% to 89.11% and macro-F1 from 0.8370 to 0.7904.

SGD+momentum is more stable than AdamW in accuracy and macro-F1 across these two learning rates (changes of 1.16 and 0.14 percentage points), consistent with momentum smoothing updates. Its PortScan recall still changes by 9.30 points, so this stability does not hold for every metric.

Since two of the three optimizers show substantial LR sensitivity, we consider **LR the first tuning priority**, while optimizer choice remains crucial. This practical conclusion does not establish that LR dominates every metric. We keep **AdamW lr=0.001**: 40/43 PortScan detections and 58 false positives, versus 43/43 and 203 for momentum SGD at 0.001. It gives us high recall without excessive false alarms. SGD's L2 and AdamW's decoupled decay also limit isolation of the optimizer effect.

### Task 5D - Test verdict

**[PDF §9.4] Locked models:** weighted 15 -> 64 -> 4 baseline (Task 4B) versus weighted 15 -> 64 -> 128 -> 32 -> 16 -> 4, AdamW lr=0.001, batch 64. Checkpoints and configuration were fixed using validation; both use the same port-free test split. We reproduced the baseline checkpoint and checked that both models matched their saved validation results before inference.

| Test metric | Weighted baseline | Selected deeper model |
| --- | --- | --- |
| Accuracy | 0.89973 | 0.93474 |
| Macro-F1 | 0.75237 | 0.81658 |
| Ordinary CE | 0.24536 | 0.18866 |
| PS precision | 0.2118 | 0.3333 |
| PS recall | 1.0000 | 0.9535 |
| PS F1 | 0.3496 | 0.4940 |
| PS detected /43 | 43 | 41 |
| PS false positives | 160 | 82 |
| Parameters | 1,284 | 14,068 |

**Q: Did complexity beat the baseline, and was it worth the runs?** The deeper model improves most reported test metrics and reduces PortScan false positives from 160 to 82, but detects 41/43 flows instead of 43/43. We retain it for this overall tradeoff, with 14,068 parameters versus 1,284 in the weighted baseline. The seven additional batch/optimizer experiments confirmed the 5A candidate without improving it. Task 5 therefore uses 11 retained experiments against the suggested ~10; three earlier unweighted trials are omitted. Baseline checkpoint reproduction does not add a new configuration. Settings and checkpoints were fixed using validation, without retuning on test. Full test reports and confusion matrices are in the notebook.

## Task 6 - Optimizations

**[PDF §10] Setup and prediction.** We use the port-free data, ReLU, unweighted CE, AdamW lr=5e-4, batch 128 and seed 42. The initial network has hidden sizes 256 -> 128 -> 64 -> 32 -> 16 and 47,924 parameters, weight_decay=0, no dropout or batch normalization, and 200 fixed epochs with final-epoch weights. Before training, we expected a fairly smooth decline, substantial early learning and possible late overfitting.

**Where we see overfitting.** The curves decline together initially, then flatten with late validation fluctuations. From epoch 140 to 200, training CE falls from 0.06258 to 0.05941 while validation CE rises from 0.06726 to 0.07374. This supports modest late overfitting rather than a large, sustained divergence.

### Saved validation results

| Run | Configuration | Validation CE | Accuracy | Macro-F1 | PS detected /43 | PS FP | Epochs | Checkpoint epoch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | Fixed 200 epochs | 0.07374 | 0.97834 | 0.92934 | 32 | 2 | 200 | 200 |
| 21 | Early stopping | 0.06726 | 0.97864 | 0.94799 | 37 | 2 | 160 | 140 |
| 22 | Smaller network + early stopping | 0.06467 | 0.97923 | 0.94770 | 37 | 2 | 160 | 140 |
| 23 | Weight decay 0.005 | 0.07680 | 0.97300 | 0.94203 | 37 | 2 | 139 | 120 |
| 24 | Dropout 0.2 | 0.07797 | 0.97270 | 0.93587 | 35 | 2 | 169 | 149 |
| 25 | Batch normalization | 0.09598 | 0.96172 | 0.88370 | 35 | 23 | 59 | 39 |

All six configurations are executed. Results refer to this split and seed; no Task 6 test evaluation is saved. Epochs count the work completed, while checkpoint epoch identifies the weights evaluated.

### Task 6A - Early stopping

**Controlled change and prediction.** We keep the original architecture and all training settings, adding patience 20 and min_delta=5e-5, with a maximum of 200 epochs. We restore the absolute minimum-validation-CE checkpoint; min_delta controls patience only. We expected fewer epochs and possibly better validation performance.

**Result.** Run 21 stops at epoch 160 and restores epoch 140. Compared with the fixed-epoch model, CE improves from 0.07374 to 0.06726 and macro-F1 from 0.92934 to 0.94799. PortScan detections rise from 32/43 to 37/43, with the same two false positives. We save 40 training epochs (20%) and obtain better validation results. This is the clearest performance-per-effort gain within Task 6.

### Task 6A bis - Smaller network

**Controlled change.** Run 22 removes only the last 16-unit hidden layer, leaving 256 -> 128 -> 64 -> 32. It retains the same unweighted loss, optimizer, seed, batch size and early stopping.

**Result.** Validation CE falls to 0.06467 and accuracy rises to 0.97923, while macro-F1 is marginally lower (0.94770 versus 0.94799). PortScan detections and false positives remain 37/43 and two. We remove only 464 parameters (0.97%), and both models complete 160 epochs and restore epoch 140. The smaller model is competitive, but this small simplification gives no clear overall gain. We keep the original early-stopping model as our Task 6 reference; the tiny score differences from one split do not establish a robust architecture ranking.

### Task 6B - Mutually exclusive regularizers

**Controlled comparisons.** Each variant starts from the original Task 6A architecture and a fresh model with the same seed and batch order. We keep early stopping and unweighted CE. Runs 23-25 enable only one regularizer each; the other two remain disabled.

- **Weight decay 0.005:** macro-F1 falls to 0.94203 and CE rises to 0.07680. PortScan stays at 37/43 with two false positives, but DoS Hulk recall falls from 0.9534 to 0.9121. Stopping after 139 epochs does not compensate for the poorer validation results.
- **Dropout 0.2 after each hidden ReLU:** macro-F1 falls to 0.93587 and PortScan detections to 35/43, with two false positives. It completes 169 epochs, more than early stopping alone. Its training loss includes active dropout, whereas validation disables it, so a lower validation curve than training is not itself evidence of better generalization.
- **BatchNorm1d before each hidden ReLU:** validation loss shows large spikes while training loss declines. Even the restored checkpoint has CE 0.09598 and macro-F1 0.88370; PortScan detections fall to 35/43 and false positives rise to 23. It stops at epoch 59 and restores epoch 39, but this configuration gives the weakest validation compromise.

**Decision.** None of the three regularizers improves on early stopping alone at the tested settings. We retain the original five-hidden-layer model with early stopping and no additional regularizer for the Task 6 comparison. This conclusion concerns these settings and this split, rather than every possible decay, dropout or normalization configuration. No directional pretraining prediction was recorded for the smaller-network and regularization trials; we report their comparison purpose without adding retrospective hypotheses.

### Baseline comparison and interim reflection

**[PDF §10] Which change helped most for the least effort?** Early stopping improves macro-F1 and rare-class recall while avoiding 20% of the fixed epoch budget. Removing the final hidden layer is nearly neutral; the three additional regularization trials do not improve the selected reference. Across the lab, sensible scaling and LR made optimization usable, removing Destination Port exposed a shortcut, and class weighting made the rare-attack recall/false-alarm tradeoff explicit. Extra depth and regularization gave smaller or inconsistent gains relative to these fundamental decisions.

**[PDF §10] Did the big network beat the simple baseline?** On validation, Task 6A improves accuracy and macro-F1 over both Task 4 references. Against the unweighted baseline it detects 37/43 rather than 31/43 PortScan flows, with two rather than 21 false positives. Against the weighted baseline it detects fewer (37/43 versus 41/43), but reduces false positives from 122 to two. We therefore improve the overall compromise without dominating rare-class recall. The required final test comparison remains pending; validation results cannot establish that verdict.

## Logbook and submission

The current logbook lists **25 retained experiments**, including **11 for Task 5** and **six for Task 6**.  Batch 64 and AdamW lr=0.001 both reuse run 12 and are counted once; baseline checkpoint reproduction does not add a new configuration.

- [ ] Report `groupID_lab1.pdf`, maximum 10 pages, with decisions, measured results and reasoning.
- [ ] Experiment logbook, separate or appendix (outside the page limit).
- [ ] Executed, rerunnable notebook/code and HTML export.
- [ ] Final package `groupID_lab1.zip`.
