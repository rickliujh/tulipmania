# tulipmania

Autonomous coding orchestration layer implementing the
[Ralph method](https://ghuntley.com/ralph/) on top of any coding-agent CLI.

> *"A dumb bash loop that keeps restarting the agent, and the agent figures out
> what to do next by reading the plan file each time."*

tulipmania is that loop, plus:
- a thin adapter layer so the same workflow drives `claude`, `codex`, `amp`,
  `opencode`, `gemini`, `aider`, or any CLI you configure
- `plan` / `build` / `plan-work` modes with the Ralph playbook prompts
- project scaffolding (`specs/`, `PROMPT_*.md`, `AGENTS.md`,
  `IMPLEMENTATION_PLAN.md`, `tulipmania.toml`)
- graceful SIGINT handling, iteration caps, optional per-iteration git push
- dry-run mode for testing your configuration without burning tokens

Runtime: Python 3.11+, stdlib only. Managed with [uv](https://docs.astral.sh/uv/).

---

## Install

Install as a CLI tool (recommended for end users):

```bash
uv tool install .          # from a clone
# or: uv tool install git+https://github.com/<you>/tulipmania
tulipmania --help
```

Develop on the source (editable):

```bash
uv sync                    # creates .venv, installs tulipmania
uv run tulipmania --help   # run via the project env
```

One-off without installing:

```bash
uv run --with . tulipmania --help
```

## Quickstart

```bash
cd your-project
tulipmania init --agent claude          # scaffold files
$EDITOR specs/your-first-spec.md        # write one topic-of-concern spec
tulipmania plan --max 2                 # generate IMPLEMENTATION_PLAN.md
tulipmania build --max 20               # loop until done or cap hit
```

Substitute `uv run tulipmania ...` for every command if you installed via
`uv sync` instead of `uv tool install`.

## Commands

| Command                           | Purpose                                            |
| --------------------------------- | -------------------------------------------------- |
| `tulipmania init [--agent NAME]`  | Scaffold prompts, `AGENTS.md`, config, `specs/`    |
| `tulipmania plan [--max N]`       | Planning mode — gap analysis, writes plan         |
| `tulipmania build [--max N]`      | Building mode — one task per iteration            |
| `tulipmania plan-work "<scope>"`  | Scoped planning on a work branch                   |
| `tulipmania run <prompt-file>`    | Run arbitrary prompt file in the loop              |
| `tulipmania adapters`             | List built-in CLI adapters                         |

Shared flags: `--max N`, `--agent NAME`, `--model NAME`, `--no-push`,
`--config PATH`, `--dry-run`.

## Adapters

Built-in entries ship in `src/tulipmania/adapters.py`. Only the `claude`
adapter has flags verified against Ralph's published workflow; the rest are
scaffolds — **check `<cli> --help` for your installed version and override
via `tulipmania.toml`** before relying on them.

```toml
# tulipmania.toml
[agent]
name = "codex"

[agents.codex]
command = ["codex", "exec", "--model", "{model}"]
default_model = "gpt-5"
stdin_prompt = true
```

`{model}` is substituted at runtime. For CLIs that don't accept prompts via
stdin, set `stdin_prompt = false` and use `{prompt_file}` in `command`.

## Ralph method: the five-minute version

Three phases, two prompts, one loop:

1. **Define requirements** — human + LLM convert JTBDs into one spec per
   topic-of-concern under `specs/`.
2. **Plan** (`tulipmania plan`) — subagents gap-analyze specs vs. `src/`,
   producing a prioritized `IMPLEMENTATION_PLAN.md`.
3. **Build** (`tulipmania build`) — each iteration: fresh context, read
   plan, pick highest-priority task, implement, validate via backpressure
   (tests/typecheck/lint commands listed in `AGENTS.md`), commit, push.

Each iteration starts from a clean context. State lives on disk:
`IMPLEMENTATION_PLAN.md` between runs, `AGENTS.md` for operational
learnings, `specs/` as the requirements source of truth.

See the playbook you were sent for the full rationale.

## Sandboxing — read this before running unattended

Ralph works by bypassing the agent's permission prompts
(`--dangerously-skip-permissions` for Claude, analogous flags elsewhere).
Your isolation layer is whatever you run it inside of:

- **Local**: Docker container with a fresh workspace and only the API keys
  needed for the task. No access to your home directory, SSH keys, browser
  cookies, or unrelated projects.
- **Remote**: E2B / Fly / GitHub Codespaces with scoped credentials.

> *"It's not if it gets popped, it's when. And what is the blast radius?"*
> — Geoffrey Huntley

tulipmania does **not** start a sandbox for you. Compose it with one.

## Escape hatches

- `Ctrl+C` → current iteration finishes, loop exits.
- `git reset --hard` → revert uncommitted changes from a bad iteration.
- `rm IMPLEMENTATION_PLAN.md && tulipmania plan` → regenerate from scratch.

## Status

v0.1 — works for the happy path with Claude. Other adapters need user
verification. File bugs as you find them.
