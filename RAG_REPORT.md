# RAG report

## k-sweep

Prompt v2, rerank, the same questions at each k. Context budget 8000 tokens, so the cutoff is the number of chunks.

| k | recall | pass | facts | cited | abstain | false abstain | judge | grounded | tokens | answer $ / 1000 | judge $ / 1000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 0.89 | 0.83 | 0.80 | 0.92 | 1.00 | 0.08 | 0.83 | 1.00 | 55886 | 1.20 | 0.19 |
| 5 | 0.96 | 0.72 | 0.80 | 0.96 | 0.50 | 0.00 | 0.86 | 0.96 | 79774 | 1.63 | 0.22 |
| 10 | 1.00 | 0.83 | 0.84 | 0.96 | 1.00 | 0.00 | 0.83 | 1.00 | 134458 | 2.29 | 0.24 |

k=5 is the current default. k=3 scores a higher pass rate and a perfect abstain rate, and its recall falls to 0.89 with a false-abstain rate of 0.08. At k=3 the Bunker Hill question (m02) abstains. At k=10 recall is 1.00, m02 cites both the price and the amenities and passes, and the answer cost rises from $1.63 to $2.29 per 1000 questions.

## Eval runs

One row per rag-eval report. Unstamped runs first, then by time.

| run | recall | pass | facts | cited | abstain | false abstain | judge | grounded | answer $ / 1000 | flaky | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v2 | 0.92 | 0.69 | 0.72 | 0.88 | 0.50 | 0.12 | 0.72 | 0.92 | 1.6810 | none | floor: pass 0.69 < 0.70; floor: abstain 0.50 < 1.00 |
| v2 2026-11-15 20:53 | 0.96 | 0.76 | 0.80 | 0.92 | 0.75 | 0.04 | 0.79 | 0.96 | 1.6493 | none | floor: abstain 0.75 < 1.00 |
| v2 2026-11-16 20:38 | 0.96 | 0.69 | 0.80 | 0.92 | 0.50 | 0.00 | 0.79 | 0.93 | 1.6372 | none | floor: pass 0.69 < 0.70; floor: abstain 0.50 < 1.00 |
| v2 2026-11-17 11:06 | 0.96 | 0.72 | 0.81 | 0.92 | 0.58 | 0.01 | 0.84 | 0.96 | 1.6435 | e02, o02, n04, f02 | floor: abstain 0.58 < 1.00 |
| v3 2026-11-17 15:58 | 0.96 | 0.76 | 0.76 | 0.96 | 1.00 | 0.00 | 0.86 | 1.00 | 1.3971 | none | baseline: facts 0.76 fell below 0.81; regression: s04 |
