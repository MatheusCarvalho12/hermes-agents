# MCP Servers & RTK — per-profile setup (verified Aug 2026)

All commands target one profile with `hermes -p <profile> ...`; each profile owns its
`mcp_servers` config and its own `.env`.

## Adding an MCP server (stdio)

```bash
echo y | hermes -p <profile> mcp add <name> \
  --env KEY=VAL \                       # server API key — REQUIRED for key-gated servers
  --command npx \
  --args -y @vendor/pkg                # --args must be the LAST option
```

- After connecting, Hermes lists the discovered tools and prompts
  `Enable all N tools? [Y/n/select]`. Without piped input the add is CANCELLED
  (context7 showed "Cancelled."; morph "Save config anyway?").
- `--env KEY=VAL` lands in `mcp_servers.<name>.env` in the profile's config.yaml
  (the standard MCP mechanism, per Morph's own docs). Keep the same key in the
  profile's `.env` too.
- Verify: `hermes -p <profile> mcp list` (status ✓ enabled) and
  `hermes -p <profile> mcp test <name>` (shows connected + tool names).
- MCP tools load only in a NEW session of that profile.

## Known servers used by this user

| Server | Command | Key | Notes |
|---|---|---|---|
| context7 | `npx -y @upstash/context7-mcp` | `CONTEXT7_API_KEY` (optional, free tier) | up-to-date lib docs; tools: `resolve-library-id`, `query-docs` |
| morph | `npx --prefer-offline -y @morphllm/morphmcp` | `MORPH_API_KEY` (~$0.80/1M tok) | WarpGrep = tools `codebase_search` (local) + `github_codebase_search`; also `edit_file` (fast apply), `reflex_*`. Needs ripgrep (`brew install ripgrep`) for local search. SDK TS/Node-only; Python via raw API protocol |

`hermes mcp catalog` (Nous-approved one-click) did not list either — manual add is the path.

## RTK — Rust Token Killer (token-saving CLI proxy)

- Install: `brew install rtk` (single Rust binary, `rtk --version`).
- Hermes integration is native:
  ```bash
  rtk init --agent hermes     # default profile: writes ~/.hermes/plugins/rtk-rewrite + enables in config.yaml
  HERMES_HOME=~/.hermes/profiles/<name> rtk init --agent hermes   # per extra profile
  ```
- Plugin `rtk-rewrite` (hook `pre_tool_call`) rewrites terminal commands before
  execution (`git status` → `rtk git status`, `ls` → `rtk ls`, `pytest` → `rtk pytest`…),
  cutting up to 90% of bash output the agent reads. Effective on next session.
- `rtk init --help` shows all supported agents (`--agent hermes` is one of them).
- Test after restart: `git status` should come back compact; `rtk gain` shows the savings dashboard.
