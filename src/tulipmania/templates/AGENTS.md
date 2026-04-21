# AGENTS.md

Operational how-to-run-this-project guide. Loaded into every Ralph iteration.
Keep under ~60 lines. Status, progress, and planning belong in
`IMPLEMENTATION_PLAN.md` — NOT here.

## Build & Run

- Install: `[install command]`
- Run locally: `[run command]`

## Validation (backpressure)

Run after implementing to get immediate feedback. These are the commands
"run the tests" in PROMPT_build.md resolves to:

- Tests: `[test command]`
- Typecheck: `[typecheck command]`
- Lint: `[lint command]`

## Operational Notes

Capture learnings about how to RUN the project here (not what was done).
Examples: "use `pnpm` not `npm` — package-lock is pnpm-lock",
"DB must be migrated before running tests: `pnpm db:migrate`".

## Codebase Patterns

Short, durable notes about where things live:
- Shared utilities: `src/lib/*`
- Specs: `specs/*.md` (one per JTBD topic)
