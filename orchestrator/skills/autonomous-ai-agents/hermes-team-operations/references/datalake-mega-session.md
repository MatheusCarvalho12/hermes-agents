# Case Study: datalake-mega (Mega Logística 360) — 2026-08-05

Concrete session this skill was distilled from. Repo: `VanguardIA-Tech/datalake-mega`
(dashboard React+TS / FastAPI / Postgres). Team: default (orchestrator) + 4 workers.

## Timeline of what was validated

1. **SOUL v2 rollout**: 4 profiles converted from 99-line Portuguese SOULs with
   30-trigger tables to ~45-60 line English SOULs (Identity → Style → Role Rules →
   Learning → Scope Discipline → Skills → Avoid → Defaults). Kits curated:
   front 23, back 16, db 6, designer 8 skills (from ~90 cloned). Cleanup via
   `hermes skills opt-out --remove` + reinstall hub skills; `humanizer` is
   bundled so it must be re-copied manually from default's skills dir.

2. **StatusBadge proof task** (small): took 22 min — scope creep (20 files
   outside task) + repeated WCAG contrast calculations. Lesson: task bodies must
   declare file boundaries; exploration must be time-boxed.

3. **Dashboard redesign task** (big): 4 runs crashed with protocol_violation.
   Root cause was NOT worker disobedience — end of log showed the model API
   dying (`HTTP 503 capacity limits`, `ReadTimeout after ~600s`, Connection
   error) after context grew to ~57k tokens. Fix: to-tickets vertical slicing.

4. **to-tickets chain** (T1/T2/T3): 3 small vertical tickets — all closed the
   protocol on their own in 2-6 min. T1: stack+baseline e2e (3 min, 5/5 e2e).
   T2: fix to green (2 min, nothing to fix). T3: lighthouse + spec checklist
   (11/11 criteria, scores 99-100 desktop, 91+ mobile).

5. **Stress test** (S1-S4, parallel): designer → docs/**, database → db/**,
   backend → api/**+tests/**, frontend → frontend/**. All 4 done, zero
   conflicts. Cross-worker contract: S2 created SQL function
   `duplocheck_resumo_mensal` → S3 consumed with inline fallback; verified
   matching numbers (34,698 findings / 42 critical) both sides.

6. **User visual feedback**: KPI cards content was touching card edges (no
   internal padding), panel titles were raw English ("Loading / unloading"),
   findings list fetched 500 and sliced 100 without lazy load. Fixed in one task
   with before/after screenshots as evidence. Spec §5.2 updated to mandate
   internal padding + Z-pattern.

7. **Context7 evidence test**: soft rule "Context7 is law" was ignored across
   4 tasks (0 mentions). Changing to "cite what Context7 confirmed in the
   summary, no citation = task returned" worked immediately — the very next
   task cited library/doc/version.

## Key measurements
- Small vertical ticket: 2-6 min, closes protocol on its own.
- Big single-scope task: 20-22 min, crashes mid-run (API 503/timeout), needs
  recovery.
- Full verification battery per small task ≈ 10+ min of the 20-min total; the
  4-line CSS fix alone was fast, the battery wasn't.
- `rtk uv run` fails with pydantic_core mismatch (inherited PYTHONPATH from the
  hermes-agent venv); `env -u PYTHONPATH` + `uv` direct works.

## PRs merged (squash, branches deleted)
- #4 dashboard redesign, #5 KPI padding + pt-BR titles + lazy load,
  #6 /api/health/libcheck (Context7-verified).
