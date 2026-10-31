# Task 2 - Experiment logbook

CPU; seed 42; Adam lr=0.001; batch 64; 20 epochs; threshold 0.5. Training-only vocabulary/scaling. Times cover training only.

## Selected training runs

| Run | Model | Reason / expectation | Val macro-F1 | Train s | Conclusion |
| --- | --- | --- | --- | --- | --- |
| 1 | Unigram Standard | API counts may distinguish the classes | 0.8029 | 5.31 | Reference model |
| 2 | Unigram Weighted | Class weights may improve goodware detection | 0.7691 | 5.32 | Goodware recall improves; macro-F1 falls |
| 3 | Unigram + bigram Standard | Adjacent API pairs may add useful information | 0.8573 | 8.96 | Selected baseline |

Also evaluated and discarded: bigram Weighted, validation macro-F1 0.7905. Full results remain in the notebook.

## Final test evaluations

Models selected on validation; same trained model evaluated on original and shuffled test, without retraining.

| Model | Selected variant | Val macro-F1 | Test macro-F1 | Shuffled test macro-F1 | Train s | Device / epochs | Changed predictions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Unigram | Standard | 0.8029 | 0.7985 | 0.7985 | 5.31 | CPU / 20 | 0 |
| Unigram + bigram | Standard | 0.8573 | 0.8440 | 0.5185 | 8.96 | CPU / 20 | 390 |
