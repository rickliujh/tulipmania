from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tulipmania import __version__
from tulipmania.adapters import BUILTIN, resolve
from tulipmania.config import load as load_config
from tulipmania.init_cmd import run as run_init
from tulipmania.loop import LoopOptions, run as run_loop


def _add_loop_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--max", dest="max_iterations", type=int, default=0, help="cap outer iterations (0=unlimited)")
    p.add_argument("--agent", help="override adapter name (claude, codex, amp, opencode, gemini, aider, or custom)")
    p.add_argument("--model", help="override model passed to the adapter")
    p.add_argument("--no-push", action="store_true", help="disable git push after each iteration")
    p.add_argument("--config", type=Path, help="path to tulipmania.toml")
    p.add_argument("--dry-run", action="store_true", help="print resolved command and exit")


def _build_loop_opts(args, mode: str, work_scope: str | None = None) -> LoopOptions:
    cfg = load_config(args.config)
    agent_name = args.agent or cfg.agent
    adapter = resolve(agent_name, cfg.agents)
    return LoopOptions(
        adapter=adapter,
        prompt_path=cfg.prompt_path(mode),
        max_iterations=args.max_iterations,
        push=(not args.no_push) and cfg.push,
        model=args.model or cfg.model,
        work_scope=work_scope,
        dry_run=args.dry_run,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tulipmania",
        description="Autonomous coding orchestration layer implementing the Ralph method.",
    )
    parser.add_argument("--version", action="version", version=f"tulipmania {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="scaffold PROMPT/AGENTS/specs and tulipmania.toml")
    p_init.add_argument("--agent", default="claude", choices=sorted(BUILTIN.keys()))
    p_init.add_argument("--force", action="store_true", help="overwrite existing files")
    p_init.add_argument("--path", type=Path, default=Path.cwd())

    p_plan = sub.add_parser("plan", help="planning mode: generate/refresh IMPLEMENTATION_PLAN.md")
    _add_loop_flags(p_plan)

    p_build = sub.add_parser("build", help="building mode: execute tasks from IMPLEMENTATION_PLAN.md")
    _add_loop_flags(p_build)

    p_work = sub.add_parser("plan-work", help="scoped planning on a work branch")
    p_work.add_argument("work_scope", help="natural-language description of the work scope")
    _add_loop_flags(p_work)

    p_run = sub.add_parser("run", help="run a custom prompt file in the Ralph loop")
    p_run.add_argument("prompt_file", type=Path)
    _add_loop_flags(p_run)

    p_adapters = sub.add_parser("adapters", help="list known adapters")

    args = parser.parse_args(argv)

    if args.command == "init":
        return run_init(args.path, args.agent, args.force)

    if args.command == "adapters":
        for name, ad in sorted(BUILTIN.items()):
            print(f"{name:10} default_model={ad.default_model or '-':<18} stdin={ad.stdin_prompt}")
            print(f"           command={' '.join(ad.command)}")
        return 0

    if args.command == "plan-work":
        branch = _current_branch()
        if branch in ("main", "master"):
            print(
                f"[tulipmania] refusing to run plan-work on {branch}. "
                "Create a work branch first: git checkout -b ralph/your-work",
                file=sys.stderr,
            )
            return 2
        opts = _build_loop_opts(args, "plan-work", args.work_scope)
        if opts.max_iterations == 0:
            opts.max_iterations = 5  # sane default for scoped planning
        return run_loop(opts)

    if args.command == "run":
        cfg = load_config(args.config)
        agent_name = args.agent or cfg.agent
        adapter = resolve(agent_name, cfg.agents)
        opts = LoopOptions(
            adapter=adapter,
            prompt_path=args.prompt_file,
            max_iterations=args.max_iterations,
            push=(not args.no_push) and cfg.push,
            model=args.model or cfg.model,
            dry_run=args.dry_run,
        )
        return run_loop(opts)

    if args.command in ("plan", "build"):
        return run_loop(_build_loop_opts(args, args.command))

    parser.error(f"unknown command: {args.command}")
    return 2


def _current_branch() -> str:
    import subprocess

    try:
        r = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, text=True, check=True
        )
        return r.stdout.strip()
    except Exception:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
