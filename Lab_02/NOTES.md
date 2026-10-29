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

## Task 2 - Bag-of-Words

**[Our note] Setup.** Two variants per representation: Standard and Weighted. Same 80/20 stratified split, seed 42 reset per run, FFNN input -> 64 -> 32 -> 1, Adam lr=0.001, 20 epochs, batch 64, threshold 0.5; CPU. Models are chosen on validation BEFORE test evaluation. The notebook writes no files; LOGBOOK.md contains only the two final test evaluations, as requested.

### Task 2A - Unigram representation

**[PDF §6.1] How many columns, what does a row represent, and can order be recovered?**

256 columns: one per distinct training API. A row represents one sequence; raw values count API occurrences. Train shape `(13060, 256)`, validation `(3265, 256)`. Positions and transitions are discarded, so order cannot be recovered. Log1p compresses counts; StandardScaler is fitted on training only and reused unchanged.

**[PDF §6.1] Different sequences with equal vectors? Same calls with different vectors?**

`[A, B, C, A]` and `[A, C, B, A]` both give `(A=2, B=1, C=1)`. `[A, B]` and `[A, B, A]` contain the same distinct APIs but different counts, hence different vectors.

**[PDF §6.1] How are unseen test calls handled, and how many samples are affected?**

CountVectorizer ignores them without adding columns or raising an error. Task 1 found 3 unseen APIs affecting 3 test samples. Known calls in those samples are still counted.

### Classifier, imbalance and validation selection

**[PDF §6.1] Explain the classifier/hyperparameters, address imbalance, predict first and report per-class behavior.**

A small FFNN learns nonlinear combinations of counts. The controlled comparison changes only loss weighting. Weighted BCE balances total class contributions with training-only weights `N/(2*n_class)`: goodware 13.3538, malware 0.5194. Expect better minority recall, potentially at the cost of missed malware; evaluate using macro-F1 rather than accuracy. These expectations were set before the fresh runs.

| Representation | Variant | Val macro-F1 | Goodware recall | Malware recall |
| --- | --- | --- | --- | --- |
| Unigram | Standard | **0.8029** | 0.5246 | 0.9933 |
| Unigram | Weighted | 0.7691 | 0.6475 | 0.9739 |
| Unigram + bigram | Standard | **0.8573** | 0.7131 | 0.9901 |
| Unigram + bigram | Weighted | 0.7905 | 0.7787 | 0.9685 |

Select **Standard for both representations**. Weights improve goodware recall but lower macro-F1 by increasing missed malware. Keeping the unweighted loss is therefore supported by validation, not test performance. Goodware remains the more difficult class.

### Task 2B - Local order

**[PDF §6.2] Add adjacent API pairs; explain expectations and observed improvement.**

`ngram_range=(1, 2)` gives 5,741 features: 256 unigrams and 5,485 bigrams. All other settings/splits remain the same. Adjacent pairs may distinguish executions with similar counts, while more features can also overfit. The selected bigram model improves validation macro-F1 from 0.8029 to 0.8573, mainly through better goodware recall. The larger input also increases model capacity; the gain is not proof that order alone explains the difference.

### Original and shuffled TEST evaluation

**[PDF §4/§6.2] Compare each selected model on original and shuffled test sequences, without retraining.**

Shuffle API calls within each TEST sample using seed 42. Preserve sample/label order, sequence length and all occurrence counts; use identical shuffled samples for both models. Reuse the selected models, fitted vectorizers/scalers and threshold. No fitting, training or model selection uses test scores.

| Selected model | Test macro-F1 | Shuffled test macro-F1 | Changed vectors | Changed predictions | Train s |
| --- | --- | --- | --- | --- | --- |
| Unigram Standard | 0.7985 | 0.7985 | 0 | 0 | 5.31 |
| Bigram Standard | **0.8440** | 0.5185 | 6,500 / 6,505 | 390 / 6,505 | 8.96 |

**[PDF §4/§6.2] What does shuffling reveal? Can unchanged scores hide changed predictions? Can this separate local and longer-range effects?**

Unigram vectors and all predictions remain identical: this representation discards order by construction. Bigram macro-F1 drops by 0.3255 and 390 predictions change, showing sensitivity to altered transitions. Goodware recall falls from 0.6996 to 0.0617. Shuffling also changes the feature distribution and can create unseen pairs; it is not a pure causal estimate of useful order. An unchanged aggregate score alone would not imply unchanged predictions. Global shuffling disrupts local and longer-range order together and cannot separate their contributions. Results use one split and one shuffle seed.

**[PDF §6.2, continued on p.7] Which BoW model is the baseline?**

**Unigram + bigram Standard**, selected by validation macro-F1 **0.8573** before opening test results. Its test macro-F1 is **0.8440**, compared with **0.7985** for unigrams. On original test, goodware recall improves (0.5144 -> 0.6996), while malware recall falls slightly (0.9933 -> 0.9883). It takes 8.96 s versus 5.31 s on CPU, 20 epochs. This is the fixed BoW baseline for later tasks; test results do not trigger further tuning.
