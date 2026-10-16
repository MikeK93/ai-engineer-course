import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PDFS = DATA / "pdfs"
TEXTS = DATA / "texts"
GOLDEN = DATA / "golden.json"
PROMPTS = ROOT / "prompts"
RESULTS = ROOT / "results"


@dataclass
class RunConfig:
    name: str
    model: str
    input_mode: str = "text"
    prompt_version: str = "v1"
    temperature: float = 0.0
    top_p: float = 1.0
    max_pages: int = 20
    max_tokens: int = 12000
    timeout: int = 120
    max_retries: int = 3
    extra_params: dict = field(default_factory=dict)


def load_config(path: str | Path) -> RunConfig:
    load_dotenv(ROOT / ".env")
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    model = os.environ.get(raw["model_env"])
    if not model:
        raise SystemExit(f"Env var {raw['model_env']} is not set (see .env.example)")
    if raw.get("input_mode", "text") not in ("text", "pdf"):
        raise SystemExit("input_mode must be 'text' or 'pdf'")
    sampling = raw.get("sampling", {})
    return RunConfig(
        name=raw["name"],
        model=model,
        input_mode=raw.get("input_mode", "text"),
        prompt_version=raw.get("prompt_version", "v1"),
        temperature=sampling.get("temperature", 0.0),
        top_p=sampling.get("top_p", 1.0),
        max_pages=raw.get("max_pages", 20),
        max_tokens=raw.get("max_tokens", 12000),
        timeout=raw.get("timeout", 120),
        max_retries=raw.get("max_retries", 3),
        extra_params=raw.get("extra_params") or {},
    )
