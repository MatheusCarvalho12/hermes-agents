---
name: hermes-multi-profile-iteration
description: "Use when rethinking multi-profile SOUL/skill architecture."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [hermes, profiles, soul, skills, kanban, validation, multi-agent]
    related_skills: [hermes-profile-engineering, kanban-orchestration, hermes-administration, to-tickets, grilling]
---

# Hermes Multi-Profile Iteration

Field-tested loop for RETHINKING and VALIDATING the architecture of a Hermes
multi-profile team (orchestrator + specialized workers): SOUL.md shape, how
skills get invoked, per-profile skill kits, and what to do when a worker "doesn't
follow the protocol". Complements `hermes-profile-engineering` (setup) and
`kanban-orchestration` (delegation/recovery) with the validation loop and the
root-cause diagnostic for protocol violations.

## When to Use

- User wants to rethink SOUL.md / SKILL.md architecture of their agent team
- Workers have skills installed but don't seem to use them ("OBRIGAR ELES A USAR")
- A kanban task shows `protocol_violation` (rc=0 without kanban_complete) repeatedly
- Per-profile skill kits are bloated (cloned everything, disabled in config)
- User asks "is the new SOUL actually going to be followed?"

## Hard Rule: Test, Don't Trust

A SOUL.md that "looks right" proves nothing. The only evidence a SOUL works is a
REAL kanban task executed under it:

1. Draft the SOUL (show the user first — they require draft-then-approve)
2. Create a small real task whose body demands the skill triggers (e.g. "load
   every skill whose trigger applies, list them in the summary")
3. Worker runs → measure: which skills loaded, did it close the protocol, time
4. Verify the DELIVERY yourself (build/tests/browser) — never trust self-report
5. Iterate the SOUL until the worker behaves; only then replicate to other profiles

Validated 2026-08: frontend SOUL v2 (English, ~45 lines vs 99) → worker loaded
10/10 requested skills and closed the protocol; the same worker previously
"ignored" a 30-trigger manual table.

## SOUL v2 Pattern (what worked)

Minimal SOUL in ENGLISH (user: "skill é em inglês"), sections:
`# Identity` → `# Style` → `# Role Rules` → `# Scope Discipline` → `# Skills` →
`# Avoid` → `# Defaults`.

- **Triggers live in the skill's frontmatter `description`** (Hermes injects
  name+description of every skill into each session; the model auto-loads by
  trigger). A manual trigger table in SOUL.md duplicates this, goes stale, and
  bloats the system prompt — cut it to ONE short paragraph of the 5-8 most
  important triggers.
- humanizer / i-have-adhd are STYLE rules (write humanized pt-BR, ADHD format),
  not "load at start of every task" — put them in #Style, don't force-load.
- context7 / morph are MCPs (habits), not skills to "carregar".
- Verification pre-done lives in the repo's AGENTS.md (per-project), with one
  line in SOUL pointing there. Not a big Verification section per profile.
- **Scope Discipline section is mandatory**: "touch ONLY files the body
  authorizes; list files before coding; STOP and ask via kanban comment to
  expand scope; time-box exploration (small ≤10 min, big ≤30 min)". This killed
  the #1 time-killer: a worker turning a 1-component task into a 20-file rewrite.
- End every task body with "CHAME kanban_complete OBRIGATORIAMENTE ao terminar"
  (even then, workers may die before it — see diagnosis below).

## Protocol Violation Diagnosis (rc=0 without kanban_complete)

Symptom: task shows `protocol_violation` / `gave_up` after N runs; each run
exited cleanly without calling kanban_complete. **Do NOT assume the worker is
disobedient.** Check the kanban log tail FIRST:

```
hermes kanban log <task> | tail -60 | grep -v heartbeat
```

Look for: `HTTP 503 ... capacity limits`, `stream drop (ReadTimeout) after
~600s`, `Connection error`, `API failed after 3 retries`. Root cause found
2026-08: the model API dropped mid-run when the task context ballooned
(~40-57k tokens) — the run died BEFORE it could call kanban_complete. The
recovery (comment + kanban_complete after verifying delivery) is in
`kanban-orchestration`.

**The durable fix is task sizing, not worker discipline:** break big work into
VERTICAL tickets that each fit in one fresh context window — use the
`to-tickets` skill (tracer-bullet vertical slices, blocking edges). Validated:
a 22-min 29-file task crashed 4x with protocol_violation; the same work as
small tickets (T1 stack+e2e, T2 fix, T3 lighthouse) closed cleanly in 2-3 min
each. Small ticket → low context → API stable → protocol closes.

## Per-Profile Kit Curation

Goal: profiles contain ONLY the skills they actually use ("só ter de fato nos
profiles as skills que eles vão usar").

1. Kit = the skills that have a trigger in the current SOUL (user-validated),
   plus humanizer + i-have-adhd (style skills used by every worker).
2. Clean with `echo y | hermes -p <profile> skills opt-out --remove` — deletes
   UNMODIFIED bundled skills; keeps hub/local. **Without the `echo y |` pipe it
   writes the marker but deletes nothing** (silent no-op).
3. `humanizer` is bundled → the opt-out removes it → re-copy manually:
   `cp -r ~/.hermes/skills/creative/humanizer ~/.hermes/profiles/<p>/skills/creative/`
4. Disable unwanted LOCAL skills (e.g. `hermes-administration` cloned into
   workers) via the `save_disabled_skills` script — see hermes-administration.
5. Verify with `COLUMNS=400 hermes -p <p> skills list | grep enabled`.

New profiles should be created `--no-skills` and installed with only the kit,
instead of clone-then-disable.

## Pitfalls

- `npx skills@latest add <owner/repo>` installs into Codex/system skills, NOT
  into Hermes (`~/.hermes/skills/`). Use `hermes skills install
  "skills-sh/<owner>/<repo>/<path>"` for Hermes. (User ran npx skills add and
  nothing appeared in Hermes.)
- `hermes skills install <id> -y` is more reliable than `echo y |`.
- Scanner can block mattpocock skills (`ask-matt` dangerous: agent_config_mod;
  `writing-for-agents` 4 findings). Respect the verdict by default, BUT the
  user (owner) may explicitly override and authorize install anyway — then copy
  the SKILL.md manually (`curl -s <raw-github-url> -o
  ~/.hermes/skills/<name>/SKILL.md`) with full transparency that the scanner
  flagged it. Validated 2026-08: user mandated ask-matt (demand router) and
  writing-for-agents (MD authoring) despite dangerous verdicts — installed
  manually on his call; both worked.
- `rtk uv run ...` fails ("Failed to spawn process") and the hermes venv
  PYTHONPATH contaminates project venvs (pydantic_core mismatch). Use
  `env -u PYTHONPATH ~/.local/bin/uv run ...`.
- A running uvicorn without `--reload` serves OLD routes — after adding an
  endpoint, restart the server or the curl returns 404 "Not Found" on the new
  path (and the delivery check falsely fails). Kill via `kill -9 <pid>` (SIGTERM
  may not stop it).
- After `opt-out --remove`, the old `grilling/` copy may remain alongside the
  newer `y/grilling/` — consolidate to ONE (keep the newest mattpocock rounds
  version), move the old one to `<name>.old-<date>` (reversible) rather than
  deleting.

## References

- `references/team-iteration-case-2026-08.md` — full case: grilling decisions,
  SOUL v2 drafts, kit tables per profile, stress-test results (4 profiles in
  parallel), mattpocock skill catalog installed.
