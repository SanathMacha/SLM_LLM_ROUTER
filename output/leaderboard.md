# SLM+LLM Cascade Router Evaluation Leaderboard

This table compares our Cascade Router strategies across all strictness thresholds against the mathematical baseline ceiling (All-LLM).

| Strategy / Strictness | Escalation Rate (95% CI) | Accuracy (95% CI) | Total Cost (USD) | Savings vs LLM | Cost/Correct (USD) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| All-LLM Baseline (Ceiling) | 100.0% (N/A) | 100.0% (N/A) | $0.0050 | 0.0% | $0.000042 |
| Cascade Router L0 | 0.0% (0.0%-0.0%) | 85.8% (79.6%-92.1%) | $0.0000 | 100.0% | $0.000000 |
| Cascade Router L1 | 14.2% (7.9%-20.4%) | 100.0% (100.0%-100.0%) | $0.0007 | 85.4% | $0.000006 |
| Cascade Router L2 | 14.2% (7.9%-20.4%) | 100.0% (100.0%-100.0%) | $0.0007 | 85.4% | $0.000006 |
| Cascade Router L3 | 14.2% (7.9%-20.4%) | 100.0% (100.0%-100.0%) | $0.0007 | 85.4% | $0.000006 |
| **Cascade Router L4 (Headline)** | **14.2% (7.9%-20.4%)** | **100.0% (100.0%-100.0%)** | **$0.0007** | **85.4%** | **$0.000006** |
| Cascade Router L5 | 100.0% (100.0%-100.0%) | 100.0% (100.0%-100.0%) | $0.0050 | 0.0% | $0.000042 |
