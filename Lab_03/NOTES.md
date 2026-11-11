# Lab 3 - Answers and notes

`[PDF §...]` marks assignment questions. Run numbers match the sequential logbook; notebook labels use configuration names. OC-SVM = One-Class SVM; LOF = Local Outlier Factor; AE = Autoencoder; FPR = false-positive rate (normal flagged as anomalous). "Anomaly" = binary_label 1 (any attack). Macro-F1 is binary (normal vs anomaly) unless stated otherwise.

**Status:** Tasks 1.1–1.2 complete. Task 1.3 and Tasks 2–7 pending.

**Knowledge assumptions (global):** labels are used only to build training subsets and to evaluate, never as a supervised signal. Preprocessing is fitted on training data only. The test set is used only where a task explicitly asks for it; any validation set is carved out of train.csv.

## Task 1 - The data from a domain-expert perspective

**[PDF §1.1] Attributes, label distribution and anomaly fraction.**

Both files have 41 features + `label` + `binary_label`: **3 categorical** (`protocol_type`, `service`, `flag`) and **38 numerical**, eight of which are 0/1 indicators (counted as numerical, as the assignment requires). Train has 18,831 connections, test 5,826.

| Label | Train | Train % | Test | Test % |
| --- | --- | --- | --- | --- |
| normal | 13,448 | 71.41 | 2,152 | 36.94 |
| dos | 2,913 | 15.47 | 2,577 | 44.23 |
| probe | 2,289 | 12.16 | 1,097 | 18.83 |
| r2l | 181 | 0.96 | 0 | 0.00 |
| **Anomalies (binary 1)** | **5,383** | **28.59** | **3,674** | **63.06** |

`binary_label` is exactly `label != normal` in both files.

**Data quality.** No missing, infinite or negative values; no duplicate rows in either file. One feature vector appears twice in train with conflicting labels (icmp/ecr_i/SF, 20 bytes: probe and normal); we keep both rather than invent a correction. Constant in train: `urgent`, `num_outbound_cmds`, `is_host_login` (carry no information for models fitted on train). Two test services (`tftp_u`, `tim_i`, one normal row each) never appear in train — the encoder must handle unseen categories. 75 test rows are identical to a training row. Several features are heavy-tailed (e.g. `src_bytes` median 207, max 3.8e8; `duration` median 0, max 42,862), which matters for scaling and for distance-based methods.

**[PDF §1.1] Implications for anomaly detection.**

- **The anomalies are not rare.** At 28.6% in train, "attack" is not the small, isolated minority most unsupervised detectors assume (OC-SVM `nu`, LOF and Isolation Forest contamination, DBSCAN noise). Attacks such as DoS/probe generate many similar connections, so they may form *dense* groups that density/isolation methods treat as normal.
- **Train and test priors differ strongly.** Contamination rises from 28.6% to 63.1% in test, and dos becomes the largest class. A threshold or `nu` tuned to the training contamination will not match the test prior; metrics that depend on the prior (precision, F1) will shift between train and test even for the same detector.
- **r2l is very rare in train (181, <1%) and absent in test.** Its test recall cannot be measured; it only affects training contamination and the per-attack analysis on train.
- **Protocol is informative but not separating:** r2l is TCP-only; probe is the only class where ICMP dominates (827/2,289), but normal also uses all three protocols.

**[PDF §1.2] Preprocessing of categorical and numerical data.**

All our detectors (OC-SVM with RBF kernel, LOF, K-Means, DBSCAN, AE reconstruction error) depend on distances, so we aim for a space where no single feature dominates only because of its units. We keep every row, including the conflicting pair. The pipeline outputs **106 features: 35 numerical + 71 one-hot**.

| Step | Columns | Choice | Reason |
| --- | --- | --- | --- |
| Drop constant columns | `urgent`, `num_outbound_cmds`, `is_host_login` | Removed | Constant in train: no information, zero-variance dimensions |
| Categorical | `protocol_type` (3), `service` (65), `flag` (11) | One-hot; levels with < 10 training rows merged into one *infrequent* column per variable (9 `service` levels, `flag=OTH`) → 3 + 57 + 11 columns | No natural order, so integer codes would invent distances. Rare levels (≤ 8 rows each) would otherwise add near-empty dimensions. `OTH` is the only rare `flag`, so `flag_infrequent` is equivalent to `OTH`: no information is lost. |
| Unseen categories | `tftp_u`, `tim_i` (test only) | Mapped to the *infrequent* service column | They behave like other rare services rather than becoming an all-zero vector with no `service` information |
| Heavy-tailed counters | 13 non-rate, non-binary features with training skewness > 2: `duration`, `src_bytes`, `dst_bytes`, `wrong_fragment`, `hot`, `num_failed_logins`, `num_compromised`, `su_attempted`, `num_root`, `num_file_creations`, `num_access_files`, `count`, `srv_count` | `log1p`, then min-max | Compresses extreme tails (`src_bytes` skew 136, max 3.8e8 vs median 207), so a few huge transfers do not set the whole scale |
| Other numerical | `*_rate`, 0/1 indicators, `dst_host_count`, `dst_host_srv_count` (22) | Min-max only | Rates and indicators are already in [0, 1]. The two `dst_host` counters are bounded at 255 and not right-skewed (skew -0.43 / -0.27), so `log1p` would only compress their informative high end. |

**Why min-max and not StandardScaler.** We first used StandardScaler and rejected it. Many features are almost always 0, so dividing by their tiny standard deviation inflates rare non-zero values: `land` (1 in ~18.8k training rows) reaches **137** standard deviations, `num_failed_logins` 66 and `num_shells` 49. Under Euclidean/RBF distances, any row with one such flag would be an extreme outlier, regardless of the other 100 features. With `log1p` + min-max, every feature lies in [0, 1] on train, the same range as the rates and the one-hot columns.

**Trade-offs.**
- Min-max is sensitive to the training maximum. `log1p` reduces this for counters.
- Only **7 test values** fall outside [0, 1]: `duration` max 1.02, `hot` 1.06, `num_file_creations` 1.24, and `count`/`srv_count` at −0.125 when the test value is 0 (train minimum is 1). We do not clip them: values outside the training range are information an anomaly detector should see.
- Each one-hot change moves the squared Euclidean distance by 2, comparable to a full-range numerical change. So `service`/`flag` carry substantial weight in distances. We keep this weighting deliberately: `service` and `flag` are domain-relevant. We will revisit it if a detector is dominated by service identity.

**[PDF §1.2] Where preprocessing parameters are estimated from.**

All parameters are estimated on **train.csv only**: constant columns, skewness rule, category levels and infrequent set, `log1p`/min-max ranges. They are then applied unchanged to test, so the test set does not influence the representation we evaluate on. Labels are never passed to the preprocessor.

We fit one preprocessor on the **full training file** (normal + anomalies) and reuse it for all tasks. This is the data an unsupervised detector would have, and a shared feature space keeps methods comparable. Normal-only scenarios (OC-SVM Task 2A, normal-only AE, PCA) therefore see min-max ranges that also cover training attacks. We consider this acceptable because the transformation uses no label. The alternative, fitting on normal traffic only, would turn attacks with extreme values into values outside [0, 1]. Any validation split needed later (Task 6) will be carved from train.csv; it shares these unsupervised statistics, but no labels or test data.

**Train → test shift.** After the train-fitted transformation, the largest mean shifts are `logged_in` (−0.40), `count` (+0.29), `dst_host_count` (+0.27) and `same_srv_rate` (−0.24). This is consistent with the much larger dos share in test: many connections to the same host, not logged in.

**[PDF §1.3] Mean / std / median heatmaps per attack label.** *Pending.*

**[PDF §1.3] Which features distinguish specific attack types?** *Pending.*

## Task 2 - One-Class SVM: impact of the anomalies

### Task 2A - Normal traffic only

**[PDF §2] Choice of `nu` vs default 0.5 (training FPR, macro-F1).** *Pending.*

**[PDF §2] Why clean normal data helps; what `nu` controls; can it be zero; effect on FPR.** *Pending.*

### Task 2B - Normal + anomalous traffic (contamination 0/10/20/50/100%)

| Subset | Anomalies included | Contamination | `nu` | Train macro-F1 |
| --- | --- | --- | --- | --- |
| | | | | |

**[PDF §2] How the contamination rate guides `nu`; the unknown-contamination case; trend; fairness of cross-subset comparison.** *Pending.*

### Task 2C - Generalisation to the test set

| Model | Test macro-F1 | TN | FP | FN | TP | dos recall | probe recall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Normal only | | | | | | | |
| 10% anomalies | | | | | | | |
| 100% anomalies | | | | | | | |

**[PDF §2] Train vs test; best model; error types; most-missed attacks and explanation from heatmaps.** *Pending.*

## Task 3 - Local Outlier Factor

**[PDF §3] Four `n_neighbors` values and selection criterion.** *Pending.*

**[PDF §3] Test results; can LOF detect the attacks; local density of attacks; effect of `n_neighbors`.** *Pending.*

## Task 4 - Anomaly detection with clustering

### Task 4A - K-Means

**[PDF §4.A] Choice of k.** *Pending.*

**[PDF §4.A] Cluster sizes, label distribution and purity.** *Pending.*

**[PDF §4.A] Silhouette per cluster; low-silhouette clusters and their labels.** *Pending.*

**[PDF §4.A] Distance-to-centroid threshold; detected vs missed attacks.** *Pending.*

**[PDF §4.A] t-SNE (3 perplexities), coloured by label vs cluster.** *Pending.*

### Task 4B - DBSCAN

**[PDF §4.B] Choice of `min_points` and ε.** *Pending.*

**[PDF §4.B] Is the noise cluster only anomalies; number of clusters.** *Pending.*

**[PDF §4.B] Similarities with LOF (examples).** *Pending.*

## Task 5 - Isolation Forest

*The PDF text skips from Task 4 to Task 6; the run budget mentions Isolation Forest as Task 5. Check the official assignment for its questions.* *Pending.*

## Task 6 - Deep anomaly detection with Autoencoders

### Task 6A - AE on normal data only

**[PDF §6] Architecture, epochs and learning rate (normal-only validation).** *Pending.*

**[PDF §6] Threshold estimation; ECDF of reconstruction errors on normal-validation / full train / test.** *Pending.*

### Task 6B - AE on normal + anomalies

**[PDF §6] Test comparison of the two AEs and explanation.** *Pending.*

## Task 7 - PCA vs Autoencoder bottleneck

**[PDF §7] AE bottleneck + OC-SVM.** *Pending.*

**[PDF §7] PCA (components from explained variance) + OC-SVM.** *Pending.*

**[PDF §7] Comparison with best Task 2 OC-SVM and AE reconstruction error; best method; are AE representations meaningful?** *Pending.*

## Final comparison and reflection

| Method | Knowledge required | Val metric | Test macro-F1 | Train time s | Notes |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

*Pending: ranking by performance, time and required knowledge; was the extra complexity useful; limitations and open questions.*

## Logbook and submission

The current logbook lists **0 retained runs** (budget ~25).

- [ ] Report `groupID_lab3.pdf`, maximum 10 pages, with decisions, measured results and reasoning.
- [ ] Experiment logbook, separate or appendix (outside the page limit).
- [ ] Executed, rerunnable notebook/code and HTML export.
- [ ] Final package `groupID_lab3.zip`.
