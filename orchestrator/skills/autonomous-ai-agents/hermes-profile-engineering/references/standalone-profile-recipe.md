# Standalone profile recipe — validated 2026-08-06 ("trader")

User demand: new profile for trading research, NEVER called by the orchestrator, direct-chat only, full research skill kit + Hermes admin skills, isolated mem0 memory.

## Result
`trader` profile: 20 skills, deepseek-v4-flash, mem0 isolated via `MEM0_USER_ID=trader-hermes`, SOUL.md in English with role rules (Nous web tools only, MT5 MCP preferred, old bot project = reference only).

## Exact steps that worked
1. `hermes profile create trader --no-skills --description "<role description>"` — output confirms: no bundled skills seeded, `.no-bundled-skills` marker auto-written (opts out of `hermes update` skill sync → NO opt-out step needed), NO config.yaml, NO API keys, starter SOUL.md (~513B), `.env` (~165B).
2. Keys: `grep -E "^(DEEPSEEK_API_KEY|MEM0_API_KEY)=" ~/.hermes/.env >> ~/.hermes/profiles/trader/.env` then `echo "MEM0_USER_ID=trader-hermes" >> ...`. NOTE: the start-anchored grep missed the MEM0_API_KEY line once (unknown line-format quirk, plain `grep -nE "MEM0"` found it); fallback that worked: extract by line number `sed -n '<N>p' ~/.hermes/.env >> target`.
3. Config (creates config.yaml from nothing): `hermes -p trader config set model.default deepseek-v4-flash` + `model.provider deepseek` + `memory.provider mem0` + `memory.memory_enabled true` + `memory.user_profile_enabled true`.
4. Skills: `cp -R` each curated skill dir from `~/.hermes/skills/<category>/<name>` into `~/.hermes/profiles/trader/skills/<category>/` preserving structure (mkdir -p first). Count verified by `find <T> -name SKILL.md | wc -l` → 20.
5. SOUL.md: English, official structure (Identity/Style/domain/Skills context-pointers/Learning/Avoid/Defaults), accent check `grep -cE '[áàâãéêíóôõúç]' SOUL.md` → 0.
6. Verify: `hermes profile list` shows trader + model; `COLUMNS=400 hermes -p trader skills list` → exactly the kit, all enabled, "0 hub-installed, 0 builtin, 20 local".

## Mem0 isolation — plugin-verified
`plugins/memory/mem0/__init__.py` (build_config, ~lines 94-99): `env_user_id = os.environ.get("MEM0_USER_ID"); if env_user_id: config["user_id"] = env_user_id`. Without MEM0_USER_ID, user_id falls back to the gateway-native id → ALL profiles share the same store (default `hermes-user`; checked: none of the 5 team profiles set it). Setting MEM0_USER_ID per profile = storage-level isolation, strictly better than relying on "don't search each other's memories". Also read from `$HERMES_HOME/mem0.json` if present.

## Why no orchestrator config needed
Orchestrator delegates ONLY via `kanban_create --assignee <profile>` — a profile with no tasks is never called. Standalone profiles don't need kanban init, MCPs, or gateway. The `--description` still helps the profile list readability but routing is by explicit assignee.

## Pitfalls hit (all real this session)
- **Secret masking can leak**: `sed -E 's/^([[:space:]]*)([A-Za-z_]+)([[:space:]]*=).*/.../'` FAILED to mask and printed the raw `MEM0_API_KEY` value into terminal output (which lands in conversation context). Fix: use the simple `s/=.*/=<set>/` mask, or test the mask against a dummy line first. Never trust a complex sed to mask.
- **macOS has no `cat -A`** (BSD cat) — use `cat -v` for invisible chars.
- `grep -oE "^[A-Z_]+="` missed a line that `grep -nE "NAME"` found in the same file — when a start-anchored pattern misses a known line, extract by line number instead of fighting the pattern.
- `--no-skills` profiles have NO config.yaml: `hermes -p <name> config set ...` creates it — do NOT hand-edit or assume defaults match the team (model was the first thing to set).
