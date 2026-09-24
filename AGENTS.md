# PUBLIC REPOSITORY RULE

When in doubt whether a file may contain user-specific data, keep it out of Git.

## Project rules

- Write all project-authored files in English.
- Store real user state and every output derived from it under the ignored `private/` directory.
- Use only fully synthetic data in tracked examples, fixtures, tests, documentation, and reports.
- Never place credentials, account identifiers, portfolio holdings, personal goals, private prompts, or provider responses in tracked files.
- Treat cloned repositories under `blueprint/` as read-only reference material and never package or commit them; `blueprint/BLUEPRINT_SOURCES.md` is the public metadata index.
- Keep public skill definitions trackable; do not blanket-ignore `.agents/`, `.codex/`, `agents/`, `skills/`, `AGENTS.md`, or `SKILL.md`.
- Do not stage, commit, push, publish, or upload artifacts without explicit user authorization for that action.
- Work on one approved project phase at a time and stop at its approval checkpoint.
