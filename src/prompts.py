from .config import PROMPTS


def load_prompt(version: str) -> str:
    raw = (PROMPTS / f"{version}.md").read_text(encoding="utf-8")
    if raw.startswith("---"):
        raw = raw.split("---", 2)[2]
    return raw.strip()
