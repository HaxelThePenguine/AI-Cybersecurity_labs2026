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

For Task 3 we currently use L=90, the maximum in train_split: retain the first 90 calls and right-pad shorter sequences. This preserves all training calls but truncates 2,639/6,505 test sequences (40.57%), potentially losing useful information. See Task 3 for the rationale.

**[Our note] Can we choose a length of 100?**

The lab explicitly allows comparing train/test length distributions. However, choosing 100 solely because it is the observed test maximum would adapt preprocessing to the test set. A length of 100 needs an independent rationale; positions beyond the training maximum would receive no real-call examples during training.

At L=90, no supplied training sequence is truncated; 40.57% of test sequences are truncated.

### 3. Vocabulary

**[PDF §5 - Vocabulary] Count distinct API calls in the training partition after the validation split. Are there unseen test calls? How many distinct calls and affected test samples?**

The training partition contains **256 distinct API calls**. The test set contains **3 distinct unseen calls**: `ControlService`, `NtDeleteKey`, and `WSASocketA`. **3 of 6,505 test samples (~0.046%)** contain at least one unseen call.

The model vocabulary remains restricted to the training partition. BoW ignores unseen calls; Task 3 maps them to UNK=1, reserving PAD=0. Graph handling remains to be defined.

### [Our note] Decisions still open

- Task 2 compared class weighting; Standard was selected on validation. Task 3 currently uses unweighted BCE; its imbalance strategy and hyperparameters remain open to tuning.
- Task 3 currently uses L=90; any changes must be justified using training/validation data.

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

## Task 3 - Fixed-length FFNNs

**[Our note] Provisional results.** These are initial runs, before tuning, on the same training/validation split as Task 2. Scores, times and the selected FFNN candidate are not final. The legacy code/output at the end of Task 3B is excluded.

### Fixed length and encoding

**[PDF §7] Why does an FFNN need fixed-length inputs? How do padding, truncation and longer test sequences work?**

A dense layer has a fixed number of input weights. We use **L=90**, the longest sequence in train_split: keep the first 90 calls and right-pad shorter inputs with PAD=0. This retains all training/validation calls. Test sequences reach 100 calls: **2,639/6,505 (40.57%)** lose their final 1-10 calls. Keeping the prefix is a simple consistent policy, but may discard useful late behaviour. L was chosen from training, not the test maximum.

**[PDF §7] How do the two encodings use the same FFNN architecture?**

- **3A:** 90 integer IDs, standardized per position using training-only statistics, then 90 -> 64 -> 32 -> 1. Scaling also transforms PAD values; they need not remain zero.
- **3B:** original integer IDs -> trainable embedding -> flatten -> 64 -> 32 -> 1. The current embedding dimension is **32**, so the FFNN receives **90 x 32 = 2,880** values. PAD's embedding stays zero with padding_idx=0.

Both use the same hidden layers with ReLU, Adam lr=0.001, batch 64, 20 epochs, unweighted BCEWithLogitsLoss and threshold 0.5; seed 42, CPU. The vocabulary contains 256 training APIs plus PAD=0 and UNK=1. Embeddings and classifier weights are learned together. These settings are starting points, not tuned optima; the larger embedding input also increases parameter count.

**[PDF §7 - Before training] Is numerical ID order meaningful? Which encoding should work better, and why?**

IDs identify APIs; their order and distances have no behavioural meaning. Standardization does not fix this. Embeddings can learn task-relevant relationships instead of imposing numerical distances, so they are the more promising representation. Improvement is not guaranteed: they add parameters and may overfit. Neither encoding gives the FFNN an explicit mechanism for recurrent sequence processing.

### Initial results and learning curves

**[PDF §7] Do the models perform similarly? Which takes longer or trains less stably? Explain using training/validation curves.**

All metrics below refer to **validation after epoch 20**, not test or a selected earlier checkpoint.

| Initial model | Macro-F1 | Goodware recall | Malware recall | CPU training s |
| --- | --- | --- | --- | --- |
| 3A - scaled IDs | 0.5589 | 0.0902 | 0.9920 | 5.72 |
| 3B - embeddings (32) | 0.6439 | 0.2295 | 0.9898 | 11.67 |

Embeddings currently improve macro-F1 by **0.0850**, detecting 28/122 goodware samples versus 11/122 for IDs. Both still favour malware heavily. Their accuracies (95.83% and 96.14%) are below the approximately 96.26% majority-class baseline; accuracy alone is misleading.

Both curves show **overfitting**. In 3A, validation loss bottoms out around epoch 7 and then rises while training loss falls. In 3B, training loss approaches zero while validation loss rises after the first few epochs and fluctuates more. This indicates poor generalization, rather than proof of optimizer instability. The embedding run takes about twice as long, consistent with its larger model and embedding updates. Timings exclude validation and are single-run measurements. Fewer epochs/early stopping and regularization are candidates for validation-based tuning; minimum validation loss need not coincide with maximum macro-F1.

**[PDF §7] Compare the best FFNN with the BoW baseline. Does keeping fixed call positions improve classification?**

The **current FFNN candidate is 3B**, with validation macro-F1 **0.6439**, versus **0.8573** for the selected unigram + bigram BoW baseline. Fixed positions have not improved classification in these initial runs. Possible reasons include arbitrary ID geometry in 3A, sensitivity to position shifts, overfitting and class imbalance. BoW aggregates evidence regardless of absolute position and bigrams retain useful local transitions. Truncation is an additional test-time limitation, not an explanation for this validation gap: no validation calls are truncated. The comparison must be revisited after tuning; it does not show that order is generally useless.

### Remaining PDF comparisons

**[PDF §7] Compare average training time per epoch on CPU and GPU for the same chosen model/configuration and batch size. How much faster or slower is GPU?**

**Pending measurement.** The saved CPU runs average approximately **0.286 s/epoch (3A)** and **0.584 s/epoch (3B)**. There is no corresponding GPU run, so no speedup can be reported. After selecting the final FFNN, compare fresh CPU/GPU runs with identical configuration, batch size and timing scope; synchronize CUDA when timing. Speedup = CPU seconds/epoch divided by GPU seconds/epoch. If CUDA is unavailable, report the comparison as unavailable. GPU need not be faster for a small model because transfer and launch overhead can dominate.

**[PDF §7; §4] Compare the best FFNN on original and shuffled test inputs. What does this reveal about call positions?**

**Pending test evaluation after validation-based model selection.** For each sample, first retain sequence[:90], then shuffle only those retained calls, then right-pad both versions identically. Reuse the trained model, vocabulary, scaler where applicable and threshold; do not retrain or fit on test. This preserves retained calls, counts and padding positions, changing only call positions.

Shuffling generally changes the FFNN's input because positions are distinct features. A score decrease would indicate sensitivity to their arrangement; unchanged aggregate scores alone would not prove order is ignored, since individual predictions may change. Report original/shuffled macro-F1, per-class behaviour and changed predictions. Shuffling disrupts both local and longer-range structure and introduces shifted inputs, so it cannot isolate their contributions. The observed effect remains unanswered until the experiment is run.

