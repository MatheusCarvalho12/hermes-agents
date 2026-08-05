# Publish & Restore — validated transcript (2026-08-05, repo: MatheusCarvalho12/hermes-agents)

Validated end-to-end on the user's machine. The user wanted: back up all Hermes profiles to a PUBLIC GitHub repo so a dead Mac doesn't lose the agents; never commit memories or env; make it restorable via "import profile".

## Profile layout (this user)
- Default/orchestrator lives at `~/.hermes/` (NOT under profiles/) — its distribution folder is named `orchestrator/`
- Dev profiles live at `~/.hermes/profiles/<name>/` (frontend-developer, backend-developer, database-developer, designer)

## Step 1 — inspect what export/install expects
```bash
hermes profile export designer -o /tmp/designer-test.tar.gz   # tar -tzf to inspect
```
`export` tars contain memories/, logs/, sessions/, cron/executions.db, caches, auth.lock → NOT for public git.

`hermes profile install --help`:
- source = git URL (github.com/user/repo, https://, git@) or LOCAL DIRECTORY containing distribution.yaml
- `--name NAME` override, `--alias` wrapper, `--force`, `-y` skip manifest preview

## Step 2 — staging + sanitize (Python, run via execute_code)
Key snippets that worked:

```python
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_\-]{8,}|ctx7sk-[A-Za-z0-9_\-]{8,}|ghp_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9\-]{10,}|AIza[A-Za-z0-9_\-]{20,}|AKIA[A-Z0-9]{16,})")
# replace matches with <SUA_CHAVE_AQUI> line by line, keep YAML structure

def load_disabled(config_path):            # yaml.safe_load -> skills.disabled set
def copy_skills(src, dst, disabled):       # skip .*, skip dirs without SKILL.md,
                                           # skip disabled names, ignore __pycache__/*.pyc
```
Copied per profile: SOUL.md, profile.yaml, mcp.json; sanitized config.yaml; enabled skills; plugins/ (no __pycache__); cron jobs (exclude .jobs.lock/.tick.lock/executions.db/output/ticker_*); hooks/ if non-empty.

Result sizes: ~1.4MB total for 5 profiles (vs ~50MB/profile raw skills dir).

## Step 3 — distribution.yaml
See `templates/distribution.yaml`. Real example (backend-developer):
```yaml
name: backend-developer
version: 1.0.0
description: "Backend developer: FastAPI, SQLAlchemy/Alembic, pytest, APIs REST, integrações e segurança."
author: Matheus Carvalho
license: MIT
hermes_requires: ">=0.12.0"
env_requires:
  - name: CONTEXT7_API_KEY
    description: "Context7 API key (opcional)"
    required: false
    default: ""
  - name: MORPH_API_KEY
    description: "Morph API key para busca de código (warpgrep)"
    required: false
    default: ""
```

## Step 4 — .gitignore (root)
```gitignore
.env
.env.*
auth.json
auth.lock
*.pem
*.key
memories/
sessions/
logs/
plans/
workspace/
home/
kanban/
kanban.db*
state.db*
hermes_state.db
response_store.db*
gateway.pid
gateway_state.json
processes.json
active_profile
.update_check
*.bak
*.bak-*
cache/
image_cache/
audio_cache/
document_cache/
browser_screenshots/
__pycache__/
*.pyc
node_modules/
.bundled_manifest
.curator_state
.usage.json
.usage.json.lock
.hub/
hermes-agent/
.worktrees/
bin/
node/
checkpoints/
sandboxes/
backups/
.hermes_history
.DS_Store
```

## Step 5 — secret scan + false positives
Regex scan found 8 hits; ALL were false positives from `sk-` prefix matching words:
- `sk-adjusted` ← "Risk-adjusted return" (scroll skill script)
- `sk-breakdown` ← "planning-and-task-breakdown" (skill name!)
Rule: grep context around each hit; `sk-` followed by lowercase word chars is usually a word, real keys are long mixed-case.

## Step 6 — git + GitHub
```bash
git init -b main && git add -A
git -c user.name="Matheus Carvalho" -c user.email="mendoncacarvalhomatheus@gmail.com" commit -m "..."
gh repo create MatheusCarvalho12/hermes-agents --public --source . --push --description "..."
```
⚠️ If you already ran `git remote add origin`, `gh repo create --push` prints the URL but skips push → repo empty on GitHub. Verify with `gh api repos/<owner>/<repo>/contents/` (404 = empty) then `git push -u origin main`.

## Step 7 — restore test (the "new machine" simulation)
```bash
git clone https://github.com/MatheusCarvalho12/hermes-agents.git /tmp/...test
cd /tmp/...test
hermes profile install ./designer --name designer-restore-test -y
# verify: SOUL.md, config.yaml, distribution.yaml, plugins/, skills/{design-principles,design-system,design-tokens,figma,i-have-adhd,typography}
# verify ABSENT: memories/ empty, .env absent, auth.json absent, sessions/ empty
hermes -p designer-restore-test chat -q "Responda apenas: OK"   # exit 0, session created
echo "designer-restore-test" | hermes profile delete designer-restore-test
```
`hermes profile delete` prompts `Type '<name>' to confirm:` — piping the name works non-interactively. Without it the delete is silently CANCELLED.

## Pitfalls not obvious from docs
- Direct URL install (`hermes profile install <url>`) fails on multi-profile repos: "No distribution.yaml at the root". Must clone and install per subfolder.
- Git author identity: profile configs are inherited by all agents, but the git author comes from `git config --global user.name/email`. The user's global was `amaterei` (Mac username) while the GitHub account is `MatheusCarvalho12` — commits landed on the right account (email links) but showed the wrong name. Fix: `git config --global user.name "Matheus Carvalho"`. Verify with `git var GIT_AUTHOR_IDENT`.
- Config.yaml may also carry an `aside` MCP with a machine-specific command path — harmless to publish, but don't expect it to work on another machine as-is.

## BUG VALIDATED 2026-08: root-only skill copy drops categorized skills
First publish showed `orchestrator` with only 4 skills (agent-browser, grilling, i-have-adhd, planning-and-task-breakdown) while the profile actually had 9 active non-builtin skills. Cause: the copy loop only scanned the top level of `skills/` and skipped category dirs (`hermes-ops/`, `autonomous-ai-agents/`, `creative/`, `github/`) — so `hermes-multi-profile-ops`, `hermes-administration`, `hermes-profile-engineering`, `hermes-profile-fleets`, `hermes-profile-distributions` were lost.
Fix (in `scripts/sync-hermes-agents.py`): enumerate enabled skills from the CLI, then `find_skill_dir()` walks the WHOLE tree matching SKILL.md frontmatter `name:`. 
Also learned: `hermes skills list --enabled-only` table separator is `│` (U+2502) — NOT `┃`; parse by fixed index `cells[1]/cells[3]/cells[5]` with `len(cells) >= 7` (filtering empty cells collapses rows whose category is blank, dropping valid skills). Skip `source == "builtin"` (ships with Hermes).
Final counts after fix: orchestrator 9, frontend 22, backend 14, database 4, designer 6 = 55 total.
