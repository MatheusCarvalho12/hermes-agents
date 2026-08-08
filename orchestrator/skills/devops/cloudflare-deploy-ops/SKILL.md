---
name: cloudflare-deploy-ops
description: 'Cloudflare deploys with wrangler (workers/containers/Pages).'
---

# Cloudflare Deploy Ops

Deploying to Cloudflare (Workers, Containers, Pages) manually with wrangler — the CI is broken or the project deploys by hand. Validated 2026-08-07 on Flowmex production (worker `flowmex-gateway`, FastApiContainer, SiscargaProxyContainer, Pages project `flowmex`).

## Credentials
- `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` from 1Password (item "Secrets Cloudfare Flowmex": fields `Api-token`, `Account-id`). Export without printing; `npx wrangler whoami` to validate.
- Never put secrets in argv. For worker secrets: `op read "op://Hermes/<item>/<field>" | npx wrangler secret put NAME --config <cfg>` (value goes via stdin, output shows only Success).
- Wrangler is not necessarily installed globally — `npx wrangler ...` works; `npm ci` in the app dir pins the lockfile version.

## CRITICAL pitfalls (each cost production downtime once)
1. **`wrangler deploy --config cfg.jsonc` WITHOUT `-e <env>` uses the TOP-LEVEL of the config, not the env block.** If the real deployment lives in `env.production`, a deploy without `-e production` uploads a worker WITHOUT the production vars → every route (healthz included) returns `{"error":"gateway_configuration_error"}` HTTP 500. Recovery: immediately `wrangler deploy --config cfg.jsonc -e production` (this deploy fixes vars AND rebuilds containers).
2. **Config files named `wrangler.production.jsonc` are NOT auto-discovered** — wrangler only auto-loads `wrangler.jsonc`/`wrangler.toml`. Always pass `--config`.
3. **`@cloudflare/containers` missing in node_modules** → deploy fails `Could not resolve "@cloudflare/containers"`. Fix: `npm ci` in the gateway dir (the lockfile has it).
4. **Containers are only managed when the `containers` block sits inside the env being deployed.** A working deploy prints `Modified application <worker>-<class>-production`. Verify with `npx wrangler containers list` (LAST MODIFIED should be now) and `containers info <id>` (`health.instances.healthy`; healthy 0 = degraded). Container names may be legacy (e.g. `flowmex-gateway-staging-fastapicontainer-staging`) — the env deploy updates the existing container; don't panic at the name.
5. **Worker deploy ≠ container deploy.** `wrangler deploy -e production` output shows "Deployed flowmex-gateway triggers" AND "Modified application ...-production"; if only the triggers line appears, containers were not touched.
6. **Cold start pós-deploy: rotas do container dão 404/erro temporário por ~25-30s.** O worker (healthz) volta a responder 200 na hora, mas o container FastAPI novo ainda está subindo — rotas NOVAS respondem 404 (ou timeout curl 000/28) nessa janela. NÃO concluir "rota não existe" sem antes aguardar ~30s e re-testar (o teste final: rota nova responde 401 = existe; 404 persistente após 2 tentativas com intervalo = problema real).

## Deploy sequence (validated)
1. `npx wrangler whoami` (auth check).
2. `npx wrangler secret list --config wrangler.production.jsonc` — confirm every `secrets.required` name exists; add missing ones via `op read ... | npx wrangler secret put NAME --config wrangler.production.jsonc`.
3. `npx wrangler deploy --config wrangler.production.jsonc -e production` — background with notify (container image build takes ~5 min).
4. Validate: `curl https://<worker>.workers.dev/healthz` → 200 ok; `containers list` (fresh LAST MODIFIED); `containers info` (healthy >= 1).

## Pages (frontend)
- Build: `cd apps/frontend && npm ci && VITE_FLOWMEX_API_BASE_URL=<real-api-url> npm run build`. Production requires the var; use the URL that ACTUALLY responds — custom domains documented in repo scripts may be dead (verify with `curl`/`dig` before building).
- Deploy: `npx wrangler pages deploy dist --project-name <proj>` — becomes a Production deployment when the current branch equals the project's production branch (main). Confirm with `npx wrangler pages deployment list --project-name <proj>` (Environment Production + branch main + recent timestamp).
- Validate code actually live: fetch the HTML, then grep the served bundles for a unique UI string from the feature. Lazy-loaded routes live in separate chunks — search ALL assets, not just index. Script: `scripts/verify-pages-bundle-string.sh`.

## Verifying backend routes are live (401/404/500 triage)
- `401` = route exists (auth required) — good.
- `404` = route does not exist (wrong path; check the real prefix — API may be `/api/v1/...` while a webhook is mounted at `/api/...`).
- `500 {"error":"gateway_configuration_error"}` = worker deployed without env vars (pitfall 1).
- `openapi.json` may be disabled — don't rely on it; grep the source for `@router.get` paths and curl them directly.

## Managed DB migration check (e.g. Neon)
- Before touching production DB: run `alembic current` (read-only) against the real connection string from 1Password. If already at head, do nothing — never run `upgrade head` without checking `current` first.
- Convert `postgresql://` → `postgresql+psycopg://` when using SQLAlchemy directly with the Neon string.

## Flowmex specifics
See `references/flowmex-production-deploy.md` (real names, vault items, domains, exact commands).
