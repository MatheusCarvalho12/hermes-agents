---
name: hermes-team-operations
description: "Use when delegating to Hermes worker profiles."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [hermes, profiles, kanban, soul, memory, orchestration, workers]
    related_skills: [kanban-orchestration, hermes-profile-engineering, hermes-multi-profile-ops, hermes-administration, to-tickets, grill-me]
---

# Hermes Team Operations

Field-validated operating rules for running a team of specialized Hermes profiles
(orchestrator `default` + worker profiles: frontend-developer, backend-developer,
database-developer, designer) that the user actually runs day to day. This skill
carries the USER-CORRECTED conventions that keep the team from needing constant
steering — the things the user has complained about more than once.

Complements `kanban-orchestration` (task mechanics) and `hermes-profile-engineering`
(profile setup). Where this skill differs: it captures the **delivery protocol,
authoring standards, and memory architecture** the user demanded after repeated
corrections, plus the root-cause diagnosis for the classic "worker doesn't close
the protocol" failure.

## When to Use
- Delegating work to profiles via kanban and preparing the handoff
- Reviewing a worker's delivery (summary, evidence, protocol closure)
- Writing or editing SOUL.md / SKILL.md files for any profile
- Choosing where to store a fact (local memory vs mem0 vs project repo)
- A worker task ended blocked/gave_up with protocol_violation
- Setting up a new profile, kit, or team-wide convention
- **Routing a NEW user demand** (ask-matt) or **auditing/authoring MDs**
  (writing-for-agents) — see convention 0 below.

## Hard Conventions (user-corrected — do not regress)

### 0. Demand routing + MD authoring (user decision 2026-08)
- **ask-matt is MANDATORY for every new user demand** routed through the
  orchestrator: load `ask-matt`, follow the flow it points to
  (grill-with-docs → to-spec → to-tickets → implement). This is the router
  the user explicitly wants used by default, every time.
- **ONLY exception: speed.** When the user says "faz isso rápido" / "faz
  agora" / priority is velocity — skip ask-matt and execute directly, as fast
  as possible. Everything else routes through it.
- **writing-for-agents is MANDATORY** whenever creating, auditing, or editing
  SOUL.md, AGENTS.md, SKILL.md, or any doc an agent consumes — including
  auditing the team's existing MDs. It is for OUR docs; never touch what
  Hermes manages under the hood.

### 1. SOUL.md / SKILL.md authoring (corrected 3x)
- **Language: ALWAYS English.** pt-BR is reserved for the rule *"respond to the
  user in Brazilian Portuguese, humanized"* inside Style. Never write SOUL/SKILL
  bodies in Portuguese. The user's UI copy is pt-BR humanized; the agent's
  instruction files are English.
- **Size: short.** SOUL ~45-60 lines; SKILL 8-15k chars. If a new section makes
  the SOUL balloon, compress to the minimum that changes behavior. A 2-line
  section is better than 10 lines of prose. The user explicitly rejected both a
  99-line SOUL and a 10-line "Learning" section.
- **Method: use `hermes-agent-skill-authoring`** (never "edit from the head").
  Show a draft in chat and get explicit OK before writing to disk. Confirm
  frontmatter/format for SKILL.md files.
- **Where conventions live:** SOUL.md = identity/voice/role rules (always
  injected). Task body = per-delivery obligation ("USE skills X, Y"). AGENTS.md
  per repo = project commands/conventions (created on demand). Skills = trigger
  via frontmatter description + procedure. Project details NEVER go in skills or
  memory — they go in the repo (docs/README).

### 2. Memory architecture (user-corrected hard)
- **mem0 (external) = durable facts**: projects, decisions, preferences, history,
  per-agent/per-project context. Call `mem0_search` before answering anything
  context-dependent; `mem0_add` for durable facts. This is the primary memory.
- **MEMORY.md local = ONLY tiny universal rules** that must be visible every
  turn (≤ a few hundred chars). NOT project facts, NOT history, NOT task state.
  If a fact is about a project, it goes to mem0 or the repo — never MEMORY.md.
- **USER.md local = universal user preferences** (TDAH style, grill-me for
  decisions, skill-authoring for edits) — this is the right place for those.
- Workers learn too: give every worker SOUL a short `# Learning` section:
  "Learned something universal in a task (habit/pitfall)? Save it with the
  memory tool. Project detail → repo. Repeated pattern → propose a skill
  (confirm with orchestrator)."

### 3. Delivery / finalization protocol (user-corrected)
1. Worker finishes task → **verify REAL delivery** (build, tests, browser,
   curl) — never trust self-report alone.
2. **Bring the stack up for the user to SEE**: front (vite) + back (uvicorn)
   on localhost, open preview. The user wants to look before anything ships.
3. **PR/merge ONLY after explicit user approval** ("pode fazer"). If the user
   says "don't merge/PR", don't.
4. After merge: **squash merge, delete local + remote branch** (zero clutter),
   `git reset --hard origin/main` on local main.
5. Stop leftover dev servers/processes when done (user hates processes left
   running); the kanban gateway stays.

## Root-Cause Diagnosis: "worker doesn't call kanban_complete"

Classic symptom: task shows `blocked` / `gave_up` with
`protocol_violation (rc=0 without kanban_complete)`.

**Do NOT assume disobedience.** The most common real cause is the MODEL API
dying mid-run:
- Check the END of the kanban log: look for `HTTP 503 capacity limits`,
  `nous stream drop (ReadTimeout) after ~600s`, `Connection error`,
  `API failed after 3 retries`.
- The worker was working normally; the run died before it could call
  `kanban_complete`. rc=0-without-complete is a symptom, not the disease.

**Fix: small vertical tickets (to-tickets pattern).** A task too big for one
context window inflates context (30-60k tokens) and makes long runs die. Split
into tracer-bullet vertical slices, each sized for a single fresh context
window. Small runs close the protocol on their own (measured: 2-6 min vs 22+).

## Parallel Multi-Profile Execution

- Multiple workers CAN run the same repo simultaneously if task bodies declare
  **file-boundary contracts**: `designer → docs/**`, `database → db/**`,
  `backend → api/** + tests/**`, `frontend → frontend/**`. Zero conflicts when
  boundaries are explicit in the body.
- Cross-worker contracts (e.g. DB creates SQL function → backend consumes it):
  define the exact signature/contract in BOTH bodies so they run in parallel
  without depending on each other; backend can use an inline fallback and
  report it.
- Monitor with background watcher (`watch-kanban-tasks.sh`) AND check in
  periodically — user wants active monitoring, not only notify-on-complete.

## Evidence Requirements That Actually Work

- **Context7**: "consult Context7" as a soft rule is ignored. The rule that
  works: *in the task summary, cite what Context7 confirmed (library + version
  consulted)*. No citation → orchestrator returns the task. Checkable
  completion criteria change behavior; vague requirements don't.
- **Skills loaded**: worker summary must list skills it loaded; missing list →
  return the task.
- **"Done" = evidence**: build output, test pass, browser screenshot, curl
  response. Never "I think it works".

## Speed: Verification Layering

- Each small task running the FULL battery (lighthouse + e2e + react-doctor +
  screenshots) is what makes simple changes feel slow (measured: 20 min for a
  4-line CSS change).
- Small task → quick verification (tests + build + lint). Full battery →
  at PR time. Keep the discipline, drop the per-task duplication.
- Time-box exploration: small ≤10 min, big ≤30 min of reading before code.

## Pitfalls
- Writing SOUL/SKILL in Portuguese (corrected 3x — the language rule above).
- Adding a section to SOUL/SKILL in a language other than English even when
  compressing (the "Learning" section was first bloated to 10 lines, then
  written in pt-BR — both rejected; final: 2 lines in English).
- Letting MEMORY.md grow with project facts (it fills 2200 chars and the
  `memory` tool refuses adds; migrate to mem0).
- Blaming the worker for protocol_violation without reading the END of the log.
- Creating a task with a huge scope and expecting the worker to close the
  protocol (context dies → crash).
- Leaving temp/scratch files (verify-*.ts, *_tmp.*, capture-*.ts) in commits —
  workers must clean up; orchestrator should gitignore them too.
- `rtk uv` breaks (pydantic_core mismatch from inherited PYTHONPATH) — use
  `env -u PYTHONPATH` + `uv` directly for project venvs.

## Verification
- Worker summary has skill list + Context7 citation (when API/lib used).
- Stack comes up for the user; they approve before merge.
- Repo clean after merge: only main, no leftover branches/processes.
- SOUL files: English, short, drafted + approved before write.

See `references/datalake-mega-session.md` for the concrete case study
(dashboard refactor, stress test, protocol fix) this skill was distilled from.
