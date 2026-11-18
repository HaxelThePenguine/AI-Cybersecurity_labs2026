# Lab 1 - Answers and notes

`[PDF §...]` marks assignment questions. Stable IDs R1-R25 match the logbook and the notebook run maps; saved outputs retain their original configuration labels. CE means cross-entropy; PS means PortScan; PS FP counts all non-PortScan flows predicted as PortScan. Elsewhere, unqualified FP has the same meaning; the extra test comparison explicitly labels binary false alarms as Benign FP.

**Status:** Tasks 2-5 and all six current Task 6 validation configurations are executed, including the smaller fixed-epoch Task 6A bis model. We retain the original Task 6A network with early stopping and no additional regularizer. The final test comparison and the extra comparison of all 25 logged models are executed; the final discussion below brings these results together.

## Scope, hypothesis provenance and timing sources

These notes describe the **25 retained configurations R1-R25** in the current notebook: six with Destination Port and nineteen port-free. A configuration specifies a model and training setup; an execution actually trains it. Reusing the trained R12 model for batch 64, AdamW LR 0.001 and Task 5D, or evaluating existing models, is inference/reuse rather than another training execution. The saved notebook supports these 25 configurations; it is not a timestamped ledger certifying the lifetime number of training executions. The historical execution total cannot be established from configuration count alone.

The logbook distinguishes hypotheses and explanatory rationales. We retain the original wrong predictions and compare each rationale with the observed result; a rationale alone does not establish when it was recorded.

All reported times now refer to the saved CPU outputs in `lab1.ipynb`. The evidence map in `LOGBOOK.md` identifies their cells. These are individual measurements including epoch validation, not repeated benchmark estimates. Missing timings remain **Not saved**; epoch savings are not claimed as measured wall-clock speedups.

## How we interpret detection quality and model choices

We distinguish **raising an attack alarm** from **identifying the correct attack type**. Attack FN counts malicious flows predicted as Benign; Benign FP counts benign flows predicted as any attack. PortScan recall instead measures correct PortScan identification: a PortScan predicted as DoS is a PortScan class FN, but still raises an attack alarm. PS FP counts every non-PortScan flow predicted as PortScan, including other attack types; it is not the same as Benign FP.

**Our threat model.** We give particular importance to catching rare PortScan activity: only 199 training examples remain, so a high aggregate score could hide weak recognition of this class. We prefer more alerts to investigate over overlooking rare attack activity, and accept a higher false-positive burden for that coverage. Scarcity motivates this focus; it does not prove that sample count alone causes every error. Higher observed recall reduces missed class identifications on this split, without guaranteeing detection of all future attacks. False alarms still consume analyst attention; we have not assigned a numerical FN/FP cost ratio or a false-alarm ceiling. We therefore state the concrete cost of each choice rather than claim a single globally best detector. Accuracy and macro-F1 summarize four-class classification; neither alone measures how many attacks pass as Benign.

**Meaning of selected.** Selection is specific to each experiment: Task 2C uses validation macro-F1; Task 4 retains weighting for its PortScan recall gain despite poorer macro-F1; Task 5A ranks only deeper candidates by PortScan recall, then macro-F1 on ties. Tasks 5B/5C weigh validation classification results against PortScan false positives, and Task 6 retains early stopping for its validation CE, macro-F1 and PortScan results. These choices do not all maximize the same metric. The binary Attack FN/Benign FP comparison was added in the extra section to interpret the fixed models; it did not retrospectively determine earlier selections. Selected thus means our task-specific validation reference, not the model with the fewest missed alarms across the whole book.

### Validation decisions and accepted costs

The following records the criteria actually used; it does not introduce a common utility after observing results. A task reference is not necessarily the preferred operational detector. PS FP includes other attacks misidentified as PortScan, so it is not a direct count of benign alerts or analyst workload.

| Decision | Candidates / comparison | Actual validation criterion | Benefit accepted | Cost / limit accepted |
| --- | --- | --- | --- | --- |
| Task 2C reference | R5 ReLU vs R6 Identity | Higher macro-F1; checkpoint by ordinary CE | 0.95135 vs 0.87240 macro-F1 | 200 vs 75 executed epochs; R5 vs R1 is a joint reconfiguration |
| Task 4 loss for exploration | R8 weighted vs R7 unweighted | Prioritize correct rare-class identification | PS TP 31 -> 41 of 43 | PS FP 21 -> 122; macro-F1 0.86815 -> 0.77160; R7 remains the aggregate-score reference |
| Task 5A deep candidate | R9-R12, with R8 retained as simple comparator | Within deep candidates: PS recall, then macro-F1 | R12: 40/43, 58 PS FP, macro-F1 0.83696 | R8 detects 41/43; this is selection within a family, not a global recall winner |
| Task 5B batch | R13 / R12 / R14: 16 / 64 / 256 | Classification results balanced against observed time | R12 has highest macro-F1, 40/43 PS and 58 PS FP | Batch 256 is faster (18.29 vs 35.16 s), but has 103 PS FP |
| Task 5C optimizer/LR | R15-R19 plus reused R12 | Qualitative PS coverage / PS FP compromise | R12 avoids 145 PS FP vs R18 | 40/43 instead of 43/43 PS; no predefined numerical tradeoff rule |
| Task 6 stopping / regularization | R20-R25 | CE, macro-F1 and PS results; retain R21 | R21 vs R20: macro-F1 0.92934 -> 0.94799; PS TP 32 -> 37; 40 fewer epochs | R21 is not the best PS recall across the lab; wall-clock time was not saved |

Task 4 accepts 101 additional PS FP for ten additional correct PS identifications; Task 5C avoids 145 PS FP while giving up three such identifications. The latter exchange is much more costly per extra correct PS identification (about 48.3 vs 10.1 PS FP), which explains the qualitative preference. These descriptive ratios are not thresholds or binary false-alarm costs. They do not make the policy uniquely reproducible or establish an operational winner. Without a prespecified common criterion, our decisions remain exploratory and local to each task. No test result changes them.

## Shared limits of interpretation

Each pipeline is evaluated on one fixed stratified split with seed 42. The port-free validation and test sets each contain only 43 PortScan flows (training has 199): one classification changes recall by 2.33 percentage points, so small differences do not establish a stable ranking. Removing Destination Port and deduplicating changes both class prevalence and the evaluated population; with-port versus port-free results therefore combine a feature change with a population change. Deduplication includes the label, leaving some identical inputs with conflicting labels across partitions: the port-free data have 18 shared input patterns between training/validation, 20 between training/test and five between validation/test. This limits input-pattern independence and does not by itself prove inflated scores. These limits bound generalization; they do not identify the cause of a particular negative result. We interpret each comparison using its observed metrics and controls.

## Device selection and saved results

We set `DEVICE` once in the notebook: `auto` tries CUDA, then XPU, then CPU; `cpu`, `cuda` and `xpu` select a backend explicitly when available in the installed PyTorch. Every task uses the same device for its model, input batches and class weights. After changing the selector, we restart the kernel and Run All to rebuild models and optimizers together. The recorded lab results and final discussion refer to the existing CPU executions; the selector applies to subsequent runs. We keep seeds and strict deterministic algorithms on CPU, while GPU runs allow faster algorithms and can give different scores or stopping epochs. Device choice alone is not a measured speedup for these small networks. PyTorch documents [Intel XPU execution](https://docs.pytorch.org/docs/stable/notes/get_start_xpu.html) and [reproducibility limits](https://docs.pytorch.org/docs/stable/notes/randomness.html).

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

The observed magnitudes motivate scaling: Flow Duration has median 31,094.5 but a maximum near 120 million, while Flow Bytes/s reaches 2.07 billion. Our limited goal is to give features comparable units for optimization without clipping or discarding finite extreme flows that might contain attack information. StandardScaler preserves their ordering and relative distances within each feature, but its mean and standard deviation are affected by those extremes; the central observations can therefore remain compressed. We accept this limitation rather than claim to have removed outlier effects or skewness. We inspect log1p(Flow Duration)+standardization because it compresses the long tail, but do not train that alternative. Task 2B subsequently shows that scaling helps optimization relative to raw inputs; it does not show that StandardScaler is better than log or robust alternatives.

Our exploratory mean one-vs-rest scores are Benign 0.0929, Brute Force 0.1424, PortScan 0.1706 and DoS Hulk 1.0462. They summarize individual-feature separation and do not predict nonlinear classifier performance reliably.

## Task 2 - Your first network

### Task 2A - Minimal classifier

**[PDF §6.1] Configuration.** Our retained minimal classifier is R1: 16 -> 64 -> 4, ReLU, ordinary CE, AdamW lr=5e-4/weight_decay=0.01, batch 64, maximum 150 epochs, patience 20, min_delta=5e-5, seed 42 and CPU. We restore the minimum-validation-loss checkpoint; min_delta controls patience.

**Stopping settings.** Patience 20 is a practical fixed tolerance for validation fluctuations, not an optimized or uniquely correct value. We keep it fixed across early-stopping comparisons. Improvements smaller than min_delta can update the saved minimum-loss checkpoint without resetting patience; stopping therefore need not occur exactly 20 epochs after the restored epoch.

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

Relative to R1, S1 changes only to raw features; S2 raises LR to 0.5; S3 lowers it to 5e-6. We reset model, optimizer and seed for every run. Before training, we predicted unstable large losses for S1, oscillation/divergence for S2 and slow learning for S3, with expected damage S2 > S1 > S3.

| Run | Setup | Val loss | Accuracy | Macro-F1 | Epochs | Best epoch | Train + val s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | Scaled reference, lr=5e-4 | 0.10890 | 0.9578 | 0.9325 | 150 | 145 | 85.31 |
| R2 | S1: raw inputs, lr=5e-4 | 1218.416544 | 0.9326 | 0.8931 | 35 | 15 | 13.25 |
| R3 | S2: scaled, lr=0.5 | 0.333414 | 0.9363 | 0.8953 | 33 | 13 | 12.41 |
| R4 | S3: scaled, lr=5e-6 | 0.370412 | 0.9004 | 0.7391 | 150 | 150 | 56.92 |

**[PDF §6.2] Failure modes and diagnosis from curves.**

- **S1:** losses are large and erratic, starting near 78,000 in training. Unequal input scales make optimization difficult and can produce extreme logits. Good accuracy can coexist with huge CE because confident mistakes are heavily penalized.
- **S2:** repeated sharp spikes show unstable updates consistent with overshooting. The run learns something useful; lr=0.5 does not cause sustained numerical divergence.
- **S3:** losses fall smoothly but slowly; the best checkpoint is epoch 150. It is under-optimized within the fixed budget, rather than unstable.

**[PDF §6.2] Ranking and which fundamental to fix first.**

By validation macro-F1, observed damage is **S3 > S1 > S2**: drops of 0.1934, 0.0394 and 0.0372 from the reference. Our ranking prediction was wrong; S1/S2 are nearly tied. By numerical loss behavior, S1 is clearly worst. Curve shapes suggest causes but are not unique diagnoses.

We would fix **scaling first**, then LR: sensible magnitudes make optimization easier to tune, while S3 shows that scaling cannot compensate for updates that are too small.

### Task 2C - Lock in our baseline

**[PDF §6.3] Selected port-based baseline.**

R5 uses 16 -> 64 -> 4, ReLU, ordinary CE, AdamW lr=1e-3/weight_decay=0.005, batch 64, up to 200 epochs, patience 20, min_delta=5e-5 and seed 42. We restore epoch 196. This is our selected port-based baseline. Relative to Task 2A, LR, weight decay and maximum epochs change together, so this is an exploratory joint reconfiguration and a deviation from the one-change-per-run rule. An archived Task 2C plan records an expectation of modest benefit from additional epochs because the earlier curves were still decreasing, and better results with ReLU than Identity. That plan uses different LR/decay values, so it supports the epoch-extension and activation rationale only; it does not document a prior justification for the current LR/decay pair. A higher LR could accelerate progress and lower decay could permit a less constrained fit; these are plausible mechanisms, not isolated effects demonstrated by R5. We cannot attribute the macro-F1 increase from 0.9325 to 0.95135 to LR, decay or epoch budget individually. This limitation does not invalidate the controlled R5/R6 activation comparison.

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

ReLU confirms our prediction (macro-F1 0.95135 versus 0.87240). Linear particularly loses Brute Force recall and PortScan precision. ReLU restores epoch 196/200; Linear restores 55/75. Their times are **73.96 s** and **26.64 s**, respectively, not a combined time.

For Task 2C, we choose the activation by validation macro-F1 and checkpoints by validation loss; later task-specific choices are explained separately. Using test scores to choose would turn test into tuning data; we evaluate the selected ReLU model there.

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

Before the unweighted run, we expected PortScan to be hardest because only 199 training examples remain. R7 confirms this: lowest F1 (0.6526) and recall (0.7209), but **31/43** PortScan flows are still detected. We reuse the Task 2C settings with 15 inputs and ordinary CE.

**[PDF §8] Where do the class weights come from?**

Training labels only, using `N / (4 * class_count)`: Benign 0.3326, Brute Force 3.9357, DoS Hulk 1.4519 and PortScan 19.7575. Using validation/test labels would feed held-out distribution information into the training objective. R8 keeps initialization, data and other settings fixed. The PortScan weight is about 59.4 times the Benign weight: per-example loss contributions from this rare class therefore matter much more to the objective. This makes a shift toward predicting PortScan plausible, potentially recovering PS examples while reducing precision; it is a mechanism consistent with the observed errors, not proof that weighting alone explains every prediction.

**[PDF §8] Prediction versus measured accuracy/macro-F1 changes.**

We predicted slightly lower accuracy, higher macro-F1 and higher PortScan recall, with possible additional false alarms. **Accuracy and macro-F1 both fall**, by 4.60 and 9.66 percentage points. The macro-F1 prediction fails; lower accuracy, higher recall and more false alarms are confirmed.

| Validation metric | Unweighted (R7) | Weighted (R8) |
| --- | --- | --- |
| Accuracy | 0.96172 | 0.91573 |
| Macro-F1 | 0.86815 | 0.77160 |
| PortScan precision | 0.5962 | 0.2515 |
| PortScan recall | 0.7209 | 0.9535 |
| PortScan F1 | 0.6526 | 0.3981 |
| PortScan detected | 31/43 | 41/43 |
| PortScan class FN | 12/43 | 2/43 |
| PortScan false positives (all non-PortScan classes) | 21 | 122 |
| Ordinary cross-entropy | 0.10506 | 0.20914 |

| Class | Unweighted F1 | Weighted F1 |
| --- | --- | --- |
| Benign | 0.9772 | 0.9511 |
| Brute Force | 0.9009 | 0.8523 |
| DoS Hulk | 0.9419 | 0.8849 |
| PortScan | 0.6526 | 0.3981 |

The weights correctly identify ten more PortScan flows (31/43 -> 41/43), reducing PortScan class FN from 12 to 2, but increase PS FP from **21 to 122**: **101 additional non-PortScan flows are classified as PortScan**. These PS FP can include other attacks and are not all necessarily benign false alarms. Likewise, the ten recovered class detections do not by themselves prove ten additional attack alarms: some original errors may have named another attack type. All four class F1 scores fall, so this is a recall-oriented tradeoff with a substantial classification cost, not an overall improvement. R7 restores epoch 129/149 (41.54 s); R8 restores 117/137 (39.97 s). Weighted checkpoint CE is 0.18363; the comparison table uses ordinary CE for both models.

**[PDF §8] Which metric should we optimize?**

For this Task 4 choice, our threat model prioritizes **correct identification of the rare PortScan class**: overlooking rare attack activity is more serious to us than raising additional alerts for investigation. With only 199 PortScan training examples, overall accuracy alone could hide weak class recognition. We therefore accept the observed precision loss and 101 extra PS FP to identify ten additional PortScan flows. We retain R8's weighted loss for Task 5 to investigate whether deeper models can reduce that cost while preserving much of the recall gain. The unweighted R7 remains the stronger reference for accuracy and macro-F1. This is a qualitative preference, with no numerical error-cost ratio or FP ceiling; higher recall is not a guarantee of catching all attacks, nor proof that weighting is the best binary detector. Macro-F1 exposes minority-class classification errors better than accuracy alone, but neither replaces Attack FN when the question is missed attack alarms. At this stage, the port-free test stays reserved for Task 5D.

## Task 5 - Varying the hyperparameters

### Task 5A - Weighted depth comparison

**[PDF §9.1] Choice and predictions.** We carry forward Task 4B's balanced training-only weights because our threat model favors coverage of rare PortScan activity and tolerates more alerts for investigation. Weighting improves correct PortScan identification but worsens macro-F1 and produces more PS FP; Task 5 explores this tradeoff. All four runs use ReLU, AdamW lr=1e-3/weight_decay=0.005, batch 64, up to 200 epochs, patience 20, min_delta=5e-5 and seed 42; split/scaler are unchanged.

- **R9, 64 -> 64:** an extra nonlinear stage should retain recall and reduce false alarms.
- **R10, 64 -> 64 -> 32:** a compact third stage may improve selectivity without losing rare flows.
- **R11, 64 -> 128 -> 32:** middle-layer expansion should capture richer interactions than R10.
- **R12, 64 -> 128 -> 32 -> 16:** our exploratory comparison suggests extra compression may reduce false alarms at similar recall.

Within the four deeper candidates, we select by PortScan recall, then macro-F1 when recall ties; this is not a global ranking of all models by Attack FN. Checkpoints minimize weighted validation CE; reported ordinary CE remains separate. 

| Run | Hidden layers | Accuracy | Macro-F1 | PS precision | PS recall | PS F1 | TP/43 | FP | Train + val s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R8 | 64 (weighted reference) | 0.91573 | 0.77160 | 0.2515 | 0.9535 | 0.3981 | 41 | 122 | 39.97 |
| R9 | 64-64 | 0.93798 | 0.80917 | 0.3277 | 0.9070 | 0.4815 | 39 | 80 | 26.72 |
| R10 | 64-64-32 | 0.94866 | 0.83485 | 0.3571 | 0.9302 | 0.5161 | 40 | 72 | 24.03 |
| R11 | 64-128-32 | 0.94243 | 0.82179 | 0.3478 | 0.9302 | 0.5063 | 40 | 75 | 26.08 |
| R12 | 64-128-32-16 | 0.94214 | 0.83696 | 0.4082 | 0.9302 | 0.5674 | 40 | 58 | 35.16 |

**[PDF §9.1] Does depth help?** We select **R12, 64-128-32-16**, among the deeper candidates: PortScan recall 0.9302 (40/43), precision 0.4082, macro-F1 0.83696; 58 false PortScan predictions. This ranking applies within the deeper family and uses PortScan recall first, macro-F1 on ties; it does not supersede the simple reference on every metric.

The weighted single-layer baseline still has higher PortScan recall (41/43 versus 40/43); the selected deeper candidate improves precision and macro-F1, but has not beaten it on the PortScan recall criterion used in this depth comparison. Added layers do not guarantee higher recall; parameter count also changes. If a single-layer model stays competitive, this small tabular task does not justify depth by itself.

Within this split, moving from 64-64 to 64-64-32 improves the reported classification metrics; widening the middle layer to 128 does not improve them. Adding the final 16-unit stage to 64-128-32 lowers PS FP at unchanged PortScan recall. These are observations for the tested widths and seed, subject to the shared limits above.

The saved execution reports 16 CPU threads; the code leaves PyTorch's thread count at its default. The current logbook retains these four weighted depth experiments. Timing includes epoch validation; comparisons use validation only.

### Task 5B - Batch size

**[PDF §9.2] Predictions.** Batch 16: better generalization from noisier updates, but slower epochs. Batch 64: a good generalization/time compromise. Batch 256: faster epochs, possibly worse generalization and more epochs to converge. Architecture, weighted loss, LR and other settings stay fixed.

**Q: Report validation results and training time, and explain both.**

| Batch | Accuracy | Macro-F1 | PS precision | PS recall | PS F1 | Epochs | Train + val s | Mean s/epoch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 16 | 0.92315 | 0.81112 | 0.3939 | 0.9070 | 0.5493 | 36 | 56.39 | 1.566 |
| 64 | 0.94214 | 0.83696 | 0.4082 | 0.9302 | 0.5674 | 71 | 35.16 | 0.495 |
| 256 | 0.93116 | 0.78885 | 0.2797 | 0.9302 | 0.4301 | 87 | 18.29 | 0.210 |

We keep **batch 64**: it has the highest accuracy and macro-F1, detects 40/43 PortScan flows with 58 false positives. Batch 16 detects 39/43 with 60 false positives, so the predicted generalization benefit is not supported. Batch 256 detects 40/43 but produces 103 false positives.

The timing prediction holds: batch 16 performs more updates and takes 1.566 s/epoch; batch 256 takes 0.210 s/epoch. Batch 256 runs for more epochs (87 versus 71 for batch 64), yet finishes sooner overall. Batch 64 takes 35.16 s, between 56.39 s and 18.29 s. Times include validation; stopping epochs and updates per epoch both affect totals. Batch 64 reuses R12; only batches 16/256 add training runs.

### Task 5C - Optimizer versus learning rate

**Question and rationale.** Can changing LR within an optimizer matter more than switching optimizer at fixed LR? The following concise rationales explain the controlled comparisons and are checked against the saved observations.

| Run | Rationale | Observation and limit |
| --- | --- | --- |
| R15 | A higher SGD LR may speed learning but make validation loss noisier. | No macro-F1 gain vs R16; acceleration to a common target was not measured. |
| R16 | SGD at LR 0.001 may learn too slowly within 200 epochs. | Best CE occurs at the epoch limit; macro-F1 is below R12. |
| R17 | Momentum may accelerate SGD, with an overshooting risk at LR 0.01. | Fewer epochs, but worse weighted CE vs R15; acceleration is not established. |
| R18 | Momentum may improve convergence relative to plain SGD at LR 0.001. | Weighted CE improves vs R16, while PS precision falls. |
| R19 | A tenfold AdamW LR increase may destabilize updates and hurt validation performance. | CE and macro-F1 worsen vs R12; these scores alone do not establish instability. |


**[PDF §9.3] What did we find?** LR strongly changes SGD's behavior: moving from 0.001 to 0.01 raises PortScan recall from 90.70% to 100%, but lowers precision from 21.55% to 16.23%. AdamW is also sensitive: the same increase drops accuracy from 94.21% to 89.11% and macro-F1 from 0.8370 to 0.7904.

SGD+momentum shows smaller changes than AdamW in final validation accuracy and macro-F1 across these two learning rates (1.16 and 0.14 percentage points). Its PortScan recall still changes by 9.30 points. Small changes in final metrics do not by themselves demonstrate smoother optimization trajectories or stability across seeds.

**Conclusion.** Performance depends on the **optimizer-LR combination**; within the tested interval, we find no general predominance of LR. At LR 0.001, AdamW's validation macro-F1 exceeds SGD's by **9.09 percentage points** (0.83696 versus 0.74602), whereas changing AdamW's LR from 0.001 to 0.01 lowers macro-F1 by **4.66 points** (0.83696 -> 0.79040). For macro-F1 in this comparison, the optimizer difference is larger. The small set of configurations supports choosing among these tested combinations rather than a universal optimizer/LR rule.

**Retained combination.** We keep **AdamW lr=0.001**: 40/43 PortScan detections and 58 false positives, versus 43/43 and 203 for momentum SGD at 0.001. This accepts three fewer correctly identified PortScan flows in exchange for 145 fewer PS FP on validation. It is a qualitative classification tradeoff, not the result of the recall-first ranking used within Task 5A or a predefined false-alarm limit. SGD's L2 and AdamW's decoupled decay also limit isolation of the optimizer effect. SGD at LR 0.001 reaches its lowest validation loss at the 200-epoch limit, so this comparison also reflects the available optimization budget.

### Task 5D - Test verdict

**[PDF §9.4] Locked models:** weighted 15 -> 64 -> 4 baseline (Task 4B) versus weighted 15 -> 64 -> 128 -> 32 -> 16 -> 4, AdamW lr=0.001, batch 64. Checkpoints and configuration were fixed using validation; both use the same port-free test split. The current code reuses the trained R8 and R12 model objects for inference; it contains no checkpoint-reproduction training in Task 5D.

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

**Additional simple reference.** The executed extra comparison also evaluates the unweighted Task 4 model on the same port-free test; including it gives the following context without changing the validation-based selection.

| Model | Accuracy | Macro-F1 | Ordinary CE | Attack FN | Benign FP |
| --- | --- | --- | --- | --- | --- |
| Task 4 - unweighted | 0.95966 | 0.85443 | 0.11314 | 76 | 49 |
| Task 4B - weighted | 0.89973 | 0.75237 | 0.24536 | 32 | 266 |
| Task 5D - selected deeper | 0.93474 | 0.81658 | 0.18866 | 23 | 178 |

The unweighted simple model has higher accuracy and macro-F1 and lower ordinary CE than the selected deeper model, but misses 76 rather than 23 attacks at the binary alarm level. The deeper model raises 178 rather than 49 benign false alarms. Against the weighted simple reference, the deeper model reduces both Attack FN (32 -> 23) and Benign FP (266 -> 178), while its PortScan class recall remains lower. The selected deeper configuration improves specific metrics relative to the weighted reference, while both simple references remain relevant to the metric-specific verdict.

**Q: Did complexity beat the baseline, and was it worth the runs?** Against the weighted reference, the deeper model improves accuracy and macro-F1 and reduces PortScan false positives from 160 to 82, but correctly identifies 41/43 PortScan flows instead of 43/43. Against the unweighted reference, it gives lower accuracy/macro-F1 and lower Attack FN at the cost of more benign false alarms. These test results describe the tradeoff of the model already selected on validation, with 14,068 parameters versus 1,284 in the weighted baseline; they do not establish a globally best detector or change our selection. The seven additional batch/optimizer experiments did not replace the 5A candidate under our qualitative validation recall/PS FP compromise; some alternatives achieve higher PortScan recall with more PS FP. The current Task 5 comparison contains 11 distinct retained configurations against the suggested ~10. Task 5D reuses the existing R8 and R12 trained models; its code does not retrain either baseline. Settings and checkpoints were fixed using validation, without retuning on test. Full test reports and confusion matrices are in the notebook.

## Task 6 - Optimizations

**[PDF §10] Setup and prediction.** We use the port-free data, ReLU, unweighted CE, AdamW lr=5e-4, batch 128 and seed 42. The initial network has hidden sizes 256 -> 128 -> 64 -> 32 -> 16 and 47,924 parameters, weight_decay=0, no dropout or batch normalization, and 200 fixed epochs with final-epoch weights. Before training, we expected a fairly smooth decline, substantial early learning and possible late overfitting.

**Where we see overfitting.** The curves decline together initially, then flatten with late validation fluctuations. From epoch 140 to 200, training CE falls from 0.06258 to 0.05941 while validation CE rises from 0.06726 to 0.07374. This supports modest late overfitting rather than a large, sustained divergence.

### Which Task 6 comparisons answer which question?

- **Task 6 -> Task 6A:** same original network; the change is early stopping with restoration of the minimum-validation-CE checkpoint.
- **Task 6 -> Task 6A bis:** both use 200 fixed epochs and final weights; the change is removal of the final 16-unit hidden layer.
- **Task 6A versus Task 6A bis:** original network with early stopping versus the smaller fixed-epoch network; this compares two alternative interventions rather than isolating architecture alone.

### Saved validation results

| Run | Configuration | Validation CE | Accuracy | Macro-F1 | PS detected /43 | PS FP | Epochs | Checkpoint epoch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R20 | Fixed 200 epochs | 0.07374 | 0.97834 | 0.92934 | 32 | 2 | 200 | 200 |
| R21 | Early stopping | 0.06726 | 0.97864 | 0.94799 | 37 | 2 | 160 | 140 |
| R22 | Smaller network, fixed 200 epochs | 0.07321 | 0.97656 | 0.89968 | 25 | 1 | 200 | 200 |
| R23 | Weight decay 0.005 | 0.07680 | 0.97300 | 0.94203 | 37 | 2 | 139 | 120 |
| R24 | Dropout 0.2 | 0.07797 | 0.97270 | 0.93587 | 35 | 2 | 169 | 149 |
| R25 | Batch normalization | 0.09598 | 0.96172 | 0.88370 | 35 | 23 | 59 | 39 |

All six current Task 6 configurations are executed; the smaller fixed-epoch model uses its final epoch, not an early-stopped checkpoint. Results refer to this split and seed; the final Task 6 test results are recorded below. Epochs count the work completed, while checkpoint epoch identifies the weights evaluated.

### Task 6A - Early stopping

**Controlled change and prediction.** We keep the original architecture and all training settings, adding patience 20 and min_delta=5e-5, with a maximum of 200 epochs. We restore the absolute minimum-validation-CE checkpoint; min_delta controls patience only. We expected fewer epochs and possibly better validation performance.

The lower validation CE is partly built into this comparison: early stopping restores the minimum on that same validation set, whereas fixed training keeps the final epoch. It is not independent evidence of better generalization; we assess the held-out test separately.

**Result.** R21 stops at epoch 160 and restores epoch 140. Compared with the fixed-epoch model, CE improves from 0.07374 to 0.06726 and macro-F1 from 0.92934 to 0.94799. PortScan detections rise from 32/43 to 37/43, with the same two false positives. We save 40 training epochs (20%) and obtain better validation results. This is the clearest performance-per-effort gain within Task 6.

### Task 6A bis - Smaller network without early stopping

**R22 rationale.** Removing a layer may reduce overfitting slightly, but can also remove useful nonlinear transformations. Macro-F1 and PS detections fall vs R20; parameter reduction is only 0.97%.


**Controlled change.** We remove only the final 16-unit hidden layer from the initial fixed-epoch Task 6 model, giving 256 -> 128 -> 64 -> 32 with 47,460 parameters. We retain unweighted CE, AdamW lr=5e-4, weight_decay=0, batch 128 and seed 42. We train for exactly 200 epochs with no dropout, batch normalization, early stopping or best-checkpoint restoration; final-epoch weights are evaluated.

**Controlled reference.** To assess size reduction, we compare Task 6A bis with the original Task 6 network: both train for 200 fixed epochs and retain final weights. We also compare 6A bis with 6A to assess the two alternative interventions.

**Size reduction at fixed training.** The smaller model completes 200 epochs: validation CE 0.07321, accuracy 0.97656 and macro-F1 0.89968. Relative to the original fixed-epoch model, CE is slightly lower (0.07374 -> 0.07321), but accuracy falls (0.97834 -> 0.97656), macro-F1 falls (0.92934 -> 0.89968), and correct PortScan identifications fall from 32/43 to 25/43. PS FP falls from two to one. This removes **464 parameters, only 0.97%** (47,924 -> 47,460), so it is a small architectural change rather than a substantial compression experiment. On this split, this specific reduction does not improve the classification compromise.

**Alternative intervention: early stopping.** The original network with early stopping has validation macro-F1 0.94799 and 37/43 PortScan identifications, versus 0.89968 and 25/43 for the smaller fixed-epoch model; PS FP is two versus one. Early stopping completes 160 rather than 200 epochs and gives the stronger validation CE/macro-F1/recall compromise of these two alternatives. This comparison changes both architecture and stopping and cannot attribute the difference to size alone.

### Task 6B - Mutually exclusive regularizers

**Rationale.** Each intervention tests a different mechanism for reducing overfitting; its expected benefit and observed result are kept separate below.

| Run | Rationale | Observation and limit |
| --- | --- | --- |
| R23 | Weight decay may reduce late overfitting, with a risk of underfitting. | CE and macro-F1 worsen vs R21; not retained. |
| R24 | Dropout may reduce co-adaptation, but hinder learning from rare examples. | Macro-F1 and PS recall worsen vs R21; 169 rather than 160 epochs. |
| R25 | Batch normalization may speed optimization, but train/evaluation statistics may cause validation fluctuations. | Validation spikes and poorer macro-F1; the spike mechanism remains untested. |


**Controlled comparisons.** Each variant starts from the original Task 6A architecture and a fresh model with the same seed and batch order. We keep early stopping and unweighted CE. Runs 23-25 enable only one regularizer each; the other two remain disabled.

- **Weight decay 0.005:** macro-F1 falls to 0.94203 and CE rises to 0.07680. PortScan stays at 37/43 with two false positives, but DoS Hulk recall falls from 0.9534 to 0.9121. Stopping after 139 epochs does not compensate for the poorer validation results.
- **Dropout 0.2 after each hidden ReLU:** macro-F1 falls to 0.93587 and PortScan detections to 35/43, with two false positives. It completes 169 epochs, more than early stopping alone. Its training loss includes active dropout, whereas validation disables it, so a lower validation curve than training is not itself evidence of better generalization.
- **BatchNorm1d before each hidden ReLU:** validation loss shows large spikes while training loss declines. Even the restored checkpoint has CE 0.09598 and macro-F1 0.88370; PortScan detections fall to 35/43 and false positives rise to 23. It stops at epoch 59 and restores epoch 39, but this configuration gives the weakest validation compromise.

**Decision.** None of the three regularizers improves the validation CE/macro-F1 compromise of early stopping alone at the tested settings. We retain the original five-hidden-layer model with early stopping and no additional regularizer for the Task 6 comparison. This conclusion concerns these settings and this split, rather than every possible decay, dropout or normalization configuration. The proposed BatchNorm train/evaluation-statistics mechanism remains untested; the observed spikes alone do not establish their cause.

### Baseline comparison and reflection

**[PDF §10] Which change helped most for the least effort?** Against the initial fixed-epoch model, early stopping improves validation CE, macro-F1 and PortScan recall while avoiding 20% of the epoch budget. Against that same fixed-epoch reference, removing the final hidden layer reduces parameters by only 0.97% and gives lower validation macro-F1 and PortScan recall; its negative result concerns this small modification. The three additional regularization trials do not improve the selected validation reference. The test comparison below shows a metric-dependent early-stopping tradeoff. Across the lab, sensible scaling and LR made optimization usable, removing Destination Port exposed a shortcut, and class weighting made the rare-attack recall/false-alarm tradeoff explicit. Extra depth and regularization gave smaller or inconsistent gains relative to these fundamental decisions.

**[PDF §10] Did the big network beat the simple baseline?** On validation, Task 6A improves accuracy and macro-F1 over both Task 4 references. Against the unweighted baseline it detects 37/43 rather than 31/43 PortScan flows, with two rather than 21 false positives. Against the weighted baseline it detects fewer (37/43 versus 41/43), but reduces false positives from 122 to two. We therefore obtain a different validation classification compromise: better macro-F1 and fewer PS FP, without dominating PortScan recall or establishing the fewest binary missed alarms across all models. The final test results are recorded below; the final discussion below brings these results together.

### Final test comparison - numerical results

**[PDF §10] Fixed models.** We evaluate the weighted Task 4B baseline and the validation-selected original Task 6A network with early stopping, using their existing trained checkpoints and the same 3,371-sample port-free test split. The Task 6A checkpoint is epoch 140. No training or test-based retuning is performed; CE is unweighted for both evaluations.

| Test metric | Weighted Task 4B baseline | Selected Task 6A |
| --- | --- | --- |
| Ordinary CE | 0.24536 | 0.06560 |
| Accuracy | 0.89973 | 0.97686 |
| Macro-F1 | 0.75237 | 0.94420 |
| PS precision | 0.2118 | 0.9722 |
| PS recall | 1.0000 | 0.8140 |
| PS F1 | 0.3496 | 0.8861 |
| PS detected /43 | 43 | 35 |
| PS missed /43 | 0 | 8 |
| PS false positives | 160 | 1 |
| Parameters | 1,284 | 47,924 |

**Early stopping versus fixed epochs on test.** The executed extra comparison provides a separate check of the original architecture's stopping rule:

| Test metric | Original Task 6, fixed 200 epochs | Original Task 6A, early stopping |
| --- | --- | --- |
| Accuracy | 0.97805 | 0.97686 |
| Macro-F1 | 0.93740 | 0.94420 |
| Ordinary CE | 0.06101 | 0.06560 |
| Attack FN | 50 | 49 |
| Benign FP | 20 | 27 |
| PS class FN /43 | 10 | 8 |

Early stopping improves test macro-F1 (0.93740 -> 0.94420) and reduces Attack FN slightly (50 -> 49), while accuracy falls (0.97805 -> 0.97686), ordinary CE rises (0.06101 -> 0.06560), and Benign FP rises (20 -> 27). It is better on macro-F1 and PortScan class recall here, not uniformly on all test metrics. We keep the selection made on validation and report this tradeoff without retuning on test. Against the weighted Task 4B reference, Task 6A improves accuracy/macro-F1 and reduces Benign FP (266 -> 27), but has more Attack FN (32 -> 49) and lower PortScan recall.

The notebook contains the executed classification reports, per-class comparison and confusion matrices. This inference adds no training experiment; the logbook contains 25 current executed configurations, including the smaller fixed-epoch model. The final discussion below relates this comparison to our threat model and experimental effort.

## Extra - All logged models on the test set

We include all 25 current configurations in two overview figures: six with Destination Port and nineteen port-free. We evaluate all 25 existing checkpoints by inference, including the smaller fixed-epoch model. The selected Task 5D checkpoint is highlighted and counted once despite its reuse across Tasks 5A/5B/5C.

**False negatives.** Attack FN counts malicious flows classified as Benign; Attack FNR divides this count by actual attacks. BF/DoS/PS FN also includes confusion with another attack type, which still triggers an attack alarm. Benign FP counts benign flows classified as any attack; PS FP instead includes any non-PortScan flow classified as PortScan. We keep these definitions separate in the tables and plots.

The with-port and port-free tests contain 1,521 and 837 attacks respectively, so their raw counts have different denominators. Within each group every model uses the same test samples. Test comparisons describe the existing models without changing validation-based selections. A model with higher macro-F1 can still have more Attack FN; neither the Task 5D highlight nor the Task 6 reference denotes the fewest missed attack alarms. Without a specified FN/FP cost ratio, we report both error counts rather than assign a universal detector ranking; the final discussion below brings these results together.

**Validation selection does not guarantee a test winner.** The compact 64-64-32 model has test macro-F1 0.82088 versus 0.81658 for the selected 64-128-32-16 model, with fewer Attack FN (20 versus 23) and Benign FP (153 versus 178), using 7,396 rather than 14,068 parameters. Both correctly identify 41/43 PortScan flows; the selected model has fewer PS FP (82 versus 99). This reverses the small validation macro-F1 advantage of the larger model (0.83696 versus 0.83485) and strengthens the case that added depth is not reliably better on this split. We report the reversal without selecting again on test.

The dropout variant also has slightly higher test macro-F1 than early stopping alone (0.94679 versus 0.94420), but more Attack FN (74 versus 49) and fewer Benign FP (14 versus 27). AdamW LR 0.01 has the fewest Attack FN among the logged port-free models (15), with 400 Benign FP, compared with 23 and 178 for Task 5D. These are descriptive tradeoffs, not new validation-based choices.

**Smaller-model test results.** Task 6A bis obtains accuracy 0.97419, macro-F1 0.90536 and ordinary CE 0.07386. It misses 55 of 837 attacks at the binary alarm level (Attack FNR 6.57%), versus 49 for the original early-stopping model, with 25 versus 27 benign false alarms. It detects 26/43 PortScan flows and has 17 PortScan class false negatives, versus 8 for early stopping; both have one PortScan false positive. These test results describe the fixed models without changing the validation-based selection.

## Final discussion - judgement across the lab

**The most useful decisions came before added complexity.** The controlled Task 2B runs show that scaling and LR make optimization usable: raw inputs produce very large, erratic CE, while the very low LR leaves macro-F1 at 0.7391 versus 0.9325 for the minimal reference within the available epoch budget. Our initial failure ranking was wrong, which makes the measured curves more informative than the prediction. Task 5C then shows an optimizer-LR interaction: the tested combinations do not establish that LR generally dominates optimizer choice.

**Inspecting the data changed the meaning of success.** Changing only Brute Force test ports drops detections from 206/214 to 8/214, exposing a shortcut despite high original accuracy. Removing Destination Port and deduplicating leaves only 285 unique labelled PortScan observations, including 199 in training. That makes rare-class errors central to our threat model. Weighting correctly identifies ten additional validation PortScan flows, but adds 101 PS false positives and lowers macro-F1. We accept that specific coverage/classification tradeoff as the starting point for Task 5, rather than describe weighting as an overall improvement.

**Depth gives a conditional return for the experiments spent.** The selected Task 5D model improves on the weighted simple reference in test macro-F1 (0.75237 -> 0.81658), Attack FN (32 -> 23) and Benign FP (266 -> 178), while correctly identifying two fewer PortScan flows. The unweighted simple reference still has higher accuracy and macro-F1, but misses 76 attacks versus 23. Task 5 uses 11 logged configurations; the additional batch/optimizer trials do not replace the depth candidate under our validation compromise. The extra test comparison also favors compact 64-64-32 over the selected deeper model on macro-F1 and both binary error counts, so the validation ranking does not persist on test. About eleven times as many parameters (14,068 versus 1,284) therefore buy a particular error tradeoff, not a universal win over a simple network.

**Early stopping is the clearest effort saving within Task 6.** It uses 160 rather than 200 epochs and improves validation macro-F1 (0.92934 -> 0.94799) and PortScan identification (32/43 -> 37/43). Removing the final layer reduces parameters by only 0.97% and worsens those classification metrics against fixed training. The tested weight decay, dropout and batch normalization variants do not improve the chosen validation compromise. On test, early stopping improves macro-F1 relative to fixed training, while accuracy and CE worsen slightly; it still offers the more useful validation reference for the effort spent.

**The final comparison remains a choice between error profiles.** Against the weighted Task 4B model, Task 6A has better test accuracy/macro-F1 and far fewer benign false alarms (266 -> 27), but more missed attack alarms (32 -> 49) and fewer correct PortScan identifications (43/43 -> 35/43). The Task 5D reference also misses fewer attacks than Task 6A (23 versus 49), at the cost of more benign false alarms (178 versus 27). Our threat model makes that coverage cost important: a higher macro-F1 alone does not establish the preferred detector. We preserve the models selected on validation and use test only to characterize these profiles; the extra comparison is descriptive, not another selection round.

Overall, our best return on effort is a defensible preprocessing pipeline, controlled checks of optimization and shortcuts, explicit treatment of imbalance, and early stopping before extra regularization. More complexity adds conditional gains. The shared limits above - one split/seed, small PortScan support and ambiguous input patterns - keep these conclusions specific to this dataset and protocol; they do not explain every failure or establish deployment readiness.

## Logbook and submission

The current logbook lists **25 executed configurations**, including **11 for Task 5** and **six for Task 6**.  Batch 64 and AdamW lr=0.001 both reuse R12 and are counted once; the current inference code reuses the existing trained model objects. This count describes retained configurations, not a verified historical execution total.

- [ ] Report `groupID_lab1.pdf`, maximum 10 pages, with decisions, measured results and reasoning.
- [ ] Experiment logbook, separate or appendix (outside the page limit).
- [ ] Executed, rerunnable notebook/code and HTML export.
- [ ] Final package `groupID_lab1.zip`.
