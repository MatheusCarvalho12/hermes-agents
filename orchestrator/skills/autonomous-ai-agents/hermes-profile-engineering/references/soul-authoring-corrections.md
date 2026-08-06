# SOUL authoring corrections — round 2026-08-06 (user, 3× corrections)

Session: architecture rework + Matt Pocock skills + 5 SOULs audited with writing-for-agents.
User corrected the SAME class of mistake 3× in one session. Read this BEFORE touching any MD.

## 1. Language: SOUL/SKILL are ALWAYS English (correction #3, loudest)

User verbatim: "Tu botou em português mano, que porra que tu tá fazendo... parece que tu esqueceu tudo de quando a gente fez o seu MD."
- Approved decision Q16 (grill session): SOUL.md 100% ENGLISH, market standard. pt-BR only as a BEHAVIOR RULE inside the doc ("responda ao usuário em pt-BR humanizado"), never as document language.
- Check before finishing: `grep -cE '[áàâãéêíóôõúç]' <SOUL.md>` must return 0.
- The compact 2-line `# Learning` section I wrote in pt-BR was the trigger — keep even tiny additions in English.

## 2. Method: dual-skill editing is MANDATORY (correction #2, standing rule)

- `hermes-agent-skill-authoring` = NATIVE Hermes skill (author: Hermes Agent, in `.bundled_manifest`) — validates FORMAT (frontmatter, name ≤64, description ≤1024, structure, size limits). Without it, Hermes may not load the doc.
- `writing-for-agents` = mattpocock skill (installed manually 2026-08-06, scanner-blocked but user-authorized) — improves WRITING: context pointers, leading words, information hierarchy, no no-ops, no duplication.
- Rule: creating/auditing/editing SOUL.md, AGENTS.md, SKILL.md = BOTH skills together. Not replacement — combination.
- The user also set: `writing-for-agents` ALWAYS when creating/auditing a profile or its MDs. Never touch what Hermes does under the hood — the skill is for OUR docs.

## 3. Size: SOUL stays lean (correction #1, earlier in session)

- First I added a 10-line `# Learning` section (bloat), user: "adicionou 10 linhas no Soul. Precisa?" → compressed to 2 lines.
- Lean target: ~50-79 lines per SOUL. Sections: Identity / Style / Role Rules / Learning / Scope Discipline / Skills (context pointers) / Avoid / Defaults.

## 4. Memory hygiene: local vs mem0 (correction, user angry)

User verbatim: "Porra, pelo amor de Deus, usa ele [mem0]... O memory.md é para coisa muito pontual... usa o externo aí para essas memórias de verdade... separado por projeto, por agente."
- MEMORY.md local = ONLY tiny universal learnings (1-2 lines each), injected every session, hard ~2.2k char limit. NEVER project facts.
- mem0 (external) = durable facts: projects, decisions, preferences, history, separated by project/agent. Practically unlimited.
- Migrated this session: 5 facts to mem0, MEMORY.md 2070 → 687 bytes.
- Workers also learn: add `# Learning` (2 lines) to worker SOULs — they have `memory_enabled: true` + mem0 key but the mechanism is inert without instruction (audit: 0 memory/skill_manage calls in 5 tasks before the section existed).

## 5. ask-matt ALWAYS (orchestrator flow)

- Every new user demand → `skill_view ask-matt` → follow the flow it points to (grill-with-docs → to-spec → to-tickets → implement).
- ONLY exception: user asks for speed ("faz isso rápido", "faz agora") → skip ask-matt, execute directly and fast.
- Recorded in default SOUL.md section `# Fluxo` items 5-6 + mem0.

## 6. Skills section format = context pointers (writing-for-agents applied)

Before (no-op prose): "Your skill list loads every session with a one-line trigger per skill. Scan it at the start of every task and load every skill whose trigger matches: ..." — the list is already injected; telling the agent to scan changes nothing.
After (context pointers): `- **frontend-design** → new screen/page/visual component` — trigger on the left, condition on the right. One trigger per branch, no synonym duplication. Applied to all 5 SOULs.

## Scanner note (dangerous verdict)

- `ask-matt` (rule `agent_config_mod`) and `writing-for-agents` (4 findings) are BLOCKED by `hermes skills install`; `--force` does NOT override a dangerous verdict.
- User is the owner and explicitly authorized both → installed manually by copying SKILL.md from the mattpocock repo into `~/.hermes/skills/<name>/`. Transparent about it; do NOT bypass the scanner without user authorization.
- `setup-matt-pocock-skills` also blocked (5 findings) — to-tickets works without it (local `.scratch/` tracker fallback).
