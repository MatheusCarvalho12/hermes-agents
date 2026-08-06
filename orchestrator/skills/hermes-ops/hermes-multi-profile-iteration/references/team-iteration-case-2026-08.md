# Case: Multi-profile team iteration — 2026-08-05

Case study from a full grilling → rework → validation cycle on the user's Hermes
team (orchestrator `default` + 4 workers: frontend-developer, backend-developer,
database-developer, designer).

## What was wrong (audited facts)

- Workers' SOUL.md were ~55-99 lines in pt-BR with a manual 30-trigger skill
  table ("OBRIGATÓRIAS PONTOUAIS"), a big Verificação section, and Context7 LEI
  blocks. Duplicated across profiles; stale (one trigger referenced a skill
  that didn't exist — `reactbits` was MCP-only).
- Profiles had been cloned with the full default skill set (~90 skills) and
  disabled in config — files still on disk.
- 3 grilling skills duplicated and divergent (`grilling/`, `y/grilling/`,
  `y/grill-me/` stub).
- No AGENTS.md in any project; project conventions lived in SOUL.md.
- The `default` profile had 63 skills but no formal triggers; specialized
  profiles had triggers but not all active skills mapped.

## Grilling decisions (user-approved)

- Scope = full rework (SOUL + SKILL + distribution + AGENTS.md + cleanup).
- Gatilho = frontmatter description (native Hermes mechanism) + task body.
- humanizer / i-have-adhd = style rules, NOT load-always.
- Verification = AGENTS.md per repo + 1 line in SOUL (no new verification skill).
- Kit per profile = skills with triggers today + humanizer + i-have-adhd.
- New profiles: `--no-skills` + install kit (not clone-then-disable).
- Consolidate grilling to the newest mattpocock rounds version.
- Default profile untouched (orchestrator is FAZ-TUDO).

## SOUL v2 — applied template (frontend example, English)

```markdown
# Identity / # Style / # Role Rules / # Scope Discipline / # Skills / # Avoid / # Defaults
```

Role Rules include: componentize everything (why), execute designer's system
(why), verify before done with evidence, Context7 before any API.
Scope Discipline: touch ONLY files the body authorizes; list files before
coding; stop-and-ask to expand scope; time-box (small ≤10 min, big ≤30 min).

## Validation evidence

1. **StatusBadge test task** (old SOUL leftovers vs new): worker loaded 10/10
   requested skills, wrote a WCAG contrast invariant test, closed protocol.
2. **Big dashboard task** (22 min, 29 files, 4x protocol_violation) — root
   cause: model API 503/ReadTimeout when context hit ~57k tokens. NOT worker
   disobedience.
3. **Vertical tickets via to-tickets**: T1 stack+e2e (3 min), T2 fix (2 min),
   T3 lighthouse+checklist (11/11) — all closed cleanly.
4. **Stress test**: 4 profiles in parallel (S1 designer spec, S2 db function,
   S3 API endpoint, S4 SEO/a11y), file-boundary contracts, all done, verified
   cross-check DB ↔ API (34,698 achados / 42 críticos matched).

## Per-profile kit tables (after cleanup)

| Profile | Active skills |
|---|---|
| frontend (23) | shadcn view-transitions spline-interactive r3f-animation scroll frontend-design accessibility responsive-design performance lighthouse vitest react-testing-library playwright docker chrome-devtools agent-browser nm-pensive-test-review react-doctor security-review code-review sentry-react-sdk humanizer i-have-adhd |
| backend (16) | api-design-principles api-testing code-review fastapi http-api humanizer i-have-adhd pytest ruff security-review sentry-fix-issues sentry-python-sdk sentry-sdk-setup sqlalchemy-alembic-expert-best-practices-code-review test-review |
| database (6) | bigquery-basics humanizer i-have-adhd postgres-best-practices sql |
| designer (8) | DesignSystem design-principles design-tokens figma humanizer i-have-adhd typography |

hermes-administration is disabled in each worker via save_disabled_skills.

## Mattpocock skills installed (2026-08, via hermes skills install)

to-tickets to-spec triage wayfinder codebase-design domain-modeling
diagnosing-bugs improve-codebase-architecture handoff prototype tdd code-review
grill-with-docs to-questionnaire teach wait-what.
Blocked by scanner (dangerous): ask-matt (agent_config_mod),
writing-for-agents (4 findings), setup-matt-pocock-skills (5 findings).

## Operational traps hit (validated)

- `echo y | hermes -p <p> skills opt-out --remove` — without the pipe, marker
  written but nothing deleted.
- humanizer is bundled → removed by opt-out → re-copy from default's
  creative/humanizer.
- `hermes skills install <id>` without `-y` → "Installation cancelled."
- `npx skills@latest add mattpocock/skills` installs to Codex/system, not
  Hermes — use `hermes skills install "skills-sh/mattpocock/skills/<cat>/<name>"`.
- `rtk uv run uvicorn` fails to spawn uv; hermes venv PYTHONPATH contaminates
  project venvs → `env -u PYTHONPATH ~/.local/bin/uv run ...`.
- uvicorn without --reload serves old routes: new endpoint 404 until restart;
  kill -9 the old PID (SIGTERM may not stop it).
- `db.connection.get_connection()` is sync psycopg2 — not awaitable.
