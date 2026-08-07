# Local stack Flowmex V1 — teste real de ponta a ponta

Validado 2026-08-07: conexão Mainô REAL (API maino.com.br 200), registro de webhook PlugBoleto REAL (200), seção Integrações renderizada no browser com status reais. Usar quando o usuário pedir "testa de verdade, usa, vê se funciona".

## 1. Env vars — config.py usa `env_prefix="FLOWMEX_"`

Secure note "Flowmex staging integrations" (`op://Hermes/qt2gasua4xmzgk4rw2lxigochy`) tem nomes SEM prefixo — mapear (senão o Settings ignora silencioso):

| Vault (sem prefixo) | Config (env correta) |
|---|---|
| MAINO_BASE_URL | FLOWMEX_BILLING_MAINO_BASE_URL |
| MAINO_CRED_KEY | FLOWMEX_BILLING_MAINO_CREDENTIAL_KEY |
| PLUGBOLETO_BASE_URL / TOKEN_SH / CNPJ_SH | FLOWMEX_BILLING_PLUGBOLETO_BASE_URL / TOKEN_SH / CNPJ_SH |
| OPENFINANCE_* | FLOWMEX_OPENFINANCE_* (+ FLOWMEX_OPENFINANCE_ENABLED=true) |
| SISCOMEX_* | FLOWMEX_SISCOMEX_* — MELHOR REMOVER para teste local (exige PROCESS_SYNC_ENABLED → fila) |
| TENANT_ORGANIZATION_ID | FLOWMEX_TENANT_ORGANIZATION_ID |
| webhook secrets | já vêm FLOWMEX_BILLING_PLUGBOLETO_WEBHOOK_SECRET / _DEDUPE_SECRET |

Extras:
- `FLOWMEX_DATABASE_URL=postgresql+psycopg://flowmex:flowmex@localhost:5432/flowmex` (driver psycopg 3 — asyncpg é rejeitado pelo validator).
- `FLOWMEX_BILLING_INTEGRATIONS_LIVE=true` (providers HTTP reais) exige R2 (abaixo).
- R2: o campo notesPlain do item "R2 flowmex-files S3" é um TOKEN da Cloudflare, NÃO o endpoint S3. S3 creds = username/credential do item; endpoint = `https://<account_id>.r2.cloudflarestorage.com` (account id = campo username do item "Cloudflare Flowmex (scoped)"). Vars: FLOWMEX_OBJECT_STORAGE_ENDPOINT_URL / ACCESS_KEY / SECRET_KEY / BUCKET=flowmex / REGION=auto.
- PlugBoleto webhook URL: `FLOWMEX_PUBLIC_APP_URL` (a property `plugboleto_webhook_url` usa public_app_url; o campo `FLOWMEX_BILLING_PLUGBOLETO_WEBHOOK_URL` existe mas NÃO é usado pela property — bug, task T6). URL http://localhost → 403 da PlugBoleto.

## 2. Auth local

- Login admin real: `FLOWMEX_AUTH_EMAIL`/`FLOWMEX_AUTH_PASSWORD` = item "Flowmex" LOGIN (`op://Hermes/kqmvz42feaoxpp6tin5midtcie`) + `FLOWMEX_AUTH_SECRET` (gerar local) + `FLOWMEX_TENANT_ORGANIZATION_ID`.
- Dev do front: o vite em modo DEV loga sozinho com `dev@flowmex.local` / `flowmex-local-password` (sem tela de login) — setar AUTH_* com esses valores para testar UI.
- Bootstrap: cria o admin na tabela `flowmex_app_users` (prefixo!) no 1º login quando count()==0; depois disso, outro email → 401. Corrigir com UPDATE direto (hash via `flowmex.domain.app_users.hash_password`).

## 3. Subir a stack

```bash
# Back (checar porta primeiro: lsof -i :8000 — processo antigo responde openapi com poucas rotas)
cd apps/api && env -u PYTHONPATH .venv/bin/uvicorn flowmex.main:app --port 8000
# Front (rtk prefixa npm run dev → usar binário; CORS dev só aceita 5173 → strictPort)
cd apps/frontend && VITE_FLOWMEX_API_BASE_URL=http://localhost:8000 ./node_modules/.bin/vite --port 5173 --strictPort
```

Empresa de teste via API: `POST /api/v1/companies` exige header `Idempotency-Key`; body sem campos extras (status → 422 extra_forbidden). Cedente local: INSERT em `cedentes` (o UPDATE do connect afeta 0 linhas se não existir → status continua false).

## 4. Fluxo real de conexão (evidência)

- `POST /api/v1/maino-credentials/me?empresa_id=<id>` body `{application_uid,email,password}` → valida contra API Mainô real (log: `POST https://api.maino.com.br/api/v2/authentication 200`), 409 mismatch se CNPJ ≠ empresa da sessão. Credencial IGCD: item `op://Hermes/4tdj67dwz6yfx3ghrcnbt27w3y` — label "Application UID" (com espaço: op read falha silencioso) → usar field id `oxhzuvcc54k3cugcc6ivaryhua`.
- `POST /api/v1/integrations/plugboleto/connect?empresa_id=<id>` → registra webhook real; `GET .../status` → `{registered, cnpj, registered_at}` (colunas da migration 0039 em cedentes).
- Diagnóstico 403 vs 200 da PlugBoleto: curl direto com as MESMAS creds isola config do app (a causa foi a URL do webhook localhost).

## 5. UI (browser)

Login dev automático → Empresas → detalhe → seção Integrações (3 cards: Mainô/PlugBoleto/Open Finance) com status reais; botão "Conectar" do Mainô abre modal de 3 campos. Screenshot = evidência visual (o drawer tem scroll próprio: scrollar `div.min-h-0.flex-1.overflow-y-auto` via JS, não browser_scroll).
