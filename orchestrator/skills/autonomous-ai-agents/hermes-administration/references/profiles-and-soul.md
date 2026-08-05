# Profiles, SOUL.md & Native Skill Creation (distilled 2026-08)

Sources: official Hermes docs (`/docs/user-guide/profiles`, `/docs/guides/use-soul-with-hermes`, `/docs/user-guide/features/personality`) + source reading of the hermes-agent repo (`agent/turn_finalizer.py`, `agent/agent_init.py`) + Anthropic `skill-creator` SKILL.md (read-only reference).

## Profiles (official doc)
- A profile = a separate `HERMES_HOME` (`~/.hermes/profiles/<name>`) with its own config.yaml, `.env`, SOUL.md, memories, sessions, skills, cron jobs, state db.
- `hermes profile create <name>` also creates a CLI alias → `<name> chat` works. Target any profile with `hermes -p <name>`; sticky default via `hermes profile use <name>`.
- Flags: `--clone` (config+.env+SOUL.md+skills from active profile), `--clone-all` (everything incl. memories/cron/plugins, excluding per-profile session history), `--clone-from <src>`, `--no-skills` (blank profile, opts out of `hermes update` skill sync), `--description "<role>"` — **used by the kanban orchestrator to route tasks by role**, always set it.
- Per-profile working dir: set `terminal.cwd` in that profile's config.yaml. Profiles do NOT sandbox the filesystem.
- Manage: `hermes profile list/show/rename/describe/delete`; delete asks for typed confirmation; the `default` profile cannot be deleted.
- Visual builder: `hermes dashboard` → http://127.0.0.1:9119 (Profile Builder: identity, model, skills, MCP in one flow).
- `hermes update` syncs new bundled skills to ALL profiles; user-modified skills are never overwritten.

## SOUL.md (official doc)
- Slot #1 of the system prompt = the agent identity; replaces the default identity text; injection-scanned; truncated if huge; loaded only from `HERMES_HOME`.
- For: tone, personality, communication style, directness, what to avoid, stance on uncertainty/disagreement.
- NOT for: paths, commands, ports, repo conventions, project workflows → those go in `AGENTS.md`.
- Suggested structure: `# Identity` / `# Style` / `# Avoid` / `# Defaults`.
- Strong = stable, broadly applicable, specific voice. Weak = generic filler ("be helpful"), contradictions, micro-managing every response shape, project details.
- Doc ships 4 example personas: pragmatic engineer, research partner, teacher, tough reviewer.
- `/personality` presets overlay SOUL.md per session (custom ones under `agent.personalities`); edits take effect on a NEW session only.

## Native skill creation (how Hermes learns skills — read-only, never modify)
- Config key `skills.creation_nudge_interval` (default 10; this user: 15). After each turn, when `_iters_since_skill >= interval` AND `skill_manage` is in valid tools, `turn_finalizer` spawns `_spawn_background_review(review_skills=True)` AFTER the user's response is delivered — it never competes with the task.
- The background review agent decides to create/patch skills via `skill_manage`, writing SKILL.md under the profile's skills dir.
- Code refs: `agent/turn_finalizer.py` (~line 698), `agent/agent_init.py` (~line 1766). READ ONLY: the user explicitly does not want the core touched (`hermes update` would overwrite).
- User prefers studying/using this native loop over installing third-party skill tools.

## Anthropic skill-creator (method reference only — NOT installed, user's request)
- Hub id: `skills-sh/anthropics/skills/skill-creator` (trusted). Raw file: `https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md` — note the NESTED path `skills/skill-creator/` (the flat `skill-creator/SKILL.md` 404s).
- Method: capture intent → interview/research (edge cases, MCPs, subagents for parallel research) → draft SKILL.md → 2-3 realistic test prompts → run with-skill AND baseline subagents in the same turn → grade + benchmark → eval viewer for the user → iterate → package.
- Description must be "pushy" (explicit when-to-use triggers — skills undertrigger otherwise). SKILL.md <500 lines; progressive disclosure (metadata → body → references/); imperative form; Input/Output examples; explain *why* instead of MUSTs.
- User's stance: don't install it (conflict risk with Hermes' native creation); use its methodology as a quality bar for hand-authored MDs.

## Hub skill audit results (2026-08-04, user's 24-name list)
Found (19/24) — verified official sources first:
- accessibility → addyosmani/web-quality-skills (Google Chrome team)
- bigquery-basics → **google/skills** (official Google)
- design-tokens → julianoczkowski/designer-skills
- fastapi → **fastapi/fastapi** (official, from the FastAPI repo itself)
- frontend-ui → DOES NOT EXIST by that name; official Anthropic equivalent is **frontend-design** (`skills-sh/anthropics/skills/frontend-design`, trusted)
- grilling → mattpocock/skills (Matt Pocock)
- http-api → clawhub `http-api` (community; Anthropic's own http-api not indexed on skills.sh)
- humanizer → already builtin (creative) — do not reinstall
- postgres-best-practices → **neondatabase/postgres-skills** (Neon, the Postgres company)
- responsive-design → wshobson/agents
- sentry-fix-issues / sentry-python-sdk / sentry-react-sdk / sentry-sdk-setup → **getsentry/sentry-for-ai** (official Sentry ×4)
- shadcn → **shadcn/ui** (official)
- simplify → brianlovin (already have builtin simplify-code — skip)
- tdd → mattpocock (already have builtin test-driven-development — skip)

Not in hub (5) — report, never auto-build: create-migration, deploy-easypanel, migration-head-preflight, opengrep, prefer-library.

Follow-up finds (user's "find more" request):
- context7 → **intellectronica/agent-skills** (official Context7 company) — docs for any lib
- morph → parcadei/continuous-claude-v3 (`morph-search` + `morph-apply`)
- ast-grep → **ast-grep/agent-skills** (official, free) — syntax-aware search/refactor, natural warpgrep substitute; warpgrep itself NOT in hub
- security-review → getsentry/skills + affaan-m
- gitleaks (as named) NOT in hub → closest: **Git Security Scanner** (clawhub, catches leaked secrets/credentials); also secret-scanning (github/awesome-copilot), secrets-management (wshobson)
- semgrep/snyk: EXIST but user rejects (paid) — never propose paid tooling

## Proposed distribution (PENDING user approval — install nothing without a yes)
- frontend-developer: shadcn, frontend-design, accessibility, responsive-design, grilling, sentry-react-sdk, context7
- backend-developer: fastapi, http-api, api-design-principles, code-review (anthropics/knowledge-work-plugins), sentry-python-sdk, sentry-sdk-setup, sentry-fix-issues, ast-grep, Git Security Scanner
- database-developer: postgres-best-practices, bigquery-basics (+ optional custom create-migration/migration-head-preflight IF user approves building)
- designer: design-tokens, design-principles, design-system
- default: NO code skills — stays orchestrator (claude-code/codex/opencode/github + hermes-admin only)
- Open questions awaiting user: ast-grep ok as warpgrep replacement? morph in/out? security-review front vs back? one security scanner enough?
- Builtins already cloned to all profiles (humanizer, simplify-code, tdd, systematic-debugging, requesting-code-review, spike, plan): trim per profile via `save_disabled_skills` against each profile's config.yaml.

## This user's setup state (for continuity)
- Plan: `default` = FAZ-TUDO + orchestrator (unchanged); dedicated profiles: `frontend-developer`, `backend-developer`, `database-developer`, `designer`.
- 2026-08-04: the 4 profiles were created with `--clone` + `--description` (kanban routing); frontend-developer SOUL.md v1 written (React/TS/shadcn/ReactBits, DRY/SOLID, no over-engineering, EN code + pt-BR humanized UI messages via humanizer); backend (FastAPI + Black/Ruff) + db + designer SOUL.md still to draft → confirm → write.
- Dev-profile SOUL.md content rules from user: DRY/SOLID, componentization (front), no over-engineering (reuse what exists), English code/comments/commits by default, ALL user-facing messages pt-BR + humanizer (never raw "Internal Server Error"), readable by other AIs.
- mem0 Platform active: `MEM0_API_KEY` in `~/.hermes/.env`, `memory.provider: mem0`, `mem0ai` in the venv.
