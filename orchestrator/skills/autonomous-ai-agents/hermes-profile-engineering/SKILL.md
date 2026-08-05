---
name: hermes-profile-engineering
description: "Set up Hermes profiles: MCPs, skills, SOUL.md, kanban."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [hermes, profiles, mcp, skills, soul, kanban, orchestration]
    related_skills: [hermes-administration, hermes-agent, i-have-adhd]
---

# Hermes Profile Engineering

Field-tested playbook for standing up and iterating a team of specialized Hermes profiles (e.g. frontend-developer, backend-developer, database-developer, designer) that a "default" orchestrator profile delegates to via Kanban. Complements the bundled `hermes-administration` skill (which covers profile basics, skills disable, memory providers) with the deeper per-profile tooling workflow. Official docs win: https://hermes-agent.nousresearch.com/docs/user-guide/profiles

## When to Use
- User wants specialized profiles with per-role skills, MCPs, and identity files
- Adding a tool/MCP/skill to an existing profile
- Writing or updating a profile's SOUL.md
- Setting up Kanban delegation from the default orchestrator

## Hard Invariants (user preferences — do not skip)
- **Confirm before writing any SOUL.md/SKILL.md**: consult official docs + `hermes-agent` skill first, show the user the draft (structure Identity/Style/Avoid/Defaults), and only write after OK. Exception: the user may pre-authorize a "base" and then edit it themselves.
- **Prefer market hub skills over creating new ones.** Only propose building a skill when nothing exists; the user hates duplicating a well-known skill (e.g. Anthropic's code-review).
- **Prefer official skills** (fastapi/fastapi, google/skills, getsentry/sentry-for-ai, shadcn/ui, antfu/skills) and check `Trust` in search results (trusted > community).
- Everything user-facing: **pt-BR, humanized** (skill humanizer). Code stays in English.
- Respond in the `i-have-adhd` style (action first, numbered steps, short lists).

## Workflow

### 1. Create a profile (clone-based)
```bash
hermes profile create <name> --clone --description "<one-line role used by kanban routing>"
```
`--clone` copies config.yaml, .env, SOUL.md, skills from default → new profile inherits model, provider keys, memory provider, and installed skills. Per-profile data lives in `~/.hermes/profiles/<name>/`. Verify with `hermes profile list` (shows model/gateway/alias).

### 2. Per-profile MCP servers
```bash
hermes mcp add --help   # --env KEY=VALUE | --command npx | --args (must be last)
hermes -p <profile> mcp add context7 --env CONTEXT7_API_KEY=... --command npx --args -y @upstash/context7-mcp
hermes -p <profile> mcp add morph --env MORPH_API_KEY=... --command npx --args --prefer-offline -y @morphllm/morphmcp
hermes -p <profile> mcp list && hermes -p <profile> mcp test <name>
```
Pitfalls: (a) **`--env` is REQUIRED for keyed MCPs** — without it the server connects but reports 0 tools (morph without MORPH_API_KEY); (b) the interactive "Enable all N tools? [Y/n]" prompt needs `echo y |` piped in or the add is cancelled; (c) keys also go in the profile's `.env` (`~/.hermes/profiles/<name>/.env`) — the MCP `--env` lands in config.yaml by design; (d) tools only load in a NEW session of that profile.

### 3. Per-profile skill installs
```bash
hermes skills search <term> | grep -E "^│"     # Name/Description/Source/Trust/Identifier table
hermes skills inspect <identifier>             # preview before install
hermes -p <profile> skills install <identifier> -y
```
Identifier formats that work: `skills-sh/<owner>/<repo>/<path>` (skills.sh), `clawhub/<name>` (clawhub — the bare name fails with "No exact match"), `<owner>/<repo>/<path>` (GitHub, e.g. `millionco/react-doctor/.agents/skills/react-doctor`), or a direct `https://.../SKILL.md` URL with `--name <x>`.

Pitfalls:
- **Scanner blocks community skills**: "Blocked (community source + caution verdict, 2 findings)" — common findings html_comment_injection / unpinned_npm_install appear even in legit skills (Addy Osmani, Sentry). Override with `--force -y` after confirming the source is reputable.
- **`-y` is more reliable than `echo y |`** (echo failed once against a URL install's confirm prompt).
- **Always pass `-p <profile>`** — forgetting it installs into the DEFAULT profile (easy silent mistake; verify with `hermes -p <profile> skills list`).
- React-doctor-style repo skills: the skill lives under `.agents/skills/<name>` in the tool's GitHub repo — install via `<owner>/<repo>/.agents/skills/<name>`.

### 4. RTK (Rust Token Killer) per profile
```bash
brew install rtk
HERMES_HOME=~/.hermes/profiles/<name> rtk init --agent hermes   # per profile!
rtk init --agent hermes                                          # default (~/.hermes)
```
Installs plugin `rtk-rewrite` (hook `pre_tool_call`) that rewrites `git status` → `rtk git status` etc. The init targets the CURRENT `HERMES_HOME`, so it must be run once per profile with the env var set. Requires ripgrep for local codebase search. Plugin only activates in a new session.

### 5. SOUL.md authoring pattern (per profile)
Structure: `# Identity` → `# Style` → `# <domain section>` → `# Skills — SEMPRE use a skill certa na hora certa` → `# Verificação` → `# Context7 — LEI` → `# Morph/warpgrep — uso seletivo` → `# Avoid` → `# Defaults`.
- The **trigger section** is the key piece: one line per installed skill mapping task → skill ("shadcn → sempre que criar componente de UI; fastapi → sempre que criar endpoint; gitleaks → antes de commit"). The user has been burned by agents that have skills installed but never call them — explicit triggers in SOUL.md fix that.
- Encode role rules: DRY/SOLID + componentização total (frontend), Black/Ruff format immediately after writing code (backend — kills lint rework loops), performant+clear SQL (DBA), design-system ownership (designer: tokens/typography/padding/components; frontend executes).
- **Context7 is law**: always consult it before using any API/lib — latest version, current docs win over stale skill knowledge.
- **Morph/warpgrep is selective**: only for big searches (schema overview, refactors, large features); point lookups use plain grep.
- **Verification once before PR**: lint/tests/react-doctor/security/code-review run as a single pre-PR pass, not during development.
- Test philosophy: few, scenario-based tests (acceptance criteria; idempotency matters — e.g. like button clicks, "new section" button must not create 30 empty rows). Never test for testing's sake.

### 6. Kanban activation (orchestrator delegates)
```bash
hermes kanban init          # creates default board
hermes gateway start        # dispatcher ticks every 60s — WITHOUT gateway, tasks stay 'ready' forever
hermes kanban create "<task>" --assignee <profile> [--idempotency-key ...]
```
Agents drive the board via `kanban_*` tools (kanban_create/list/show/comment); the profile `--description` set at creation is what routes tasks to the right role. Orchestrator profile (default) should get a SOUL.md defining the delegate-via-kanban flow + grilling (requirements) + planning-and-task-breakdown skills.

## Pitfalls
- `hermes config set skills.disabled '["a"]'` silently stores a STRING — use the app API `save_disabled_skills` (see hermes-administration) or `hermes skills config`.
- Plugin/MCP/tool changes only take effect in a NEW session of the target profile — always tell the user to open a fresh session to test.
- Same API keys (MORPH_API_KEY, CONTEXT7_API_KEY) can be reused across profiles — add to each profile's `.env` + MCP `--env`.
- `hermes profile list` after creating profiles: only `default` exists until you create the others; cloned profiles keep the starter SOUL.md until you rewrite it.

## Verification
- `hermes -p <profile> skills list` shows installed hub skills (builtin filtered with `grep -v builtin`)
- `hermes -p <profile> mcp test <name>` confirms tools discovered
- `hermes profile list` shows all profiles + gateway status
- Open a new session in the profile and run `git status` to confirm RTK rewrite is active

See `references/mcp-and-tool-recipes.md` for the concrete context7/morph configs and the per-role skill assignment table from the first full setup.
