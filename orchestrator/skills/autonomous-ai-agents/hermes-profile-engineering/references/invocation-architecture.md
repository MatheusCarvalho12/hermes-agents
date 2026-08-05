# Architecture rework — decision tree (grill-me session, 2026-08-05)

Live status: **tree COMPLETE (Q1–Q17 answered) and EXECUTION IN PROGRESS on frontend-developer**. Full design confirmed by user; replication to other 3 profiles waits for the validation-loop result (SOUL v2 test task `t_1fde025e`).

## Goal (user, verbatim)
"Só ter de fato nos profiles as skills que eles vão usar e OBRIGAR ELES A USAR pq parece que não tá sendo usada."

## Settled decisions

### Q1 — Scope: **C** (full architecture: SOUL + SKILL + per-profile distribution + AGENTS.md + dedup)

### Q2 — Pains, in order: **a, b, c** (invocation → SOUL bloat → polluted profiles), "vamos por partes"

### Q3 — Where the skill trigger lives: **4 (hybrid)** — frontmatter `description` (native trigger, injected every session at Level 0 progressive disclosure) + kanban task body (per-delivery mandatory skills). SOUL.md loses its trigger table.

### Q4 — Enforcement: **3 + 4** — task body says "USE skills: X, Y, Z" and worker must prove in summary; SOUL keeps only a lean start-of-task ritual (3 items, not 30). Auto-reporte stays but validates what the task asked, not a generic list.

### Q5 — "OBRIGATÓRIAS SEMPRE" corrected by user:
- humanizer → ONLY for site copy / messages to people (conditional trigger, NOT always)
- i-have-adhd → ONLY when responding to the user (style rule, not a skill to load)
- context7 → the real always-habit, but it's an MCP — becomes a tools-section rule, not "skill to load"

### Q6 — SOUL shape: **2 (lean SOUL with role rules)** — Identity/Style/Avoid/Defaults (~30 lines) + 5–8 role rules that can't live in a skill (front×designer ownership, immediate formatting on backend). Trigger table and verification blocks LEAVE the SOUL.

### Q7 — Where pre-PR verification goes: **1 + 2** — repo conventions (commands, build, docker compose, what to test) → AGENTS.md; the exact verification sequence → a per-role skill. SOUL keeps one line "rode a skill de verificação antes do done".
User's concern (accepted): repos without AGENTS.md (or where one can't be created) must not break. Layered model answers it: SOUL always loaded → task carries the obligation → AGENTS.md only when workspace points at the repo → skill fires on trigger. Missing AGENTS.md is a convenience gap, not a dependency.

### Q8 — AGENTS.md creation: **2 (on demand)** — create per repo the first time that repo is worked on ("toda vez que for um repo que tu nunca viu, a gente faz"). Start with the active repo (mega/datalake-mega).

### Q9 — New profiles: **clean + bespoke** — `--no-skills` + install only the curated kit ("limpo e fazemos sob medida").

### Q10 — Existing profiles: **1** — `hermes skills opt-out --remove` + reinstall curated kit.

### Q11 — Duplicated grilling skills: **consolidate to the most recent mattpocock version** (rounds/frontier — `y/grilling`), delete `grilling/` (old one-at-a-time) and `y/grill-me/` (stub). NOTE: duplicate name `grilling` already caused skill_view ambiguity error this session.

### Q12 — default/orchestrator profile: **1 (KEEP as-is)** — 63 skills, FAZ-TUDO role; never the risk surface.

### Q13 — Per-role verification skill: **c (do NOT create)** — verification lives in AGENTS.md (commands) + 1 line in SOUL ("rode a verificação antes do done"). Create a skill only if 2 real repos show repetition.

### Q14 — Curated kit per profile = **the skills that already have triggers in today's SOUL** (user validated them one by one) + humanizer + i-have-adhd. Kit table: `templates/soul-v2-worker.md`.

### Q15 — Execution order: **confirmed** (1 consolidate grilling → 2 clean profiles → 3 reinstall kit → 4 rewrite SOULs with skill-authoring, draft shown first → 5 AGENTS.md on demand).

### Q16 — SOUL language: **English** (market standard; user: "não vejo skill em português, tinha que tá tudo em inglês"), keeping only the rule "responda pt-BR ao usuário". Q17 — **test real antes de replicar** (task de prova, medir, iterar).

## Execution status (2026-08-05, frontend-developer done)

1. **SOUL v2 aplicado** no frontend (45 linhas inglês; era 99 pt). Backup: `SOUL.md.bak-20260805-175231`. Draft aprovado pelo usuário antes de aplicar.
2. **Limpeza**: `echo y | hermes -p frontend-developer skills opt-out --remove` → ~70 bundled removidas. **Pitfall real**: sem o pipe `echo y |`, o comando grava o marker e NÃO apaga nada ("Marker kept; no skills deleted").
3. **humanizer é bundled** → saiu na limpeza; reposto via `cp -r ~/.hermes/skills/creative/humanizer <profile>/skills/creative/` (está no kit).
4. **hermes-administration sobreviveu** (skill local) → desabilitada via `save_disabled_skills` (script do hermes-administration) rodado com `HERMES_HOME=<profile>` + venv do hermes-agent.
5. **Kit final frontend**: 23 skills ativas via `COLUMNS=400 hermes -p frontend-developer skills list` (21 kit + humanizer + i-have-adhd; hermes-administration disabled).
6. **Task de prova criada**: `t_1fde025e` (StatusBadge component no datalake-mega frontend/) — desenhada para disparar frontend-design, accessibility, shadcn, vitest, lighthouse, nm-pensive, react-doctor, code/security-review. Monitor: `watch-kanban-tasks.sh`.
7. **Próximo**: medir skills carregadas no summary + entrega real (build/testes/branch) → iterar SOUL se preciso → só então replicar SOUL v2 + kit nos outros 3 perfis (backend, database, designer).

## Facts established during audit (don't re-derive)

- Default SOUL.md (orchestrator) = 45 lines, no skill-trigger section, 63 active skills.
- Workers: frontend SOUL = 99 lines / 7.7KB (biggest offender), backend 90 lines; designer/database leaner (~55/68).
- Every profile cloned ~90 skills from default; `skills.disabled` in each profile's config trims at runtime but FILES REMAIN ON DISK.
- Dead trigger found: frontend SOUL lists skill `reactbits` — it exists only as an MCP, not as a skill. Trigger table rot is real.
- Zero AGENTS.md / .hermes.md / CLAUDE.md under ~/dev (checked maxdepth 2) — repo conventions currently live only in SOULs (wrong layer per docs).
- 77 skill groups physically duplicated across profiles (from earlier audit session @session:default/20260805_165719_2742f7).
- Native docs facts (hermes-agent.nousresearch.com/docs/user-guide/features/skills + /personality):
  - Level 0 skills_list() → name+description of ALL skills, ~3k tokens, injected every session; full content only on demand (progressive disclosure).
  - SOUL.md = identity slot #1, voice only; repo conventions belong in AGENTS.md ("if it follows you everywhere → SOUL.md; if it belongs to a project → AGENTS.md").
  - `--no-skills` at profile create; `hermes skills opt-out` / `opt-out --remove` / `opt-in --sync` with `.no-bundled-skills` marker; `--remove` deletes only UNMODIFIED bundled skills.

## Next step after Q9–Q12 answered
Present final design (whole tree) to user, get confirmation, THEN execute (per user's standing rule: draft in chat first, never write SOUL/SKILL files unprompted). Execution involves: rewrite 4 worker SOULs lean, write frontmatter descriptions as triggers, create AGENTS.md on first-touch repos, clean profiles, consolidate grilling skills, adjust default SOUL flow if needed.
