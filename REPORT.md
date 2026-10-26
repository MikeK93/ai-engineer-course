# Report: model x prompt version x sampling

<!-- AUTO:START -->
| run | model | input | prompt | golden | temp / top_p | docs | field acc % | valid % (first try) | latency p50 / p95 s | $ per 1000 docs |
|---|---|---|---|---|---|---|---|---|---|---|
| [20261016-195356_api_t0](results/20261016-195356_api_t0/report.md) | gemini/gemini-2.5-flash | text | v1 | v1 | 0.0 / 1.0 | 2 | 76.8 | 100 (100) | 8.6 / 15.2 | 7.54 |
| [20261018-143618_api_t0_v2](results/20261018-143618_api_t0_v2/report.md) | gemini/gemini-2.5-flash | text | v2 | v1 | 0.0 / 1.0 | 2 | 71.4 | 100 (100) | 8.7 / 14.5 | 7.61 |
| [20261018-144118_api_t0_v2](results/20261018-144118_api_t0_v2/report.md) | gemini/gemini-2.5-flash | text | v2 | v1 | 0.0 / 1.0 | 2 | 76.8 | 100 (100) | 8.9 / 14.8 | 8.07 |
| [20261019-122933_api_t07_v2](results/20261019-122933_api_t07_v2/report.md) | gemini/gemini-2.5-flash | text | v2 | v1 | 0.7 / 0.9 | 2 | 71.4 | 100 (100) | 8.4 / 11.3 | 6.36 |
| [20261020-161038_api_t0_v3](results/20261020-161038_api_t0_v3/report.md) | gemini/gemini-2.5-flash | text | v3 | v2 | 0.0 / 1.0 | 2 | 91.1 | 100 (100) | 8.6 / 11.6 | 6.07 |
| [20261020-163310_api_t0_pdf_v3](results/20261020-163310_api_t0_pdf_v3/report.md) | gemini/gemini-2.5-flash | pdf | v3 | v2 | 0.0 / 1.0 | 2 | 89.3 | 100 (100) | 18.0 / 18.5 | 7.46 |
| [20261021-172003_api_t0_pdf_v3](results/20261021-172003_api_t0_pdf_v3/report.md) | gemini/gemini-2.5-flash | pdf | v3 | v3 | 0.0 / 1.0 | 2 | 83.9 | 100 (100) | 19.5 / 32.6 | 8.44 |
| [20261025-170855_api_t0_pdf_v3](results/20261025-170855_api_t0_pdf_v3/report.md) | openrouter/google/gemini-2.5-flash | pdf | v3 | latest | 0.0 / 1.0 | 10 | 83.2 | 100 (100) | 5.4 / 9.0 | 1.67 |
| [20261025-171014_api_t0_pdf_v3](results/20261025-171014_api_t0_pdf_v3/report.md) | openrouter/google/gemini-3.5-flash | pdf | v3 | latest | 0.0 / 1.0 | 10 | 78.6 | 100 (90) | 15.0 / 28.8 | 35.15 |
| [20261025-171331_api_t0_pdf_v3](results/20261025-171331_api_t0_pdf_v3/report.md) | openrouter/openai/gpt-5.6-sol | pdf | v3 | latest | 0.0 / 1.0 | 10 | 78.9 | 100 (100) | 10.6 / 14.9 | 187.15 |
| [20261025-184113_api_t0_pdf_google_gemini-2.5-flash_v4](results/20261025-184113_api_t0_pdf_google_gemini-2.5-flash_v4/report.md) | openrouter/google/gemini-2.5-flash | pdf | v4 | latest | 0.0 / 1.0 | 10 | 86.8 | 100 (100) | 6.5 / 9.6 | 1.56 |
| [20261026-110848_api_t0_pdf_v4](results/20261026-110848_api_t0_pdf_v4/report.md) | openrouter/google/gemini-3.5-flash | pdf | v4 | latest | 0.0 / 1.0 | 10 | 86.1 | 100 (100) | 14.9 / 19.4 | 33.72 |
| [20261026-112244_api_t0_pdf_v4](results/20261026-112244_api_t0_pdf_v4/report.md) | openrouter/google/gemini-3.5-flash | pdf | v4 | latest | 0.0 / 1.0 | 10 | 87.9 | 100 (100) | 12.5 / 16.5 | 34.70 |
| [20261026-112950_api_t0_pdf_v4](results/20261026-112950_api_t0_pdf_v4/report.md) | openrouter/google/gemini-3.5-flash | pdf | v4 | latest | 0.0 / 1.0 | 10 | 89.3 | 100 (100) | 13.2 / 27.1 | 31.34 |
| [20261026-113445_api_t0_pdf_google_gemini-2.5-flash_v4](results/20261026-113445_api_t0_pdf_google_gemini-2.5-flash_v4/report.md) | openrouter/google/gemini-2.5-flash | pdf | v4 | latest | 0.0 / 1.0 | 10 | 89.6 | 100 (100) | 5.2 / 11.5 | 1.86 |
| [20261026-113554_api_t0_pdf_openai_gpt-5.6-sol_v4](results/20261026-113554_api_t0_pdf_openai_gpt-5.6-sol_v4/report.md) | openrouter/openai/gpt-5.6-sol | pdf | v4 | latest | 0.0 / 1.0 | 10 | 85.4 | 100 (100) | 11.1 / 42.0 | 248.27 |
| [20261026-121226_local_t0_text_v4](results/20261026-121226_local_t0_text_v4/report.md) | ollama_chat/qwen2.5:3b | text | v4 | latest | 0.0 / 1.0 | 10 | 49.3 | 90 (90) | 57.8 / 88.4 | 0.00 |
<!-- AUTO:END -->

## Error analysis

_3-5 characteristic errors here: what was returned instead of what, and why._

- Price related fields were not correctly extracted due to weak prompt no guiding to specific sections within docs;
- Total floors also lacked value due to business terminology - "Story"/"Stories" = "Floor"/"Floors";
- Size related fields sometimes picked up wrong value. Schema updates helped to guide towards rules;
- Local `qwen2.5:3b` on extracted text,scored 49.3% field accuracy. While the accuracy is low now, it can potentially be tweaked if the volume of input docs grows and cost of provider's api gets higher.


## Production choice

_One paragraph: the chosen model, prompt version and sampling, and the conditions under which you would change the decision._

Looks like `gemini-2.5-flash` shows best results in terms of %. However, despite the fact that `gemini-3.5-flash` is a bit behind the 2.5 flash, when comparing results side-by-side I would prefer to use 3.5 over 2.5 because it all comes to the gaps in specific fields. 2.5 was not picking up critical fields correctly such as prise and size, where 3.5 showed excelent results.

Another model that was under test is `openai-gpt5.6-sol` which shows the worst results among these 3 models and shows (which is expected) the highest cost per 1000 docs.

So my choice for production would be `gemini-3.5-flash`. Feels like a good balance between speed, cost and accuracy. If the cost would be too hight I'd move to `gemini-2.5-flash` and work out the prompt + schema to gain more accuracy for critical fields.

Worth noting that the API runs were done with raw PDF files being passed to the model because the files contained images describing listed property which will result in 0 text after pdf -> text convertion.

The local run supports the same choice. `ollama_chat/qwen2.5:3b` (text, prompt v4, temperature 0) reached 49.3% field accuracy, 90% valid responses, and about 58s / 88s latency at $0 per 1000 docs. Address fields and `deal_type` are usable (city, zip, and street around 80-90%), and everything that depends on an enum or on a figure inside an image is not. I would use it only if API cost had to be zero and the task were limited to those address and deal-type fields. For the full schema I would stay on `gemini-3.5-flash` with the PDF input. 