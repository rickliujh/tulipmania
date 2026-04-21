"""CLI adapter registry.

Each adapter describes how to invoke a coding-agent CLI non-interactively so
Ralph's outer loop can feed it a prompt and let it run to completion.

The `claude` adapter uses the flags documented in the Ralph playbook and is
verified against Anthropic's Claude Code CLI. Other adapters are provided as
starting points — confirm flags against the CLI's current `--help` before
enabling them. Users override or add adapters via `tulipmania.toml`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Adapter:
    name: str
    command: tuple[str, ...]
    default_model: str | None = None
    # If stdin_prompt=True, prompt text is piped via stdin. Otherwise the token
    # "{prompt_file}" in `command` is substituted with the prompt file path.
    stdin_prompt: bool = True
    env: dict[str, str] = field(default_factory=dict)

    def render(self, model: str | None) -> list[str]:
        resolved_model = model or self.default_model or ""
        return [part.replace("{model}", resolved_model) for part in self.command]


BUILTIN: dict[str, Adapter] = {
    # Verified per Ralph playbook.
    "claude": Adapter(
        name="claude",
        command=(
            "claude",
            "-p",
            "--dangerously-skip-permissions",
            "--output-format=stream-json",
            "--model",
            "{model}",
            "--verbose",
        ),
        default_model="opus",
        stdin_prompt=True,
    ),
    # The adapters below are scaffolds. Flags differ across CLI versions — run
    # `<cli> --help` and adjust in tulipmania.toml before relying on them.
    "codex": Adapter(
        name="codex",
        command=("codex", "exec", "--model", "{model}"),
        default_model="gpt-5",
        stdin_prompt=True,
    ),
    "amp": Adapter(
        name="amp",
        command=("amp",),
        stdin_prompt=True,
    ),
    "opencode": Adapter(
        name="opencode",
        command=("opencode", "run", "--model", "{model}"),
        stdin_prompt=True,
    ),
    "gemini": Adapter(
        name="gemini",
        command=("gemini", "-y", "-m", "{model}"),
        default_model="gemini-2.5-pro",
        stdin_prompt=True,
    ),
    "aider": Adapter(
        name="aider",
        command=("aider", "--yes-always", "--model", "{model}", "--message-file", "{prompt_file}"),
        stdin_prompt=False,
    ),
}


def resolve(name: str, overrides: dict[str, dict] | None = None) -> Adapter:
    overrides = overrides or {}
    if name in overrides:
        cfg = overrides[name]
        base = BUILTIN.get(name)
        command = cfg.get("command")
        if command is None and base is None:
            raise ValueError(f"adapter '{name}' has no command and no builtin base")
        return Adapter(
            name=name,
            command=tuple(command) if command else base.command,
            default_model=cfg.get("default_model", base.default_model if base else None),
            stdin_prompt=cfg.get("stdin_prompt", base.stdin_prompt if base else True),
            env=cfg.get("env", {}),
        )
    if name not in BUILTIN:
        raise KeyError(
            f"unknown adapter '{name}'. built-in: {sorted(BUILTIN)}; "
            "define [agents.<name>] in tulipmania.toml to add your own."
        )
    return BUILTIN[name]
