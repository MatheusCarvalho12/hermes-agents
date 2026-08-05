---
name: hermes-profile-fleets
description: "Set up Hermes multi-profile teams (skills, MCPs, kanban)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [hermes, profiles, mcp, skills, kanban, orchestration]
    related_skills: [hermes-administration, hermes-agent]
---

# Hermes Profile Fleets

Setting up and running a team of specialized Hermes profiles (frontend-developer, backend-developer, database-developer, designer) with the default profile as orchestrator. Covers profile creation, per-profile SOUL.md, per-profile skills/MCPs/plugins, system tools (RTK, gitleaks, react-doctor), and kanban delegation. The protected `hermes-administration` skill is the CLI/keys reference; this one carries the multi-profile workflow verified end-to-end.

## When to Use
- User wants specialized developer profiles + an orchestrator default
- Adding per-profile skills, MCP servers, or system tools
- Setting up kanban delegation so the default profile routes work to profiles
- Authoring per-profile SOUL.md files

## Hard Rules (user conventions — do not skip)
1. ALWAYS confirm with the user BEFORE creating profiles, writing SOUL.md, or installing skills — show the plan/proposal first. The user explicitly requires this ("confirma comigo primeiro").
2. Prefer existing hub skills over building new ones. Only build if truly necessary, and ASK FIRST.
3. NO skill duplication across profiles — each skill goes to the ONE profile where it makes sense. Built-ins (humanizer, simplify-code, test-driven-development) are already in every profile via `--clone`; fine-tune by disabling per profile.
4. Default profile = orchestrator: no code skills; keeps management/delegation. Question-asking skills (grilling, planning-and-task-breakdown) belong to the ORCHESTRATOR, not to executors — the user corrected this.
5. `--description` is not decoration: the kanban decomposer uses it to route tasks by role.
6. Tools/plugins/MCPs only load in a NEW session (prompt caching) — say so after every change.

## Workflow
### 1. Create profiles
```bash
hermes profile create frontend-developer --clone --description "Descreve o papel (kanban roteia por isso)."
```
- `--clone` copies config.yaml, .env, SOUL.md and skills from the active profile → new profiles inherit model, mem0 provider, disabled-skills list.
- Each profile becomes a command (`frontend-developer chat`) and can be targeted with `hermes -p <name> <cmd>`.
- Verify: `hermes profile list`.

### 2. Write per-profile SOUL.md (official structure)
File: `~/.hermes/profiles/<name>/SOUL.md` — replaces identity (system-prompt slot #1), effective in new sessions.
- Official skeleton: Identity / Style / Avoid / Defaults — use `templates/soul-template.md`.
- SOUL.md = tone/personality/communication ONLY. Project specifics (paths, commands, conventions) belong in AGENTS.md.
- Strong = specific voice, stable, broad. Weak = "be helpful" filler, contradictions, micro-management.
- Write in the user's language (pt-BR) and embed their code conventions (English code, pt-BR user-facing messages humanized, DRY/SOLID, no over-engineering, gitleaks before commit).

### 3. Install skills per profile
```bash
echo y | hermes -p <profile> skills install <identifier>
```
Identifier formats that work:
- `skills-sh/owner/repo/skill-name` (skills.sh indexed, e.g. skills-sh/getsentry/sentry-for-ai/sentry-python-sdk)
- plain clawhub names (e.g. `http-api`)
- GitHub path incl. subfolders (e.g. `millionco/react-doctor/.agents/skills/react-doctor`)
- Find: `hermes skills search <term>` · Preview: `hermes skills inspect <identifier>` (inspect may fail to resolve some clawhub names while install still works).

### 4. Add MCP servers per profile
```bash
echo y | hermes -p <profile> mcp add <name> --env KEY=value --command npx --args -y <pkg>
```
Pitfalls:
- The flow asks "Enable all N tools? [Y/n/select]" — pipe `echo y |` or it CANCELS without saving.
- "Server connected but reported no tools" = the server needs its API key in the process env. Pass `--env KEY=value` (stored in that profile's config.yaml mcp_servers.<name>.env — the ecosystem-standard place) AND mirror the key into the profile's `.env`.
- Verify: `hermes -p <profile> mcp list` / `mcp test <name>`.

### 5. System tools that span profiles
- RTK (Rust Token Killer, brew): `rtk init --agent hermes` installs the rtk-rewrite plugin into the CURRENT HERMES_HOME. For every profile: `HERMES_HOME=~/.hermes/profiles/<name> rtk init --agent hermes`. Needs ripgrep (Morph WarpGrep needs it too).
- Gitleaks (brew): plain CLI, no per-profile setup — add "run gitleaks detect before commit" to the relevant SOUL.mds.
- React Doctor: `npx react-doctor@latest` CLI + skill installed from the repo (step 3).

### 6. Kanban orchestration
- `hermes kanban init` + gateway running (`hermes gateway start`) — dispatcher lives in the gateway, tick ~60s.
- Orchestrator (default) uses the kanban toolset: `kanban_create --assignee <profile>`. Workers read via kanban_show, comment progress, complete with evidence. States: triage → todo → ready → running → blocked → done. Idempotency keys exist for dedup.

## User's Testing Philosophy (embed in dev SOUL.mds)
Few tests, the RIGHT ones: think of real usage SCENARIOS (acceptance criteria — functional and non-functional) and code only those tests. The user hates TDD that produces useless tests. Canonical examples: a like button must be idempotent (clicking 100x = 1 like, not 1M); a "New chat" button must not create 30 empty DB rows — a chat only becomes real after a message is sent. Idempotency and state transitions are the scenarios that matter.

## Pitfalls
- `hermes config set skills.disabled '["a"]'` SILENTLY FAILS (stored as a quoted string; loader treats it as ONE name). Use `save_disabled_skills` from `hermes_cli.skills_config` with the app venv python (see hermes-administration).
- Morph MCP exposes WarpGrep as `codebase_search` (+ `github_codebase_search`); extra tools (reflex_*) can be toggled with `hermes -p <profile> mcp configure`.
- react-doctor covers lint/a11y/architecture/bundle — NOT runtime performance (that's Lighthouse).
- Context7 and Morph are MCPs, NOT skills — user corrected this conflation.
- RTK = Rust Token Killer (rtk-ai/rtk), NOT Redux Toolkit — user corrected this conflation.
- anthropics/skills repo has no `code-review`/`frontend-ui`/`http-api` under those names: frontend-ui → `frontend-design`; code-review lives in `anthropics/knowledge-work-plugins`.

## References
- `references/profile-stack-inventory.md` — per-profile stack (skills/MCPs/tools, identifiers, status) + hub audit notes
- `templates/soul-template.md` — official-structure SOUL.md starter with the user's conventions
