# Task 2 - Final test evaluations

Standard/Weighted selected on validation; same trained model evaluated on original and shuffled test. Seed 42, Adam lr=0.001, batch 64, threshold 0.5. Time covers training only. Filled manually; no historical runs.

| Model | Selected variant | Val macro-F1 | Test macro-F1 | Shuffled test macro-F1 | Train s | Device / epochs | Changed predictions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Unigram | Standard | 0.8029 | 0.7985 | 0.7985 | 5.31 | CPU / 20 | 0 |
| Unigram + bigram | Standard | 0.8573 | 0.8440 | 0.5185 | 8.96 | CPU / 20 | 390 |
