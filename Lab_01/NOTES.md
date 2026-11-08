# Lab 1 - Answers and notes

`[PDF §...]` marks assignment questions. Results are from the saved notebook; historical runs are identified explicitly.

**Status:** Tasks 2-4 and 5A are complete. Run 8 is our simple port-free reference; **run 10 (64 -> 64)** is our best depth candidate. Tasks 5B-5D and 6 are pending.

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

**[PDF §6.1] Configuration and historical attempts.**

We use 16 -> 64 -> 4, ReLU, ordinary cross-entropy, AdamW lr=5e-4/weight_decay=0.01, batch 64, seed 42 and CPU. Each checkpoint is selected by minimum validation loss; min_delta controls the patience counter. The current notebook shows run 2.

| Run | Historical attempt | Maximum epochs | Patience | min_delta | Best epoch | Val loss | Accuracy | Macro-F1 | Train + val s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | First attempt | 100 | 20 | 1e-4 | 98 | 0.11698 | 0.9519 | 0.9234 | 26.55 |
| 2 | Second attempt; current notebook output | 150 | 20 | 5e-5 | 145 | 0.10890 | 0.9578 | 0.9325 | 39.12 |

**Prediction before the first scaled run:** Brute Force would be hardest because it has only 999 training samples; DoS Hulk might be easier given its higher exploratory separation score. Benign's low score suggested possible difficulty despite its larger support.

**Historical run 1, 100 epochs:**

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| Benign | 0.9670 | 0.9643 | 0.9656 | 2886 |
| Brute Force | 0.7743 | 0.9299 | 0.8450 | 214 |
| DoS Hulk | 0.9711 | 0.9259 | 0.9479 | 580 |
| PortScan | 0.9403 | 0.9299 | 0.9351 | 728 |

**Run 2, 150 epochs, currently saved:**

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| Benign | 0.9663 | 0.9740 | 0.9701 | 2886 |
| Brute Force | 0.8089 | 0.9299 | 0.8652 | 214 |
| DoS Hulk | 0.9907 | 0.9207 | 0.9544 | 580 |
| PortScan | 0.9496 | 0.9313 | 0.9404 | 728 |

**[PDF §6.1] Best epoch, convergence and per-class interpretation.**

We restore epochs 98 and 145 respectively. Neither run triggers early stopping. Final train/validation CE is 0.1176/0.1174 for run 1 and 0.10901/0.11041 for run 2: curves flatten together without sustained validation deterioration, although small improvements continue.

Brute Force has the lowest F1 in both runs (0.8450 -> 0.8652), supporting our prediction. Its recall stays 0.9299 while precision improves (0.7743 -> 0.8089); it is not uniquely weakest by recall. Benign performs best despite its low exploratory score. The heuristic averages features, misses nonlinear interactions and compares Benign with a heterogeneous mixture of attack classes. Class frequency is consistent with the outcome, but does not prove its cause. Run 2 changes both the epoch budget and min_delta, so the gain is not attributable to epochs alone.

### Task 2B - Why the fundamentals matter

**[PDF §6.2] Hypotheses and controlled changes.**

Relative to run 2, S1 changes only to raw features; S2 raises LR to 0.5; S3 lowers it to 5e-6. We reset model, optimizer and seed for every run. Before training, we predicted unstable large losses for S1, oscillation/divergence for S2 and slow learning for S3, with expected damage S2 > S1 > S3.

| Run | Setup | Val loss | Accuracy | Macro-F1 | Epochs | Best epoch | Train + val s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | Scaled reference, lr=5e-4 | 0.10890 | 0.9578 | 0.9325 | 150 | 145 | 39.12 |
| 3 | S1: raw inputs, lr=5e-4 | 1218.416544 | 0.9326 | 0.8931 | 35 | 15 | 9.24 |
| 4 | S2: scaled, lr=0.5 | 0.333414 | 0.9363 | 0.8953 | 33 | 13 | 8.80 |
| 5 | S3: scaled, lr=5e-6 | 0.370412 | 0.9004 | 0.7391 | 150 | 150 | 39.71 |

**[PDF §6.2] Failure modes and diagnosis from curves.**

- **S1:** losses are large and erratic, starting near 78,000 in training. Unequal input scales make optimization difficult and can produce extreme logits. Good accuracy can coexist with huge CE because confident mistakes are heavily penalized.
- **S2:** repeated sharp spikes show unstable updates consistent with overshooting. The run learns something useful; lr=0.5 does not cause sustained numerical divergence.
- **S3:** losses fall smoothly but slowly; the best checkpoint is epoch 150. It is under-optimized within the fixed budget, rather than unstable.

**[PDF §6.2] Ranking and which fundamental to fix first.**

By validation macro-F1, observed damage is **S3 > S1 > S2**: drops of 0.1934, 0.0394 and 0.0372 from the reference. Our ranking prediction was wrong; S1/S2 are nearly tied. By numerical loss behavior, S1 is clearly worst. Curve shapes suggest causes but are not unique diagnoses.

We would fix **scaling first**, then LR: sensible magnitudes make optimization easier to tune, while S3 shows that scaling cannot compensate for updates that are too small.

### Task 2C - Lock in our baseline

**[PDF §6.3] Selected port-based baseline.**

Run 7 uses 16 -> 64 -> 4, ReLU, ordinary CE, AdamW lr=1e-3/weight_decay=0.005, batch 64, up to 200 epochs, patience 20, min_delta=5e-5 and seed 42. We restore epoch 196. Run 6 changed both LR and epoch budget relative to run 2; run 7 then changed only weight decay (0.01 -> 0.005), improving validation macro-F1 by 0.00059. This is a small single-seed gain.

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

ReLU confirms our prediction (macro-F1 0.95135 versus 0.87240). Linear particularly loses Brute Force recall and PortScan precision. ReLU restores epoch 196/200; Linear restores 55/75. Their times are **52.36 s** and **18.87 s**, respectively, not a combined time.

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

Before the unweighted run, we expected PortScan to be hardest because only 199 training examples remain. Run 8 confirms this: lowest F1 (0.6526) and recall (0.7209), but **31/43** PortScan flows are still detected. We reuse the Task 2C settings with 15 inputs and ordinary CE.

**[PDF §8] Where do the class weights come from?**

Training labels only, using `N / (4 * class_count)`: Benign 0.3326, Brute Force 3.9357, DoS Hulk 1.4519 and PortScan 19.7575. Using validation/test labels would feed held-out distribution information into the training objective. Run 9 keeps initialization, data and other settings fixed.

**[PDF §8] Prediction versus measured accuracy/macro-F1 changes.**

We predicted slightly lower accuracy, higher macro-F1 and higher PortScan recall, with possible additional false alarms. **Accuracy and macro-F1 both fall**, by 4.60 and 9.66 percentage points. The macro-F1 prediction fails; lower accuracy, higher recall and more false alarms are confirmed.

| Validation metric | Unweighted (run 8) | Weighted (run 9) |
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

The weights recover ten more PortScan flows but increase false PortScan predictions from **21 to 122**. Recall gains are outweighed by precision loss. Run 8 restores epoch 129/149 (30.14 s); run 9 restores 117/137 (28.40 s). Weighted checkpoint CE is 0.18363; the comparison table uses ordinary CE for both models.

**[PDF §8] Which metric should we optimize?**

We prioritize **macro-F1**: every class contributes equally, and precision matters alongside recall. Accuracy can hide rare attacks; recall alone can reward excessive false alarms. We monitor rare-class recall/precision and retain **run 8** as the simple port-free reference. Full reports/heatmaps are in the notebook; the port-free test is reserved for the later fixed-model comparison.

## Task 5 - Varying the hyperparameters

### Task 5A - Depth

**[PDF §9.1] Architecture rationale and recorded hypotheses.**

- **64 -> 64 (run 10): minimal extension.** We keep the baseline's 64-unit representation and add one nonlinear transformation, without narrowing it. We expected the extra stage to combine flow statistics into more useful decision boundaries and improve macro-F1, particularly on PortScan.
- **64 -> 32 -> 16 (run 11): progressive compression.** Three hidden stages learn a narrower representation with fewer parameters than 64 -> 64 (3,700 versus 5,444). We expected this capacity constraint to improve generalization, with the risk of discarding information needed for rare attacks.
- **64 -> 64 -> 64 (run 12): constant-width follow-up.** After run 10 improved, we added a third 64-unit stage to test further depth without the bottleneck. We expected a modest additional gain, while recognizing the overfitting risk of 9,604 parameters. Contrasting the two three-layer designs also lets us examine narrowing versus retaining width.

All use run 8's unweighted port-free setup: ReLU, AdamW lr=1e-3/weight_decay=0.005, batch 64, up to 200 epochs, patience 20, min_delta=5e-5 and seed 42. Split and scaler stay fixed; each model starts fresh and restores its lowest-validation-loss checkpoint. We chose two initial architectures and one follow-up, not a grid.

| Run | Hidden layers | Accuracy | Macro-F1 | PortScan F1 | Parameters | Train + val s |
| --- | --- | --- | --- | --- | --- | --- |
| 8 | 64 (reference) | 0.96172 | 0.86815 | 0.6526 | 1,284 | 30.14 |
| 10 | 64 -> 64 | 0.97774 | 0.93556 | 0.8571 | 5,444 | 35.63 |
| 11 | 64 -> 32 -> 16 | 0.96973 | 0.88019 | 0.6535 | 3,700 | 29.42 |
| 12 | 64 -> 64 -> 64 | 0.97359 | 0.91461 | 0.7826 | 9,604 | 29.72 |

**[PDF §9.1] Does depth help?**

Yes, in the first extension: **64 -> 64** improves macro-F1 by 0.06741 over the single-layer baseline. Runs 10/11 both detect 33/43 PortScan flows, but run 10 makes only one false PortScan prediction versus 25 for run 11. Run 12 detects 36/43, but makes 13 false predictions and has lower F1 than run 10.

Our minimal-extension hypothesis is supported; the bottleneck and further-depth hypotheses are not. **Run 10 is our selected candidate.** One extra layer helps, but simply adding more depth does not. Had the single-layer model remained competitive, simplicity would have been preferable; here its lower macro-F1 supports a modest increase in complexity. Parameter count also varies, so this is not an isolated test of depth alone.

We used **3 of about 10 Task 5 runs**. Timings include per-epoch validation and different stopping epochs, so they are not a pure speed comparison. These are single-seed results; run 8 remains the simple reference and the port-free test is untouched.

**[PDF §9.2 - 5B] Batch size.** Pending: compare three sizes, recording predictions for generalization/time before each new run.

**[PDF §9.3 - 5C] Optimizer versus LR.** Pending: compare SGD, momentum SGD and AdamW with LR variation, within the remaining Task 5 budget.

**[PDF §9.4 - 5D] Final verdict.** Pending after validation comparisons: test the selected model against run 8 and judge the gain against its run cost.

## Task 6 - Optimizations

**[PDF §10] Large model and overfitting.** Pending: 256 -> 128 -> 64 -> 32 -> 16, ReLU, CE, AdamW lr=5e-4, batch 128, about 150-200 epochs, explicit weight_decay=0 and no early stopping. Record the curve prediction first.

**[PDF §10] Optimization and final reflection.** Pending: try a smaller model/early stopping first, then weight decay, dropout and batch normalization one change at a time. Compare with run 8 and use the completed logbook to judge performance per unit of effort.

## Logbook and submission

We have **13 recorded training entries (1-12 and 7bis)**; Task 5 has used three. Runs 1 and 6 remain historical entries. Preprocessing/inference consume no training runs. The PDF asks for about 25 runs overall and about 10 within Task 5.

- [ ] Report `groupID_lab1.pdf`, maximum 10 pages, with decisions, measured results and reasoning.
- [ ] Experiment logbook, separate or appendix (outside the page limit).
- [ ] Executed, rerunnable notebook/code and HTML export.
- [ ] Final package `groupID_lab1.zip`.
