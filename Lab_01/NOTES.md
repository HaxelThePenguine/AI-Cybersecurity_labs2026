# Lab 1 - Answers and notes

**Labels:** `[PDF §...]` identifies questions/requests from the assignment (wording may be shortened). `[Our note]` identifies additional discussion. Pending answers are explicitly marked.

**Current progress:** We have implemented Task 1 preprocessing and started Task 2A, but our training attempt was interrupted. We checked the counts below against `Materiale/dataset_lab_1.csv` using our preprocessing pipeline. We have not completed a baseline or measured classification metrics yet. We have recorded this attempt in `LOGBOOK.md`; for subsequent runs, we will record our hypotheses before training.

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

We have implemented two candidate transformations: StandardScaler on all features, and log1p on Flow Duration followed by StandardScaler on all features. Histograms compare the transformed training Flow Duration. **We have not yet connected either transformation to our training tensors:** our saved attempt uses raw X_train/X_val/X_test. We still need to choose and apply the baseline scaling and justify it using validation results.

We computed the following training-only statistics to quantify the scale differences and long tails:

| Feature | Minimum | Median | 99th percentile | Maximum |
| --- | --- | --- | --- | --- |
| Flow Duration | 1 | 31,094.5 | 117,651,856.57 | 119,998,546 |
| Flow Bytes/s | 0 | 5,250.04 | 12,333,333 | 2,070,000,000 |

Standardization centres/scales features but does not remove skewness or make it robust to extreme values: large values influence mean and standard deviation. Log1p compresses Flow Duration's upper tail and is defined at zero; applying it to this feature alone does not address every heavy-tailed feature. These observations motivate our scaling comparison, but we have not trained models to compare the two transformations yet and cannot claim a classification improvement.

**[Our note] Exploratory class separability.** We computed a one-vs-rest Fisher-like score and averaged it over features: Benign 0.092924, Brute Force 0.142394, PortScan 0.170629, DoS Hulk 1.046245. This is an exploratory heuristic, not a classifier result or proof of which class is hardest. We have not yet recorded a pre-training prediction for our next run.

## Task 2 - Your first network

### Task 2A - Minimal classifier

**[PDF §6.1] State architecture, loss, optimizer, batch size, learning rate and stopping criterion.**

Our initial attempt uses **16 -> 64 -> 4**, one hidden ReLU layer, CrossEntropyLoss, AdamW with lr=5e-4, batch size 64 and a requested 100 epochs. We did not explicitly pass AdamW's weight_decay; the installed implementation defaults to **0.01**, so this attempt is not free of weight decay. Training batches are shuffled; validation/test batches are not. Saved output reports CPU. The device variable does not move the model/tensors to a GPU.

We declared PATIENCE=20 and MIN_DELTA=1e-4, but have not connected them to the loop yet. The loop has **no early stopping and no best-checkpoint save/restore**. `num_epochs=100` is separate from the unused MAX_EPOCHS variable. Only the split seed is fixed; network initialization and training shuffle seeds are not set.

**[PDF §6.1 - Predict first] Which classes should be hardest, and why?**

**We did not document a hypothesis before this attempt.** Brute Force has only 999 training samples, which gives us reason to expect difficulties detecting it. This is our current interpretation, not a recorded advance hypothesis for the interrupted run. We will write the next run's hypothesis in LOGBOOK.md before training.

**[PDF §6.1] Show training/validation curves, the validation classification report, convergence and per-class results. How is the best epoch selected?**

Our saved attempt ends in **KeyboardInterrupt**, after 17 fully printed epochs. Epoch 1: training loss 38,434.1401; validation loss 2,240.3676. Epoch 17: training loss 2,128.4318; validation loss 2,784.0391. Among those 17 epochs, the minimum printed validation loss is **819.4080 at epoch 15** (training loss 2,366.9472); its weights were not saved. It is not a selected checkpoint.

Losses fluctuate strongly. Raw, differently scaled features are a plausible contributor, but there is no matched scaled run establishing causality. No loss plot, classification report, macro-F1, accuracy or per-class recall is available. Convergence/generalization and class-level predictions therefore remain unanswered. We have therefore not established a completed Task 2A baseline yet.

### Task 2B - Why the fundamentals matter

**[PDF §6.2] Predict, run and plot S1 (raw features), S2 (too-high LR), S3 (too-low LR); name/explain each failure, rank severity and diagnose curves.**

**Pending.** We still need to complete our scaled Task 2A baseline. We will then vary one fundamental at a time while keeping the rest of the setup fixed. The interrupted raw-input attempt is not a completed S1 comparison: there is no corresponding completed baseline and no documented advance hypothesis. No S2/S3 runs or observed ranking exist.

### Task 2C - Lock in the baseline

**[PDF §6.3] Report validation/test classification reports and generalization; switch activation as a controlled experiment and discuss test-set selection.**

**Pending.** No finalized baseline, test inference or activation comparison exists. We will select the activation on validation; selecting it from test scores would make test part of our tuning process.

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

**Pending.** Our single interrupted run has no classification scores, so we cannot draw this conclusion yet. We will compare our measured validation improvements, training times and run costs once the experiments are complete.

## Logbook, reproducibility and submission

**[PDF §4] One row per training run, task tag, one change, hypothesis BEFORE running, validation result and conclusion; about 25 runs in total.**

We have logged the one training attempt visible in our saved notebook, including its interruption and the missing advance hypothesis. Our preprocessing and documentation work do not count as training runs. We still need to reconcile any earlier reruns before stating an exact remaining budget, because overwritten outputs would not be recoverable from the notebook.

**[PDF §2/§11] Required deliverables and reasoning.**

- [ ] Report `groupID_lab1.pdf`, maximum 10 pages, with decisions, tables, curves and explanations tied to our results.
- [ ] Complete logbook (separate or report appendix; excluded from page limit), including advance hypotheses for future runs.
- [ ] Fully executed, rerunnable `.ipynb`, with outputs and appropriate seeds.
- [ ] HTML export of the notebook.
- [ ] Our final package `groupID_lab1.zip`, containing notebook/code, report, HTML and logbook.

We use these notes and our logbook as working material for the final report. We have organized the notebook by task and marked our remaining work; the existing code and saved outputs are unchanged.
