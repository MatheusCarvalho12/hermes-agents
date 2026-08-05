# MCP & Tool Recipes (per-profile, verified)

Concrete working configs from the first full multi-profile setup (frontend/backend/database/designer + default orchestrator).

## MCP servers (per profile, via `hermes -p <profile> mcp add`)

| MCP | Command | Env | Notes |
|---|---|---|---|
| context7 | `npx -y @upstash/context7-mcp` | `CONTEXT7_API_KEY` (free tier, optional but better rate limits) | docs for any lib, up to date — the user's LAW |
| morph | `npx --prefer-offline -y @morphllm/morphmcp` | `MORPH_API_KEY` (paid: ~$0.80/1M tokens) | WarpGrep = `codebase_search` + `github_codebase_search`; also `edit_file` (fast apply) + `reflex_*` tools |
| shadcn | `npx shadcn@latest mcp` | none | official shadcn MCP; also covers React Bits via its registry |
| reactbits | `npx reactbits-dev-mcp-server` | none | community (ceorkm), 135+ animated components |

Keyed MCPs REQUIRE `--env KEY=VAL` at add time or the server "connects but reports no tools" (auth missing). Mirror the key into the profile's `.env` too. All MCP adds need `echo y |` for the "Enable all N tools?" prompt.

## Per-profile distribution (as approved by user)

- **frontend-developer**: MCPs context7 + morph + shadcn + reactbits. Skills: shadcn, frontend-design (Anthropic), accessibility, responsive-design, performance (Addy Osmani), lighthouse (onnokh, via raw URL + `--name`), vitest (antfu), react-testing-library, react-doctor (from its repo), security-review + code-review (both devs), sentry-react-sdk, nm-pensive-test-review, view-transitions, scroll, spline-interactive, r3f-animation.
- **backend-developer**: MCPs context7 + morph. Skills: fastapi (official), http-api (clawhub), api-design-principles (wshobson), ruff (Astral official), sqlalchemy-alembic-expert-best-practices-code-review (wispbit), sentry-python-sdk / sentry-sdk-setup / sentry-fix-issues (official), security-review + code-review, nm-pensive-test-review.
- **database-developer**: MCP morph (+ context7 added later). Skills: postgres-best-practices (Neon), bigquery-basics (Google).
- **designer**: no MCPs. Skills: design-tokens, design-principles, design-system, figma (OpenAI, trusted), typography.
- **default** (orchestrator): no code skills. Skills: grilling (Matt Pocock), planning-and-task-breakdown (Addy Osmani). NO http-api (mistakenly installed without `-p` once — always pass `-p`).

## System tools (span all profiles)

- **RTK** (Rust Token Killer, brew): `HERMES_HOME=~/.hermes/profiles/<name> rtk init --agent hermes` per profile → plugin `rtk-rewrite` (hook pre_tool_call) compresses terminal output. Needs ripgrep.
- **Gitleaks** (brew): plain CLI; add "run `gitleaks detect` before commit" to dev SOUL.mds (front + back; NOT dba per user).
- **React Doctor** (npx react-doctor@latest): CLI + skill from `millionco/react-doctor/.agents/skills/react-doctor` (skill scans lint/a11y/bundle/architecture — NOT runtime perf; that's Lighthouse).

## Hub audit notes (official sources preferred)

- `skills-sh/fastapi/fastapi/fastapi`, `skills-sh/getsentry/sentry-for-ai/*`, `skills-sh/shadcn/ui/shadcn`, `skills-sh/google/skills/bigquery-basics`, `skills-sh/neondatabase/postgres-skills/*`, `skills-sh/astral-sh/claude-code-plugins/ruff`, `skills-sh/antfu/skills/vitest`, `skills-sh/openai/skills/figma` (trusted), `skills-sh/addyosmani/web-quality-skills/{accessibility,performance}`, `skills-sh/anthropics/skills/frontend-design`, `skills-sh/anthropics/knowledge-work-plugins/code-review`.
- clawhub identifiers: install with `clawhub/<name>` prefix (e.g. `clawhub/http-api`, `clawhub/nm-pensive-test-review`); bare names fail with "No exact match" and `inspect` may not resolve them even when install works. Some clawhub identifiers never resolve (e.g. cinematic-scroll) — fall back to an alternative skill.
- Scanner (skills-guard) blocks community skills with "caution verdict" (html_comment_injection / unpinned_npm_install) even for reputable sources (Addy Osmani, Sentry) → `--force -y` after vetting the source.
- Anthropic repo gotchas: no `code-review`/`frontend-ui`/`http-api` in `anthropics/skills` under those names — frontend-ui → `frontend-design`; code-review is in `anthropics/knowledge-work-plugins`; skill-creator exists there but user prefers NOT installing it (market skill as reference method only).

## CLI quirks hit this session

- **`hermes skills uninstall` does NOT accept `-y`** ("unrecognized arguments: -y") — pipe `echo y | hermes skills uninstall <name>` (install accepts `-y`; uninstall does not).
- **Kanban toolset is gated**: `hermes tools enable kanban` → "Unknown toolset". The check reads top-level config `toolsets: [kanban]` (see `_profile_has_kanban_toolset` in tools/kanban_tools.py). Do NOT set `toolsets` blindly — it may replace the default tool bundle. The CLI (`hermes kanban create/list/comment --assignee <profile>`) is fully functional without the toolset; gateway must be running (`hermes gateway start`, launchd-supervised) or tasks stay `ready` forever.
- **Front × designer handoff** (user-approved rule): designer owns the design system (branding, tokens, master components, new screens with visual direction); frontend implements everything with autonomy INSIDE the system. For a new screen: create TWO kanban tasks and link the designer one as PARENT (`kanban_link`) of the frontend one — the front task only becomes ready when the design is done. Front returns to designer only for (a) new screens needing visual direction or (b) design-system/branding changes. Orchestrator mediates any disagreement — never open-ended designer↔frontend discussion.
- **Zero-cost frontend animation/3D skills** (user approved, all free): view-transitions (native View Transitions API), scroll (scroll-driven CSS), r3f-animation (React Three Fiber, open source), spline-interactive (Spline — freemium app; paid features out for now). Each gets a trigger line in the frontend SOUL.md.
