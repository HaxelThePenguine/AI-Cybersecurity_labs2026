# Lab 2 - Answers and notes

**Labels:** `[PDF §...]` identifies questions/requests from the assignment (wording may be shortened). `[Our note]` identifies additional discussion. Pending answers are explicitly marked.

## Task 1 - Look at the data before you model it

### 1. Class balance

**[PDF §5.1] Report the proportion of malware vs goodware in train and test.**

| Dataset | Malware | Goodware |
| --- | --- | --- |
| Train | 15,714 (96.26%) | 611 (3.74%) |
| Test | 6,262 (96.26%) | 243 (3.74%) |

The training set contains approximately 26 malware samples per goodware sample.

**[PDF §5.1] What accuracy would always predicting the majority class achieve? Why can accuracy be misleading?**

On training data, always predicting malware achieves 96.26% accuracy while misclassifying every goodware sample. Accuracy therefore hides failure on the minority class.

**[PDF §5.1] Choose the metrics to report throughout the lab and explain why.**

- **Macro-F1 (primary):** averages the two class F1 scores equally, preventing the majority class from dominating the score. Each class F1 balances precision and recall.
- **Per-class precision and recall:** reveal which class suffers. Recall measures the fraction of each actual class correctly identified; precision measures the reliability of predictions for that class.
- **Confusion matrix:** shows correct predictions and both error types as counts, making their practical impact explicit.

**[PDF §5.1] What are the consequences of missing malware versus classifying goodware as malware?**

Taking malware as the positive class:
- **False negative:** malware classified as goodware; a threat goes undetected. Malware recall tracks detection coverage.
- **False positive:** goodware classified as malware; unnecessary alerts or blocking of legitimate software. Goodware recall tracks how much benign software avoids false alarms.

Both errors matter. We use macro-F1 for balanced model comparison and per-class metrics to inspect the trade-off; their operational costs have not been quantified.

### 2. Sequence lengths

**[PDF §5.2] Are the length distributions similar? Report minimum, maximum and typical lengths, and describe differences.**

| Statistic | Train | Test |
| --- | --- | --- |
| Samples | 16,325 | 6,505 |
| Minimum | 60 | 70 |
| 25th percentile | 67 | 79 |
| Median | 75 | 87 |
| Mean | 75.03 | 86.33 |
| 75th percentile | 83 | 94 |
| Maximum | 90 | 100 |
| Standard deviation | 8.95 | 9.11 |

Test sequences are longer across the reported quartiles, with similar dispersion. This indicates a shift in sequence lengths between the datasets.

**[PDF §5.2] How might length differences affect the models in Task 3?**

A candidate length of 90 covers all sequences in the supplied training file but truncates test sequences longer than 90, potentially losing useful calls. Shorter inputs need padding. The final length and truncation policy remain undecided and should be justified using training data and, where needed, validation results.

**[Our note] Can we choose a length of 100?**

The lab explicitly allows comparing train/test length distributions. However, choosing 100 solely because it is the observed test maximum would adapt preprocessing to the test set. A length of 100 needs an independent rationale; positions beyond the training maximum would receive no real-call examples during training.

Pending: inspect the length histograms and quantify the fraction truncated once a candidate length is fixed.

### 3. Vocabulary

**[PDF §5 - Vocabulary] Count distinct API calls in the training partition after the validation split. Are there unseen test calls? How many distinct calls and affected test samples?**

The training partition contains **256 distinct API calls**. The test set contains **3 distinct unseen calls**: `ControlService`, `NtDeleteKey`, and `WSASocketA`. **3 of 6,505 test samples (~0.046%)** contain at least one unseen call.

The model vocabulary remains restricted to the training partition. For BoW, unseen calls are ignored. Handling for later sequence/graph models remains to be defined.

### [Our note] Decisions still open

- Whether and how to address class imbalance during training.
- Fixed sequence length, after inspecting length distributions.

### [Our note] Data quality checks

Train and test contain no missing required values, invalid sequences, invalid labels, duplicate sequences within either dataset, or sequences with conflicting labels within either dataset. These checks require no row removal. API names, call order and repetitions are preserved. Cross-partition overlap is not covered by these checks.

### [PDF §3] How is the validation set created?

We use an 80/20 stratified split of the supplied training data, with `random_state=42`. Stratification preserves the rare goodware proportion; the fixed seed makes the split reproducible. The resulting partitions contain 13,060 training samples and 3,265 validation samples. Model selection uses validation only.

## Task 2A - Unigram Bag-of-Words

**[PDF §6.1] Choose a classifier, explain/tune its hyperparameters, and address class imbalance.**

- Classifier: small FFNN, `256 -> 64 -> 32 -> 1`, with ReLU hidden activations and one malware logit. It can learn nonlinear combinations of API counts; this is a BoW classifier, not the position-based FFNN in Task 3.
- Preprocessing: training-only CountVectorizer; `log1p` compresses large counts; StandardScaler uses training statistics only. Validation uses the fitted transformations.
- Starting settings: Adam, learning rate `0.001`, batch size `64`, `20` epochs, decision threshold `0.5`, seed `42`. These are starting choices, not demonstrated optimal values; no hyperparameter comparison is recorded yet.
- Current loss: unweighted BCEWithLogitsLoss. It operates on logits and is suitable for binary classification, but gives each sample equal weight despite the class imbalance. **The imbalance requirement remains unresolved**: a weighting strategy or a reasoned decision to keep this loss must still be evaluated/documented.

**[PDF §6.1] How many columns are produced, what does each row represent, and can call order be recovered?**

The raw unigram matrix has **256 columns**, one per distinct training API. Each row represents a sequence, and each entry counts an API's occurrences. Shapes: training `(13060, 256)`, validation `(3265, 256)`. Order cannot be recovered. After `log1p` and scaling, inputs are transformed counts rather than literal counts.

**[PDF §6.1] Give different sequences with the same unigram vector. What is lost? Can sequences with the same APIs produce different vectors?**

`[A, B, C, A]` and `[A, C, B, A]` both give `(A=2, B=1, C=1)`: positions and transitions are lost. `[A, B]` and `[A, B, A]` contain the same distinct APIs but have different counts, so their vectors differ.

**[PDF §6.1] How does CountVectorizer handle unseen test calls, and how many samples are affected?**

It ignores unseen calls: no new columns and no error. The 3 unseen APIs affect 3 test samples; known calls in those samples are still counted.

**[PDF §6.1] Predict performance before training, then report performance and explain the rare-class result.**

**Before training:** no run-specific hypothesis was recorded for the existing run. Do not invent one retrospectively; write hypotheses before future runs.

**Observed:** the saved run before notebook cleanup reports the following validation results after 20 epochs. These are historical results, not a new execution of the refactored cells.

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| Goodware (0) | 0.7733 | 0.4754 | 0.5888 | 122 |
| Malware (1) | 0.9799 | 0.9946 | 0.9872 | 3,143 |

**Macro-F1: 0.7880; accuracy: 0.9752.** The model detects most malware but correctly identifies fewer than half of goodware samples. Thus high accuracy hides poor minority-class recall. The imbalance and unweighted loss are plausible contributors; their causal effect requires a controlled comparison.

## Task 2B - Unigrams + bigrams

**[PDF §6.2] Include individual API calls and adjacent pairs using `ngram_range=(1, 2)`.**

Use the same `train_split` and `val_split`, with `tokenizer=identity` and the standard word analyzer. The recorded representation has **5,741 features**: 256 unigrams and 5,485 bigrams. Repeat the same log/scaling steps and FFNN settings; adjust only the input layer size. The larger input also increases model size.

**[PDF §6.2] Do you expect adjacent API pairs to improve classification? Explain before training.**

Adjacent pairs could distinguish execution patterns that share similar call counts. They also introduce more sparse features and parameters, which may increase overfitting. No pre-run hypothesis is recorded for the existing attempt; this reasoning is a current interpretation, not a retroactive prediction. Record an explicit hypothesis before the next run.

**[PDF §6.2] Did results match expectations? Explain improvement or lack of improvement.**

Pending: the saved bigram output contains training losses through epoch 9, but no completed validation report. Training-loss reduction alone cannot establish better classification or an advantage over unigrams.

**[PDF §6.2 and §4] Check representation changes and compare both models on original and shuffled test sequences, without retraining.**

Pending measurement. Expected behavior:
- Unigram count vectors remain identical because shuffling preserves each API's count. With the same fitted preprocessing and deterministic evaluation, predictions should also remain identical.
- Bigram vectors can change because adjacency changes. Reuse the fitted vectorizer/scaler and trained model for evaluation; do not refit them on shuffled data.
- Report both original/shuffled test metrics and whether individual predictions change. An unchanged aggregate score alone does not imply unchanged predictions for the bigram model.
- A drop would indicate sensitivity to the altered order/transition distribution, not prove that order necessarily improves performance. Global shuffling alters local and longer-range order together, so it cannot separate their contributions.

**[PDF §6.2, continued on p.7] Select the best unigram or bigram BoW model on validation and use it as the baseline.**

Pending: compare completed validation macro-F1 results. The historical unigram score is 0.7880; no completed bigram score is available. Do not select or tune on test performance.

### [PDF §4] Experiment logbook and run budget

All training attempts, including BoW attempts, belong in the lab logbook. Record settings, what changed, validation results and conclusions; mark missing historical hypotheses/timings as not recorded. Future runs need a hypothesis and a reason to spend a run before training. Keep changes controlled and within the approximate 30-run lab budget. No new training runs were executed to update these notes.
