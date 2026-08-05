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

## Procedure: Profiles & SOUL.md (user's standing rules)
1. **Confirm BEFORE creating anything**: show the plan (which profiles, clone vs blank) and get a yes before `hermes profile create`; same for SOUL.md/SKILL.md content — draft in chat, user validates, then write to disk. The user corrected this twice (profiles were created without confirmation and flagged).
2. **Read official docs before writing MDs**: `/docs/user-guide/profiles` + `/docs/guides/use-soul-with-hermes` + `/docs/user-guide/features/personality`. Doc-grounded MDs only — never improvised identity files.
3. Always pass `--description "<role>"` at create time — the kanban orchestrator routes tasks by role.
4. SOUL.md official structure: `# Identity` / `# Style` / `# Avoid` / `# Defaults`; identity+voice only (paths, commands, conventions go in `AGENTS.md`); changes take effect on a NEW session.
5. Per-profile skill trim = same `save_disabled_skills` script, run against that profile's home (each profile owns its config.yaml / skills.disabled).
6. User prefers Hermes' NATIVE skill-creation loop (background review, `skills.creation_nudge_interval`) over third-party tools; Anthropic `skill-creator` is method reference only, never installed (conflict risk).

Distilled docs, the native skill-creation mechanism (with code refs), the skill-creator methodology, the hub skill audit table, and profile setup state: `references/profiles-and-soul.md`.

## Procedure: Hub Skill Audit & Distribution (this user's workflow)
1. User supplies a skill list (names from memory/hub) → **audit, never build**: `hermes skills search <term>` → table with Name/Source/Trust/Identifier (`skills-sh/owner/repo/path`). Preview with `hermes skills inspect <id>` (also resolves some raw GitHub paths).
2. **Search-by-term misses official skills**: "frontend-ui" has no hit — the Anthropic official is `frontend-design` (trusted, `skills-sh/anthropics/skills/frontend-design`). When a name won't resolve, list the source repo directly: `curl -s https://api.github.com/repos/<owner>/<repo>/contents/<path> | grep '"name"'`.
3. **Verify "official" by source repo** (user wants official-with-docs first): google/skills (bigquery-basics), fastapi/fastapi (fastapi), shadcn/ui (shadcn), getsentry/sentry-for-ai (sentry-* ×4), neondatabase/postgres-skills (postgres-best-practices), intellectronica/agent-skills (context7), ast-grep/agent-skills, anthropics/skills (frontend-design, webapp-testing) + anthropics/knowledge-work-plugins (code-review).
4. **Check builtins before proposing**: `hermes skills list` — humanizer, simplify-code, test-driven-development, github-code-review are already builtin; don't propose/install duplicates (user flagged "tdd"/"simplify" that way).
5. **Per-profile install**: skills do NOT propagate from default to already-cloned profiles — install into the target profile: `hermes -p <profile> skills install <id>`. No duplication across profiles; the `default` profile stays free of code skills (it's the orchestrator).
6. **User's standing rules**: (a) use market/hub skills, never hand-build one unless user approves ("não cria tu mesmo nenhuma skill ainda"); (b) "me fala antes de por" — present the full distribution and get a yes BEFORE installing anything; (c) no repetition between profiles; (d) paid tools rejected (semgrep, snyk) — propose free/open-source alternatives (opengrep→ast-grep; gitleaks→Git Security Scanner on clawhub).

## Pitfalls
- `hermes skills install` and `hermes mcp add` both block on interactive confirms (y/N, `Enable all N tools? [Y/n/select]`) — pipe `echo y |`; without it the command is silently CANCELLED and nothing is saved.
- A key-gated MCP server that connects but reports "no tools" almost always means its API key never reached the subprocess — pass it via `--env KEY=VAL` on `mcp add`, not just the profile `.env`.
- `hermes skills install` blocks on an interactive y/N confirm even after a clean scan — pipe `echo y |` for automation.
- Names in `skills.disabled` must match folder/display names from `hermes skills list` (the "enabled" column reflects the setting).
- `hermes memory setup` is interactive and TTY-only; for scripted platform setup: `hermes config set memory.provider mem0` + `MEM0_API_KEY` in `.env` (mem0ai auto-installs on activation).
- Overlap by design: bundled `hermes-agent` skill + official docs win on config keys/commands; this skill carries verified workarounds.
