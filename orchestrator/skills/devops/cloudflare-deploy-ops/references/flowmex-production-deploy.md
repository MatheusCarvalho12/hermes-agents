# Flowmex production deploy — facts validated 2026-08-07

CI is broken; deploys are manual via wrangler. Repo: devflowmex/flowmex (apps/gateway = Cloudflare Worker + Containers; apps/frontend = Vite → Pages).

## Real names / URLs
- Worker: `flowmex-gateway` → `https://flowmex-gateway.matheuscarvalho.workers.dev` (healthz path: `/healthz`).
- ⚠️ `gateway.flowmex.com.br` and `api.flowmex.com.br` have NO DNS (dead) — the repo's `validate-pages-deployment.mjs` documents them anyway. Real front build uses `VITE_FLOWMEX_API_BASE_URL=https://flowmex-gateway.matheuscarvalho.workers.dev`.
- Containers (Cloudflare): `flowmex-gateway-siscargaproxycontainer-production` (2 inst) + `flowmex-gateway-staging-fastapicontainer-staging` (legacy name; this IS the prod FastAPI container, updated by `-e production` deploy).
- Pages project: `flowmex` → `flowmex.pages.dev` (production branch = main).
- Front production origin allowed by worker CORS: `https://flowmex.pages.dev`.

## 1Password (vault Hermes)
- `Secrets Cloudfare Flowmex` = `ppt3a6rtzg42xtgw2shj5u5nla` → `Api-token`, `Account-id` (CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID).
- `Flowmex staging` = `qt2gasua4xmzgk4rw2lxigochy` → PLUGBOLETO_*, FLOWMEX_BILLING_PLUGBOLETO_WEBHOOK_SECRET, FLOWMEX_BILLING_PLUGBOLETO_WEBHOOK_DEDUPE_SECRET, TEST_CNPJ (= 57371674000110, NOT a real PlugBoleto cedente).
- `Banco de dados Flowmex` = `5l2tcno7z4y7rzl65lpwztw3ke` → field `Connection string` (Neon: `postgresql://neondb_owner:...@ep-shiny-dust-acilckht-pooler.sa-east-1.aws.neon.tech/...`). Alembic was already at head `0038_billing_exchange_flag` (2026-08-07).
- GitHub: `MatheusCarvalho12` (gh authed).

## Exact commands
```bash
export OP_SERVICE_ACCOUNT_TOKEN=$(python3 -c "import re; l=[x for x in open('/Users/amaterei/.hermes/.env') if 'OP_SERVICE_ACCOUNT_TOKEN' in x][0]; print(re.search(r'ops_[A-Za-z0-9_\-]+', l).group(0))")
export CLOUDFLARE_API_TOKEN=$(op read "op://Hermes/ppt3a6rtzg42xtgw2shj5u5nla/Api-token")
export CLOUDFLARE_ACCOUNT_ID=$(op read "op://Hermes/ppt3a6rtzg42xtgw2shj5u5nla/Account-id")
cd ~/dev/flowmex-v1/apps/gateway
npx wrangler whoami
npx wrangler secret list --config wrangler.production.jsonc
op read "op://Hermes/qt2gasua4xmzgk4rw2lxigochy/FLOWMEX_BILLING_PLUGBOLETO_WEBHOOK_SECRET" | npx wrangler secret put FLOWMEX_BILLING_PLUGBOLETO_WEBHOOK_SECRET --config wrangler.production.jsonc
npx wrangler deploy --config wrangler.production.jsonc -e production   # NEVER without -e production
npx wrangler containers list && npx wrangler containers info <ID>
# front:
cd ~/dev/flowmex-v1/apps/frontend && npm ci
VITE_FLOWMEX_API_BASE_URL=https://flowmex-gateway.matheuscarvalho.workers.dev npm run build
npx wrangler pages deploy dist --project-name flowmex
npx wrangler pages deployment list --project-name flowmex
# Neon migration check (read-only first):
export FLOWMEX_DATABASE_URL=$(op read "op://Hermes/5l2tcno7z4y7rzl65lpwztw3ke/Connection string")
cd ~/dev/flowmex-v1/apps/api && env -u PYTHONPATH .venv/bin/python -m alembic current
```

## PlugBoleto webhook (TecnoSpeed)
- Cadastro: `POST https://plugboleto.com.br/api/v1/webhooks` (produção only). Headers: `cnpj-sh`, `token-sh`, `cnpj-cedente` (real cedente CNPJ — TEST_CNPJ fails with `Cedente não encontrado` 401). Body: `{ativo, url, eventos{registrou,liquidou,baixou,protestou,alterou,rejeitou}, headers{auth:<WEBHOOK_SECRET>}}`. Consulta: `GET /api/v1/webhooks` with same headers (⚠️ response body ECHOES the auth header value — don't leak it into chat/logs).
- Real cedente for Flowmex (2026-08-07): IGCD `46.972.197/0001-21` (found via Neon query on empresas; cedentes table was EMPTY, 0 convênios configured).
- Endpoint receiver (V1): `POST /api/webhooks/plugboleto` (mounted at `/api`, no session auth, header `auth` == FLOWMEX_BILLING_PLUGBOLETO_WEBHOOK_SECRET, hmac.compare_digest; 503 not_configured; 401 invalid; unknown tipoWH → 200 ignored; orphan idintegracao → 200 accepted; dedupe_key `plugboleto_wh:` + HMAC-SHA256(dedupe_secret, tipoWH|idintegracao) on billing_outbox unique constraint).

## Route verification triage (prod)
- `/api/v1/companies`, `/api/v1/processes`, `/api/v1/processes/facets`, `/api/v1/finance/accounts/<id>/movements`, `/api/v1/clients`, `/api/v1/receivables/operations` → 401 (live). `openapi.json` is disabled (0 paths) — don't use it.

## Mainô credentials re-registration (incident 2026-08-07)
- Symptom: sync jobs fail with `credential_missing` (IGCD) / `projection_error` (others) in `maino_sync_state` + `flowmex_maino_sync_jobs`; UI error "o maino nao consegue atualizar as notas da empresa".
- Root cause: `empresa_maino_credentials.credentials_enc` (AESGCM, key = `MAINO_CRED_KEY` in "Flowmex staging" item = worker secret `FLOWMEX_BILLING_MAINO_CREDENTIAL_KEY`) was encrypted with a LOST key → `InvalidTag` decrypt on ALL 17 rows (test: decrypt blob with vault key, check AESGCM tag).
- Fix (validated, all via API):
  1. Align worker secret with vault key: `op read "op://Hermes/qt2gasua4xmzgk4rw2lxigochy/MAINO_CRED_KEY" | npx wrangler secret put FLOWMEX_BILLING_MAINO_CREDENTIAL_KEY --config wrangler.production.jsonc` + redeploy `-e production` (~6 min; secrets only apply after redeploy).
  2. Re-register credentials: `POST /api/v1/maino-credentials` (AdminSession; body `{"credentials":[{application_uid,email,password}]}`). Service authenticates EACH credential against Mainô and maps companies by CNPJ automatically → `configured_count: 17, unmatched_cnpjs: [], rejected_indices: []`.
  3. Source of credentials: FILE "CHAVES API MAINÔ (1).txt" inside 1Password item "Chaves de API Mainô" (`x7ii723dq4vu5f2i2a6eebv3oe`, file id `rq45mv4bkyqsqqya6a7gz5zst4` — `op read` by NAME with accents returns empty; use the file id) + item "Mainô — IGCD" (`4tdj67dwz6yfx3ghrcnbt27w3y`: Application UID/username/password) + TUKTUK/RLS accounts in the same "Chaves de API Mainô" item.
  4. Validate: `POST /api/v1/maino-sync` per company (Idempotency-Key header REQUIRED; body `{"empresa_id":"emp-..."}`) → 202 + job_id; poll `GET /api/v1/maino-sync/{job_id}` → `terminal_status: completed`; confirm `maino_sync_state.status='completed'` for all 17 and `notas_fiscais` count growing.
- Lesson: when stored credentials "don't work" for every company at once, suspect the ENCRYPTION KEY (lost/rotated), not the credentials themselves — decrypt-test with the vault key before re-entering anything.
