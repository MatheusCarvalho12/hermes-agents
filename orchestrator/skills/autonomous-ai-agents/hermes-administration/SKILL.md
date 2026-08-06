---
name: hermes-administration
description: "Administer Hermes: skills, memory providers, profiles."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [hermes, admin, skills, memory, profiles, config]
    related_skills: [hermes-agent, hermes-agent-skill-authoring]
---

# Hermes Administration

Field-tested operator knowledge for administering Hermes itself: skill lifecycle, memory providers, profiles. Complements the bundled `hermes-agent` skill (official config reference) — this one carries the source-verified workarounds and pitfalls. Official docs always win on key/command existence: https://hermes-agent.nousresearch.com/docs/

## When to Use
- User asks to install/disable/enable/curate skills, or wants a profile with a trimmed skill set
- User asks to switch memory provider (mem0, honcho, etc.) or check memory status
- Creating or managing profiles (`hermes profile create`), especially specialized dev profiles (frontend/backend/db/designer) with curated per-profile skill sets
- Auditing hub skills (search/inspect/verify official source) and proposing a per-profile distribution

## Hard Invariants
- Never hand-edit `config.yaml` — use `hermes config set KEY VAL` or the app's own Python APIs (`hermes_cli.config.load_config` / `save_config`)
- Secrets (API keys) go in `~/.hermes/.env`, never in config.yaml
- Tool/feature changes (new memory tools, disabled skills) take effect only in a NEW session (`/reset`) — prompt caching forbids mid-conversation changes
- Confirm with the user BEFORE creating/editing any SKILL.md; consult official docs + bundled `hermes-agent` skill first

## Quick Reference
| Task | Command |
|---|---|
| List skills | `hermes skills list` |
| Install from hub | `hermes skills install owner/repo/path` (blocks on y/N prompt → pipe `echo y \|`) |
| Disable skills | see Procedure below — do NOT use `hermes config set skills.disabled` |
| Interactive enable/disable | `hermes skills config` (TTY required) |
| Memory provider setup | `hermes memory setup` (interactive) / `status` / `off` / `reset` |
| Create profile | `hermes profile create <name> [--clone|--clone-all|--clone-from X|--no-skills] [--description "role"]` |
| Add MCP server | `hermes mcp add <name> --command npx --args ...` (pipe `echo y |`; `--env KEY=VAL`; `--args` must be last) |
| MCP per profile | `hermes -p <profile> mcp add/list/test ...` |
| RTK integration | `rtk init --agent hermes`; per profile: `HERMES_HOME=~/.hermes/profiles/<p> rtk init --agent hermes` |
| Per-profile skills | each profile has its own config.yaml → run the disable-skill script against that profile's home (see Procedure: Disable Skills) |

## Procedure: Disable Skills (the correct way)

`hermes config set skills.disabled '["a","b"]'` SILENTLY FAILS: the value is stored as a quoted YAML string, and the loader (`agent.skill_utils._normalize_string_set`) treats a string as ONE skill name — so nothing matches and the skills stay enabled. The key also isn't in the defaults schema (it's read dynamically), so the setter warns "not a recognized config key" and skips list coercion.

Correct path — use the app's own API (same code path the interactive `hermes skills config` uses):
1. Backup: `cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak-$(date +%Y%m%d-%H%M%S)`
2. Script (repo root = `$HERMES_HOME/hermes-agent`):
```python
import sys
sys.path.insert(0, "$HERMES_HOME/hermes-agent")  # expand $HERMES_HOME
from hermes_cli.skills_config import save_disabled_skills
from hermes_cli.config import load_config
save_disabled_skills(load_config(), {"skill-a", "skill-b"})
```
3. Run with the app's venv python: `$HERMES_HOME/hermes-agent/venv/bin/python script.py`
4. Verify: `hermes config get skills.disabled` shows a real YAML list, and loader agrees — `from agent.skill_utils import get_disabled_skill_names; print(get_disabled_skill_names())`

Config shape written: `skills.disabled: [skill-a, skill-b]` (global) and `skills.platform_disabled: {platform: [...]}` (per-platform). Reversible — clear the list to re-enable; nothing is deleted from disk.

New pitfalls (validated 2026-08 on the 4-dev-profile trim):
- `hermes skills list` truncates long names with "…" — set `COLUMNS=400` (or wider) to read canonical names before computing the disabled set.
- Disabled names MUST be the CLI's canonical DISPLAY names, not folder names from `ls skills/`: `Design System` (display) ≠ `design-system` (folder); `test-review` ≠ `nm-pensive-test-review`. Trust the CLI, not the filesystem.
- Profiles created with `--clone` inherit the FULL `skills/` directory of the source (~75-90 skills) — per-profile trim is a REQUIRED post-clone step. Ready-made script + current team distribution: `hermes-multi-profile-ops/scripts/trim-profile-skills.py` (run with the app's venv python).

## Procedure: Native Profile Cleanup (`hermes skills opt-out --remove`)
Native alternative to the disabled-list trim for profiles that cloned everything — validated 2026-08 on frontend-developer (90+ → 23 skills):
1. `hermes -p <profile> skills opt-out --remove` — deletes UNMODIFIED bundled skills from disk; hub/local/modified skills are kept. Verify with `COLUMNS=400 hermes -p <profile> skills list`.
2. **Blocks on an interactive y/N confirm** — pipe `echo y |`. Bare run only creates the `.no-bundled-skills` marker and prints "Marker kept; no skills deleted".
3. **Bundled skills in the curated kit get removed too** (e.g. `humanizer` is bundled) — re-copy them from the default profile: `mkdir -p <profile>/skills/creative && cp -r ~/.hermes/skills/creative/humanizer <profile>/skills/creative/`.
4. **Cloned admin skills survive opt-out** (e.g. `hermes-administration` is local, not bundled) — they stay on disk; disable them per-profile via the `save_disabled_skills` script with `HERMES_HOME=<profile-home>` env set (see Disable Skills above). After cleanup, curate the kit: reinstall missing hub skills per profile, then re-verify with `hermes -p <profile> skills list`.

## Procedure: MCP Servers & RTK (per-profile tooling)
- Add per profile: `hermes -p <profile> mcp add <name> --command npx --args ...` (`--args` must be the LAST option). After discovery it prompts `Enable all N tools? [Y/n/select]` — under a pipe it CANCELS and saves nothing → prefix `echo y |`. Verify with `hermes -p <p> mcp list` / `mcp test <name>` (test shows the discovered tool names).
- Key-gated servers connect but report "no tools" when the key never reaches the process → pass `--env KEY=VAL` (stored as `mcp_servers.<name>.env` in that profile's config.yaml — official mechanism) and also keep the key in the profile's `.env`. `hermes mcp catalog` (Nous-approved, one-click) rarely contains these — add manually.
- MCP tools only load in a NEW session of that profile.
- Known per-profile MCPs for this user: **context7** (`npx -y @upstash/context7-mcp`, free tier, `CONTEXT7_API_KEY` optional) for up-to-date lib docs; **Morph** (`npx --prefer-offline -y @morphllm/morphmcp`, needs `MORPH_API_KEY`, ~$0.80/1M tokens) — its WarpGrep surfaces as the `codebase_search` + `github_codebase_search` tools (needs ripgrep installed; SDK is TS/Node-only).
- **RTK (Rust Token Killer)** (`brew install rtk`): token-saving CLI proxy that rewrites shell commands (`git status` → `rtk git status`, up to 90% less bash output). Hermes integration is native: `rtk init --agent hermes` writes a `rtk-rewrite` plugin (hook `pre_tool_call`) into `$HERMES_HOME/plugins/` and enables it in config.yaml. To enable in EVERY profile, run it once per profile with `HERMES_HOME=~/.hermes/profiles/<name>`. Effective on next session.

Quick-starts and caveats: `references/mcp-and-rtk-setup.md`.

## Memory Providers
Built-in memory (MEMORY.md/USER.md, `memory` tool) is ALWAYS active; ONE external provider at a time: honcho, openviking, mem0, hindsight, holographic, retaindb, byterover. External providers surface their own tools (`mem0_*` etc.), visible only in a new session.

See `references/memory-providers.md` for mem0's three modes (platform/oss/selfhosted), env vars, and plugin internals.

## Memory policy: local MEMORY.md vs external mem0 (USER CORRECTION 2026-08-05 — strong)
The user corrected this forcefully ("Porra, pelo amor de Deus, usa ele"): **project/personal facts go to the EXTERNAL provider (mem0), never to the local MEMORY.md.** The local file is for TINY universal lessons only ("aprendizado que precisa ficar de memória pra nunca mais errar, válido para tudo"). Rules:
- **MEMORY.md local** = a handful of structured, tiny, universal lessons (≤ ~700 bytes in practice). NOT project paths, NOT task outcomes, NOT per-profile kits, NOT the user's repo list — those are mem0 material.
- **mem0 (external)** = real memories, separated by project/agent — projects, architecture decisions, environment facts, preferences, per-agent learning.
- **Per-profile workers** (frontend/backend/db/designer) have `memory_enabled: true` + mem0 key in their own `.env`; their cloned `memories/MEMORY.md` may carry ORCHESTRATOR content from `--clone` — that's wrong for them, rewrite it per role or let their SOUL Learning section drive it.
- **When the local file overflows** (`memory` tool errors "over the limit"), the fix is MIGRATE to mem0 (mem0_add each project fact), not compress harder: batch-remove the project entries from local and keep only universal lessons.
- **Workers need a `# Learning` section in their SOUL.md** to actually use memory (the mechanism exists but is inert without instruction — 0 memory/skill_manage calls across 5 tasks before the section was added): "when a task teaches you something UNIVERSAL, SAVE IT with the memory tool; project details go in the repo, never memory/skills; repeated procedure (5+ steps) → propose a skill, confirm with orchestrator."


## Procedure: Profiles & SOUL.md (user's standing rules)
1. **Confirm BEFORE creating anything**: show the plan (which profiles, clone vs blank) and get a yes before `hermes profile create`; same for SOUL.md/SKILL.md content — draft in chat, user validates, then write to disk. The user corrected this twice (profiles were created without confirmation and flagged).
2. **Read official docs before writing MDs**: `/docs/user-guide/profiles` + `/docs/guides/use-soul-with-hermes` + `/docs/user-guide/features/personality`. Doc-grounded MDs only — never improvised identity files.
3. Always pass `--description "<role>"` at create time — the kanban orchestrator routes tasks by role.
4. SOUL.md official structure: `# Identity` / `# Style` / `# Avoid` / `# Defaults`; identity+voice only (paths, commands, conventions go in `AGENTS.md`); changes take effect on a NEW session.
5. Per-profile skill trim = same `save_disabled_skills` script, run against that profile's home (each profile owns its config.yaml / skills.disabled).
6. User prefers Hermes' NATIVE skill-creation loop (background review, `skills.creation_nudge_interval`) over third-party tools; Anthropic `skill-creator` is method reference only, never installed (conflict risk).

Distilled docs, the native skill-creation mechanism (with code refs), the skill-creator methodology, the hub skill audit table, and profile setup state: `references/profiles-and-soul.md`.

## Procedure: Read-only Hermes Architecture Audit
Use when the user asks for an inventory or architecture review of `HERMES_HOME` and explicitly forbids edits. The detailed checklist lives in `references/read-only-architecture-audit.md`.

1. Resolve the real home from `$HERMES_HOME` (fallback `~/.hermes`) and enumerate only the root plus `profiles/*`; never assume a container path.
2. Run `hermes profile list` and record profile names and gateway status. A stopped gateway is an operational finding for Kanban dispatch, not proof that no process exists.
3. Use `COLUMNS=400 hermes [-p <profile>] skills list` as the canonical source for skill display names, source, trust, enabled/disabled status, and counts. Filesystem `SKILL.md` inventory is supplemental: use it to detect duplicate files, duplicate frontmatter names, and folder/display-name mismatches such as renamed or title-cased skills.
4. Map profile-level `SOUL.md` files and inspect only structural metadata (headings, line counts, skill/trigger mentions). Distinguish authoritative profile context from nested repository/vendor `AGENTS.md` files; report `.hermes.md` and `CLAUDE.md` presence/absence explicitly.
5. Inspect `config.yaml` for MCP server names, `enabled` flags, command shape, argument counts, and the presence of secret-bearing environment keys. Never print `.env`, `auth.json`, token values, API-key values, or raw MCP arguments that may contain secrets.
6. Compare skill hashes and canonical frontmatter names across profiles. Separate expected isolated-profile copies from actionable collisions: same canonical name with divergent content, or multiple files collapsing to one CLI entry.
7. Produce a short report with absolute paths, canonical CLI counts/names, trigger coverage, MCP topology, and verified risks. This procedure is read-only: do not create backups, edit config, or write reports to disk.

## Procedure: Hub Skill Audit & Distribution (this user's workflow)
1. User supplies a skill list (names from memory/hub) → **audit, never build**: `hermes skills search <term>` → table with Name/Source/Trust/Identifier (`skills-sh/owner/repo/path`). Preview with `hermes skills inspect <id>` (also resolves some raw GitHub paths).
2. **Search-by-term misses official skills**: "frontend-ui" has no hit — the Anthropic official is `frontend-design` (trusted, `skills-sh/anthropics/skills/frontend-design`). When a name won't resolve, list the source repo directly: `curl -s https://api.github.com/repos/<owner>/<repo>/contents/<path> | grep '"name"'`.
3. **Verify "official" by source repo** (user wants official-with-docs first): google/skills (bigquery-basics), fastapi/fastapi (fastapi), shadcn/ui (shadcn), getsentry/sentry-for-ai (sentry-* ×4), neondatabase/postgres-skills (postgres-best-practices), intellectronica/agent-skills (context7), ast-grep/agent-skills, anthropics/skills (frontend-design, webapp-testing) + anthropics/knowledge-work-plugins (code-review).
4. **Check builtins before proposing**: `hermes skills list` — humanizer, simplify-code, test-driven-development, github-code-review are already builtin; don't propose/install duplicates (user flagged "tdd"/"simplify" that way).
5. **Per-profile install**: skills do NOT propagate from default to already-cloned profiles — install into the target profile: `hermes -p <profile> skills install <id>`. No duplication across profiles; the `default` profile stays free of code skills (it's the orchestrator).
6. **User's standing rules**: (a) use market/hub skills, never hand-build one unless user approves ("não cria tu mesmo nenhuma skill ainda"); (b) "me fala antes de por" — present the full distribution and get a yes BEFORE installing anything; (c) no repetition between profiles; (d) paid tools rejected (semgrep, snyk) — propose free/open-source alternatives (opengrep→ast-grep; gitleaks→Git Security Scanner on clawhub).

## Procedure: Install a Skill Pack (mattpocock-style) — the RIGHT command (validated 2026-08-05)
- **`npx skills@latest add <owner>/<repo>` NÃO instala no Hermes.** It targets Codex/other agents (`~/.codex/skills/`, project skills) — verified: after the user ran `npx skills@latest add mattpocock/skills`, nothing landed in `~/.hermes/skills/` and `npx skills list` showed only 3 local skills. Always use Hermes' own installer:
  `hermes skills install "skills-sh/mattpocock/skills/engineering/<name>" -y` (add `-p <profile>` to target a profile).
- **The CLI search only shows a handful of hits; enumerate the full pack via GitHub API**: `curl -s https://api.github.com/repos/mattpocock/skills/contents/skills/<cat> | grep '"name"'`. Categories: engineering (ask-matt, code-review, codebase-design, diagnosing-bugs, domain-modeling, grill-with-docs, implement, prototype, research, resolving-merge-conflicts, tdd, to-spec, to-tickets, triage, wayfinder, wizard), productivity (grill-me, grilling, handoff, teach, to-questionnaire, wait-what, writing-for-agents), misc (git-guardrails-claude-code, setup-pre-commit, ...), in-progress.
- **Scanner blocks with "dangerous verdict" are NOT overridable** (`--force` does not override dangerous): mattpocock `ask-matt` (agent_config_mod) and `writing-for-agents` (4 findings) refused. `caution` verdicts ARE overridable with `--force -y` after confirming the source is reputable.
- **Duplicate-name consolidation**: `hermes skills install` can create a name collision with an existing local skill (e.g. `grilling` existed in both `~/.hermes/skills/grilling/` (old one-question-at-a-time) and `y/grilling/` (rounds/frontier) plus a `y/grill-me/` stub → `skill_view` errors "Ambiguous skill name"). Fix: keep ONE canonical version (the mattpocock rounds one), move the old dir to `~/.hermes/skills/<name>.old-YYYYMMDD` (backup, not delete), verify with `COLUMNS=400 hermes skills list`.

## Pitfalls
- **Mac quente / CPU 100%? Procure processo órfão `hermes serve` ANTES de culpar Chrome.** Real case 2026-08: `ps -Ao pid,pcpu,comm -r` mostrou um `python -m hermes_cli.main serve --host 127.0.0.1 --port 0` órfão (PPID 1) a 99% CPU por ~1h, esquentando o Mac; o usuário suspeitava do Chrome, mas nenhum Google Chrome real estava aberto (só crashpad handlers de apps Electron — Claude/Aside/Wispr — que são normais). Confirmar com `sample <pid> 2` (main thread presa em loop de I/O), matar com `kill -9 <pid>` (SIGTERM não pega loop travado), verificar com `ps -p <pid>` + `uptime` (load cai). `hermes serve --port 0` legítimos rodam a <2% CPU; 90%+ = travado. Cron jobs ativos aparecem em `cronjob action=list` — 0 jobs + processo órfão = servidor de sessão antigo preso.
- `hermes skills install` and `hermes mcp add` both block on interactive confirms (y/N, `Enable all N tools? [Y/n/select]`) — pipe `echo y |`; without it the command is silently CANCELLED and nothing is saved.
- A key-gated MCP server that connects but reports "no tools" almost always means its API key never reached the subprocess — pass it via `--env KEY=VAL` on `mcp add`, not just the profile `.env`.
- `hermes skills install` blocks on an interactive y/N confirm even after a clean scan — pipe `echo y |` for automation.
- Names in `skills.disabled` must match folder/display names from `hermes skills list` (the "enabled" column reflects the setting).
- `hermes memory setup` is interactive and TTY-only; for scripted platform setup: `hermes config set memory.provider mem0` + `MEM0_API_KEY` in `.env` (mem0ai auto-installs on activation).
- Overlap by design: bundled `hermes-agent` skill + official docs win on config keys/commands; this skill carries verified workarounds.
