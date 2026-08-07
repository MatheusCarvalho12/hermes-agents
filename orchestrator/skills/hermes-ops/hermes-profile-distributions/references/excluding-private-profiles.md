# Excluding a private profile from the GitHub distribution — validated recipe (2026-08, `trader`)

Context: user created a STANDALONE private profile (`trader`, trading agent) that must never appear in the public backup repo `MatheusCarvalho12/my-hermes-agents` (staging dir `~/dev/hermes-agents/`, auto-sync cron every 2h via `~/.hermes/scripts/sync-hermes-agents.py`). The user's requirement: "de alguma forma deixa não deixa ele subir".

## Why it is safe by default
The sync script enumerates profiles from hardcoded lists:
```python
PROFILES = ["frontend-developer", "backend-developer", "database-developer", "designer", "default"]
AGENT_META = { ... }  # also hardcoded; drives README badges/rows
```
No glob over `~/.hermes/profiles/*` → a new profile does NOT auto-join the build. Verified: after creating `trader`, `git status --porcelain` in the staging repo showed zero `trader` paths and the remote contents had no `trader` folder. BUT the guard below exists so a future edit of the lists can't leak it.

## Layer 1 — guard in the sync script (local, ~/.hermes/scripts/sync-hermes-agents.py)
```python
PROFILES = [...]
LABEL = {"default": "orchestrator"}
EXCLUDED_PROFILES = {"trader"}   # NUNCA remover — standalone/privado

def build():
    skills_by_profile = {}
    leaked = (set(PROFILES) | set(AGENT_META)) & EXCLUDED_PROFILES
    if leaked:
        raise SystemExit(f"sync: PERIGO — perfil excluído {sorted(leaked)} na lista de publicação. Abortando.")
    ...
```
Behavior verified: injecting `trader` into `PROFILES` OR `AGENT_META` → `SystemExit` with "PERIGO ... Abortando".

## Layer 2 — .gitignore in the staging repo (pushed to GitHub, protects the remote)
Append to `~/dev/hermes-agents/.gitignore`:
```
# ── Perfis privados — NUNCA publicar ──────────────────────
trader/
```
Commit + push immediately (don't wait for the 2h cron):
```bash
cd ~/dev/hermes-agents && git add .gitignore && git commit -m "chore: exclui trader/ do backup publico" && git push origin main
```
Note: this changes the working tree → the next `sync --check` reports "MUDANÇAS" (expected; the cron commits the rest).

## Layer 3 — verification (empirical, not self-report)
```bash
git -C ~/dev/hermes-agents check-ignore -v trader/        # → .gitignore:47:trader/	trader/
git -C ~/dev/hermes-agents status --porcelain | grep trader || true   # no output = clean
gh api repos/MatheusCarvalho12/my-hermes-agents/contents/ --jq '.[].name'   # no trader folder
~/.hermes/hermes-agent/venv/bin/python ~/.hermes/scripts/sync-hermes-agents.py --check   # repo state
```

## Ad-hoc verification harness (no canonical suite exists for cron scripts)
Create via `tempfile.mkstemp(prefix="hermes-verify-", suffix=".py")`, run with the hermes venv python, delete after. Core pattern — import the module by path and monkeypatch the lists:
```python
import importlib.util, subprocess, sys
spec = importlib.util.spec_from_file_location(
    "sync_mod", "/Users/amaterei/.hermes/scripts/sync-hermes-agents.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert "trader" not in m.PROFILES and "trader" not in m.AGENT_META
assert "trader" in m.EXCLUDED_PROFILES
for field in ("PROFILES", "AGENT_META"):
    mm = importlib.util.module_from_spec(spec); spec.loader.exec_module(mm)
    (mm.PROFILES if field == "PROFILES" else mm.AGENT_META).update(...)  # inject leak
    try:
        mm.build(); raise AssertionError("did not abort")
    except SystemExit as e:
        assert "PERIGO" in str(e) and "trader" in str(e)
```
Ran 9/9 PASS, exit 0: imports cleanly, trader not in lists, trader in EXCLUDED, guard aborts on both leak paths, gitignore ignores, no trader in repo status, no trader on remote.

## Pitfalls hit
- A start-anchored grep can silently miss a key line: `grep -oE "^[A-Z_]+="` did NOT show `MEM0_API_KEY=` in the same file where `grep -nE "MEM0"` found it at line 497 (cause not root-caused; the copy itself worked). Always verify copied `.env` keys by NAME afterwards (`grep -oE "(KEY1|KEY2)" <target>`), and never print values — a masking sed can fail and leak a key into terminal output.
- macOS has no `cat -A` (BSD cat) — use `cat -v` for invisible chars.
- The sync script itself is NOT in the repo (lives in `~/.hermes/scripts/`) — the .gitignore layer is the only one that reaches GitHub; keep both.
