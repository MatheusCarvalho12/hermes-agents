---
name: cloudflare-deploy
description: 'Deploy Cloudflare via wrangler: Workers, Containers, Pages.'
---

# Cloudflare Deploy (wrangler)

Deploy e operação de Worker + Containers + Pages + secrets via `wrangler` CLI, validado em produção real (Flowmex V1, 2026-08-07) com CI quebrado — todo deploy é manual.

## Pré-requisitos
1. Credenciais: `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` via `op read` do 1Password (NUNCA em argv/output).
2. `npx wrangler` (versão do package-lock do repo; `npx wrangler@latest` se precisar de comando novo).
3. Validar acesso: `npx wrangler whoami` (mostra a conta do token).

## Deploy de Worker + Containers (o passo crítico)
1. **SEMPRE `--config <arquivo> -e <env>`**: `npx wrangler deploy --config wrangler.production.jsonc -e production`.
   - ⚠️ PITFALL CRÍTICO (validado: quebrou produção): deploy SEM `-e production` sobe o TOP-LEVEL do config (sem vars, sem containers) e o worker passa a responder `{"error":"gateway_configuration_error"}` HTTP 500 em TODAS as rotas. Correção: re-deploy com `-e production` (o worker volta em ~1 min).
2. Containers (Cloudflare Containers/Durable Objects) são buildados DURANTE o deploy (~5-7 min; output só aparece no fim — não matar o processo).
3. Após o deploy: `curl <workers.dev>/healthz` (ou o health path real — ver `HEALTH_PATH` no código, ex.: `/healthz` não `/health`) → esperar `200 {"status":"ok"}`.
4. Estado dos containers: `npx wrangler containers list` (estado/instâncias) e `containers info <id>` (imagem, health: `healthy` pode estar 0 enquanto instância sobe). Nomes podem ser legados (ex.: `...staging-fastapicontainer-staging` é o container que PRODUÇÃO usa) — não confiar no nome, conferir `LAST MODIFIED`/health.
5. Secrets: `op read "op://Vault/Item/campo" | npx wrangler secret put NOME --config wrangler.production.jsonc` — valor via stdin, nunca em argv. O deploy falha se alguma secret listada em `secrets.required` não existir — criar ANTES do deploy.

## Deploy de Pages (frontend)
1. Build com a env correta: `VITE_FLOWMEX_API_BASE_URL=<url-viva> npm run build` (a var é OBRIGATÓRIA em prod — sem ela o build passa mas o app abre com tela de erro de config).
2. `npx wrangler pages deploy dist --project-name <nome>` (projeto listado via `wrangler pages project list`).
3. Validar: `wrangler pages deployment list --project-name <nome>` — o deployment ativo é o `Environment=Production` + `Branch=main` + commit mais recente; `curl <projeto>.pages.dev` 200 e bundle contém a URL da API nova (grep no JS servido).

## Domínios
- Sem custom domain configurado, o domínio real é `<worker>.workers.dev` (workers_dev:true). Verificar DNS antes de assumir custom domain (`dig` — domínio documentado pode estar morto: ex.: `gateway.flowmex.com.br` sem registro).
- Custom domains são configurados fora do wrangler (dashboard) — não adicionar ao config sem prova de DNS.

## Verificação pós-deploy
- healthz 200 + um endpoint real (401 = rota viva exigindo sessão; 500 = config quebrada; 404 = path errado — conferir prefixo real, ex.: `/api/v1/...`).
- `wrangler containers list` com instâncias live.
- Deployment do Pages em Production.

## Pitfalls
- `--config` é obrigatório quando o arquivo se chama `wrangler.<env>.jsonc` (o wrangler procura `wrangler.jsonc`/`wrangler.toml` por padrão — erro "No environment found").
- `npm ci` pode falhar no pacote de containers (`@cloudflare/containers`) se node_modules não existir — instalar antes do deploy.
- Build de container gera log com `tail -40` no fim; o progresso real (Pushed/Modified application) só aparece no final.
- Deploy de worker NÃO rebuilda containers automaticamente se só o worker mudou; o container é atualizado quando o deploy `-e <env>` roda com o config que o referencia.
