# Lab 1 - Answers and notes

**Labels:** `[PDF §...]` identifies questions/requests from the assignment (wording may be shortened). `[Our note]` identifies additional discussion. Pending answers are explicitly marked.

**Current progress:** We have completed Tasks 2A-2C and selected run 7 as our baseline. The logbook records runs 1-7 and the Linear comparison as 7bis. Task 3 counterfactual and port-free preprocessing are complete; Tasks 4-6 remain pending.

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

**[PDF §6.1] Our setup and historical attempts.**

We use 16 -> 64 -> 4, ReLU, unweighted cross-entropy, AdamW lr=5e-4 and weight_decay=0.01, batch 64, seed 42 and CPU (one thread). We standardize using training-only statistics and restore the lowest-validation-loss checkpoint. The two attempts below are historical stages of the same baseline; the notebook currently shows **run 2**.

| Run | Historical attempt | Maximum epochs | Patience | min_delta | Best epoch | Val loss | Accuracy | Macro-F1 | Train + val s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | First attempt | 100 | 20 | 1e-4 | 98 | 0.11698 | 0.9519 | 0.9234 | 26.55 |
| 2 | Second attempt; current notebook output | 150 | 20 | 5e-5 | 145 | 0.10890 | 0.9578 | 0.9325 | 41.57 |

**[PDF §6.1 - Predict first] Which classes did we expect to be hardest?**

Before our first scaled attempt, we expected Brute Force to be hardest because it has only 999 training samples (4.86%). DoS Hulk's higher exploratory separability score suggested easier classification; Benign's low score suggested possible difficulty despite its larger support.

**Run 1 - first attempt, 100 epochs (historical validation report).**

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| Benign | 0.9670 | 0.9643 | 0.9656 | 2886 |
| Brute Force | 0.7743 | 0.9299 | 0.8450 | 214 |
| DoS Hulk | 0.9711 | 0.9259 | 0.9479 | 580 |
| PortScan | 0.9403 | 0.9299 | 0.9351 | 728 |

Brute Force had the lowest F1 (0.8450), mainly due to precision (0.7743), despite recall 0.9299. Our prediction held for F1, but not as a prediction of uniquely low recall.

**Run 2 - second attempt, 150 epochs (report currently saved in the notebook).**

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| Benign | 0.9663 | 0.9740 | 0.9701 | 2886 |
| Brute Force | 0.8089 | 0.9299 | 0.8652 | 214 |
| DoS Hulk | 0.9907 | 0.9207 | 0.9544 | 580 |
| PortScan | 0.9496 | 0.9313 | 0.9404 | 728 |

Brute Force remains the hardest class by F1 (0.8652), with higher precision (0.8089) and unchanged recall (0.9299). Macro-F1 improves from 0.9234 to 0.9325. Epoch budget and min_delta both changed, so this is not an isolated one-factor comparison.

**[PDF §6.1] Best checkpoint and convergence.**

We select by minimum validation loss, rather than automatically keeping the final epoch: epoch 98 for run 1 and epoch 145 for run 2. Early stopping did not trigger in either attempt. In run 1, train/validation losses end at 0.1176/0.1174; in run 2 they end at 0.10901/0.11041. The curves stay close and flatten, without sustained validation deterioration. Continued small improvements do not establish complete convergence. Both attempts use validation only.

**[Our note] Why the Fisher-like heuristic misranked Benign (written after run 2; our recorded hypothesis above is unchanged).** The score separates the classes poorly: Benign, Brute Force and PortScan all fall between 0.09 and 0.17, so it gives no reliable ranking among them; only DoS Hulk stands out (1.05). It also ignores class frequencies, and Benign's one-vs-rest "rest" group combines three heterogeneous attack classes, which inflates the denominator. Class frequency matched the outcome better: Brute Force has 999 training samples, about 13.5 times fewer than Benign (13,467; roughly one order of magnitude) and 2.7-3.4 times fewer than DoS Hulk (2,708) and PortScan (3,394), and it has the lowest F1, although through precision rather than recall.

### Task 2B - Why the fundamentals matter

**[PDF §6.2] What did we change and predict before training?**

We keep our run 2 setup: seed 42, the same split, FFNN 16 -> 64 -> 4 with ReLU, AdamW weight_decay=0.01, batch 64, maximum 150 epochs, patience 20 and min_delta=5e-5. Each variant starts from fresh, identically seeded weights and a new optimizer. S1 changes only scaling; S2 and S3 change only LR.

Before training, we expected S2 > S1 > S3 in severity: S2 would oscillate or diverge, S1 would have large/unstable losses, and S3 would improve too slowly. We expected scaling to be the first fundamental to fix.

**[PDF §6.2] What happened?**

| Run | Setup | Val loss | Accuracy | Macro-F1 | Epochs | Best epoch | Train + val s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | Scaled reference, lr=5e-4 | 0.10890 | 0.9578 | 0.9325 | 150 | 145 | 41.57 |
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

**[PDF §6.3] Which model is our baseline?**

We lock **run 7**: StandardScaler fitted on training only; 16 -> 64 -> 4 with ReLU; unweighted cross-entropy; AdamW lr=1e-3, weight_decay=0.005; batch 64; maximum 200 epochs; patience 20; min_delta=5e-5; seed 42; CPU. We restore the minimum-validation-loss checkpoint at **epoch 196**. Training plus per-epoch validation took **50.33 s for ReLU alone**.

Compared with run 6, we changed only weight decay (0.01 -> 0.005). Validation macro-F1 increases from 0.95076 to **0.95135** (+0.00059), accuracy from 0.96688 to **0.96756**, and loss decreases from 0.09209 to **0.08986**. We retain this as our best measured baseline, while recognizing that the improvement is small and comes from one seed. The earlier run 2 -> run 6 comparison changed both LR and epoch budget, so it does not isolate the LR effect.

**[PDF §6.3] Compare validation and test. Does it generalize?**

The full classification reports and confusion-matrix heatmaps are in the notebook.

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

Test - validation is **+0.02 percentage points in accuracy** and **+0.38 points in macro-F1**. Per-class F1 is also close; the largest difference is Brute Force (+0.0147). These results support good generalization on this stratified split. We freeze this baseline now.

**[PDF §6.3] Does switching the activation change per-class behavior?**

Our advance prediction was that ReLU would outperform Linear, particularly on the harder classes. We compare them with identical initialization and settings, including weight_decay=0.005. Linear means Identity between the two linear layers, giving an overall linear classifier.

| Class | ReLU precision | ReLU recall | ReLU F1 | Linear precision | Linear recall | Linear F1 |
| --- | --- | --- | --- | --- | --- | --- |
| Benign | 0.9716 | 0.9844 | 0.9780 | 0.9472 | 0.9321 | 0.9396 |
| Brute Force | 0.9132 | 0.9346 | 0.9238 | 0.8071 | 0.7430 | 0.7737 |
| DoS Hulk | 0.9665 | 0.9448 | 0.9555 | 0.9941 | 0.8672 | 0.9263 |
| PortScan | 0.9685 | 0.9286 | 0.9481 | 0.7827 | 0.9299 | 0.8500 |

ReLU has validation macro-F1 **0.95135**, versus **0.87240** for Linear. The biggest F1 loss without ReLU is on Brute Force (0.9238 -> 0.7737): recall falls from 0.9346 to 0.7430. PortScan precision also drops sharply (0.9685 -> 0.7827), while DoS Hulk loses recall (0.9448 -> 0.8672) despite higher precision. The nonlinear model provides a better balance here; the benefit is not identical across classes. ReLU completes 200 epochs, restoring epoch 196; Linear stops at 75, restoring epoch 55. Linear (run 7bis) took **18.05 s**, separate from ReLU's 50.33 s.

**[PDF §6.3] Would comparing the activations on test be fair for selection?**

No. We choose the activation and hyperparameters using validation macro-F1, with checkpoint selection by validation loss. Choosing from test scores would make test part of tuning and bias the reported generalization estimate. We evaluate only the selected ReLU model on test.

## Task 3 - When a feature biases the model

**[PDF §7] Is Brute Force always on port 80 a general property? What might our model learn?**

We think our model may indeed have learned a port-based shortcut: all Brute Force flows in our dataset use Destination Port 80. We verified 1,507/1,507 in the raw data, 1,427/1,427 after cleaning and 214/214 in our test split. This association is an artefact of this dataset, not a general property of brute-force attacks, which can target services on other ports. The association makes port 80 a possible clue for our model; it does not establish that the model uses only that feature.

**[PDF §7 - Predict first] What do we expect after changing Brute Force test ports from 80 to 8080?**

Before inference, we expect Brute Force recall to decrease: if our baseline relies on the port-80 association, changing that feature could make it miss otherwise identical Brute Force flows. We did not predict its exact size.

**[PDF §7] Counterfactual test without retraining.**

We reuse our trained Task 2C baseline (run 7) and its fitted StandardScaler. We copy the original raw test features and change only Destination Port for the 214 Brute Force samples, from 80 to 8080. We keep all labels, other feature values, non-Brute-Force samples, training and validation data unchanged. We transform both test versions with the existing scaler; we do not fit preprocessing again or retrain the network.

The Task 3 cells print both classification reports, confusion-matrix heatmaps, aggregate metrics, Brute Force recall before/after and the number of changed predictions. They also check that the model weights, original test inputs and non-Brute-Force predictions remain unchanged.

**[PDF §7] Did our prediction hold? What does this reveal about our model?**

Yes, our prediction was confirmed. Changing only Destination Port from 80 to 8080 for the 214 Brute Force test flows reduces their recall from **0.9626 to 0.0374**, a drop of **92.52 percentage points**. We correctly detect **206/214** before the change, but only **8/214** afterwards. All **198 changed predictions** move from Brute Force to Benign; the eight flows originally predicted as PortScan remain PortScan. Predictions for every non-Brute-Force sample remain unchanged.

| Metric | Original test | Brute Force port 8080 |
| --- | --- | --- |
| Brute Force recall | 0.9626 | 0.0374 |
| Brute Force precision | 0.9156 | 0.2963 |
| Brute Force F1 | 0.9385 | 0.0664 |
| Overall accuracy | 0.96779 | 0.92287 |
| Macro-F1 | 0.95516 | 0.72906 |
| Cross-entropy | 0.08612 | 0.40250 |

This makes us think that our model had learned a strong shortcut linking Brute Force to port 80. Its Brute Force detection almost collapses when that single feature changes, even though the remaining flow characteristics and model weights are identical. In this experiment, detection depends heavily on the dataset's port association rather than robust, port-independent Brute Force behavior. The model may still use other features, but they do not preserve detection after this change.

The overall accuracy still exceeds 92% because Brute Force accounts for only 214/4,408 test samples. Macro-F1 and per-class recall expose the failure that accuracy alone would hide. We performed inference only with the unchanged Task 2C baseline and fitted scaler; this comparison adds no training run.

### Task 3B - Port-free preprocessing

**[PDF §7, pp.6-7] Count the classes after cleaning and compare with before. Which class shrinks, and by how much?**

We reload the original CSV and remove Destination Port before cleaning and deduplication. We keep the same cleaning policy: missing values, exact duplicate rows, non-finite values and negative values in the selected non-negative features still present. Clean samples decrease from **29,384 to 22,468**, with **15 input features** remaining.

| Class | With port | Without port | Removed | Removed % | New share % |
| --- | --- | --- | --- | --- | --- |
| Benign | 19,240 | 16,888 | 2,352 | 12.22 | 75.16 |
| Brute Force | 1,427 | 1,427 | 0 | 0.00 | 6.35 |
| DoS Hulk | 3,868 | 3,868 | 0 | 0.00 | 17.22 |
| PortScan | 4,849 | 285 | 4,564 | 94.12 | 1.27 |

**PortScan collapses from 4,849 to 285 samples: 4,564 fewer, a reduction of 94.12%.** DoS Hulk and Brute Force remain unchanged. Benign also shrinks by 2,352 samples (12.22%), so its change is smaller proportionally but not negligible.

**[PDF §7] Why does PortScan collapse? What did the earlier model know about it?**

Many PortScan flows differed only in Destination Port. Once we remove it, their remaining feature vectors and labels become identical, so deduplication merges them. Much of the original sample diversity therefore reflected different scanned ports rather than distinct behavior in the retained features. Our earlier model could exploit that port-specific structure; good PortScan scores did not by themselves establish robust recognition of diverse, port-independent scan behavior. This does not mean that every remaining feature is useless.

**[PDF §7] Which class is now rarest, and how balanced is the dataset?**

PortScan is now the rarest class: **285 samples (1.27%)**. Benign accounts for **75.16%**, DoS Hulk **17.22%**, and Brute Force **6.35%**. The largest-to-smallest class ratio is about **59.3:1**, compared with about 13.5:1 before removal. The imbalance is therefore substantially stronger, and the identity of the rarest class changes from Brute Force to PortScan.

**[PDF §7] Do we still deduplicate? Why?**

Yes. We keep deduplication because repeated identical labelled vectors could otherwise appear in both training and held-out partitions after a random split, making evaluation depend on repeated observations. Keeping them just to restore PortScan's sample count would not add new feature information. The trade-off is a much smaller, less representative sample of unique PortScan patterns and greater uncertainty in its metrics. We treat the new counts as counts of unique labelled observations, not real traffic prevalence, and assess per-class metrics alongside macro-F1.

**Our new split and scaling.** We create a fresh stratified 70/15/15 split with random_state=42, preserving class proportions as closely as integer counts allow. We fit a new label encoder and StandardScaler on the new training partition only, then reuse them unchanged on validation/test.

| Class | Train | Validation | Test |
| --- | --- | --- | --- |
| Benign | 11,821 | 2,533 | 2,534 |
| Brute Force | 999 | 214 | 214 |
| DoS Hulk | 2,708 | 580 | 580 |
| PortScan | 199 | 43 | 43 |
| Total | 15,727 | 3,370 | 3,371 |

The notebook keeps the port-free data in the `_3b` variables and the scaled inputs in `X_train_std_3b`, `X_val_std_3b`, `X_test_std_3b`. We use this dataset for the rest of the lab; the earlier port-based baseline and counterfactual remain separate.

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

Our logbook contains eight training entries, labelled 1-7 and 7bis: two Task 2A baselines, S1-S3, the selected ReLU configurations and the controlled Linear comparison. We recorded our S1-S3 hypotheses before training. Preprocessing and inference do not consume training runs; the whole-lab budget is approximately 25 runs.

**[PDF §2/§11] Required deliverables and reasoning.**

- [ ] Report `groupID_lab1.pdf`, maximum 10 pages, with decisions, tables, curves and explanations tied to our results.
- [ ] Complete logbook (separate or report appendix; excluded from page limit), including advance hypotheses for future runs.
- [ ] Fully executed, rerunnable `.ipynb`, with outputs and appropriate seeds.
- [ ] HTML export of the notebook.
- [ ] Our final package `groupID_lab1.zip`, containing notebook/code, report, HTML and logbook.

We use these notes and our logbook as working material for the final report. We have organized the notebook by task and marked our remaining work; the existing code and saved outputs are unchanged.

