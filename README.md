# Structured Extraction Service

Extracts structured data (see `src/schema.py`) from commercial real estate PDFs, compares models and prompt versions, and scores them against a golden set.

## Requirements

- Python 3.11+
- An API key for one provider supported by [LiteLLM](https://docs.litellm.ai/docs/providers) (Gemini, OpenAI, Anthropic, OpenRouter, ...)
- [Ollama](https://ollama.com) for the local model

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then fill in the key
ollama pull qwen2.5:3b      # local model
ollama list                 # check Ollama is running before local runs
```

`.env` variables:

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` / `OPENROUTER_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | Key for the provider you use |
| `EXTRACT_MODEL` | API model as a LiteLLM string, e.g. `gemini/gemini-2.5-flash`, `openai/gpt-4o-mini`, `openrouter/google/gemini-2.5-flash` |
| `LOCAL_MODEL` | Local model, e.g. `ollama_chat/qwen2.5:3b` |
| `OLLAMA_API_BASE` | Ollama URL, default `http://localhost:11434` |

Switching provider means changing `EXTRACT_MODEL` and the matching key. No code changes.

## Workflow

```powershell
# 1. (optional) extract and cache text from all PDFs into data/texts/
python main.py extract

# 2. run a config on the golden set (10 documents) or on everything; the run is scored automatically
python main.py run --config configs/api_t0.yaml --golden
python main.py run --config configs/local_t0.yaml --golden
python main.py run --config configs/api_t0.yaml          # all 30 documents

# 3. (optional) re-score a run, e.g. after changing the scoring rules
python main.py eval results/<run_id>

# 4. run the whole comparison: every config in configs/ x prompt versions, on the golden set
python main.py grid --prompts v1 v2

# 5. aggregate all scored runs into REPORT.md
python main.py report --all
```

Then fill in the error analysis and production choice in `REPORT.md`. `report --all` only rewrites the table between the `AUTO` markers.

Every run creates `results/<run_id>/` with:

| File | Content |
|---|---|
| `config.json` | Resolved config (model, prompt version, sampling, limits) |
| `<document>.json` | Output, status, repair flag, latency, tokens, cost |
| `run.jsonl` | One log line per document (model, prompt version, sampling, status) |
| `metrics.json`, `report.md` | Created by `eval`: accuracy, validity, latency, cost, top errors |

## Commands

| Command | Options | Description |
|---|---|---|
| `python main.py extract` | | Extract text from every PDF in `data/pdfs/` and cache it in `data/texts/` |
| `python main.py run` | `--config FILE` (required), `--golden`, `--limit N`, `--golden-version V` | Extract structured data for the documents, then score the run if it contains golden documents. `--golden` restricts to the golden-set documents, `--limit` to the first N |
| `python main.py eval RUN_DIR` | `--golden-version V` (`v1` = `golden.json`, otherwise `golden_V.json`) | Score a run against `data/golden.json` and write `metrics.json` and `report.md` into the run folder |
| `python main.py grid` | `--configs FILE...`, `--prompts V...`, `--all`, `--limit N`, `--golden-version V` | Run several configs on the golden set and score each. Default is every file in `configs/`. `--prompts v1 v2` repeats each config per prompt version. `--all` uses all documents |
| `python main.py report --all` | | Aggregate every scored run in `results/` into the table in `REPORT.md`; hand-written sections are kept |

## Configs (`configs/*.yaml`)

| Key | Meaning |
|---|---|
| `name` | Run label, used in the run folder name |
| `model_env` | Env var that holds the model string (`EXTRACT_MODEL` or `LOCAL_MODEL`) |
| `input_mode` | `text` (extract text from the PDF) or `pdf` (send the raw PDF; API models only) |
| `prompt_version` | File in `prompts/` without extension, e.g. `v1` |
| `sampling.temperature`, `sampling.top_p` | Sampling parameters |
| `max_pages`, `max_tokens` | Truncation. `text` mode applies both, `pdf` mode only `max_pages` |
| `timeout`, `max_retries` | Per-call timeout (seconds) and retry count |
| `extra_params` | Passed to the provider, e.g. `num_ctx: 8192` for Ollama |

To compare sampling settings, copy a config and change `name` and `sampling`. Included: `*_t0` (temperature 0, top_p 1.0) and `*_t07` (temperature 0.7, top_p 0.9) for the API and local model.

`input_mode: pdf` sends the raw PDF and works only with API models that accept PDFs (Gemini, OpenAI, Anthropic). It is not supported for Ollama.

## How processing works

1. The document is loaded in `text` or `pdf` mode and truncated per config.
2. The prompt from `prompts/<version>.md` is sent with structured output enforced by the schema.
3. The response is validated against the schema. If invalid, one repair attempt sends the invalid output and the validation error back to the model.
4. If it is still invalid, the record is marked `failed`.

## Metrics

- **Field accuracy:** per field and overall, against the golden set. Strings are compared case-insensitively, numbers within 1%, lists as sets. Failed records count as wrong.
- **Valid %:** responses valid against the schema, overall and on the first try.
- **Latency:** p50 and p95 in seconds, including the repair call.
- **Cost:** per 1000 documents, from LiteLLM pricing. Local models cost $0.

## Prompts

Prompts live in `prompts/<version>.md` with front-matter. `prompts/CHANGELOG.md` explains what changed in each version and why.

To add a version: create `prompts/v3.md` with `version` and `date` front-matter, add a changelog entry (what changed, why), and use it with `grid --prompts v3` or `prompt_version: v3` in a config.

## Submission notes

- Commit `.env.example`, never `.env`.
- Commit `data/`, `prompts/`, `results/` and `REPORT.md`.

## Layout

```
main.py            CLI
src/               schema, config, documents, llm, pipeline, evaluate
configs/           run configs
prompts/           prompt versions and changelog
data/pdfs/         source documents
data/texts/        cached extracted text
data/golden.json   golden set (gs* documents)
results/           run outputs and reports
```
