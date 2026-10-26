import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PDFS = DATA / "pdfs"
TEXTS = DATA / "texts"
GOLDEN = DATA / "golden.json"


def _vnum(path: Path) -> int:
    m = re.search(r"v(\d+)$", path.stem)
    return int(m.group(1)) if m else 1


def latest_golden_version() -> str:
    files = [GOLDEN, *DATA.glob("golden_v*.json")]
    return f"v{max(_vnum(f) for f in files)}"


def latest_prompt_version() -> str:
    return f"v{max(_vnum(f) for f in PROMPTS.glob('v*.md'))}"


def golden_path(version: str | None = None) -> Path:
    """v1 (or None) is golden.json; any other version is golden_<version>.json; 'latest' is the highest."""
    if version == "latest":
        version = latest_golden_version()
    if not version or version == "v1":
        return GOLDEN
    return DATA / f"golden_{version}.json"

PROMPTS = ROOT / "prompts"
RESULTS = ROOT / "results"


def model_variants(model_env: str) -> list[str]:
    """Default model, then any comma-separated extras in EXTRA_<MODEL_ENV>S.

    EXTRACT_MODEL reads EXTRA_EXTRACT_MODELS. LOCAL_MODEL reads EXTRA_LOCAL_MODELS.
    Blank entries and duplicates of an earlier model are skipped.
    """
    load_dotenv(ROOT / ".env")
    primary = os.environ.get(model_env)
    if not primary:
        raise SystemExit(f"Env var {model_env} is not set (see .env.example)")
    seen = {primary}
    models = [primary]
    for part in os.environ.get(f"EXTRA_{model_env}S", "").split(","):
        model = part.strip()
        if model and model not in seen:
            seen.add(model)
            models.append(model)
    return models


def model_tag(model: str) -> str:
    """Short run-name suffix: the provider and model, without the LiteLLM route prefix."""
    parts = [p for p in model.split("/") if p]
    tail = parts[-2:] if len(parts) >= 2 else parts
    return re.sub(r"[^A-Za-z0-9._+-]+", "-", "_".join(tail))


@dataclass
class RunConfig:
    name: str
    model: str
    model_env: str
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
    model_env = raw["model_env"]
    model = model_variants(model_env)[0]
    if raw.get("input_mode", "text") not in ("text", "pdf"):
        raise SystemExit("input_mode must be 'text' or 'pdf'")
    sampling = raw.get("sampling", {})
    return RunConfig(
        name=raw["name"],
        model=model,
        model_env=model_env,
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
