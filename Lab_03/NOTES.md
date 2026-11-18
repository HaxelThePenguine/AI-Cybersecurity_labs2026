# Lab 3 - Answers and notes

`[PDF §...]` marks assignment questions. Run numbers match the sequential logbook; notebook labels use configuration names. OC-SVM = One-Class SVM; LOF = Local Outlier Factor; AE = Autoencoder; FPR = false-positive rate (normal flagged as anomalous). "Anomaly" = binary_label 1 (any attack). Macro-F1 is binary (normal vs anomaly) unless stated otherwise.

**Status:** Tasks 1, 2 (2A, 2B, 2C) and 3 complete. Tasks 4–7 pending.

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

**Setup.** No refit: the three known-contamination models of Task 2A/2B (run 1 normal only, `nu = 0.01`; run 3 10%, `nu = 0.0481`; run 6 100%, `nu = 0.2930`) are applied to `Lab3_test.csv` with the train-fitted preprocessing. Test: 2,152 normal, 2,577 dos, 1,097 probe, no r2l (63.1% attacks). Logbook row 2C. "Train" = full train.csv score of the same model (Task 2B).

**[PDF §2] Macro-F1, confusion matrix and per-attack recall on the test set.**

| Model | Train macro-F1 | **Test macro-F1** | Train FPR | Test FPR | TN | FP | FN | TP | Precision (anomaly) | dos recall train → test | probe recall train → test |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Normal only (run 1) | 0.9367 | **0.7971** | 0.010 | 0.308 | 1,489 | 663 | 409 | 3,265 | 0.831 | 0.910 → 0.848 | 0.844 → 0.985 |
| 10% anomalies (run 3) | 0.7638 | 0.7297 | 0.029 | 0.268 | 1,576 | 576 | 936 | 2,738 | 0.826 | 0.501 → 0.688 | 0.523 → 0.881 |
| 100% anomalies (run 6) | 0.7402 | 0.7084 | 0.155 | 0.414 | 1,262 | 890 | 654 | 3,020 | 0.772 | 0.609 → 0.760 | 0.681 → 0.967 |

Confusion matrices: notebook, Task 2C (three panels). Rows = true (normal, anomaly), columns = predicted.

Recall by sub-group (train → test), to see which attacks are missed:

| Group | n train / test | Normal only | 10% | 100% |
| --- | --- | --- | --- | --- |
| dos SYN (`serror_rate` > 0.5) | 1,675 / 548 | 1.000 → 0.996 | 0.545 → 0.761 | 0.643 → 0.852 |
| dos non-SYN | 1,238 / 2,029 | 0.788 → 0.807 | 0.440 → 0.668 | 0.563 → 0.735 |
| probe icmp | 827 / 142 | 0.917 → 0.972 | 0.403 → 0.824 | 0.605 → 0.923 |
| probe tcp | 1,147 / 659 | 0.977 → 0.998 | 0.746 → 0.894 | 0.891 → 0.979 |
| probe udp | 315 / 296 | 0.171 → 0.963 | 0.025 → 0.878 | 0.114 → 0.963 |

**[PDF §2] How do training and test results differ?**

- **Macro-F1 drops for every model**, most for the normal-only one (0.937 → 0.797). The drop does not come from missed attacks. It comes from **false alarms**: test FPR is 27–41%, against 1–15% on train.
- **The cause is a shift in normal traffic.** 834 of the 2,152 normal test connections (38.8%) are UDP connections to service `private` with high-rate traffic statistics (median `count` 220, `dst_host_same_src_port_rate` 0.84). In training normal traffic this pattern is almost absent: 199 `private` connections (1.5%), median `count` 2, `dst_host_same_src_port_rate` 0.01. Overall, 41.4% of normal test connections have `count` > 100, against 7.5% in train. A detector that learnt "normal" from the training file has never seen this kind of normal traffic, so it flags it. 67% of these connections are flagged by the normal-only model, 57% by run 3 and 66% by run 6. The FP rate on the other normal connections is only 7.7% for runs 1 and 3 (25.8% for run 6, whose boundary is tighter).
- In Task 1.3 these features describe DoS and probe (high `count`, `dst_host_same_src_port_rate` ≈ 1 for probe). In the test set, legitimate traffic shows the same values. A feature-based detector cannot tell them apart without seeing this traffic as normal during training.
- **Attack recall is higher on test than on train** for every model, especially for probe (normal only 0.844 → 0.985; run 3 0.523 → 0.881). The test attacks are more extreme versions of the training ones. UDP probe, for example, has median `count` 105 vs 17 in train and `dst_host_diff_srv_rate` 0.76 vs 0.22: run 1 detects 96% of it on test, against only 17% on train. The contaminated models still benefit: the attacks they enclosed in training were the less extreme ones.
- **The test prior changes the metric.** With 63% attacks, precision on the anomaly class stays high (0.77–0.83) even with a 30–40% FPR, because the attacks outnumber the normal connections. The training macro-F1 of the three models was computed at 28.6% contamination, so the two numbers are not directly comparable (same issue as in Task 2B).

**[PDF §2] Which model performs best on unseen traffic?**

**The normal-only model (run 1): macro-F1 0.797**, ahead of 10% (0.730) and 100% (0.708). It has the highest recall on both dos and probe and the fewest FN (409). The ranking of train.csv is preserved, but the gap shrinks from 0.17 to 0.07, because the normal-traffic shift affects all three models.

Our hypothesis that run 6 would overtake run 3 on an attack-heavy test (logbook row 2C) was wrong. Run 6 does detect more attacks (FN 654 vs 936), but its larger `nu` also excludes more normal test traffic (FP 890 vs 576, FPR 41%). In this test set, the extra false alarms weigh more than the extra detections.

**[PDF §2] Are errors mainly false alarms or missed attacks?**

It depends on the model:
- **Normal only:** mainly **false alarms** (FP 663 vs FN 409). 85% of its FP (561/663) are the shifted UDP `private` normal connections. Normal connections with rare error flags are also flagged: RSTR 82%, REJ 61%, S2 75%, the same pattern as for LOF in Task 3.
- **10% anomalies:** mainly **missed attacks** (FN 936 vs FP 576). Its boundary encloses part of the dos/probe region it saw in training.
- **100% anomalies:** mainly **false alarms** (FP 890 vs FN 654). The larger `nu` (0.293) moves the boundary inside the normal region.

Before running we expected errors to be mainly missed attacks for all models. This was true only for run 3.

**[PDF §2] Which attack types are most frequently missed, and why (link to the heatmaps)?**

- **DoS is the most missed type for all three models** (recall 0.85 / 0.69 / 0.76; probe 0.99 / 0.88 / 0.97).
- **Non-SYN DoS is missed most** (normal only: 0.807, vs 0.996 for SYN-flood). This is the bimodality of DoS seen in Task 1.3. SYN-flood connections (`serror_rate` = 1, zero bytes, very high `count`) are far from every normal pattern. The other DoS group is not.
- **The missed DoS of the normal-only model are almost all one attack pattern:** 91% use `http` with flag SF, and 324 of the 393 have the same `src_bytes` = 54,540. Compared with detected DoS, they are logged in (`logged_in` mean 0.88 vs 0.01), have non-zero `dst_bytes` (0.51 vs 0.00), low `count` (0.18 vs 0.80) and `same_srv_rate` ≈ 1. On all these features they look like a normal web session. In the heatmaps, normal traffic is the class with `logged_in` = 1, non-zero bytes and `same_srv_rate` = 1. The only anomalous element is a request much larger than normal http (`src_bytes` 54,540 vs normal http median 243). After `log1p` + min-max it is a small shift in one feature out of 106, and the RBF boundary encloses it. This is a payload-based attack: the traffic features of Task 1.3 cannot reveal it.
- **Probe is almost never missed on test** (16/1,097 for the normal-only model). The few misses are SF connections without REJ errors (`rerror_rate` 0 vs 0.49 for detected probe), mostly to service `other`. As noted in Task 1.3, probe is heterogeneous: the REJ-error part is easy to detect, while the part without errors is closer to normal traffic.
- **R2L is absent from the test set**, so its generalisation cannot be measured. On train it was the most-missed class for the normal-only model (0.017), as the heatmaps predicted (Task 2A).

**Summary.** Clean normal training data remains the most useful knowledge on unseen traffic: it beats both contaminated models. However, the "normal" it learns is only the normal traffic of the training file. When legitimate traffic changes (here, high-rate UDP `private`), a one-class model has no way to know that the new pattern is benign. Under this shift FPR rises from 1% to 31%.

Notebook: Task 2C cells (results table, confusion matrices, sub-group recall and diagnostics).

## Task 3 - Local Outlier Factor

**Knowledge assumed.** LOF is fitted on the full training file (normal + all attacks, no labels). Only the aggregate training contamination (0.286) is used, to set the threshold (known-contamination setting, as in Task 2). Euclidean distance on the 106 preprocessed features.

**[PDF §3] Four `n_neighbors` values and selection criterion.**

We test **5, 20 (sklearn default), 100, 500**, log-spaced to include the extremes: 5 is a very local density estimate; 500 is larger than the whole r2l class (181) and comparable with groups of repeated DoS connections. The four fits form one diagnostic sweep (logbook run 8). Criterion: **highest binary macro-F1 on the training file** (labels for evaluation only), checked against the threshold-free **ROC-AUC** of the LOF score, so that ranking quality is separated from the threshold. With the known contamination, exactly 28.6% of the points are flagged, so FP = FN at every k.

| `n_neighbors` | LOF threshold | Macro-F1 | FPR | dos recall | probe recall | r2l recall | ROC-AUC | Macro-F1 `'auto'` (LOF > 1.5) | Fit s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 1.139 | 0.5145 | 0.2776 | 0.292 | 0.317 | 0.414 | 0.497 | 0.4984 | 0.5 |
| 20 | 1.138 | 0.5294 | 0.2690 | 0.340 | 0.310 | 0.359 | 0.513 | 0.5339 | 0.4 |
| **100** | 1.236 | **0.5774** | 0.2416 | 0.533 | 0.240 | 0.166 | **0.593** | 0.5829 | 0.5 |
| 500 | 1.267 | 0.5224 | 0.2731 | 0.447 | 0.148 | 0.381 | 0.488 | 0.5539 | 1.6 |

**Selected: `n_neighbors = 100`**, the best value on both criteria. The margin is small, though: the best AUC is only 0.59, and with k = 5 and k = 500 the LOF score ranks attacks no better than chance (AUC ≈ 0.5). Flagging 28.6% of points at random would give macro-F1 ≈ 0.5 with recall 0.286 for every class. The `'auto'` threshold (no knowledge of the contamination) flags 11–22% of the points and gives a similar macro-F1. The threshold is therefore not the limitation; the score itself is.

**[PDF §3] Test results; can LOF detect the attacks; local density of attacks; effect of `n_neighbors`.**

Test (logbook run 9, `novelty=True`, threshold from the training contamination): **macro-F1 0.5691**, ROC-AUC 0.605, FPR 0.352, recall **dos 0.611, probe 0.336**. Confusion matrix: TN 1,395, FP 757, FN 1,731, TP 1,943. 46% of the test is flagged (vs 28.6% in train): the larger dos share in test pushes more points above the training threshold. Errors go both ways: one third of normal traffic is flagged, and 47% of the attacks are missed, mostly probe.

- **LOF does not detect the attacks in a useful way.** Its train/test performance is close to a random detector at the same flag rate. With the OC-SVM trained on clean normal data (Task 2A, run 1), the gap is large: macro-F1 0.94 on train.
- **Attacks are not less dense than their neighbours.** The median LOF is ≈ 1.04–1.09 for every class at k = 5 and k = 20. Normal traffic has the same values. LOF measures *relative* density, not distance from normal traffic. As Task 1 suggested, DoS consists of many near-identical connections (zero bytes, same host, `serror_rate` = 1), so each DoS point sits in a dense group of other DoS points, with LOF ≈ 1. **Our hypothesis for probe was wrong:** we expected isolated points, but scans and sweeps also repeat the same connection pattern many times and form dense groups. Probe is the class LOF misses most. **False positives are not explained by rare or extreme normal traffic** (diagnostic at k = 100, notebook): only 5.9% of the 3,249 FP use a service with < 100 training rows, and only 5.0% have bytes or duration above the normal 99th percentile. Most FP are ordinary `http`, `domain_u`, `smtp` and `ftp_data` connections, flagged at a near-uniform rate of 20–30% per service: this is the near-random part of the score. The one clear pattern is error flags. Normal connections with flags S0, S1, RSTO, RSTR, S2 or S3 are flagged 93–100% of the time, and REJ 50%. FP also have higher `rerror` rates and lower `dst_host_srv_count` / `logged_in`. These normal connections look partly like DoS (S0) and probe (REJ), so they lie at the edge of the dense attack groups, where they are sparser than their neighbours. With 28.6% contamination, the attacks are not a small, isolated minority, which is exactly the assumption LOF relies on.
- **Effect of `n_neighbors`.** Small k (5, 20) compares each point only with its own micro-cluster, so a point inside a DoS group looks perfectly normal. At **k = 100** the neighbourhood of a DoS point extends beyond its group: median LOF for dos rises to 1.275 and dos recall to 0.53. At **k = 500** the neighbourhoods are so wide that densities are averaged across classes, and dos (median 1.05) and probe (1.02) look normal again. **R2L behaves the opposite way.** Its 181 connections are all distinct (no duplicates), and 179 of them are `ftp`/`ftp_data` with flag SF, so they form one compact group of their own. At k = 5 and k = 20, 88–92% of an r2l point's neighbours are other r2l points; the median LOF is 1.09 and recall 0.41/0.36, so r2l is slightly sparser than its own group. At k = 100 the neighbours are 71% r2l and 29% normal; the median LOF is 1.00, as dense as its neighbours, and recall falls to 0.17. At k = 500 (more than the 181 r2l points) 81% of the neighbours are normal; LOF rises to 1.10 and recall to 0.38, because the r2l group as a whole is sparser than the normal ftp traffic around it. No single k fits all attacks, because the attack groups have very different sizes.

## Task 4 - Anomaly detection with clustering

### Task 4A - K-Means

**Knowledge assumed.** K-Means is fitted on the full training file (normal + all attacks, no labels), on the same 106 preprocessed features (Euclidean distance). k is chosen **without labels**. Labels are used only afterwards, to describe the clusters and to evaluate the detector. The detector threshold uses the aggregate training contamination (policy a) or a "rare attacks" prior (policy b), as in Task 2.

**[PDF §4.A] Choice of k.**

Diagnostic sweep k = 2…30 (logbook run 10, `n_init=10`, seed 42), with two unsupervised criteria: the SSE elbow and the mean silhouette.

| k | 2-3 | 4-6 | 7-9 | **10** | 11-15 | 16-30 |
| --- | --- | --- | --- | --- | --- | --- |
| SSE drop when adding the k-th cluster | 22% | 13-21% | 7-9% | 9% | 3-7% | 1-4% |
| Mean silhouette | 0.37 / 0.36 | 0.40-0.43 | 0.45-0.47 | **0.487** | 0.41-0.44 | 0.38-0.45 |

The SSE decreases smoothly with no sharp elbow. Up to k = 10 every added cluster still reduces the SSE by 7-9% or more; after k = 10 the gain stays at about 7% or less, and falls below 5% from k = 15. With seed 42 the mean silhouette is highest at k = 10, then drops to 0.41 at k = 11 and oscillates at larger k.

**Robustness to the initialisation (logbook run 12).** We repeated the same procedure (`n_init=10`) for k = 8-12 with five seeds:

| k | 8 | 9 | **10** | 11 | 12 |
| --- | --- | --- | --- | --- | --- |
| Mean silhouette (5 seeds) | 0.457 | 0.471 | **0.485** | 0.445 | 0.419 |
| Range | 0.450-0.469 | 0.465-0.475 | 0.473-0.490 | 0.414 / 0.491 | 0.418-0.421 |

The oscillations are **local optima** of K-Means, not structure in the data. Each seed can converge to a different solution. With a single initialisation (`n_init=1`, exploratory check) the silhouette varies by 0.07-0.11 at the same k, more than between neighbouring k. Even with `n_init=10`, k = 11 has two solutions, at 0.414 (the one seed 42 found) or 0.491, so the drop at k = 11 in run 10 was an artefact of the seed. The decrease from k = 12 is real, because it is stable across seeds. The silhouette is therefore high and flat for k = 9-11. **We keep k = 10**: it has the highest mean silhouette and is the most stable across seeds, while k = 11 depends on the initialisation. It is also the last k where the SSE gain is still about 9%.

Our hypothesis was partly wrong. We expected the best silhouette at k = 2-3 (a coarse split such as SYN flood vs the rest), but k = 2-3 is the worst: a coarse split puts very different services (http, DNS, ftp…) in the same cluster, so points are not cohesive with their own group. The data have about ten natural groups, more than the four labels, as Task 1 suggested: normal traffic differs by `service`/`flag`, DoS is bimodal, probe is heterogeneous.

**[PDF §4.A] Cluster sizes, label distribution and purity.**

Run 11 (k = 10). The last column describes each cluster from its most frequent raw `protocol_type`/`service`/`flag` values and its median `serror_rate`, `rerror_rate`, `count` and `src_bytes`, and is used only to interpret it. The attack technique names (SYN flood, port scan, ping sweep) are our interpretation: the dataset only has the four labels.

| Cluster | Size | normal | dos | probe | r2l | Purity | What it is |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 7,251 | 7,055 | 196 | 0 | 0 | 0.973 | http (100%), SF |
| 3 | 1,841 | 1,841 | 0 | 0 | 0 | **1.000** | UDP, domain_u (DNS, 97%) |
| 2 | 1,757 | 15 | 1,657 | 85 | 0 | 0.943 | SYN flood: flag S0 (96%), median `serror_rate` 1, `count` 171, 0 bytes |
| 0 | 1,642 | 1,493 | 0 | 25 | 124 | 0.909 | ftp_data (68%), telnet (12%), finger (7%), SF |
| 9 | 1,620 | 1,556 | 0 | 7 | 57 | 0.960 | smtp (86%), ftp (14%), SF |
| 4 | 1,417 | 50 | 343 | 1,024 | 0 | 0.723 | port scan: REJ (60%) / RSTR (33%), median `rerror_rate` 1, many different services |
| 6 | 1,169 | 666 | 188 | 315 | 0 | **0.570** | UDP, private (56%) / other (39%) |
| 8 | 871 | 57 | 0 | 814 | 0 | 0.935 | ping sweep: ICMP eco_i (echo request, 100%), median `count` 1 (one connection to the same host in the 2-s window), 8 bytes |
| 7 | 746 | 204 | 529 | 13 | 0 | 0.709 | ICMP ecr_i (echo reply, 77%) / urp_i (17%), median `count` 284, 1,032 bytes |
| 5 | 517 | 511 | 0 | 6 | 0 | 0.988 | http (98%), flag REJ (99%) |

- **Sizes** range from 517 to 7,251. The http cluster alone holds 38.5% of the training set.
- **Only one cluster is pure** (DNS, normal only). The size-weighted purity is 0.911, but this number is inflated by normal traffic, which is 71% of the data and dominates the largest clusters.
- **Normal traffic is split by service**: http, DNS, ftp_data, smtp, plus a normal http cluster with flag REJ. Normal also occurs inside every attack cluster.
- **Attacks are split by technique, not by label.** DoS goes to five clusters: SYN flood (57% of dos, in an almost pure cluster), ICMP echo reply (18%), REJ (12%), http (7%) and UDP (7%). Probe goes to three: REJ port scans (45%), ICMP ping sweep (36%, purity 0.935) and UDP (14%).
- **r2l has no cluster of its own.** Its 181 points are fewer than the smallest cluster (517): 68% fall in the ftp_data cluster and 32% in the smtp cluster. As Task 1 showed, r2l looks like normal ftp/smtp traffic except for a few content features.

**[PDF §4.A] Silhouette per cluster; low-silhouette clusters and their labels.**

Silhouette computed on all 18,831 points (mean 0.487).

| Cluster | 0 ftp_data | 6 UDP | 4 REJ | 9 smtp | 7 ICMP ecr_i | 2 SYN flood | 1 http | 5 http REJ | 3 DNS | 8 ping sweep |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Mean silhouette | **0.196** | **0.208** | **0.224** | 0.318 | 0.377 | 0.559 | 0.601 | 0.609 | 0.663 | **0.700** |
| Negative share | 4.3% | 8.1% | 3.5% | 0% | 3.9% | 0.1% | 0% | 0% | 0% | 0% |

- **The three lowest-silhouette clusters are the mixed ones.** ftp_data contains normal + 124 r2l + 25 probe; UDP contains normal 666 + probe 315 + dos 188, with purity 0.57 and 8% negative silhouettes; REJ contains probe 1,024 + dos 343 + normal 50. Inside the REJ cluster the 50 normal points have a mean silhouette of 0.007: they lie exactly on the boundary with another cluster. In the ICMP echo reply cluster, the 204 normal points have 0.148 against 0.475 for dos.
- Low silhouette is not only caused by the attack points. The normal points of the ftp_data cluster also have a low silhouette (0.194): the cluster mixes several services (ftp_data is only 68%), so it is wide.
- **The most cohesive cluster is an attack cluster**: the ping sweep (0.700). The SYN flood is also well separated (0.559). We did not expect this. These attacks repeat the same connection pattern many times, so they form compact groups, as already seen with LOF in Task 3.

**[PDF §4.A] Distance-to-centroid threshold; detected vs missed attacks.**

The anomaly score is the Euclidean distance from the closest centroid of the run-11 model. There is no new fit; the logbook row "4A-det" is not counted in the budget. We use one **global** threshold with two policies, as in Task 2:
- **(a) known contamination**: flag the 28.6% farthest points (threshold = the 71.4th percentile of the training distances);
- **(b) unknown contamination**: prior "attacks are rare", flag the 5% farthest points (same prior as `nu = 0.05` in run 7).

| Policy | Macro-F1 | FPR | Recall dos | Recall probe | Recall r2l | Precision |
| --- | --- | --- | --- | --- | --- | --- |
| (a) known, 28.6% | **0.654** | 0.198 | 0.398 | 0.607 | **0.972** | 0.506 |
| (b) prior, 5% | 0.473 | 0.041 | 0.027 | 0.125 | 0.138 | 0.415 |

The threshold-free ROC-AUC of the distance score is **0.729**, against 0.593 for LOF (k = 100) in Task 3.

- **Detected.** Almost all r2l is detected (176 of 181, 97%), but for two different reasons. In the smtp cluster (57 r2l, all flagged) r2l is really atypical: its mean distance from the centroid is about twice that of the normal points of the cluster (1.79 vs 0.92; threshold 1.08). The largest contributions come from `is_guest_login`, `hot` and from being ftp connections in a mostly smtp cluster. In the ftp_data cluster (124 r2l, 119 flagged) r2l is **not** clearly farther from the centroid than normal traffic: mean distance 1.22 vs 1.18, both above the threshold (1.08). Its distance is driven by host statistics (`dst_host_same_src_port_rate`, `dst_host_same_srv_rate`, `dst_host_count`), and it is flagged only because the whole cluster is wide: 47% of the normal points there are flagged too. The REJ probe + dos cluster is detected almost entirely (1,020 of 1,024 probe, 337 of 343 dos), because the cluster is wide. All 188 UDP dos and 67% of the UDP probe are detected for the same reason.
- **Missed.** The **ICMP ping sweep** is missed: only 25 of its 814 probe points are flagged (3.1%). So is the **ICMP echo reply DoS**: 24 of 529 (4.5%); the cluster's 32% flag rate comes almost entirely from its 204 normal points, which are all flagged. Two thirds of the **SYN flood** DoS is missed: 555 of 1,657 flagged (33.5%). These attacks form compact clusters with their own centroid, so most points are close to "their" centre.
- **False positives** come from the wide clusters. In the UDP cluster 658 of its 666 normal points are flagged. The ftp_data cluster gives 705 FP and smtp 354. Compact normal clusters are rarely flagged (http 5%, DNS 14%).
- **What the score really measures.** With a global threshold on the raw distance, the decision mainly reflects **how spread the cluster is**: wide clusters are flagged almost entirely, whether they hold attacks (REJ) or normal traffic (UDP), and compact clusters pass, even when they are attacks (ping sweep). This is the same limit as LOF. The attacks are not a small, isolated minority; they form dense groups that receive their own centroid.
- **Policy (b)** flags only 5% and catches almost nothing. Its precision (0.42) is even lower than with (a) (0.51): the farthest points are largely unusual normal connections. The assumption "attacks are rare" does not hold on a training set with 28.6% contamination.
- K-Means does better than LOF on the training file (macro-F1 0.654 vs 0.577, AUC 0.73 vs 0.59), but it remains a weak detector: one normal connection in five is flagged, and 60% of the DoS is missed.

**[PDF §4.A] t-SNE (3 perplexities), coloured by label vs cluster.**

t-SNE of all 18,831 training points (`init='pca'`, seed 42) with perplexity **5, 30 and 100** (81, 84 and 107 s). Each embedding is shown twice, coloured by attack label and by K-Means cluster (k = 10). The reading is **visual only**: t-SNE preserves local neighbourhoods, but the distances between islands and their sizes are not reliable. We therefore state only patterns that appear at all three perplexities and agree with the K-Means tables.

- **Effect of perplexity.** At 5 the map is a uniform disc of short filaments: only very local structure, no clear groups. At 30 and 100 the points separate into islands, which are more compact at 100. The conclusions below hold at 30 and 100 and are already visible as sectors at 5.
- **Label vs cluster colouring: the main difference.** In the label view, normal traffic is a single colour spread over many separate islands. The cluster view splits it into http (cluster 1), DNS (3), ftp_data (0), smtp (9), http-REJ (5) and UDP (6). K-Means follows the **service/flag structure** that t-SNE also shows, while the labels group very different traffic under one name. The same holds for the attacks: "dos" is several distant islands (SYN flood, ICMP echo reply, smaller groups), and each matches one K-Means cluster. A cluster therefore describes an attack *technique* (SYN flood, ping sweep, port scan) better than the label does.
- **Where the two views disagree (largest overlaps).**
  - (1) **r2l inside normal islands.** The small r2l groups sit inside or at the edge of normal ftp_data/smtp islands (clusters 0 and 9). r2l shares protocol, service, flag, login status and byte volumes with this traffic and differs only on a few content features (`hot`, `is_guest_login`).
  - (2) **Probe and dos interleaved** in the REJ islands (cluster 4) and in the UDP islands (cluster 6), together with normal UDP traffic. These points share protocol, service and flag; the one-hot columns weigh as much as a full-range numerical feature in the Euclidean distance, so these points end up close to each other.
  - (3) **Clusters split over several islands.** Some single clusters appear as two or more separate islands, so K-Means merged groups that t-SNE keeps apart: http (cluster 1), smtp/ftp (9), ftp_data/telnet/finger (0) and especially UDP (6). This agrees with their low silhouette and, for UDP, its purity of 0.57.
- **Attacks that fall in close regions.** Most DoS and probe islands (SYN flood, REJ scans, UDP) lie on the same side of the map, away from the bulk of normal traffic, at all three perplexities. They share no payload, no login, many connections per host and high error rates. The exception is the ICMP ping sweep, which forms its own island elsewhere. r2l instead lies among normal islands. We do not read more into the distances between islands.
- **Compactness of the attack islands.** The ping sweep (cluster 8) is one dense, isolated island, consistent with its silhouette of 0.70. It is missed by the distance-to-centroid detector because every point is close to its own centre. The SYN flood (cluster 2) shows a dense core plus a halo of scattered points. This is consistent with only part of it (37%) being flagged, but we did not check that the flagged points are the halo.

### Task 4B - DBSCAN

**Knowledge assumed.** DBSCAN is fitted on the full training file (normal + all attacks, no labels), on the same 106 preprocessed features (Euclidean distance). Neither the labels nor the contamination are used to choose `min_samples` and ε. Noise (cluster −1) is treated as anomaly; there is no threshold to set.

**[PDF §4.B] Choice of `min_points` and ε.**

- **`min_points` (`min_samples` in sklearn, the point itself included) = 100.** We consider "normal" a behaviour that is repeated in at least about 100 similar connections; whatever belongs to no such group is an anomaly. 100 is also the neighbourhood size of the LOF selected in Task 3 (`n_neighbors` = 100), so the two density-based methods work at the same scale and can be compared directly.
- **ε from the k-distance plot** (logbook run 13). For every training point we compute the distance to its 100th nearest neighbour, sort the values and take the elbow with the kneedle rule (the point of the normalised curve farthest from the diagonal). We declared this criterion before seeing the curve. Result: **ε = 0.570**, at 67.6% of the sorted points, so at most 32.4% of the points can be noise.
- **The curve has no sharp elbow.** It rises gradually from about the 60th percentile (median 100-distance 0.30, 90th percentile 1.42). Our hypothesis (a flat curve with a jump in the last few percent, leaving 5-15% above ε) was wrong.
- **A plateau at √2 ≈ 1.414** contains 956 points (933 dos). In our encoding, connections that differ only in `service` are √2 apart (two one-hot columns change). These points are **SYN-flood connections spread over many services** (bgp, Z39_50, imap4…), with fewer than 100 connections per service, so their 100th neighbour always has a different service. The ε choice around √2 therefore decides their fate. With ε < √2 they cannot be core points and become noise. With a larger ε (the visual elbow of the upper tail, ε ≈ 1.45, would leave only 6.7% of the points above ε) they would merge across services into a dense cluster and be missed. We kept the declared criterion (ε = 0.570) and did not fit the alternative, to save runs.

**[PDF §4.B] Is the noise cluster only anomalies; number of clusters.**

DBSCAN (logbook run 14) finds **18 clusters**. 67.6% of the points are core points and **25.1% are noise** (4,728 points).

| | normal | dos | probe | r2l |
| --- | --- | --- | --- | --- |
| Points in noise | 2,237 | 1,536 | 933 | 22 |
| Share of the noise | 47.3% | 32.5% | 19.7% | 0.5% |
| Share of the label in noise | 16.6% | 52.7% | 40.8% | 12.2% |

- **No, the noise is not only anomalies.** Almost half of it is normal traffic: 2,237 connections, 16.6% of all normal traffic. They come from many services (http 373, other 298, domain_u 230, telnet 209, private 199, ftp_data 188, smtp 172) and are mostly flag SF (1,776), with some error flags (REJ 190, S1 86, S0 80, RSTO 44…). As a detector the noise gives **macro-F1 0.653**, FPR 0.166, precision 0.527, recall dos 0.527, probe 0.408, r2l 0.122.
- **The clusters are much purer than with K-Means.** 14 of the 18 are pure, and each one corresponds to a single `service` + `flag` combination. Several clusters are **attacks**, and DBSCAN does not flag them because they are dense:
  - SYN flood on `private` (602 dos);
  - ICMP echo reply dos (509);
  - ICMP ping sweep (686 probe, plus 111 probe with 40 normal);
  - five port-scan clusters with flag REJ or RSTR, of 100-181 points each (four probe, one dos). About 100 identical repeated connections are enough to look "normal" to DBSCAN.
- **What is detected.** All 956 points of the √2 plateau are noise: 1,055 SYN-flood connections on 54 different services are detected, while the 602 on `private` are missed. **r2l is mostly missed**: 105 of its 181 points are inside the normal ftp_data cluster and 54 inside the ftp cluster. The group is compact, and 181 points are enough to be dense with `min_samples` = 100. Our hypothesis (r2l partly noise) was wrong. We also expected tens of clusters, not 18.
- Compared with K-Means (known-contamination threshold), DBSCAN reaches the same macro-F1 (0.653 vs 0.654) with fewer FP (FPR 0.166 vs 0.198), but it catches different attacks: more dos (0.53 vs 0.40), less probe (0.41 vs 0.61) and almost no r2l (0.12 vs 0.97).

**[PDF §4.B] Similarities with LOF (examples).**

LOF is recomputed with the Task 3 selection (`n_neighbors` = 100, known contamination). It is the same deterministic model as logbook run 8 (macro-F1 0.5774 again), so it is not a new run. Both methods use the density of the 100 nearest neighbours.

| | Flagged | Macro-F1 | FPR | Recall dos | Recall probe | Recall r2l |
| --- | --- | --- | --- | --- | --- | --- |
| DBSCAN noise | 25.1% | 0.653 | 0.166 | 0.527 | 0.408 | 0.122 |
| LOF, k = 100 | 28.6% | 0.577 | 0.242 | 0.534 | 0.240 | 0.166 |

**Agreement.** 2,787 points are flagged by both, 1,941 only by DBSCAN, 2,596 only by LOF, and 11,507 by neither. The two methods agree on 75.9% of the points. 58.9% of the DBSCAN noise is also flagged by LOF, and 51.8% of the LOF flags are DBSCAN noise. The median LOF value is 1.41 for DBSCAN noise and 1.05 for clustered points. The two methods overlap, but they are far from identical.

**Examples by group** (labels and raw features used only to define the groups):

| Group | n | DBSCAN noise | LOF flag | Both | Median 100-distance | Median LOF value |
| --- | --- | --- | --- | --- | --- | --- |
| SYN flood on `private` | 607 | 0.8% | 24.2% | 0.8% | 0.11 | 1.04 |
| SYN flood on other services | 1,050 | **100%** | **93.2%** | 93.2% | 1.42 | **3.62** |
| ICMP echo reply dos | 529 | 3.8% | 28.4% | 3.8% | 0.37 | 1.06 |
| ICMP ping sweep probe | 816 | 2.3% | 13.1% | 1.6% | 0.25 | 1.07 |
| Port-scan probe (REJ/RSTR) | 1,005 | 44.6% | 28.3% | 22.5% | 0.72 | 1.03 |
| r2l | 181 | 12.2% | 16.6% | 12.2% | 0.29 | 1.00 |
| Normal, error flag | 785 | 58.6% | 66.0% | 42.8% | 0.96 | 1.38 |
| Normal, flag SF | 12,662 | 14.0% | 21.6% | 6.6% | 0.21 | 1.05 |

- **Same blind spot: dense attack groups.** The SYN flood on `private`, the ICMP echo reply dos and the ping sweep have a very small 100-distance (0.11-0.37) and a LOF value of about 1: each point is as dense as its neighbours. Both methods miss them; DBSCAN almost completely (≤ 4%), LOF mostly (13-28%).
- **Same strength: the SYN flood spread over many services.** We expected only DBSCAN to flag it, but **LOF flags 93% of it too** (median LOF value 3.6, the highest of all groups), so our expectation was wrong. Those points are at √2 from their 100th neighbour, beyond ε, so DBSCAN marks them as noise. For LOF, their neighbours belong to much denser groups (e.g. the SYN flood on `private`, 100-distance 0.11), so these points are far less dense than their neighbours. The two criteria differ (absolute radius vs relative density), but here they agree.
- **Same weak point on r2l.** r2l is compact (100-distance 0.29, LOF value 1.00) and both methods mostly miss it (12% and 17%). The 22 r2l points that DBSCAN marks as noise are also flagged by LOF.
- **Same source of false positives: normal traffic with error flags.** Normal connections with S0, S1, S2, S3, REJ, RSTO or RSTR are flagged by both: 58.6% by DBSCAN and 66.0% by LOF, against 14.0% and 21.6% for normal SF traffic. They lie at the edge of the dense attack groups, as we found for LOF in Task 3.
- **Where they differ.** LOF flags more scattered normal SF traffic, because it always flags 28.6% of the points. DBSCAN flags more port-scan probe (44.6% vs 28.3%): scans that do not reach 100 similar connections stay outside every cluster even though their relative density is not lower than their neighbours'. In short, DBSCAN needs a large enough absolute density, while LOF needs a lower density than the neighbours.

## Task 5 - Isolation Forest

**Not part of the assignment.** The PDF text goes from Task 4 to Task 6. Isolation Forest is still mentioned in the objectives and in the run budget ("a couple for Isolation Forest (Task 5)"), but the teaching staff confirmed that the task was removed on purpose. We do not implement it. The ~2 runs the guide reserved for it cover the extra clustering run (Task 4 uses 5 runs instead of ~4), so the total stays within the ~25 budget (about 22 planned).

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

The current logbook lists **9 retained runs** (budget ~25): Task 2 runs 1-7, Task 3 runs 8-9. Task 2C is a test evaluation of runs 1, 3, 6 and uses no budget.

- [ ] Report `groupID_lab3.pdf`, maximum 10 pages, with decisions, measured results and reasoning.
- [ ] Experiment logbook, separate or appendix (outside the page limit).
- [ ] Executed, rerunnable notebook/code and HTML export.
- [ ] Final package `groupID_lab3.zip`.
