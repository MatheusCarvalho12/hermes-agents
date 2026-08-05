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
