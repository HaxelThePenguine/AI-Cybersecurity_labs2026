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

The model vocabulary remains restricted to the training partition. Handling unseen calls will be defined for each representation.

### [Our note] Decisions still open

- Whether and how to address class imbalance during training.
- Fixed sequence length, after inspecting length distributions.

### [Our note] Data quality checks

Train and test contain no missing required values, invalid sequences, invalid labels, duplicate sequences within either dataset, or sequences with conflicting labels within either dataset. These checks require no row removal. API names, call order and repetitions are preserved. Cross-partition overlap is not covered by these checks.

### [PDF §3] How is the validation set created?

We use an 80/20 stratified split of the supplied training data, with `random_state=42`. Stratification preserves the rare goodware proportion; the fixed seed makes the split reproducible. The resulting partitions contain 13,060 training samples and 3,265 validation samples. Model selection uses validation only.

## Task 2A - Unigram Bag-of-Words

**[PDF §6.1] How many columns are produced, what does each row represent, and can call order be recovered?**

There are 256 columns, one per distinct API observed in the training partition. Each row represents one sequence; values are API occurrence counts. Call order cannot be recovered.

**[PDF §6.1] Give different sequences with the same unigram vector. Can sequences containing the same API calls produce different vectors?**

`[A, B, A]` and `[A, A, B]` both give counts `(A=2, B=1)`: order is lost. `[A, B]` and `[A, A, B]` contain the same distinct calls but produce different vectors because their counts differ.

**[PDF §6.1] How does CountVectorizer handle unseen test calls, and how many samples are affected?**

It ignores unseen calls rather than adding columns or raising an error. This affects 3 test samples; known calls in those samples are still counted.

**[PDF §6.1] Choose and justify a classifier and its hyperparameters, addressing class imbalance.**

Pending: select the classifier and imbalance strategy before training. No classifier has been trained yet.

**[PDF §6.1] Predict performance before training, then report validation and per-class results.**

Pending: record the hypothesis in the experiment logbook before the first training run, then evaluate on validation.
