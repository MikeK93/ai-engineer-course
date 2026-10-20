# Report: model x prompt version x sampling

<!-- AUTO:START -->
| run | model | input | prompt | temp / top_p | docs | field acc % | valid % (first try) | latency p50 / p95 s | $ per 1000 docs |
|---|---|---|---|---|---|---|---|---|---|
| [20261016-195356_api_t0](results/20261016-195356_api_t0/report.md) | gemini/gemini-2.5-flash | text | v1 | 0.0 / 1.0 | 2 | 76.8 | 100 (100) | 8.6 / 15.2 | 7.54 |
| [20261018-143618_api_t0_v2](results/20261018-143618_api_t0_v2/report.md) | gemini/gemini-2.5-flash | text | v2 | 0.0 / 1.0 | 2 | 71.4 | 100 (100) | 8.7 / 14.5 | 7.61 |
| [20261018-144118_api_t0_v2](results/20261018-144118_api_t0_v2/report.md) | gemini/gemini-2.5-flash | text | v2 | 0.0 / 1.0 | 2 | 76.8 | 100 (100) | 8.9 / 14.8 | 8.07 |
| [20261019-122933_api_t07_v2](results/20261019-122933_api_t07_v2/report.md) | gemini/gemini-2.5-flash | text | v2 | 0.7 / 0.9 | 2 | 71.4 | 100 (100) | 8.4 / 11.3 | 6.36 |
<!-- AUTO:END -->

## Error analysis

_Write 3-5 characteristic errors here: what was returned instead of what, and why._

## Production choice

_One paragraph: the chosen model, prompt version and sampling, and the conditions under which you would change the decision._
