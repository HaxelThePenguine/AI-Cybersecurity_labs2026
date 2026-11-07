# Lab 1 - Answers and notes

**Labels:** `[PDF §...]` identifies questions/requests from the assignment (wording may be shortened). `[Our note]` identifies additional discussion. Pending answers are explicitly marked.

**Current progress:** We have implemented Task 1 preprocessing and completed our Task 2A baselines and Task 2B comparisons. Our logbook contains runs 1-5; Task 2C and Tasks 3-6 remain pending. We have not evaluated test.

## Task 1 - Preprocessing

### 1. Inspect the data

**[PDF §5.1] Report samples, classes, balance and data-quality issues.**

The raw CSV contains **31,507 samples**, 16 numerical features and one label column. We retain Destination Port as a numerical feature, as required by the assignment.

| Class | Raw samples | Raw % | Clean samples | Clean % | Removed |
| --- | --- | --- | --- | --- | --- |
| Benign | 20,000 | 63.48 | 19,240 | 65.48 | 760 |
| DoS Hulk | 5,000 | 15.87 | 3,868 | 13.16 | 1,132 |
| PortScan | 5,000 | 15.87 | 4,849 | 16.50 | 151 |
| Brute Force | 1,507 | 4.78 | 1,427 | 4.86 | 80 |

Brute Force is the rarest class before and after this cleaning. Benign is the majority. Our cleaning affects the classes unevenly, especially DoS Hulk, so we base our subsequent analysis on the cleaned distribution.

The raw file has **20 missing cells**, all in Flow Bytes/s, affecting 20 rows, and **2,111 duplicate rows** (`duplicated().sum()`, excluding first occurrences). Our pipeline additionally removes rows with infinities and selected negative measurements. The final dataset has no missing values, infinities or exact duplicate rows. We still need to complete our checks for implausible/degenerate values: our current negative-value filter does not cover every feature.

### 2. Cleaning decisions

**[PDF §5.2] What did you do with missing values/duplicates, why, and how many samples remain?**

We remove incomplete rows, exact duplicates, non-finite rows, and rows negative in selected non-negative feature columns. The operations are sequential:

| Step | Rows removed at this step | Rows remaining |
| --- | --- | --- |
| Raw CSV | - | 31,507 |
| Drop missing values | 20 | 31,487 |
| Drop exact duplicates | 2,094 | 29,393 |
| Replace +/- infinity with NaN, then drop NaN | 7 | 29,386 |
| Reject selected negative feature values | 2 | 29,384 |

**2,123 rows are removed overall.** The raw duplicate count (2,111) differs from the 2,094 removed during deduplication because missing-value removal happens first; we therefore do not add these counts as independent raw-file totals.

The negative-value filter covers Flow Duration, Flow IAT Mean, Fwd PSH Flags, Bwd Packet Length Mean, Bwd Packet Length Max, SYN Flag Count, Fwd Packet Length Mean, Fwd IAT Std, Packet Length Mean, Fwd Packet Length Max, Subflow Fwd Packets, Total Fwd Packets and Destination Port. We currently select these columns by position; we still need to replace the indices with explicit names to make this choice clearer. Flow Bytes/s, Flow Packets/s and Down/Up Ratio are not covered by that filter.

**[Our note] Our cleaning rationale.** We remove the few incomplete/non-finite rows rather than impute their values. We deduplicate before splitting to prevent identical full rows from appearing across partitions, while recognizing that this changes empirical traffic frequencies and may remove genuine repeated flows. We reject negative durations/counts/lengths because these measurements should be non-negative. We documented this rationale after implementing the pipeline. We still need to check the remaining feature-validity conditions and possible conflicting labels.

### 3. Split and label encoding

**[PDF §5.3] Which split, should it be stratified, and where do you fit preprocessing?**

We use two stratified splits with `random_state=42` produce approximately **70% train / 15% validation / 15% test**. Stratification preserves the rare Brute Force class in each partition.

| Class | Train | Validation | Test |
| --- | --- | --- | --- |
| Benign | 13,467 | 2,886 | 2,887 |
| Brute Force | 999 | 214 | 214 |
| DoS Hulk | 2,708 | 580 | 580 |
| PortScan | 3,394 | 728 | 727 |
| Total | 20,568 | 4,408 | 4,408 |

We fit LabelEncoder on training labels and reuse it for validation/test: Benign=0, Brute Force=1, DoS Hulk=2, PortScan=3. We fit both candidate scalers on training only. Fitting a scaler on all data would let held-out distributions affect preprocessing and compromise independent evaluation. We will select models/hyperparameters on validation and reserve test for the requested fixed-model evaluations.

### 4. Scaling, tails and exploratory statistics

**[PDF §5.4] Which scaling was picked and why? How do outliers inform the choice?**

We have implemented two candidate transformations: StandardScaler on all features, and log1p on Flow Duration followed by StandardScaler on all features. Histograms compare the transformed training Flow Duration. We use StandardScaler for Task 2A, fitting it on training only and passing the standardized arrays to the model. It addresses the large differences in feature scale while keeping our starting pipeline simple. We have not trained the log1p alternative, so we cannot claim it is better or worse.

We computed the following training-only statistics to quantify the scale differences and long tails:

| Feature | Minimum | Median | 99th percentile | Maximum |
| --- | --- | --- | --- | --- |
| Flow Duration | 1 | 31,094.5 | 117,651,856.57 | 119,998,546 |
| Flow Bytes/s | 0 | 5,250.04 | 12,333,333 | 2,070,000,000 |

Standardization centres/scales features but does not remove skewness or make it robust to extreme values: large values influence mean and standard deviation. Log1p compresses Flow Duration's upper tail and is defined at zero; applying it to this feature alone does not address every heavy-tailed feature. These observations motivate our scaling comparison, but we have not trained models to compare the two transformations yet and cannot claim a classification improvement.

**[Our note] Exploratory class separability.** We computed a one-vs-rest Fisher-like score and averaged it over features: Benign 0.092924, Brute Force 0.142394, PortScan 0.170629, DoS Hulk 1.046245. This is an exploratory heuristic, not a classifier result or proof of which class is hardest. Before our first scaled Task 2A baseline, we predicted that Brute Force would be hardest and DoS Hulk easier; we compare this prediction with our results below.

## Task 2 - Your first network

### Task 2A - Minimal classifier

**[PDF §6.1] What did we choose, and why?**

We use 16 -> 64 -> 4, one hidden ReLU layer, unweighted cross-entropy, AdamW lr=5e-4 and explicit weight_decay=0.01, batch 64. This gives us a small nonlinear reference model before tuning. We standardize using training-only statistics, seed initialization and shuffling with 42, and use CPU (one thread). We train up to 100 epochs with patience 20 and min_delta=1e-4; we restore the lowest-validation-loss weights. Small validation improvements still update the best checkpoint; min_delta controls patience only.

**[PDF §6.1 - Predict first] Which classes do we expect to be hardest?**

Before our first scaled baseline, we expected Brute Force to be hardest because it has only 999 training samples (4.86%). DoS Hulk may be easier because its exploratory separability score is highest (1.046). Benign's low score (0.093) suggests possible difficulty despite its larger support. These are hypotheses, not conclusions from classification results.

**[PDF §6.1] How do we select the best epoch? Do the curves converge, and does our prediction hold?**

We restore **epoch 98**, the minimum-validation-loss checkpoint (CE **0.11698**). We reached 100 epochs; patience-based early stopping did not trigger. The final printed epoch is not automatically our selected model.

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| Benign | 0.9670 | 0.9643 | 0.9656 | 2886 |
| Brute Force | 0.7743 | 0.9299 | 0.8450 | 214 |
| DoS Hulk | 0.9711 | 0.9259 | 0.9479 | 580 |
| PortScan | 0.9403 | 0.9299 | 0.9351 | 728 |

**Validation accuracy: 0.9519; macro-F1: 0.9234.** Training plus per-epoch validation: 26.55 s on CPU. The notebook contains the full loss curves and classification report.

Our losses drop from 0.7473/0.4903 (train/validation, epoch 1) to 0.1176/0.1174 (epoch 100). They remain close and flatten, without sustained validation deterioration. Improvement is still gradual near the end, so we cannot claim complete convergence.

Our hardest-class prediction holds for **F1**: Brute Force is lowest at 0.8450. We detect 199/214 Brute Force flows (recall 0.9299), but 58/257 Brute Force predictions are false positives (precision 0.7743). Its weakness is therefore precision rather than uniquely low recall: DoS Hulk has slightly lower recall (0.9259). DoS Hulk performs well, but Benign has the highest F1 despite its low exploratory separability score. The heuristic did not correctly rank all classes. These results come from one seed/split; test remains unused.

**[Our note] Why the Fisher-like heuristic misranked Benign (written after run 2; our recorded hypothesis above is unchanged).** The score separates the classes poorly: Benign, Brute Force and PortScan all fall between 0.09 and 0.17, so it gives no reliable ranking among them; only DoS Hulk stands out (1.05). It also ignores class frequencies, and Benign's one-vs-rest "rest" group combines three heterogeneous attack classes, which inflates the denominator. Class frequency matched the outcome better: Brute Force has 999 training samples, about 13.5 times fewer than Benign (13,467; roughly one order of magnitude) and 2.7-3.4 times fewer than DoS Hulk (2,708) and PortScan (3,394), and it has the lowest F1, although through precision rather than recall.

Our exploratory raw-input attempt was interrupted; the numbered comparisons below refer to our completed scaled baselines and controlled Task 2B runs.

### Task 2B - Why the fundamentals matter

**[PDF §6.2] What did we change and predict before training?**

We keep our run 2 setup: seed 42, the same split, FFNN 16 -> 64 -> 4 with ReLU, AdamW weight_decay=0.01, batch 64, maximum 150 epochs, patience 20 and min_delta=5e-5. Each variant starts from fresh, identically seeded weights and a new optimizer. S1 changes only scaling; S2 and S3 change only LR.

Before training, we expected S2 > S1 > S3 in severity: S2 would oscillate or diverge, S1 would have large/unstable losses, and S3 would improve too slowly. We expected scaling to be the first fundamental to fix.

**[PDF §6.2] What happened?**

| Run | Setup | Val loss | Accuracy | Macro-F1 | Epochs | Best epoch | Train + val s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | Scaled reference, lr=5e-4 | 0.10890 | 0.9578 | 0.9325 | 150 | 145 | 39.91 |
| 3 | S1: raw inputs, lr=5e-4 | 1218.416544 | 0.9326 | 0.8931 | 35 | 15 | 9.24 |
| 4 | S2: scaled, lr=0.5 | 0.333414 | 0.9363 | 0.8953 | 33 | 13 | 8.80 |
| 5 | S3: scaled, lr=5e-6 | 0.370412 | 0.9004 | 0.7391 | 150 | 150 | 39.71 |

All metrics use the minimum-validation-loss checkpoint, restored after training. Times include training and per-epoch validation. The notebook contains the three loss plots; test remains unused.

- **S1 - missing scaling:** training starts with a loss around 78,000 and both curves remain large and erratic. Early stopping occurs at epoch 35; we restore epoch 15. Unequal feature scales make optimization poorly conditioned and can produce very large logits. Despite accuracy 0.9326, validation CE is 1218.416544: correct labels on many samples do not prevent a huge penalty from confident mistakes. The model learned useful boundaries, but its loss behavior is poor.
- **S2 - excessive LR:** training and validation losses repeatedly spike; validation reaches roughly 14 before falling again. Large updates can overshoot low-loss regions instead of settling. Early stopping occurs at epoch 33; we restore epoch 13. Macro-F1 is 0.8953, below the reference. Our prediction of instability holds, but we did not observe sustained numerical divergence or complete learning failure at lr=0.5.
- **S3 - tiny LR:** the curves decrease smoothly but slowly, from about 1.36 to 0.37. We reach all 150 epochs and the best checkpoint is the last one. This is slow optimization/under-training within our epoch budget, rather than the oscillation seen in S2. Macro-F1 falls to 0.7391 despite accuracy 0.9004.

**[PDF §6.2] Rank the damage and choose which fundamental to fix first.**

Using validation macro-F1, our observed ranking is **S3 > S1 > S2**, with S1 and S2 very close. Relative to the reference (0.9325), the drops are 0.1934, 0.0394 and 0.0372 respectively. Our initial severity ranking was wrong: the tiny LR hurts classification most within 150 epochs, even though its curve looks smoother. If we rank numerical loss behavior instead, S1 is the clearest failure; a single ranking does not describe every symptom. We have only one seeded run per variant and do not interpret the small S1/S2 difference as a robust ordering.

We would still fix **scaling first**, then choose a sensible LR. Scaling addresses the feature-magnitude differences that make optimization difficult; the S3 result shows that scaling alone is not enough when updates are too small for the available budget. These runs change one fundamental at a time, not their interaction.

**[PDF §6.2] What would the curve shape suggest if we did not know the change?**

Very large, erratic losses would make us inspect feature scales and extreme values. Repeated sharp spikes would make us inspect an excessive LR. A smooth but slow decline would suggest a tiny LR and insufficient optimization time. These are diagnostic clues, not unique proofs: our controlled changes let us connect these particular curves to their causes.

### Task 2C - Lock in our baseline

**[PDF §6.3] How do we choose and evaluate our baseline?**

Our editable setup is in `HP_2C`: width 64, batch 64, AdamW lr=5e-4, weight_decay=0.01, maximum 200 epochs, patience 20, min_delta=5e-5 and seed 42. Relative to run 2, we initially extend only the epoch budget. We use the same training-fitted StandardScaler and the shared training loop, which restores the lowest-validation-loss checkpoint.

**Before training:** we expect a modest benefit from additional epochs and better validation performance from ReLU than from removing the hidden activation. We will check the per-class metrics rather than assume a benefit for every class.

**[PDF §6.3] Does changing activation affect per-class behavior? Can we choose on test?**

We train ReLU and Linear (Identity) candidates from identically seeded linear-layer weights, keeping all other settings fixed. We print each validation classification report, confusion matrix, loss, accuracy, macro precision/recall/F1, weighted F1, epochs and training time. We select the activation by validation macro-F1; ReLU wins an exact tie. Without a hidden nonlinearity, the two linear layers form an overall linear classifier.

We then freeze our setup and evaluate only the selected model on test. Choosing between activations using test scores would turn test into tuning data and bias our generalization estimate. Our test cell is separate from tuning and reports the full classification report, confusion matrix and validation/test gaps, including per-class F1.

**Results pending.** The code is ready; no Task 2C training or test evaluation has been executed yet. We will record the two training attempts in the logbook when run and judge generalization from the measured gaps.

## Task 3 - When a feature biases the model

**[PDF §7] Discuss the port-80 artefact; predict Brute Force recall after changing only its TEST destination port 80 -> 8080, then evaluate the unchanged Task 2C baseline.**

**Pending.** The assignment states the port association; it is not evidence that our model has learned it. We still need to verify the association and record our prediction. We will use the fitted baseline scaler for the counterfactual inputs and evaluate the fixed model without retraining. No counterfactual result is available.

**[PDF §7, pp.6-7] Remove Destination Port from the original data, redo cleaning/split/scaling, compare class counts, identify the collapsed/rarest class and defend deduplication.**

**Pending measurement and decision.** No port-free pipeline/counts exist in the notebook. Removing a distinguishing feature can make previously distinct rows identical. We still need to measure the class-specific change and justify our deduplication decision. We will use port-free data for all subsequent tasks.

## Task 4 - The rare class: loss and imbalance

**[PDF §8] Predict the hardest class, retrain the port-free baseline and report per-class detection. Then compare weighted cross-entropy; explain weight partition, accuracy versus macro-F1 and metric choice.**

**Pending.** No port-free training or weighted-loss comparison exists. We will compute class weights from training labels only, so validation/test do not influence the training objective. We still need to record our expected accuracy/macro-F1 trade-off, run the comparison and interpret the per-class results. We have not measured a direction of change yet.

## Task 5 - Varying the hyperparameters

**[PDF §9.1 - 5A] Justify 2-3 deeper candidates and assess whether depth helps.**

**Pending.** We will compare our deeper candidates against the simple port-free Task 4 baseline on validation. We have not selected or trained those candidates yet.

**[PDF §9.2 - 5B] Compare three batch sizes; predict generalization and wall-clock time, then measure both.**

**Pending.** No batch-size comparison or training-time measurement exists.

**[PDF §9.3 - 5C] Compare SGD, SGD+momentum and AdamW while varying LR; does optimizer or LR dominate?**

**Pending.** No controlled optimizer/LR comparison exists. We have about 10 training runs for the whole of Task 5 and still need to allocate them across the comparisons.

**[PDF §9.4 - 5D] Compare the validation-selected best model and the Task 4 baseline on TEST; was complexity worth the runs?**

**Pending.** We have not selected these models or run this comparison yet. We will base our verdict on our logbook and the fixed-model test evaluations.

## Task 6 - Optimizations

**[PDF §10] Predict/train the port-free 256 -> 128 -> 64 -> 32 -> 16 network (ReLU, CE, AdamW lr=5e-4, batch 128, about 150-200 epochs, no regularization/early stopping) and locate overfitting in the curves.**

**Pending.** We have not run this experiment yet. We will explicitly use weight_decay=0 for the initial unregularized run because AdamW's default is nonzero.

**[PDF §10] Try a smaller model or early stopping first, then weight decay, dropout and batch normalization one change at a time; what helps most? Compare the final large network with the Task 4 baseline on TEST.**

**Pending.** We have about six runs for this task. We will evaluate each modification on validation before adding another. We have no optimization results or final comparison yet.

**[PDF §10 - Final reflection] Which decisions bought the most performance per unit of effort?**

**Pending.** We have only established our initial working baseline, so we cannot compare the benefits of later design choices yet. We will compare our measured validation improvements, training times and run costs once the experiments are complete.

## Logbook, reproducibility and submission

**[PDF §4] One row per training run, task tag, one change, hypothesis BEFORE running, validation result and conclusion; about 25 runs in total.**

Our logbook contains five numbered runs: two Task 2A baselines and S1-S3 for Task 2B. We recorded our S1-S3 hypotheses before training. Preprocessing and inference do not consume training runs; the whole-lab budget is approximately 25 runs.

**[PDF §2/§11] Required deliverables and reasoning.**

- [ ] Report `groupID_lab1.pdf`, maximum 10 pages, with decisions, tables, curves and explanations tied to our results.
- [ ] Complete logbook (separate or report appendix; excluded from page limit), including advance hypotheses for future runs.
- [ ] Fully executed, rerunnable `.ipynb`, with outputs and appropriate seeds.
- [ ] HTML export of the notebook.
- [ ] Our final package `groupID_lab1.zip`, containing notebook/code, report, HTML and logbook.

We use these notes and our logbook as working material for the final report. We have organized the notebook by task and marked our remaining work; the existing code and saved outputs are unchanged.

