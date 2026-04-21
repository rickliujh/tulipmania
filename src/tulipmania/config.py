from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


CONFIG_FILENAME = "tulipmania.toml"


@dataclass
class Config:
    agent: str = "claude"
    model: str | None = None
    push: bool = True
    agents: dict[str, dict] = field(default_factory=dict)
    prompts: dict[str, str] = field(default_factory=dict)
    root: Path = field(default_factory=Path.cwd)

    def prompt_path(self, mode: str) -> Path:
        default = {
            "plan": "PROMPT_plan.md",
            "build": "PROMPT_build.md",
            "plan-work": "PROMPT_plan_work.md",
        }
        relative = self.prompts.get(mode, default.get(mode, f"PROMPT_{mode}.md"))
        return self.root / relative


def load(path: Path | None = None) -> Config:
    root = Path.cwd()
    cfg_path = path or (root / CONFIG_FILENAME)
    if not cfg_path.exists():
        return Config(root=root)

    data = tomllib.loads(cfg_path.read_text())
    agent_cfg = data.get("agent", {})
    loop_cfg = data.get("loop", {})
    return Config(
        agent=agent_cfg.get("name", "claude"),
        model=agent_cfg.get("model"),
        push=loop_cfg.get("push", True),
        agents=data.get("agents", {}),
        prompts=data.get("prompts", {}),
        root=cfg_path.parent.resolve(),
    )
