from __future__ import annotations

import shutil
import sys
from importlib.resources import files
from pathlib import Path


TEMPLATE_FILES = [
    ("PROMPT_plan.md", "PROMPT_plan.md"),
    ("PROMPT_build.md", "PROMPT_build.md"),
    ("PROMPT_plan_work.md", "PROMPT_plan_work.md"),
    ("AGENTS.md", "AGENTS.md"),
    ("IMPLEMENTATION_PLAN.md", "IMPLEMENTATION_PLAN.md"),
    ("tulipmania.toml", "tulipmania.toml"),
]

EXTRA_DIRS = ["specs", "src", "src/lib"]


def run(root: Path, agent: str = "claude", force: bool = False) -> int:
    root.mkdir(parents=True, exist_ok=True)
    pkg = files("tulipmania.templates")

    for src_name, dest_name in TEMPLATE_FILES:
        dest = root / dest_name
        if dest.exists() and not force:
            print(f"[tulipmania] skip existing: {dest_name}")
            continue
        content = pkg.joinpath(src_name).read_text()
        if dest_name == "tulipmania.toml":
            content = content.replace('name = "claude"', f'name = "{agent}"')
        dest.write_text(content)
        print(f"[tulipmania] wrote {dest_name}")

    for d in EXTRA_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)

    gitkeep = root / "specs" / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()

    print("[tulipmania] init complete. Next: edit specs/*.md, then `tulipmania plan`.")
    return 0
