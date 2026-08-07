---
name: hermes-profile-distributions
description: "Use to back up Hermes profiles as git distributions."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [hermes, profiles, distribution, backup, github, install]
    related_skills: [hermes-administration, hermes-multi-profile-ops, github-repo-management]
---

# Hermes Profile Distributions (backup / publish / restore via git)

A **profile distribution** packages a complete Hermes agent (SOUL.md, config, skills, plugins, cron, MCP) as a git repo so it can be installed on another machine with one command: `hermes profile install <git-url>`. This is the OFFICIAL mechanism for "back up my agents to GitHub so I can restore after a hardware failure".

Official docs: https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions

## When to use
- User wants to back up Hermes profiles/agents to GitHub ("se meu Mac quebrar eu pego de lá")
- User wants to share a specialized agent with a team or publicly
- User wants to deploy the same agent to multiple machines
- Restoring a profile on a fresh install

## Two mechanisms — do NOT confuse them

| Mechanism | Command | What it includes | Use for |
|---|---|---|---|
| **Profile export** | `hermes profile export <name> -o out.tar.gz` | EVERYTHING: memories/, logs/, sessions/, cron db, caches, auth.lock | Full local backup, private archive |
| **Profile distribution** | git repo with `distribution.yaml` | SOUL.md, config.yaml, skills/, plugins/, cron/, mcp.json — installer STRIPS `.env`, `auth.json`, `memories/`, `sessions/`, `logs/`, `state.db*` | Git/GitHub sharing, restore on new machine |

`hermes profile export` tars are NOT safe for public GitHub (they contain user data). Use distributions for git.

## Security invariants (user's standing rules — confirmed 2026-08)
1. NEVER commit: `.env`, `auth.json`, `memories/`, `sessions/`, `logs/`, `state.db*`, caches, `plans/`, `home/`, `workspace/`, `*.bak-*`.
2. **Sanitize `config.yaml` BEFORE commit**: MCP API keys live INSIDE `mcp_servers.<name>.env` in the profile config (real case: `CONTEXT7_API_KEY: ctx7sk-...`, `MORPH_API_KEY: sk-...` were found embedded and had to be scrubbed). Grep for `api_key|token|secret|sk-|ctx7sk-|ghp_|AIza|AKIA` and replace values with `<SUA_CHAVE_AQUI>`.
3. The installer strips hard-excluded paths on ITS side too — but that protects installers, NOT the author. The repo author is exposed; scan before push.
4. Only copy ENABLED skills (the `skills.disabled` list in config.yaml tells you what to skip). Copying the whole `skills/` dir ships ~50MB of disabled clutter per profile.

## PITFALL: skills live at ANY depth — copy recursively, not root-only
Skills are stored in category folders (`hermes-ops/hermes-multi-profile-ops/`, `autonomous-ai-agents/hermes-administration/`, `creative/humanizer/`) AND at the root (`grilling/`, `i-have-adhd/`). A copy script that only scans the top level silently DROPS every categorized skill — real case: the orchestrator published with 4 skills instead of 9 (missing `hermes-multi-profile-ops`, `hermes-administration`, etc.). Rule: enumerate active skills from the CLI, then `find_skill_dir()` each one by walking the whole tree for a `SKILL.md` whose frontmatter `name:` matches.

**CLI enumeration technique** (`hermes -p <profile> skills list --enabled-only`, `COLUMNS=400`):
- Table separator is `│` (U+2502 BOX DRAWINGS LIGHT VERTICAL), NOT `┃`.
- Parse by FIXED cell index, not by filtering empties: `cells = [c.strip() for c in line.split("│")]` → `['', name, category, source, trust, status, '']` → require `len(cells) >= 7`, read `name=cells[1]`, `source=cells[3]`, `status=cells[5]`. If you filter empty cells first, rows with an empty category collapse to 4 cells and get dropped (that's exactly how the designer's 6 non-builtin skills were lost).
- Only include `source != "builtin"` — builtin skills ship with Hermes and don't belong in the distribution.

## Auto-sync: keep the distribution repo current without being asked (validated 2026-08)
User requirement: "toda vez que atualizar alguma coisa, faz push automático, muda a versão" — a repo that stays fresh as a portfolio. Working pattern (scripts/sync-hermes-agents.py, cron every 2h):
1. Script re-runs the full publish workflow: rebuild staging from live profiles → sanitize configs → bump PATCH version in each `distribution.yaml` → regenerate README (agent table + skill counts + date) → `git add/commit/push`, tag `v<version>` from the orchestrator manifest.
2. Silent when nothing changed (`git status --porcelain` empty → exit 0, no commit, no push) → zero CPU/bandwidth when idle, perfect for a cron watchdog.
3. Cron: `cronjob action=create no_agent=true script=sync-hermes-agents.sh schedule="every 2h"` (sh wrapper execs the venv python; script path resolves under ~/.hermes/scripts/). Test once with `cronjob action=run`.
4. **`--check` mode must NOT mutate**: don't bump versions or write README when only reporting; guard the bump with `if status and not check_only`.

## Excluding a profile from the distribution (private/standalone agents — validated 2026-08, profile `trader`)
Some profiles must NEVER reach the public backup repo (e.g. a private trading agent the user talks to directly). The auto-sync script enumerates profiles via hardcoded `PROFILES`/`AGENT_META` lists — a newly created profile does NOT auto-join (no glob over `~/.hermes/profiles/*`), but harden it anyway so a future edit can't leak it:
1. **Guard in the sync script** (`~/.hermes/scripts/sync-hermes-agents.py`): `EXCLUDED_PROFILES = {"<name>"}` + abort at the top of `build()`:
   `leaked = (set(PROFILES) | set(AGENT_META)) & EXCLUDED_PROFILES; if leaked: raise SystemExit("sync: PERIGO — ...")` — aborts even if someone later adds the name to either list. Note: the script lives under `~/.hermes/scripts/` and is NOT versioned in the repo — the guard is local-only.
2. **`.gitignore` entry in the staging repo** (`~/dev/hermes-agents/.gitignore`): `<name>/` under a `# ── Perfis privados — NUNCA publicar ──` section. This file IS pushed to GitHub → protects the remote even if `git add -A` ever runs with the folder present. Commit+push the .gitignore change immediately (don't wait for the 2h cron).
3. **Verify remote**: `gh api repos/<owner>/<repo>/contents/ --jq '.[].name'` shows no `<name>` folder; `git -C <repo> check-ignore -v <name>/` confirms the ignore rule.
4. Full recipe + the ad-hoc verification harness (importlib monkeypatch of PROFILES/AGENT_META asserting SystemExit): `references/excluding-private-profiles.md`.

## Publish workflow (validated 2026-08, repo: MatheusCarvalho12/hermes-agents)
Full step-by-step with code in `references/publish-and-restore.md`. Summary:

1. Stage a clean dir (e.g. `~/dev/hermes-agents/`), one subfolder per profile.
2. Per profile, copy: `SOUL.md`, `profile.yaml`, `mcp.json`; `config.yaml` **sanitized**; enabled `skills/` only (skip `__pycache__`, `.pyc`, `.hub/`, `.bundled_manifest`, `.curator_state`, `.usage.json`); `plugins/`; real `cron/` jobs (skip locks/db/output); `hooks/` if non-empty.
3. Write `distribution.yaml` per profile (see `templates/distribution.yaml`). Fields: name, version, description, author, license, `hermes_requires`, `env_requires` (list of optional/required env vars the agent needs — checked by installer against `.env`).
4. Root `.gitignore` with the full exclusion list (see reference).
5. Secret-scan the staging dir (regex below). Watch FALSE POSITIVES: substrings like "sk-adjusted" (Risk-adjusted) and "sk-breakdown" (task-breakdown) match `sk-` patterns but are words, not keys — eyeball each hit in context before fixing.
6. Commit with the user's git identity, create repo, push.

## PITFALL: `gh repo create --source . --push` silently skips push
If `git remote add origin` already ran (or `gh repo create` reports "Unable to add remote"), the repo is created EMPTY on GitHub and the push never happens. The command still prints the repo URL, so it LOOKS successful. ALWAYS verify after create:
```bash
gh api repos/<owner>/<repo>/commits/main --jq '.commit.author.name'   # errors "empty" if push failed
gh api repos/<owner>/<repo>/contents/ --jq '.[].name'                 # lists files only after push
git push -u origin main                                               # fix: push explicitly
```

## PITFALL: `hermes profile install <git-url>` requires `distribution.yaml` at the repo ROOT
A repo with multiple profiles in subfolders (orchestrator/, frontend-developer/, ...) fails with `Error: No distribution.yaml at the root`. Multi-profile repos install from a CLONE, using the local-directory source form (officially supported):
```bash
git clone https://github.com/<owner>/<repo>.git
cd <repo>
hermes profile install ./designer --alias            # one per profile subfolder
hermes profile install ./designer --name my-name -y   # override name, skip manifest prompt
```
Single-profile repos can install directly from the URL (`hermes profile install github.com/you/research-bot`).

## Restore + verify on a fresh machine
1. `git clone` the repo.
2. `hermes profile install ./<folder> --alias` per profile (or `--name X` to avoid clobbering an existing profile).
3. Verify what came and what did NOT (memories/.env/auth.json/sessions must be empty).
4. Smoke test: `hermes -p <name> chat -q "Responda apenas: OK"` → exit 0.
5. Cleanup test profile: `echo "<name>" | hermes profile delete <name>` (delete prompts for typed confirmation — pipe the name).

## Update flow (pull changes without losing user data)
```bash
git pull && hermes profile update <name>
```
Distribution-owned files (SOUL.md, config.yaml, skills/, cron/, mcp.json) are replaced; user-owned (memories/, sessions/, .env, auth.json, logs/) are never touched.

## Verification checklist (before telling the user it's done)
- [ ] `git log -1` shows the USER's name/email (`Matheus Carvalho <mendoncacarvalhomatheus@gmail.com>`)
- [ ] `git ls-remote origin main` / `gh api .../contents/` lists files (push really landed)
- [ ] Secret scan of the remote tree finds nothing (`gh api .../git/trees/main?recursive=1` + grep)
- [ ] A test install from a clone actually boots and answers
- [ ] Test profile deleted afterwards (no residue in `~/.hermes/profiles/`)

## Support files
- `references/publish-and-restore.md` — exact copy/sanitize/scan code + validated transcript
- `templates/distribution.yaml` — manifest starter per profile
- `scripts/sync-hermes-agents.py` — full auto-sync script (rebuild → sanitize → bump → README → push + tag); run with the Hermes venv python (`~/.hermes/hermes-agent/venv/bin/python`)
- `scripts/sync-hermes-agents.sh` — cron wrapper; wire as `cronjob action=create no_agent=true script=sync-hermes-agents.sh schedule="every 2h"`
