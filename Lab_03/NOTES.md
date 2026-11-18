# Lab 3 - Answers and notes

`[PDF §...]` marks assignment questions. Run numbers match the sequential logbook; notebook labels use configuration names. OC-SVM = One-Class SVM; LOF = Local Outlier Factor; AE = Autoencoder; FPR = false-positive rate (normal flagged as anomalous). "Anomaly" = binary_label 1 (any attack). Macro-F1 is binary (normal vs anomaly) unless stated otherwise.

**Status:** Task 1 and Task 2A complete. Tasks 2B–7 pending.

**Knowledge assumptions (global):** labels are used only to build training subsets and to evaluate, never as a supervised signal. Preprocessing is fitted on training data only. The test set is used only where a task explicitly asks for it; any validation set is carved out of train.csv.

## Task 1 - The data from a domain-expert perspective

**[PDF §1.1] Attributes, label distribution and anomaly fraction.**

Both files have 41 features + `label` + `binary_label`: **3 categorical** (`protocol_type`, `service`, `flag`) and **38 numerical**, eight of which take only 0/1 values (counted as numerical, as the assignment requires): five true indicators (`land`, `logged_in`, `root_shell`, `num_shells`, `is_guest_login`) plus `urgent`, `num_outbound_cmds` and `is_host_login`, which are 0/1 only because they are always 0 in train (`urgent` is in fact a counter). Train has 18,831 connections, test 5,826.

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
- **Protocol is informative but not separating:** r2l is TCP-only; probe has the highest ICMP share of any class (827/2,289, 36%), although TCP is still its most frequent protocol (1,147); normal also uses all three protocols.

**[PDF §1.2] Preprocessing of categorical and numerical data.**

All our detectors (OC-SVM with RBF kernel, LOF, K-Means, DBSCAN, AE reconstruction error) depend on distances, so we aim for a space where no single feature dominates only because of its units. We keep every row, including the conflicting pair. The pipeline outputs **106 features: 35 numerical + 71 one-hot**.

| Step | Columns | Choice | Reason |
| --- | --- | --- | --- |
| Drop constant columns | `urgent`, `num_outbound_cmds`, `is_host_login` | Removed | Constant in train: no information, zero-variance dimensions |
| Categorical | `protocol_type` (3), `service` (65), `flag` (11) | One-hot; `service` levels with < 10 training rows merged into one *infrequent* column → 3 + 57 + 11 columns | No natural order, so integer codes would invent distances. The 9 rarest services (≤ 8 rows each) would otherwise add near-empty dimensions. |
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

**[PDF §1.3] Heatmaps.** Training set, 35 numerical features after Task 1.2 (the 38 numerical attributes minus the 3 columns constant in train, which would show the same value in every row) (`log1p` + min-max), so all columns share one [0, 1] colour scale; raw `src_bytes` would flatten the others. Values below are mean / median / std from the heatmaps.

**[PDF §1.3] Which features distinguish specific attack types?**

- **Normal:** logged in (median 1), non-zero bytes (`src_bytes` median 0.28, `dst_bytes` 0.39), same service and host-service counters at their maximum (`same_srv_rate`, `dst_host_srv_count`, `dst_host_same_srv_rate` medians 1). Error rates ≈ 0.
- **DoS:** many connections to the same host (`count` mean 0.74 vs 0.23 normal; `dst_host_count` median 1.00), no payload (bytes median 0), not logged in (mean 0.07), low `same_srv_rate` (median 0.11). SYN-error rates (`serror_rate`, `dst_host_serror_rate`…) have median 1 but mean 0.57 and std 0.49: DoS is **bimodal**, SYN-flood connections (serror = 1) plus a second group with serror = 0. `wrong_fragment` is non-zero only for DoS (mean 0.06, std 0.25).
- **Probe:** many different services/ports (`dst_host_diff_srv_rate` 0.40 vs 0.04; `diff_srv_rate` 0.25 vs 0.03), same source port (`dst_host_same_src_port_rate` median 1.00 vs 0.01), few connections per destination service (`dst_host_srv_count` median 0.01 vs 1.00), almost no bytes, not logged in. REJ-error rates have mean 0.44 but median 0 and std ≈ 0.5, and most traffic features have std 0.4–0.5: probe is the **most heterogeneous** class (e.g. port scans vs host sweeps).
- **R2L:** the class **closest to normal**: logged in (1.00), normal-like `src_bytes` (median 0.29 vs 0.28), `same_srv_rate` and `dst_host_same_srv_rate` median 1. It differs on content features (`hot` mean 0.26 vs 0.01, `is_guest_login` 0.31 vs 0.01) and on host statistics (`dst_host_count` median 0.03, `dst_host_same_src_port_rate` median 1.00). Std of `hot` / `is_guest_login` ≈ 0.35–0.47: only part of R2L shows these signs.
- **Not discriminative:** `num_failed_logins`, `num_compromised`, `su_attempted`, `num_root`, `num_file_creations`, `num_access_files`, `root_shell`, `num_shells`, `land` are ≈ 0 in every class.

**Expectations for later tasks.** DoS and probe differ from normal mainly on traffic features and should be detectable by distance-based methods. DoS is however numerous and made of repeated, near-identical connections (zero bytes, same host, serror = 1), so it may form **dense groups** that LOF/DBSCAN treat as normal. R2L looks most like normal and is expected to be missed most often (only measurable on train). Probe's high variability may produce isolated points, easy for LOF/Isolation Forest.

## Task 2 - One-Class SVM: impact of the anomalies

### Task 2A - Normal traffic only

**[PDF §2] Choice of `nu` vs default 0.5 (training FPR, macro-F1).** RBF, `gamma='scale'`, fitted on the 13,448 normal training connections. FPR is computed on normal training data; macro-F1 and recall on the full train.csv (attacks never seen in fitting).

| Run | `nu` | Train FPR | Macro-F1 | dos recall | probe recall | r2l recall | FP | FN | SV | Fit s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.01 | 0.0104 | 0.9367 | 0.910 | 0.844 | 0.017 | 140 | 796 | 153 | 0.1 |
| 2 | 0.5 | 0.5000 | 0.6367 | 0.974 | 1.000 | 0.994 | 6,724 | 78 | 6,726 | 5.7 |

We keep **`nu = 0.01`** (run 1). The default flags half of normal traffic; its higher recall does not compensate.

**[PDF §2] Why clean normal data helps; what `nu` controls; can it be zero; effect on FPR.**

- **Clean data:** the OC-SVM learns the support of whatever it is given. With normal data only, the boundary describes normal traffic, and every point outside is by construction a false alarm, so the accepted FPR can be set directly. Attacks in training would be enclosed by the boundary (Task 2B).
- **`nu`:** upper bound on the fraction of training points outside the boundary and lower bound on the fraction of support vectors. SV 1.1% / 50.0% ≥ `nu`. FPR 0.5000 ≤ 0.5; for `nu = 0.01` the bound is exceeded by 6 points (140 outside vs 134.5), because the solver stops at a tolerance (`tol = 1e-3`) and some points lying on the boundary end up with a slightly negative decision value.
- **Choice:** with clean data, `nu` ≈ accepted training FPR. We accept ~1% (~134 connections) as slack for rare but legitimate normal patterns (rare services, sparse indicators from Task 1).
- **Zero:** not allowed (sklearn requires `nu ∈ (0, 1]`). As `nu → 0` the boundary must enclose every training point, noise included, and becomes loose around attacks.
- **Effect on FPR:** training FPR tracks `nu` almost exactly (0.0104 vs 0.01; 0.5000 vs 0.5).
- **What is missed (run 1):** R2L is almost entirely inside the normal region (3/181 detected), as expected from Task 1.3. 9% of DoS and 16% of probe are also missed. All missed DoS are of the non-SYN kind: SYN-flood DoS (`serror_rate` > 0.5, 1,675 rows) have recall 1.000, the other 1,238 DoS 0.788 (the bimodality seen in Task 1.3). With `nu = 0.5` R2L is caught (0.994) only because the boundary shrinks to the densest half of normal traffic.

### Task 2B - Normal + anomalous traffic (contamination 0/10/20/50/100%)

**Setup.** All 13,448 normal connections + a fraction of the 5,383 training anomalies, drawn from one random permutation (seed 42), so the subsets are nested (10% ⊂ 20% ⊂ 50% ⊂ 100%). The 0% subset is the Task 2A model (run 1). Same RBF, `gamma='scale'`: it is recomputed on each subset but changes by only ~3% (0.146 normal-only, 0.141 full train), so the kernel is effectively unchanged. Labels are used only to build the subsets. *Subset* metrics are computed on the training subset itself (the "training score" the assignment asks for); *full-train* metrics on the whole train.csv, the same set for every model.

| Run | Anomalies included (dos / probe / r2l) | Contamination c | `nu` | Subset FPR | Subset macro-F1 | Full-train macro-F1 | dos / probe / r2l recall (full train) | FP | FN | SV | Fit s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0% (0) | 0 | 0.01 | 0.0104 | n/a (one class) | 0.9367 | 0.910 / 0.844 / 0.017 | 140 | 796 | 153 | 0.1 |
| 3 | 10% (538: 289 / 232 / 17) | 0.0385 | 0.0481 | 0.0288 | 0.7242 | 0.7638 | 0.501 / 0.523 / 0.110 | 387 | 2,708 | 685 | 0.5 |
| 4 | 20% (1,077: 576 / 458 / 43) | 0.0741 | 0.0834 | 0.0464 | 0.7354 | 0.7656 | 0.534 / 0.543 / 0.193 | 624 | 2,548 | 1,219 | 1.0 |
| 5 | 50% (2,692: 1,410 / 1,183 / 99) | 0.1668 | 0.1751 | 0.0912 | 0.7463 | 0.7661 | 0.585 / 0.626 / 0.409 | 1,227 | 2,170 | 2,834 | 3.5 |
| 6 | 100% (5,383), **known c** | 0.2859 | 0.2930 | 0.1546 | 0.7402 | 0.7402 | 0.609 / 0.681 / 0.586 | 2,079 | 1,945 | 5,523 | 8.7 |
| 7 | 100% (5,383), **unknown c** | (0.2859) | 0.05 | 0.0286 | 0.5059 | 0.5059 | 0.079 / 0.139 / 0.083 | 384 | 4,820 | 968 | 1.0 |

FP/FN are on the full train.csv. For run 6/7 the subset is the full train.csv, so the two scores coincide.

| Run | `nu` | Fraction left outside (subset) | Attacks among outside points | SYN-flood DoS recall | Other DoS recall |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.01 | 0.010 | 0.00 | 1.000 | 0.788 |
| 3 | 0.048 | 0.048 | 0.43 | 0.545 | 0.440 |
| 4 | 0.083 | 0.083 | 0.48 | 0.610 | 0.432 |
| 5 | 0.175 | 0.175 | 0.57 | 0.642 | 0.509 |
| 6 | 0.293 | 0.293 | 0.62 | 0.643 | 0.563 |
| 7 | 0.05 | 0.050 | 0.60 | 0.081 | 0.077 |

**[PDF §2] How does knowing the contamination rate guide `nu`?**

`nu` bounds the fraction of training points left outside the boundary. If the contamination `c` is known, the natural choice is to leave out at least all anomalies, plus the 1% slack for rare but legitimate normal traffic chosen in Task 2A: **`nu = c + 0.01·(1 − c)`** (0.0481 / 0.0834 / 0.1751 / 0.2930; for `c = 0` it gives back 0.01). The OC-SVM fills this budget exactly (second table, "fraction left outside" = `nu`).

What `c` does **not** guarantee is *which* points are left out: the model excludes the points in the least dense regions, not the attacks. Only 43% (10%) to 62% (100%) of the excluded points are attacks; the rest are normal connections, so FPR rises with `nu` (2.9% → 15.5%), well above the 1% slack we planned.

**[PDF §2] What did we do when the contamination rate was unknown?**

On the 100% subset we did not use the true rate. We applied the standard anomaly-detection prior that attacks are rare (a few % of the traffic) and set **`nu = 0.05`**. It is a deliberate guess, not an estimate from the data. Here it underestimates the true rate (0.286) by a factor of ~6.

**[PDF §2] How do the results change as more anomalies are included?**

- **The big drop is between 0% and 10%.** Full-train macro-F1 falls from 0.937 to 0.764 with only 538 attacks (2.9% of the subset). We had expected only a small drop (logbook run 3, hypothesis rejected). DoS recall halves (0.910 → 0.501), and SYN-flood DoS, all detected by the normal-only model, fall to 0.545.
- **Why:** attacks are not isolated points. DoS and probe are repeated, near-identical connections (Task 1.3): their median distance to the 5th nearest neighbour (dos 0.088, probe 0.057, r2l 0.064) is as small as or smaller than that of normal traffic (0.085). Once a few of them are in the training data, they form dense regions and the boundary grows to include them. This is not memorisation of the included points: attacks **never seen** in fitting are enclosed almost as much as the included ones (run 3 recall dos 0.497 vs 0.529, probe 0.519 vs 0.560).
- **From 10% to 100%:** the subset macro-F1 changes little (0.724 → 0.746 → 0.740); full-train macro-F1 is flat (0.764–0.766) until 50% and drops to 0.740 at 100%. Recall rises with `nu` (dos 0.50 → 0.61, r2l 0.11 → 0.59), but false alarms grow faster (387 → 2,079 FP). The two effects roughly cancel. The rise in recall comes from the larger `nu`, not from the model "understanding" attacks better.
- **R2L** rises from 0.017 to 0.586 as `nu` grows: R2L is only 181 rows, too few to form a dense region, so it ends up among the excluded low-density points.

**[PDF §2] Does knowing the contamination rate help in the 100% case?**

Yes, clearly: macro-F1 **0.740** (known, `nu = 0.293`) vs **0.506** (unknown, `nu = 0.05`). With `nu = 0.05` the boundary encloses 92% of the attacks (DoS recall 0.079). It produces few false alarms (384), but detects almost nothing. We had expected a small gap (logbook run 7, rejected in magnitude). The 100% model is still far below the normal-only model (0.937): knowing `c` only tells the model *how many* points to exclude, not *which ones*, while clean normal data tells it what normal looks like.

**[PDF §2] Is comparing scores across training subsets fair?**

Not fully, for three reasons:
1. **Different priors.** Each subset has a different share of anomalies (3.8% → 28.6%). Precision and F1 depend on this prior, so the same detector would get different scores on different subsets. This is why the subset curve starts lower than the full-train curve at 10% (0.724 vs 0.764).
2. **Different evaluation sets and `nu`.** Each model is scored on its own subset with its own `nu`. Training and evaluation data coincide, so the scores measure how well the boundary fits the training data, not detection on unseen traffic.
3. **Full-train scores are only partly fairer.** They use the same 18,831 rows for every model, but the included attacks are training data for some models and unseen for others. The comparison on unseen data is Task 2C (test set).

Notebook: Task 2B cells (subset table, runs 3–7, plot, diagnostic cell).

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

The current logbook lists **2 retained runs** (budget ~25).

- [ ] Report `groupID_lab3.pdf`, maximum 10 pages, with decisions, measured results and reasoning.
- [ ] Experiment logbook, separate or appendix (outside the page limit).
- [ ] Executed, rerunnable notebook/code and HTML export.
- [ ] Final package `groupID_lab3.zip`.
