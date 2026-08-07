# Deploy manual de produção — Cloudflare/wrangler (validado 2026-08-07, flowmex)

Quando o CI está quebrado o orquestrador deploya na mão. Fluxo completo e pitfalls em `cloudflare-deploy-ops` (SKILL + references/flowmex-production-deploy.md + scripts/verify-pages-bundle-string.sh). Resumo dos pontos que custaram downtime:

1. **NUNCA `wrangler deploy --config X.jsonc` sem `-e production`** — o deploy usa o TOP-LEVEL do config, sobe o worker SEM as vars de produção → `{"error":"gateway_configuration_error"}` 500 em TODAS as rotas (healthz inclusive). Recovery imediato: `wrangler deploy --config X.jsonc -e production` (corrige vars + rebuilda containers; build ~5 min → background com notify).
2. **Config não auto-descoberto**: `wrangler.production.jsonc` não é lido sem `--config`.
3. **`@cloudflare/containers` ausente** → `npm ci` no apps/gateway resolve (lock tem a dep).
4. **Worker deploy ≠ container deploy**: confirmar com `wrangler containers list` (LAST MODIFIED novo) + `containers info <id>` (healthy >= 1). Nome do container pode ser legado (`...staging-fastapicontainer-staging`) — o deploy -e production atualiza o existente.
5. **Secrets do worker**: `op read ... | wrangler secret put NAME --config X.jsonc` (stdin, nunca argv). Conferir `secret list` antes do deploy (falta de secret required quebra o deploy).
6. **Validação pós-deploy**: rotas 401 = vivas / 404 = path errado (prefixo real costuma ser `/api/v1/...`; webhooks podem ser `/api/...` — conferir) / 500 config = deploy sem env. `openapi.json` pode estar desabilitado — usar grep no source para achar paths.
7. **Front Pages**: build exige `VITE_FLOWMEX_API_BASE_URL` com URL que REALMENTE responde (domínios custom documentados no repo podem estar mortos — validar com curl/dig). Deploy: `wrangler pages deploy dist --project-name <proj>`; confirmar com `pages deployment list` (Environment Production + branch main). Prova de código no ar: buscar string única de UI do autor em TODOS os assets (chunks lazy!) — script `verify-pages-bundle-string.sh`.
8. **Migration de banco gerenciado (Neon)**: `alembic current` read-only antes de qualquer `upgrade head`; Neon do flowmex estava no head 0038. URL `postgresql://` → `postgresql+psycopg://` para SQLAlchemy direto.
