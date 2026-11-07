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

The vocabulary remains restricted to train_split. BoW ignores unseen calls; Tasks 3/4 map them to UNK=1, reserving PAD=0. UNK is a real call; PAD is an artificial filler. Graph handling remains to be defined.

### [Our note] Decisions still open

- Task 2 selected Standard after comparing class weights. Tasks 3/4 start with the same unweighted BCE policy; further imbalance/regularization choices remain subject to validation.
- Task 3 currently uses L=90; any changes must be justified using training/validation data.

### [Our note] Data quality checks

Train and test contain no missing required values, invalid sequences, invalid labels, duplicate sequences within either dataset, or sequences with conflicting labels within either dataset. These checks require no row removal. API names, call order and repetitions are preserved. Cross-partition overlap is not covered by these checks.

### [PDF §3] How is the validation set created?

We use an 80/20 stratified split of the supplied training data, with `random_state=42`. Stratification preserves the rare goodware proportion; the fixed seed makes the split reproducible. The resulting partitions contain 13,060 training samples and 3,265 validation samples. Model selection uses validation only.

## Task 2 - Bag-of-Words

**[Our note] Recorded baseline.** Standard/Weighted per representation; same 80/20 split, seed 42 per run, FFNN input -> 64 -> 32 -> 1, Adam lr=0.001, 20 epochs, batch 64, threshold 0.5. The reference results/times below come from completed CPU runs; they are not new GPU measurements. Select on validation before evaluating test. The current notebook can also use CUDA/XPU.

### Task 2A - Unigram representation

**[PDF §6.1] How many columns, what does a row represent, and can order be recovered?**

256 columns: one per distinct training API. A row represents one sequence; raw values count API occurrences. Train shape `(13060, 256)`, validation `(3265, 256)`. Positions and transitions are discarded, so order cannot be recovered. Log1p compresses counts; StandardScaler is fitted on training only and reused unchanged.

**[PDF §6.1] Different sequences with equal vectors? Same calls with different vectors?**

`[A, B, C, A]` and `[A, C, B, A]` both give `(A=2, B=1, C=1)`. `[A, B]` and `[A, B, A]` contain the same distinct APIs but different counts, hence different vectors.

**[PDF §6.1] How are unseen test calls handled, and how many samples are affected?**

CountVectorizer ignores them without adding columns or raising an error. Task 1 found 3 unseen APIs affecting 3 test samples. Known calls in those samples are still counted.

### Classifier, imbalance and validation selection

**[PDF §6.1] Explain the classifier/hyperparameters, address imbalance, predict first and report per-class behavior.**

A small FFNN learns nonlinear combinations of counts; two compact hidden layers keep the classifier simple. Adam lr=0.001 and batch 64 are starting settings, with a fixed 20-epoch budget; they are not claimed to be globally optimal. The controlled comparison changes only loss weighting. Weighted BCE balances total class contributions with training-only weights `N/(2*n_class)`: goodware 13.3538, malware 0.5194. Expect better minority recall, potentially at the cost of missed malware; evaluate using macro-F1 rather than accuracy. These expectations were set before the fresh runs.

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

**[Our note] Status.** Theory and initial validation results are available. Hyperparameters and conclusions remain provisional. Values below are the latest saved outputs, retained through the readability cleanup; final results/timings must be confirmed after tuning and the XPU runtime fixes. No complete CPU/GPU benchmark or FFNN test ablation is saved.

### Length and representations

**[PDF §7] Why does an FFNN need fixed length? How do we handle padding, truncation and longer test inputs?**

A dense layer has a fixed number of input weights. We choose **L=90**, the maximum in train_split: retain the first 90 calls and right-pad shorter inputs. No training/validation calls are lost. Test reaches 100 calls, so **2,639/6,505 samples (40.57%)** lose their final 1-10 calls. This simple prefix policy can discard late behaviour; L is justified from training, not the test maximum.

**[PDF §7] How do the two FFNN encodings share the same architecture?**

Current code uses ReLU hidden layers **256 -> 128**, Adam lr=0.001, batch 64, 20 epochs, unweighted BCE and threshold 0.5; seed 42. These are current settings, not a completed tuning result.

- **3A:** 90 IDs -> training-only, column-wise StandardScaler -> 256 -> 128 -> 1. Scaling also transforms PAD zeros; original integer matrices are retained separately.
- **3B:** 90 IDs -> trainable embedding of **16 values per API** -> flatten **90 x 16 = 1,440** values -> 256 -> 128 -> 1. PAD's embedding stays zero. Embedding and FFNN weights learn together.

The same SequenceFFNN class defines both hidden architectures; only encoding and input width differ. Vocabulary: 256 training APIs plus PAD=0 and UNK=1.

**[PDF §7 - Before training] Is ID order meaningful? Which encoding is more promising?**

API IDs are arbitrary categories: numerical order/distance has no behavioural meaning, and scaling does not fix it. Embeddings can learn useful task-specific relationships, so they are more promising. Extra parameters can also overfit; better results are not guaranteed.

### Saved validation evidence

**[PDF §7] Are performance and training behaviour similar? Use the learning curves and timings.**

Saved metrics evaluate the **last epoch (20)**, not the epoch with best validation score:

| Model | Macro-F1 | Goodware precision | Goodware recall | Malware precision | Malware recall |
| --- | --- | --- | --- | --- | --- |
| 3A - scaled IDs | 0.5744 | 0.2043 | 0.1557 | 0.9675 | 0.9765 |
| 3B - embeddings | 0.6557 | 0.5833 | 0.2295 | 0.9708 | 0.9936 |

3B detects **28/122 goodware** versus **19/122** for 3A, but still misses most benign samples. Accuracy is 94.58%/96.51%; the majority-class baseline is about 96.26%, so accuracy hides this weakness. Saved training times are 6.90 s/11.89 s; these individual runs do not establish CPU/GPU speedup.

Both curves show **overfitting**: training loss falls while validation loss rises after the first few epochs; 3B's training loss approaches zero. This is poor generalization, not evidence of insufficient capacity. Larger hidden/embedding dimensions add capacity without fixing imbalance or sensitivity to absolute positions. Batch size alone does not directly solve this gap. Validation-based checkpoint selection/early stopping and then a controlled regularization trial are proposed; **neither early stopping nor new regularization is currently implemented**. Minimum validation loss need not maximize macro-F1.

**[PDF §7] Does the best FFNN improve on the BoW baseline? Why might it fail?**

The **provisional FFNN candidate is 3B: macro-F1 0.6557**, below bigram BoW **0.8573** on the same validation split. Fixed positions have not helped in these runs. Possible explanations include arbitrary ID geometry in 3A, overfitting, minority scarcity and sensitivity to position shifts. BoW aggregates calls independently of absolute position, while bigrams preserve local transitions. Truncation affects longer test inputs, not this validation comparison. This does not prove that order is useless; revisit after tuning.

### Remaining comparisons

**[PDF §7] Compare average CPU/GPU epoch time with identical model configuration and batch size.**

**Pending matched benchmark.** The Task 4 benchmark can include the selected FFNN when Task 3 has also run. It copies identical initial weights, repeats seeded batches and synchronizes CUDA/XPU timers. Report CPU seconds/epoch divided by GPU seconds/epoch; no completed paired results are saved. A GPU need not be faster for small workloads. CUDA being unavailable does not exclude the Intel XPU GPU.

**[PDF §7; §4] Evaluate the best FFNN on original and shuffled test. What does shuffling reveal?**

**Pending FFNN implementation/evaluation after final validation selection.** First retain sequence[:90], shuffle only retained real calls, then right-pad both versions identically. Reuse model, vocabulary, scaler if applicable and threshold; never fit/retrain on test. Positions change, but retained calls, counts and PAD locations do not. A drop would show sensitivity to arrangement; unchanged aggregate scores can still hide changed predictions. Global shuffling cannot isolate local versus long-range contributions and also shifts the input distribution. No observed FFNN shuffle conclusion is available yet.

## Task 4 - Recurrent models

**[Our note] Status.** The notebook implements vanilla RNN, BiRNN and unidirectional LSTM independently of Tasks 2/3. Current settings: embedding 16, hidden 64, one recurrent layer, Adam lr=0.002, batch 512, 40 epochs, unweighted BCE, threshold 0.5. RNN_CLIP_NORM=None disables clipping. Treat settings/results as provisional; BiRNN/LSTM selection and final comparisons are not complete in the saved outputs reviewed here.

### Sequence handling and parameters

**[PDF §8] Is padding/truncation needed? Can test sequences be longer than training sequences?**

RNNs reuse the same transition weights at each timestep, so they accept variable lengths without changing the input layer. We encode **full original lists**; no training/validation/test truncation is needed. Mini-batches are right-padded to their longest sample, then pack_padded_sequence uses real lengths to exclude PAD. UNK remains a real timestep. Longer test sequences increase work/memory and may still be harder to classify, even though the architecture accepts them.

**[PDF §8] Compare RNN/FFNN trainable parameter counts. What changes when sequence length increases?**

Calculated for current vocabulary/architecture, with biases and trainable embeddings included:

| Model | Parameters at L=90 |
| --- | --- |
| FFNN IDs (256 -> 128) | 56,321 |
| FFNN embeddings (16; 256 -> 128) | 406,049 |
| Vanilla RNN (16; hidden 64) | 9,441 |
| BiRNN (16; hidden 64 per direction) | 14,753 |
| LSTM (16; hidden 64) | 25,185 |

With vocabulary, hidden size and layers fixed, increasing length leaves recurrent parameter counts unchanged because weights are shared across timesteps. FFNN flattening enlarges the first Linear layer: at L=100, the two FFNNs have 58,881/447,009 parameters. More timesteps still increase RNN computation and activation memory.

### Architectural choices and saved observations

**[PDF §8] Explain vanilla RNN behaviour and any training difficulties.**

The completed saved vanilla run ends at validation **macro-F1 0.7131**, goodware precision/recall **0.5972/0.3525**, malware precision/recall **0.9753/0.9908**. It identifies 43/122 goodware; imbalance remains a major limitation. Training loss falls from 0.3222 to 0.0594; validation improves from 0.2065 to 0.1265 but later fluctuates/levels off as the training gap grows. This suggests some overfitting; curves alone do not prove exploding/vanishing gradients. Clipping may address large gradients, not overfitting or XPU runtime faults. The code retains epoch-40 weights, not an earlier peak checkpoint.

**[PDF §8] Is bidirectional access to later calls appropriate?**

Yes for **offline classification** after the full trace is collected. It is not causal for an online decision at time t that must use only calls observed up to t. BiRNN concatenates forward/backward final states of the last layer; packing keeps these states tied to real calls. Its greater cost/parameter count must be justified by completed validation results, which are still pending here.

**[PDF §8] Why choose a unidirectional LSTM? Compare results and curves with the other variants.**

One direction isolates the cell change relative to vanilla RNN instead of also adding bidirectionality. Input/forget/output gates and cell state regulate retained information and may help with distant dependencies. More parameters do not guarantee better validation. **Full BiRNN/LSTM results and learning-curve comparison remain pending**; partial BiRNN logs are not a completed score or evidence that a variant loses.

### Costs, baseline and order

**[PDF §8] Compare recurrent and FFNN training time per epoch. Which is faster and why?**

Saved vanilla RNN time is **3.546 s/epoch**; saved FFNN totals correspond to about 0.345/0.595 s/epoch. These are **indicative, not a controlled timing comparison**: batch sizes differ (512 versus 64) and outputs predate the final cleanup/runtime confirmation. RNN timesteps depend on earlier states, limiting parallelism over time; FFNN layers process positions together. Re-measure selected models under stated conditions before drawing a final speed conclusion.

**[PDF §8] Compare the selected RNN's CPU/GPU epoch time with matched settings.**

**Pending completed benchmark and final variant selection.** The implementation recreates CPU/XPU or CPU/CUDA runs with identical initial weights, architecture, epochs, batch size and sample order, timing training only. An enabled flag is not a measured result; no saved speedup is available.

**[PDF §8] Does processing calls sequentially outperform FFNN and BoW, including bigrams?**

The saved vanilla RNN's **0.7131** exceeds the provisional FFNN scores **0.5744/0.6557**, but remains below unigram BoW **0.8029** and bigram BoW **0.8573**. These runs differ in settings/capacity, so the gap cannot be assigned solely to sequential processing. Useful local transitions, minority scarcity, optimization and generalization may contribute. The final best-RNN comparison awaits all completed variants and tuning.

**[PDF §8; §4] Compare original/shuffled test for the frozen best RNN and interpret call order.**

**Implemented, results pending.** After validation selection, shuffle all real calls within each full test sequence and then pad through the same loader. Reuse weights, vocabulary and threshold without retraining. Report macro-F1, per-class precision/recall, confusion matrices and changed predictions. A performance change indicates sensitivity to arrangement; unchanged aggregate metrics do not prove identical decisions. This ablation cannot separate local from longer-range effects. RUN_FINAL_TEST remains disabled in the reviewed setup.

## [Our note] Execution and GPU compatibility

The first cell selects TASKS and DEVICE; shared data/split/vocabulary preparation never trains skipped models. Cross-task tables include only completed models from the current session. Adam uses fused execution plus a gradient/step synchronization workaround on Intel XPU; CPU/CUDA keep PyTorch defaults. These runtime changes do not add layers, early stopping or regularization. Synthetic diagnostics and isolated timing tests are not substitutes for the required matched CPU/GPU experiment.

