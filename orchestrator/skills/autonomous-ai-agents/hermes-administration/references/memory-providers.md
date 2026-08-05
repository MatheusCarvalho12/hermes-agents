# Memory Providers — mem0 deep dive

Source-verified against `<repo>/plugins/memory/mem0/` (install location: `$HERMES_HOME/hermes-agent/plugins/memory/mem0/`).

## mem0 — three modes

| Mode | Needs | Cost | Setup |
|---|---|---|---|
| `platform` (DEFAULT) | `MEM0_API_KEY` from https://app.mem0.ai (free tier exists) | free tier / paid | Manual: `hermes config set memory.provider mem0` + key in `~/.hermes/.env`; or `hermes memory setup` → mem0 → Platform |
| `oss` | own LLM + embedder + vector store (qdrant, etc.) | free | `hermes memory setup` → Open Source; extra packages installed by the flow (qdrant-client, psycopg2-binary, ollama) |
| `selfhosted` | running mem0 server (default port 8888, `X-API-Key` auth; omit key only for AUTH_DISABLED servers) | free | `hermes memory setup` → Self-hosted server; uses `/search` and `/memories` routes |

Config lives in `$HERMES_HOME/mem0.json` (behavioral settings — mode, host, rerank, etc.). Only the secret belongs in `.env`.

## Internals (from plugins/memory/mem0/__init__.py)
- `mode` defaults to `"platform"`; override via env `MEM0_MODE` or mem0.json
- `api_key` resolved with `get_secret("MEM0_API_KEY")`; required in platform mode
- Backend precedence: `oss` > `host` (selfhosted) > `platform`
- Per-platform isolation: memory channel defaults to `"cli"` unless a platform context is passed

## Tools the provider adds (new session only — /reset required)
- `mem0_search` — semantic search; `rerank` optional (platform mode only, default off)
- `mem0_add` — store fact verbatim, no LLM extraction
- `mem0_update` — update by `memory_id` + `text`
- `mem0_delete` — delete by ID
- `mem0_list` — list all memories; `page`/`page_size` (default 100, max 200)

The `mem0ai` package auto-installs when the provider is activated.

## CLI
- `hermes memory setup [provider]` — interactive picker (TTY only); passing a provider name skips the picker but still prompts
- `hermes memory status` — show current provider config
- `hermes memory off` — disable external provider, back to built-in only
- `hermes memory reset` — ERASES built-in memory (MEMORY.md and USER.md) — destructive, confirm first

## Other providers
honcho, openviking, hindsight, holographic, retaindb, byterover — same slot: only one external provider active at a time, built-in always runs alongside.
