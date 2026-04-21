from __future__ import annotations

import os
import signal
import string
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from tulipmania.adapters import Adapter


@dataclass
class LoopOptions:
    adapter: Adapter
    prompt_path: Path
    max_iterations: int = 0  # 0 = unlimited
    push: bool = True
    model: str | None = None
    work_scope: str | None = None
    dry_run: bool = False


_interrupted = False


def _install_sigint():
    def handler(signum, frame):
        global _interrupted
        _interrupted = True
        print("\n[tulipmania] interrupt received — finishing current iteration then stopping.", file=sys.stderr)

    signal.signal(signal.SIGINT, handler)


def _render_prompt(text: str, work_scope: str | None) -> str:
    if work_scope is None:
        return text
    template = string.Template(text)
    return template.safe_substitute(WORK_SCOPE=work_scope)


def _current_branch() -> str:
    out = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _push(branch: str) -> None:
    r = subprocess.run(["git", "push", "origin", branch])
    if r.returncode != 0:
        subprocess.run(["git", "push", "-u", "origin", branch], check=False)


def run(opts: LoopOptions) -> int:
    if not opts.prompt_path.exists():
        print(f"[tulipmania] prompt file not found: {opts.prompt_path}", file=sys.stderr)
        return 2

    _install_sigint()

    cmd = opts.adapter.render(opts.model)
    prompt_text = opts.prompt_path.read_text()
    prompt_text = _render_prompt(prompt_text, opts.work_scope)

    branch = ""
    try:
        branch = _current_branch()
    except subprocess.CalledProcessError:
        pass

    _banner(opts, branch)

    if opts.dry_run:
        print("[tulipmania] dry-run: would execute:", " ".join(cmd))
        print("[tulipmania] prompt bytes:", len(prompt_text))
        return 0

    env = {**os.environ, **opts.adapter.env}
    if opts.work_scope:
        env["WORK_SCOPE"] = opts.work_scope

    iteration = 0
    while not _interrupted:
        if opts.max_iterations and iteration >= opts.max_iterations:
            print(f"[tulipmania] reached max iterations: {opts.max_iterations}")
            break

        rc = _run_once(opts.adapter, cmd, prompt_text, opts.prompt_path, env)
        if rc != 0:
            print(f"[tulipmania] agent exited non-zero (rc={rc}); continuing loop.", file=sys.stderr)

        if opts.push and branch:
            _push(branch)

        iteration += 1
        print(f"\n======================== LOOP {iteration} ========================\n")

    return 0


def _run_once(adapter: Adapter, cmd: list[str], prompt_text: str, prompt_path: Path, env: dict) -> int:
    if adapter.stdin_prompt:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, env=env, text=True)
        try:
            proc.communicate(prompt_text)
        except KeyboardInterrupt:
            proc.terminate()
            proc.wait()
            raise
        return proc.returncode

    expanded = [part.replace("{prompt_file}", str(prompt_path)) for part in cmd]
    proc = subprocess.Popen(expanded, env=env)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
        raise
    return proc.returncode


def _banner(opts: LoopOptions, branch: str) -> None:
    bar = "━" * 40
    print(bar)
    print(f"Agent:  {opts.adapter.name}")
    print(f"Model:  {opts.model or opts.adapter.default_model or '(adapter default)'}")
    print(f"Prompt: {opts.prompt_path}")
    print(f"Branch: {branch or '(not a git repo)'}")
    if opts.work_scope:
        print(f"Work:   {opts.work_scope}")
    if opts.max_iterations:
        print(f"Max:    {opts.max_iterations} iterations")
    print(f"Push:   {'on' if opts.push else 'off'}")
    print(bar)
