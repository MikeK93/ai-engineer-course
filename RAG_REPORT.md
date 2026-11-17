# RAG report

## k-sweep

Prompt v2, rerank, the same questions at each k. Context budget 8000 tokens, so the cutoff is the number of chunks.

| k | recall | pass | facts | cited | abstain | false abstain | judge | grounded | tokens | answer $ / 1000 | judge $ / 1000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 0.89 | 0.83 | 0.80 | 0.92 | 1.00 | 0.08 | 0.83 | 1.00 | 55886 | 1.20 | 0.19 |
| 5 | 0.96 | 0.72 | 0.80 | 0.96 | 0.50 | 0.00 | 0.86 | 0.96 | 79774 | 1.63 | 0.22 |
| 10 | 1.00 | 0.83 | 0.84 | 0.96 | 1.00 | 0.00 | 0.83 | 1.00 | 134458 | 2.29 | 0.24 |

k=5 is the current default. k=3 scores a higher pass rate and a perfect abstain rate, and its recall falls to 0.89 with a false-abstain rate of 0.08. At k=3 the Bunker Hill question (m02) abstains. At k=10 recall is 1.00, m02 cites both the price and the amenities and passes, and the answer cost rises from $1.63 to $2.29 per 1000 questions.
